"""Unit tests for dev/support scripts under .scripts/.

These are fast and deterministic (no LLM, no network). The mailmap checker reads
`git log` from the current working directory, so each test builds a throwaway git
repo with crafted authors and runs the script against it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from git_environment import outside_any_repository

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_MAILMAP = REPO_ROOT / ".scripts" / "check_mailmap.py"

pytestmark = pytest.mark.python_scripts


def _git(repo: Path, *args: str, **env: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=outside_any_repository(**env),
    )


def _commit(repo: Path, name: str, email: str, msg: str) -> None:
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", msg],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        # The inherited environment is kept, minus the `GIT_` namespace, and
        # the identity set on top. Keeping the rest is what makes this work on
        # Windows, where git needs SYSTEMROOT to resolve anything at all and
        # reads USERPROFILE rather than HOME; dropping that namespace is what
        # keeps the commit in `repo` when this suite is run from a git hook,
        # which exports `GIT_DIR` and `GIT_INDEX_FILE` pointing at the real one.
        env=outside_any_repository(
            GIT_AUTHOR_NAME=name,
            GIT_AUTHOR_EMAIL=email,
            GIT_COMMITTER_NAME=name,
            GIT_COMMITTER_EMAIL=email,
            HOME=str(repo),
            USERPROFILE=str(repo),
        ),
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "x")
    _git(repo, "config", "user.email", "x@example.com")
    return repo


def _run_check(repo: Path) -> subprocess.CompletedProcess[str]:
    # The checker reads `git log` from its working directory, so it needs the
    # scrub as much as the fixtures do: run from a commit hook and left with
    # `GIT_DIR` set, it reports the authors of *this* repository and the test
    # fails on a mailmap that is not the one it wrote.
    return subprocess.run(
        [sys.executable, str(CHECK_MAILMAP)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=outside_any_repository(),
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
    (repo / ".mailmap").write_text("Grace Hopper <grace@example.com>\n", encoding="utf-8")
    result = _run_check(repo)
    assert result.returncode == 1
    assert "missing mailmap entry for Ada Lovelace" in result.stdout


def test_unsorted_lines_flagged(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _commit(repo, "Ada Lovelace", "ada@example.com", "c1")
    (repo / ".mailmap").write_text(
        "Ada Lovelace <ada@example.com>\nAaron Swartz <aaron@example.com>\n", encoding="utf-8"
    )
    result = _run_check(repo)
    assert result.returncode == 1
    assert "not sorted properly" in result.stdout


def test_clean_mailmap_passes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _commit(repo, "Ada Lovelace", "ada@example.com", "c1")
    (repo / ".mailmap").write_text("Ada Lovelace <ada@example.com>\n", encoding="utf-8")
    result = _run_check(repo)
    assert result.returncode == 0, result.stdout


CHECK_MARKDOWN_STYLE = REPO_ROOT / ".scripts" / "check_markdown_style.py"


def _run_markdown_style(tmp_path: Path, body: str) -> subprocess.CompletedProcess[str]:
    doc = tmp_path / "doc.md"
    doc.write_text(body, encoding="utf-8")
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


def _decoy_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A repository the environment points at, standing in for the one being committed to.

    This is what a git hook leaves behind it: `GIT_DIR` and `GIT_INDEX_FILE`
    naming the real repository, exported for everything the hook starts. The
    suite is run from such a hook, so the fixtures below build their throwaway
    repositories inside somebody's commit whether they know it or not.
    """
    decoy = tmp_path / "decoy"
    decoy.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=decoy, check=True, capture_output=True, text=True)
    monkeypatch.setenv("GIT_DIR", str(decoy / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(decoy / ".git" / "index"))
    return decoy


def _history(repo: Path) -> str:
    listed = subprocess.run(
        ["git", "-C", str(repo), "log", "--oneline"],
        capture_output=True,
        text=True,
        check=False,
        env=outside_any_repository(),
    )
    return listed.stdout.strip()


def test_a_fixtures_commit_lands_in_the_fixture_and_not_in_the_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The suite runs from a commit hook, and must not commit into the commit.

    Found the hard way: three commits authored by this file's "Ada Lovelace"
    on a working branch, and a file staged out of another test's fixture. The
    tests passed throughout, because writing to the wrong repository is not a
    failure of anything they assert - which is why this asserts it directly.
    """
    decoy = _decoy_repository(tmp_path, monkeypatch)
    repo = _init_repo(tmp_path)
    _commit(repo, "Ada Lovelace", "ada@example.com", "c1")

    assert _history(repo), "the fixture has no history, so the commit went somewhere else"
    assert not _history(decoy), "the fixture committed into the repository the environment named"


NEXT_VERSION = REPO_ROOT / ".scripts" / "next-version.py"


def _next(current: str, level: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(NEXT_VERSION), current, level],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("current", "level", "expected"),
    [
        ("0.4.2", "patch", "0.4.3"),
        ("0.4.2", "minor", "0.5.0"),
        # The one worth pinning: a major zeroes what is beneath it. Getting this
        # wrong yields 1.4.2, which looks like a version and is permanent.
        ("0.4.2", "major", "1.0.0"),
        ("0.9.9", "minor", "0.10.0"),
    ],
)
def test_the_bump_is_the_one_the_label_named(current: str, level: str, expected: str) -> None:
    result = _next(current, level)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == expected


def test_something_that_is_not_a_version_is_refused(tmp_path: Path) -> None:
    """A release computed from a `VERSION` somebody edited by hand must stop here.

    The next line of the workflow writes the result back and tags it, and a tag
    is not takeable-back once a copy of it is on somebody's disk.
    """
    result = _next("v0.4", "patch")
    assert result.returncode != 0
    assert "not a version" in result.stderr
