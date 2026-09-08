#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Lint an OKF bundle against the specification and its own declared floor.

Wraps the vendored `okf_validate.py` rather than reimplementing it, and adds the
two things the specification leaves to a producer: the fields this bundle
requires beyond OKF's single mandatory `type`, and whether every concept is
reachable from an index.

Blocking scope is the point of the design. Given file arguments, only findings
in those files fail; everything else is still reported. A commit is then never
blocked by a file the author did not touch, which is what makes a whole-bundle
check tolerable in a pre-commit hook.

What may fail a run is deliberately narrow: the specification's hard rules, and
the fields the bundle's own floor declares. Everything OKF marks as guidance is
reported and never blocks, so the floor file remains the only place that decides
what a concept must carry. Broken links fall out of that rule rather than
needing an exception, and a bundle that publishes has a stricter gate anyway:
`mkdocs build --strict` refuses a link whose target is not among the built files.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

RESERVED = {"index.md", "log.md"}
VALIDATOR = Path(__file__).resolve().parent / "okf_validate.py"

MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


@dataclass
class Findings:
    blocking: list[str] = field(default_factory=list)
    reported: list[str] = field(default_factory=list)

    def add(self, path: str, message: str, *, blocks: bool) -> None:
        (self.blocking if blocks else self.reported).append(f"{path}: {message}")


def split_finding(text: str) -> tuple[str, str]:
    """Split the validator's `<relative path>: <message>` string into its parts.

    The report is a list of prose strings rather than records, so the path has to
    be recovered by splitting. A line without the separator keeps its whole text
    as the message and is attributed to the bundle itself, so an unrecognised
    emitter is reported rather than crashing the run.
    """
    path, separator, message = text.partition(": ")
    return (path, message) if separator else ("", text)


def run_validator(bundle: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(bundle), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        sys.exit(f"bundle_lint: could not read the validator's report\n{result.stderr}")


def concept_files(bundle: Path) -> list[Path]:
    return sorted(p for p in bundle.rglob("*.md") if p.is_file() and p.name not in RESERVED)


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, _, rest = text.partition("---\n")
    raw, sep, _ = rest.partition("\n---")
    if not sep:
        return {}
    try:
        return yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        return {}


def check_floor(bundle: Path, floor_file: Path, in_scope: Callable[[Path], bool], findings: Findings) -> None:
    try:
        declared = yaml.safe_load(floor_file.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        sys.exit(f"bundle_lint: cannot read the floor declaration {floor_file}: {exc}")
    required = declared.get("required") or []
    if not required:
        sys.exit(f"bundle_lint: {floor_file} declares no `required:` fields")

    for path in concept_files(bundle):
        rel = path.relative_to(bundle).as_posix()
        meta = frontmatter(path)
        for name in required:
            value = meta.get(name)
            if value is None or (isinstance(value, (str, list, dict)) and not value):
                findings.add(
                    rel,
                    f"floor: required field `{name}` is absent or empty",
                    blocks=in_scope(path),
                )


def check_coverage(bundle: Path, in_scope: Callable[[Path], bool], findings: Findings) -> None:
    linked: set[Path] = set()
    for index in bundle.rglob("index.md"):
        for raw_target in MARKDOWN_LINK.findall(index.read_text(encoding="utf-8")):
            target = raw_target.split("#")[0].strip()
            if not target or "://" in target:
                continue
            linked.add((index.parent / target).resolve())

    for path in concept_files(bundle):
        if path.resolve() not in linked:
            findings.add(
                path.relative_to(bundle).as_posix(),
                "coverage: not linked from any index.md",
                blocks=in_scope(path),
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bundle-root", required=True, type=Path)
    parser.add_argument("--floor", type=Path)
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args()

    bundle = args.bundle_root
    if not bundle.is_dir():
        sys.exit(f"bundle_lint: --bundle-root {bundle} is not a directory")
    if args.floor is not None and not args.floor.is_file():
        sys.exit(f"bundle_lint: --floor {args.floor} does not exist")

    # No file arguments means nothing is out of scope: everything blocks. With
    # them, the caller is a per-file hook and only the author's own files do.
    if args.files:
        scoped = {p.resolve() for p in args.files}

        def in_scope(path: Path) -> bool:
            return path.resolve() in scoped
    else:

        def in_scope(_: Path) -> bool:
            return True

    findings = Findings()
    report = run_validator(bundle)
    for text in report.get("errors", []):
        path, message = split_finding(text)
        findings.add(path, message, blocks=in_scope(bundle / path))
    # Only the specification's hard rules and the bundle's own floor may block.
    # Everything the validator marks as guidance is reported and nothing more,
    # so the floor file stays the single statement of what a concept must carry.
    for text in report.get("warnings", []):
        path, message = split_finding(text)
        findings.add(path, message, blocks=False)

    if args.floor is not None:
        check_floor(bundle, args.floor, in_scope, findings)
    if args.coverage:
        check_coverage(bundle, in_scope, findings)

    for line in findings.reported:
        print(f"  warn   {line}")
    for line in findings.blocking:
        print(f"  ERROR  {line}")

    if findings.blocking:
        print(f"\n{len(findings.blocking)} blocking finding(s) in {bundle}")
        return 1
    print(f"{bundle}: ok" + (f" ({len(findings.reported)} warning(s))" if findings.reported else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
