"""Unit tests for skills/fkb/scripts/fkb.

Fast and deterministic (no LLM, no network, no git). Each test builds a throwaway
bundle and a throwaway manifest under tmp_path, pointing `XDG_CONFIG_HOME` at it,
and runs the CLI as a subprocess the way a person or an agent would.

The test that matters most is the last one. The design's constraint is one
implementation behind two entry points - a bundle's standalone pre-commit hook,
and this CLI - and a constraint nothing checks is a wish. So the two are run over
the same broken file and their findings compared.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "skills" / "fkb" / "scripts"
FKB = SCRIPTS / "fkb"
BUNDLE_LINT = SCRIPTS / "bundle_lint.py"

pytestmark = pytest.mark.python_scripts

INDEX = '---\nokf_version: "0.2"\n---\n\n# Bundle\n\n'
LOG = "# Update Log\n\n## 2026-01-01\n\n- created\n"
FLOOR = "required:\n- type\n- title\n- description\n- status\n- generated\n"


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
    if omit != "generated":
        lines.append('generated:\n  by: "human:tester"\n  at: 2026-01-01')
    return "---\n" + "\n".join(lines) + f"\n---\n\n# {title}\n"


def _bundle(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True)
    (root / "index.md").write_text(INDEX + "".join(f"- [{name}]({name})\n" for name in files), encoding="utf-8")
    (root / "log.md").write_text(LOG, encoding="utf-8")
    (root / "okf-floor.yaml").write_text(FLOOR, encoding="utf-8")
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _workspace(tmp_path: Path, bundles: dict[str, str]) -> dict[str, str]:
    """Write a manifest naming the given bundles, and return the env that finds it."""
    config = tmp_path / "config" / "fkb"
    config.mkdir(parents=True)
    lines = ["bundles:"]
    for name, path in bundles.items():
        lines += [f"  {name}:", f"    path: {path}", "    writable: true"]
    (config / "workspace.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"XDG_CONFIG_HOME": str(tmp_path / "config")}


def _run(script: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    # Same reasoning as the bundle_lint tests: the pytest interpreter often has
    # no pyyaml, in which case uv resolves the script's own inline metadata.
    if importlib.util.find_spec("yaml") is None:
        command = ["uv", "run", "--script", str(script), *args]
    else:
        command = [sys.executable, str(script), *args]
    return subprocess.run(command, capture_output=True, text=True, check=False, env={**os.environ, **(env or {})})


def test_list_reports_path_tier_and_publish(tmp_path: Path) -> None:
    """`list` is what an agent reads before choosing where to write, so it must say who may cite what."""
    _bundle(tmp_path / "open", {"alpha.md": _concept("Alpha")})
    _bundle(tmp_path / "shut", {"beta.md": _concept("Beta")})
    config = tmp_path / "config" / "fkb"
    config.mkdir(parents=True)
    (config / "workspace.yaml").write_text(
        f"bundles:\n"
        f"  open:\n    path: {tmp_path / 'open'}\n"
        f"    referenceable_by: '*'\n    writable: true\n"
        f"    publish: https://example.invalid/kb\n"
        f"  shut:\n    path: {tmp_path / 'shut'}\n",
        encoding="utf-8",
    )
    result = _run(FKB, "list", env={"XDG_CONFIG_HOME": str(tmp_path / "config")})
    assert result.returncode == 0, result.stdout + result.stderr
    assert "open" in result.stdout
    assert "https://example.invalid/kb" in result.stdout
    assert "sealed" in result.stdout


def test_omitted_policy_fails_closed(tmp_path: Path) -> None:
    """A bundle added without policy must disclose nothing and accept no writes."""
    _bundle(tmp_path / "shut", {"beta.md": _concept("Beta")})
    env = _workspace(tmp_path, {})
    (tmp_path / "config" / "fkb" / "workspace.yaml").write_text(
        f"bundles:\n  shut:\n    path: {tmp_path / 'shut'}\n", encoding="utf-8"
    )
    result = _run(FKB, "list", env=env)
    assert "sealed" in result.stdout
    assert "write      no" in result.stdout


def test_missing_manifest_says_what_to_write(tmp_path: Path) -> None:
    """Setup is hand-written until the journal says what `init` should ask, so the error has to teach it."""
    result = _run(FKB, "list", env={"XDG_CONFIG_HOME": str(tmp_path / "empty")})
    assert result.returncode != 0
    assert "workspace.yaml" in result.stderr
    assert "bundles" in result.stderr


def test_lint_picks_up_the_bundles_own_floor(tmp_path: Path) -> None:
    """The floor is the bundle's declaration; the CLI must read it rather than carry its own list."""
    _bundle(tmp_path / "kb", {"alpha.md": _concept("Alpha", omit="description")})
    env = _workspace(tmp_path, {"kb": str(tmp_path / "kb")})
    result = _run(FKB, "lint", env=env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "required field `description`" in result.stdout


def test_lint_names_one_bundle(tmp_path: Path) -> None:
    """Linting everything on every call gets ignored; naming one has to be possible."""
    _bundle(tmp_path / "good", {"alpha.md": _concept("Alpha")})
    _bundle(tmp_path / "bad", {"beta.md": _concept("Beta", omit="title")})
    env = _workspace(tmp_path, {"good": str(tmp_path / "good"), "bad": str(tmp_path / "bad")})
    result = _run(FKB, "lint", "good", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "beta.md" not in result.stdout


def test_unknown_bundle_lists_the_known_ones(tmp_path: Path) -> None:
    """A typo in a bundle name is the common case, so the error carries the alternatives."""
    _bundle(tmp_path / "kb", {"alpha.md": _concept("Alpha")})
    env = _workspace(tmp_path, {"kb": str(tmp_path / "kb")})
    result = _run(FKB, "lint", "kbb", env=env)
    assert result.returncode != 0
    assert "kb" in result.stderr


def test_cli_and_hook_report_the_same_finding(tmp_path: Path) -> None:
    """One implementation, two entry points.

    The standalone hook exists so a bundle can enforce itself without the
    federation installed, which is only safe if it and `fkb lint` agree. Run
    both over the same broken file and compare what they say about it.
    """
    root = _bundle(tmp_path / "kb", {"alpha.md": _concept("Alpha", omit="status")})
    env = _workspace(tmp_path, {"kb": str(root)})

    hook = _run(BUNDLE_LINT, "--bundle-root", str(root), "--floor", str(root / "okf-floor.yaml"))
    cli = _run(FKB, "lint", env=env)

    def findings(text: str) -> set[str]:
        return {line.strip() for line in text.splitlines() if line.strip().startswith("ERROR")}

    assert hook.returncode == cli.returncode == 1, hook.stdout + cli.stdout
    assert findings(hook.stdout) == findings(cli.stdout)
    assert "alpha.md: floor: required field `status` is absent or empty" in hook.stdout
