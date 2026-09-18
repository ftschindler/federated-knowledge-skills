"""Unit tests for `fkb sync`: one per row of the refusal table in DESIGN §10.

The command's product is not the four git calls. It is the list of situations in
which running them would trample work somebody was in the middle of, and an
untested row of that list is a row that will be wrong - silently, on a day when
a person had something half-written in the tree.

Every test runs against real repositories with a real bare remote on disk, over
`file://`. There is nothing here a fake git would prove: the questions are what
git does to a working tree when a rebase conflicts and what a remote says when
somebody pushed first, and both are the behaviour under test rather than a
detail of it.

Fast and offline all the same, which is why these sit in the `python_scripts`
layer beside the rest of the CLI's tests.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from fake_home import FakeHome, have
from git_environment import outside_any_repository

pytestmark = [pytest.mark.python_scripts, pytest.mark.skipif(not have("git"), reason="sync needs git")]

INDEX = '---\nokf_version: "0.2"\n---\n\n# Shared\n'
CONCEPT = """---
type: note
title: {title}
description: Something the team knows.
status: draft
generated:
  by: "human:tester"
  at: 2026-01-01
---

# {title}
"""

IDENTITY = ["-c", "user.email=test@invalid", "-c", "user.name=Test", "-c", "commit.gpgsign=false"]


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    done = subprocess.run(
        ["git", "-C", str(root), *IDENTITY, *args],
        capture_output=True,
        text=True,
        check=False,
        env=outside_any_repository(GIT_TERMINAL_PROMPT="0"),
    )
    assert done.returncode == 0, f"git {' '.join(args)} failed:\n{done.stdout}{done.stderr}"
    return done


@pytest.fixture
def shared(fake_home: FakeHome) -> Path:
    """One bundle on a staging branch, tracking a bare remote, registered as shared.

    A bare remote rather than a second working tree, because that is the shape a
    forge has: a checkout cannot be pushed into on its current branch, and a test
    that worked around that would be testing an arrangement nobody uses.
    """
    remote = fake_home.root / "remotes" / "team.git"
    remote.mkdir(parents=True)
    subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(remote)], check=True, env=outside_any_repository())

    bundle = fake_home.workspace_root / "team"
    bundle.mkdir(parents=True)
    (bundle / "index.md").write_text(INDEX, encoding="utf-8")
    (bundle / "log.md").write_text("# Log\n\n## 2026-01-01\n\n- created\n", encoding="utf-8")
    (bundle / ".gitattributes").write_text("index.md merge=union\nlog.md merge=union\n", encoding="utf-8")
    git(bundle, "init", "-q", "-b", "main", ".")
    # The identity goes into the repository rather than onto the git calls this
    # file makes, because `sync` rebases through git as the person's own machine
    # would, and a fake home has no global config for it to find. Filing already
    # refuses to invent one, so a checkout without it is not a state to test here.
    git(bundle, "config", "user.email", "test@invalid")
    git(bundle, "config", "user.name", "Test")
    git(bundle, "add", "-A")
    git(bundle, "commit", "-qm", "initial")
    git(bundle, "remote", "add", "origin", remote.as_uri())
    git(bundle, "push", "-q", "-u", "origin", "main")
    git(bundle, "checkout", "-q", "-b", "staging")
    git(bundle, "push", "-q", "-u", "origin", "staging")

    manifest = fake_home.root / ".config" / "fkb"
    manifest.mkdir(parents=True, exist_ok=True)
    (manifest / "workspace.yaml").write_text(
        f"bundles:\n  team:\n    path: {bundle}\n    writable: true\n    sync: staging\n",
        encoding="utf-8",
    )
    return bundle


def file_concept(bundle: Path, name: str, title: str) -> None:
    """What filing leaves behind: a concept, committed through the bundle's own hooks."""
    (bundle / name).write_text(CONCEPT.format(title=title), encoding="utf-8")
    git(bundle, "add", "-A")
    git(bundle, "commit", "-qm", f"file {title}")


def remote_holds(bundle: Path, path: str, branch: str = "staging") -> bool:
    listed = subprocess.run(
        ["git", "-C", str(bundle), "ls-tree", "--name-only", f"origin/{branch}", path],
        capture_output=True,
        text=True,
        check=False,
        env=outside_any_repository(),
    )
    return bool(listed.stdout.strip())


def test_a_clean_checkout_fetches_rebases_and_pushes(fake_home: FakeHome, shared: Path) -> None:
    """The row that carries the product: filing on one machine reaches the others."""
    file_concept(shared, "alpha.md", "Alpha")

    result = fake_home.run("sync")
    assert result.returncode == 0, result.stdout + result.stderr
    git(shared, "fetch", "-q", "origin", "staging")
    assert remote_holds(shared, "alpha.md"), f"the concept never left the machine:\n{result.stdout}"


def test_a_push_rejected_by_a_teammate_is_retried_once(fake_home: FakeHome, shared: Path) -> None:
    """Somebody pushing first is the ordinary case, not an error to report.

    The second checkout below is what a teammate is. Its commit lands first, and
    this one has to replay on top rather than refusing or forcing.
    """
    theirs = fake_home.root / "theirs"
    subprocess.run(
        ["git", "clone", "-q", "-b", "staging", (fake_home.root / "remotes" / "team.git").as_uri(), str(theirs)],
        check=True,
        env=outside_any_repository(),
    )
    file_concept(theirs, "beta.md", "Beta")
    git(theirs, "push", "-q", "origin", "staging")

    file_concept(shared, "alpha.md", "Alpha")
    result = fake_home.run("sync")
    assert result.returncode == 0, result.stdout + result.stderr

    git(shared, "fetch", "-q", "origin", "staging")
    assert remote_holds(shared, "alpha.md"), "the rebase-and-retry did not get this machine's commit out"
    assert remote_holds(shared, "beta.md"), "the teammate's commit was overwritten rather than rebased onto"


def test_a_conflicting_rebase_is_aborted_and_named(fake_home: FakeHome, shared: Path) -> None:
    """Two people writing the same concept is a question about what is true.

    The assertions are about what is left behind rather than the wording: the
    rebase must not be sitting half-applied, and this machine's commit must
    still be here, because the whole point of refusing is that nothing is lost.
    """
    theirs = fake_home.root / "theirs"
    subprocess.run(
        ["git", "clone", "-q", "-b", "staging", (fake_home.root / "remotes" / "team.git").as_uri(), str(theirs)],
        check=True,
        env=outside_any_repository(),
    )
    file_concept(theirs, "same.md", "Their version")
    git(theirs, "push", "-q", "origin", "staging")

    file_concept(shared, "same.md", "Our version")
    result = fake_home.run("sync")

    assert result.returncode != 0
    assert "same.md" in result.stdout, f"the conflict does not name the file:\n{result.stdout}"
    assert not (shared / ".git" / "rebase-merge").exists(), "a half-finished rebase was left in the checkout"
    assert not (shared / ".git" / "rebase-apply").exists(), "a half-finished rebase was left in the checkout"
    assert "Our version" in (shared / "same.md").read_text(encoding="utf-8"), "this machine's work was discarded"


def test_other_uncommitted_work_stops_the_push_and_says_so(fake_home: FakeHome, shared: Path) -> None:
    """An unpushed commit is not a failure; a stashed-away draft would be.

    Nothing here may decide that a half-written file is finished, so the branch
    is left where it is and the file is named.
    """
    file_concept(shared, "alpha.md", "Alpha")
    (shared / "draft.md").write_text("half a thought\n", encoding="utf-8")

    result = fake_home.run("sync")
    assert result.returncode != 0
    assert "draft.md" in result.stdout, f"the refusal does not name what is in the way:\n{result.stdout}"
    assert (shared / "draft.md").is_file(), "the uncommitted file was moved out of the way"
    assert not remote_holds(shared, "alpha.md"), "it pushed anyway"


def test_a_checkout_on_another_branch_is_reported_rather_than_switched(fake_home: FakeHome, shared: Path) -> None:
    """Somebody preparing a pull request is in the middle of something deliberate."""
    git(shared, "checkout", "-q", "-b", "a-pull-request")
    file_concept(shared, "alpha.md", "Alpha")

    result = fake_home.run("sync")
    assert result.returncode != 0
    assert "a-pull-request" in result.stdout and "staging" in result.stdout, (
        f"the refusal names neither the branch it found nor the one it wanted:\n{result.stdout}"
    )
    on = git(shared, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    assert on == "a-pull-request", "the command switched branches under the person"


def test_a_rebase_in_progress_is_left_completely_alone(fake_home: FakeHome, shared: Path) -> None:
    """The one row where doing nothing includes not even looking further."""
    file_concept(shared, "same.md", "Ours")
    git(shared, "checkout", "-q", "-b", "other", "HEAD~1")
    file_concept(shared, "same.md", "Theirs")
    conflicting = subprocess.run(
        ["git", "-C", str(shared), *IDENTITY, "rebase", "staging"],
        capture_output=True,
        text=True,
        check=False,
        env=outside_any_repository(),
    )
    assert conflicting.returncode != 0, "the fixture did not manage to leave a rebase in progress"

    result = fake_home.run("sync")
    assert result.returncode != 0
    assert "rebase" in result.stdout.lower(), f"the refusal does not say what is in progress:\n{result.stdout}"
    assert (shared / ".git" / "rebase-merge").exists() or (shared / ".git" / "rebase-apply").exists(), (
        "the person's rebase was aborted for them"
    )
    git(shared, "rebase", "--abort")


def test_a_detached_head_is_refused(fake_home: FakeHome, shared: Path) -> None:
    """There is no branch to push, and creating one would be inventing intent."""
    git(shared, "checkout", "-q", "--detach", "HEAD")

    result = fake_home.run("sync")
    assert result.returncode != 0
    assert "detached" in result.stdout.lower()


def test_a_branch_with_no_upstream_keeps_the_commit(fake_home: FakeHome, shared: Path) -> None:
    """Nothing is pushed, and the refusal is the one-off command that fixes it."""
    git(shared, "branch", "--unset-upstream")
    file_concept(shared, "alpha.md", "Alpha")

    result = fake_home.run("sync")
    assert result.returncode != 0
    assert "push -u" in result.stdout, f"the refusal carries no remedy:\n{result.stdout}"
    assert git(shared, "log", "-1", "--format=%s").stdout.strip() == "file Alpha", "the commit was not kept"


def test_a_bundle_with_no_sync_branch_is_not_an_error(fake_home: FakeHome) -> None:
    """The default, and the whole of backwards compatibility: nothing to do."""
    bundle = fake_home.bundle("private")
    manifest = fake_home.root / ".config" / "fkb"
    manifest.mkdir(parents=True, exist_ok=True)
    (manifest / "workspace.yaml").write_text(
        f"bundles:\n  private:\n    path: {bundle}\n    writable: true\n", encoding="utf-8"
    )

    named = fake_home.run("sync", "private")
    assert named.returncode == 0, named.stdout + named.stderr
    assert "sync" in named.stdout

    everything = fake_home.run("sync")
    assert everything.returncode == 0, everything.stdout + everything.stderr


def test_check_reports_and_changes_nothing(fake_home: FakeHome, shared: Path) -> None:
    """The dry run is a flag so that it and the real run cannot disagree about the rules."""
    file_concept(shared, "alpha.md", "Alpha")

    result = fake_home.run("sync", "--check")
    assert result.returncode == 0, result.stdout + result.stderr
    git(shared, "fetch", "-q", "origin", "staging")
    assert not remote_holds(shared, "alpha.md"), "`--check` pushed"


def test_a_sealed_bundle_may_not_declare_a_sync_branch(fake_home: FakeHome) -> None:
    """`writable: false` with a `sync` branch is a contradiction, refused on load.

    Not at the first push: a manifest that is wrong about who may write where
    should fail before anything acts on it, which is where the mutually
    non-prefixing `publish` check already sits.
    """
    bundle = fake_home.bundle("upstream")
    manifest = fake_home.root / ".config" / "fkb"
    manifest.mkdir(parents=True, exist_ok=True)
    (manifest / "workspace.yaml").write_text(
        f"bundles:\n  upstream:\n    path: {bundle}\n    sync: staging\n", encoding="utf-8"
    )

    result = fake_home.run("list")
    assert result.returncode != 0
    assert "writable" in result.stderr, f"the refusal does not say which half to change:\n{result.stderr}"


def test_lint_says_when_a_shared_checkout_has_drifted(fake_home: FakeHome, shared: Path) -> None:
    """The cheap half of the same fact, available with no network call.

    A checkout on the wrong branch takes commits and passes every other check
    here. The only symptom is that nothing filed reaches anybody, which is a
    thing to be told rather than to work out.
    """
    git(shared, "checkout", "-q", "-b", "a-pull-request")

    result = fake_home.run("lint", "team")
    assert "a-pull-request" in result.stdout and "staging" in result.stdout, (
        f"lint says nothing about the drifted checkout:\n{result.stdout}"
    )
    assert result.returncode == 0, "a branch elsewhere is not a defect in the knowledge"


def test_add_puts_a_shared_bundle_on_its_branch(fake_home: FakeHome) -> None:
    """A clone lands on the protected default branch, which is the wrong place to file.

    This is what makes leaving the reviewed branch as the repository's default
    safe: nobody has to remember, so nobody finds out days later from a teammate
    who never saw the concept.
    """
    remote = fake_home.root / "remotes" / "team"
    remote.mkdir(parents=True)
    (remote / "index.md").write_text(INDEX, encoding="utf-8")
    git(remote, "init", "-q", "-b", "main", ".")
    git(remote, "add", "-A")
    git(remote, "commit", "-qm", "initial")
    git(remote, "branch", "staging")

    assert fake_home.run("init", "--workspace-root", str(fake_home.workspace_root)).returncode == 0
    added = fake_home.run("add", "team", "--clone", remote.as_uri(), "--writable", "--sync", "staging")
    assert added.returncode == 0, added.stdout + added.stderr

    checkout = fake_home.workspace_root / "team"
    on = git(checkout, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    assert on == "staging", f"the checkout was left on `{on}`, where filing cannot leave the machine"


def test_a_sync_branch_without_writable_is_refused_at_add(fake_home: FakeHome) -> None:
    """The same contradiction, caught where it is cheapest: before it is written down."""
    assert fake_home.run("init", "--workspace-root", str(fake_home.workspace_root)).returncode == 0
    refused = fake_home.run("add", "elsewhere", "--new", "--sync", "staging")
    assert refused.returncode != 0
    assert "writable" in refused.stderr


def test_a_scaffolded_bundle_carries_the_union_merge_attributes(fake_home: FakeHome) -> None:
    """The index and the log are where two people collide over lines neither disputes.

    Written for every bundle, shared or not, because the day a bundle is shared
    is not the day anybody remembers to add this.
    """
    assert fake_home.run("init", "--workspace-root", str(fake_home.workspace_root)).returncode == 0
    assert fake_home.run("add", "mine", "--new", "--writable").returncode == 0

    attributes = (fake_home.workspace_root / "mine" / ".gitattributes").read_text(encoding="utf-8")
    assert "index.md merge=union" in attributes
    assert "log.md merge=union" in attributes
