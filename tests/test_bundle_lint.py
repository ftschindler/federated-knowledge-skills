"""Unit tests for skills/fkb/scripts/bundle_lint.py.

Fast and deterministic (no LLM, no network, no git). Each test builds a throwaway
OKF bundle under tmp_path and runs the linter as a subprocess, the way a
pre-commit hook does, so both the exit code and the emitted report are covered.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_LINT = REPO_ROOT / "skills" / "fkb" / "scripts" / "bundle_lint.py"

pytestmark = pytest.mark.python_scripts

INDEX = '---\nokf_version: "0.2"\n---\n\n# Bundle\n\n'
LOG = "# Update Log\n\n## 2026-01-01\n\n- created\n"


def _concept(title: str, *, omit: str = "") -> str:
    """A concept whose frontmatter is warning-free, minus the omitted field."""
    fields = {
        "type": "note",
        "title": title,
        "description": f"About {title}.",
        "tags": "[example]",
        "status": "draft",
    }
    fields.pop(omit, None)
    lines = [f"{key}: {value}" for key, value in fields.items()]
    lines.append('generated:\n  by: "human:tester"\n  at: 2026-01-01')
    return "---\n" + "\n".join(lines) + f"\n---\n\n# {title}\n"


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _bundle(tmp_path: Path, files: dict[str, str], *, links: tuple[str, ...] = ()) -> Path:
    root = tmp_path / "bundle"
    root.mkdir(parents=True)
    body = "".join(f"- [{target}]({target})\n" for target in links)
    _write(root, "index.md", INDEX + body)
    _write(root, "log.md", LOG)
    for rel, text in files.items():
        _write(root, rel, text)
    return root


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    # The linter needs pyyaml. The test interpreter is often an ephemeral pytest
    # environment without it, in which case uv resolves the script's own inline
    # metadata instead. The shebang is never relied upon either way.
    if importlib.util.find_spec("yaml") is None:
        command = ["uv", "run", "--script", str(BUNDLE_LINT), *args]
    else:
        command = [sys.executable, str(BUNDLE_LINT), *args]
    return subprocess.run(command, capture_output=True, text=True, check=False)


def test_clean_bundle_passes(tmp_path: Path) -> None:
    """A conformant bundle must not cost the author a false failure."""
    root = _bundle(tmp_path, {"alpha.md": _concept("Alpha")})
    result = _run("--bundle-root", str(root))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok" in result.stdout


def test_concept_without_type_fails_and_is_named(tmp_path: Path) -> None:
    """`type` is OKF's one mandatory field, and the report has to say which file lacks it."""
    root = _bundle(tmp_path, {"alpha.md": _concept("Alpha", omit="type")})
    result = _run("--bundle-root", str(root))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "alpha.md" in result.stdout
    assert "ERROR" in result.stdout


def test_floor_field_blocks_only_when_declared(tmp_path: Path) -> None:
    """The floor is the bundle's own promise, so it must bind only when the bundle declares it."""
    root = _bundle(tmp_path, {"alpha.md": _concept("Alpha")})
    floor = tmp_path / "floor.yaml"
    floor.write_text("required:\n  - owner\n", encoding="utf-8")

    without = _run("--bundle-root", str(root))
    assert without.returncode == 0, without.stdout + without.stderr

    with_floor = _run("--bundle-root", str(root), "--floor", str(floor))
    assert with_floor.returncode == 1, with_floor.stdout + with_floor.stderr
    assert "`owner`" in with_floor.stdout


def test_missing_floor_file_is_an_error(tmp_path: Path) -> None:
    """A floor that silently vanished must fail loudly rather than degrade to no floor."""
    root = _bundle(tmp_path, {"alpha.md": _concept("Alpha")})
    result = _run("--bundle-root", str(root), "--floor", str(tmp_path / "absent.yaml"))
    assert result.returncode != 0
    assert "does not exist" in result.stderr


def test_missing_bundle_root_is_an_error(tmp_path: Path) -> None:
    """A mistyped bundle root must not read as an empty, therefore clean, bundle."""
    result = _run("--bundle-root", str(tmp_path / "absent"))
    assert result.returncode != 0
    assert "not a directory" in result.stderr


def test_file_arguments_scope_what_blocks(tmp_path: Path) -> None:
    """A commit must never be blocked by a file its author did not touch."""
    root = _bundle(
        tmp_path,
        {"good.md": _concept("Good"), "bad.md": _concept("Bad", omit="type")},
    )

    scoped_to_good = _run("--bundle-root", str(root), str(root / "good.md"))
    assert scoped_to_good.returncode == 0, scoped_to_good.stdout + scoped_to_good.stderr
    assert "warn" in scoped_to_good.stdout
    assert "bad.md" in scoped_to_good.stdout

    scoped_to_bad = _run("--bundle-root", str(root), str(root / "bad.md"))
    assert scoped_to_bad.returncode == 1, scoped_to_bad.stdout + scoped_to_bad.stderr
    assert "ERROR  bad.md" in scoped_to_bad.stdout


def test_broken_link_reports_without_blocking(tmp_path: Path) -> None:
    """OKF requires consumers to tolerate broken cross-links, so they inform and never block."""
    root = _bundle(
        tmp_path,
        {"alpha.md": _concept("Alpha") + "\nSee [gone](gone.md).\n"},
        links=("alpha.md",),
    )
    result = _run("--bundle-root", str(root), "--coverage")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "cross-link target not found" in result.stdout


def test_coverage_requires_a_link_from_some_index(tmp_path: Path) -> None:
    """An unlinked concept is unreachable knowledge, and any index.md is enough to reach it."""
    unlinked = _bundle(tmp_path / "a", {"alpha.md": _concept("Alpha")})
    result = _run("--bundle-root", str(unlinked), "--coverage")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "not linked from any index.md" in result.stdout

    linked = _bundle(tmp_path / "b", {"alpha.md": _concept("Alpha")}, links=("alpha.md",))
    result = _run("--bundle-root", str(linked), "--coverage")
    assert result.returncode == 0, result.stdout + result.stderr


def test_coverage_accepts_a_subdirectory_index(tmp_path: Path) -> None:
    """Nested sections carry their own index, and coverage has to count those links too."""
    root = _bundle(tmp_path, {"sub/beta.md": _concept("Beta")})
    _write(root, "sub/index.md", "# Sub\n\n- [beta](beta.md)\n")
    result = _run("--bundle-root", str(root), "--coverage")
    assert result.returncode == 0, result.stdout + result.stderr
