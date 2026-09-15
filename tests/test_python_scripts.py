"""Unit tests for dev/support scripts under .scripts/.

These are fast and deterministic (no LLM, no network). The mailmap checker reads
`git log` from the current working directory, so each test builds a throwaway git
repo with crafted authors and runs the script against it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_MAILMAP = REPO_ROOT / ".scripts" / "check_mailmap.py"

pytestmark = pytest.mark.python_scripts


def _git(repo: Path, *args: str, **env: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _commit(repo: Path, name: str, email: str, msg: str) -> None:
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", msg],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        # The inherited environment is kept and only the identity overridden.
        # A hand-built one listing PATH and HOME is enough on Linux and not on
        # Windows, where git needs SYSTEMROOT to resolve anything at all and
        # reads USERPROFILE rather than HOME.
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": name,
            "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": name,
            "GIT_COMMITTER_EMAIL": email,
            "HOME": str(repo),
            "USERPROFILE": str(repo),
        },
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "x")
    _git(repo, "config", "user.email", "x@example.com")
    return repo


def _run_check(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_MAILMAP)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def test_missing_mailmap_fails(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _commit(repo, "Ada Lovelace", "ada@example.com", "c1")
    result = _run_check(repo)
    assert result.returncode == 1
    assert "No mailmap found" in result.stdout


def test_missing_entry_flagged(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _commit(repo, "Ada Lovelace", "ada@example.com", "c1")
    (repo / ".mailmap").write_text("Grace Hopper <grace@example.com>\n")
    result = _run_check(repo)
    assert result.returncode == 1
    assert "missing mailmap entry for Ada Lovelace" in result.stdout


def test_unsorted_lines_flagged(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _commit(repo, "Ada Lovelace", "ada@example.com", "c1")
    (repo / ".mailmap").write_text("Ada Lovelace <ada@example.com>\nAaron Swartz <aaron@example.com>\n")
    result = _run_check(repo)
    assert result.returncode == 1
    assert "not sorted properly" in result.stdout


def test_clean_mailmap_passes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _commit(repo, "Ada Lovelace", "ada@example.com", "c1")
    (repo / ".mailmap").write_text("Ada Lovelace <ada@example.com>\n")
    result = _run_check(repo)
    assert result.returncode == 0, result.stdout


CHECK_MARKDOWN_STYLE = REPO_ROOT / ".scripts" / "check_markdown_style.py"


def _run_markdown_style(tmp_path: Path, body: str) -> subprocess.CompletedProcess[str]:
    doc = tmp_path / "doc.md"
    doc.write_text(body)
    return subprocess.run(
        [sys.executable, str(CHECK_MARKDOWN_STYLE), str(doc)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("rule", ["---", "***", "___", "- - -", "* * *", "_ _ _", "-----"])
def test_thematic_break_flagged(tmp_path: Path, rule: str) -> None:
    result = _run_markdown_style(tmp_path, f"# T\n\n{rule}\n\n## S\n")
    assert result.returncode == 1
    assert f"`{rule}` separator" in result.stdout


@pytest.mark.parametrize("line", ["- item", "*emphasis*", "__bold__", "-- two", "**"])
def test_non_breaks_allowed(tmp_path: Path, line: str) -> None:
    result = _run_markdown_style(tmp_path, f"# T\n\n{line}\n")
    assert result.returncode == 0, result.stdout


def test_em_dash_flagged(tmp_path: Path) -> None:
    result = _run_markdown_style(tmp_path, "# T\n\nA sentence \u2014 with an em dash.\n")
    assert result.returncode == 1
    assert "em dash" in result.stdout


def test_frontmatter_and_tables_allowed(tmp_path: Path) -> None:
    body = "---\nname: x\n---\n\n# T\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n"
    result = _run_markdown_style(tmp_path, body)
    assert result.returncode == 0, result.stdout


def test_code_fences_exempt(tmp_path: Path) -> None:
    body = "# T\n\n```yaml\n---\nkey: value \u2014 quoted\n```\n"
    result = _run_markdown_style(tmp_path, body)
    assert result.returncode == 0, result.stdout
