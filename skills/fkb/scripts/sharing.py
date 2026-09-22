"""Moving commits to and from a bundle several people write into.

Fetch, rebase, push is four git calls nobody needs wrapped. What is worth
shipping is the list of situations in which running them would trample work
somebody was in the middle of, which is the table in DESIGN §10 and the whole
content of this module.

Two rules shape everything below. **It moves commits and never makes one**:
filing commits through the bundle's own hooks, where the gate can actually run,
so nothing here stages, commits or amends. And **it refuses rather than
resolves**: no stashing, no branch switching, no aborting somebody's rebase for
them. Each of those situations means a person was in the middle of something
deliberate, and the cost of guessing wrong is unrecoverable where the cost of
refusing is a line of output.

An unpushed commit is therefore not a failure. The knowledge is saved under the
hooks, the person's other work is untouched, and the next clean run carries it
along with everything else.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Every outcome carries one of these, so a caller can act on the shape of what
# happened without reading the prose. `blocked` is the only one that is an
# error: the rest are states this command exists to report calmly.
NOTHING_TO_DO = "nothing-to-do"
PUSHED = "pushed"
UP_TO_DATE = "up-to-date"
WOULD = "would"
BLOCKED = "blocked"


@dataclass
class Outcome:
    """What one bundle's sync did, or declined to do, and why.

    `remedy` is separate from `summary` because the skill relays a refusal
    verbatim and must not have to compose one: an agent that assembled the
    advice itself would be deciding, which is exactly what the refusal exists to
    prevent.
    """

    bundle: str
    kind: str
    summary: str
    remedy: str = ""
    details: list[str] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return self.kind == BLOCKED


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """One git call in the bundle, with the terminal shut.

    `GIT_TERMINAL_PROMPT=0` is not a detail: a fetch against a remote that wants
    credentials otherwise hangs forever behind a prompt nobody is watching,
    inside a command an agent ran without being asked to.
    """
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def _mid_operation(root: Path) -> str | None:
    """The name of the multi-step git operation in progress here, if there is one."""
    git_dir = _git(root, "rev-parse", "--git-dir")
    if git_dir.returncode != 0:
        return None
    base = (root / git_dir.stdout.strip()).resolve()
    for marker, what in (
        ("rebase-merge", "a rebase"),
        ("rebase-apply", "a rebase"),
        ("MERGE_HEAD", "a merge"),
        ("CHERRY_PICK_HEAD", "a cherry-pick"),
        ("BISECT_LOG", "a bisect"),
    ):
        if (base / marker).exists():
            return what
    return None


def _dirty(root: Path) -> list[str]:
    """Paths the working tree holds that no commit does.

    Untracked files count. A rebase does not touch them, so this is stricter
    than git would be - and deliberately: an untracked file in a bundle is
    usually a concept somebody is still writing, and moving the branch under it
    is how the filing it belongs to ends up half on the remote.
    """
    listed = _git(root, "status", "--porcelain")
    if listed.returncode != 0:
        return []
    return [line[3:].strip() for line in listed.stdout.splitlines() if line.strip()]


def _conflicted(root: Path) -> list[str]:
    listed = _git(root, "diff", "--name-only", "--diff-filter=U")
    return [line.strip() for line in listed.stdout.splitlines() if line.strip()]


def _upstream(root: Path, branch: str) -> str | None:
    found = _git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{branch}@{{upstream}}")
    return found.stdout.strip() if found.returncode == 0 and found.stdout.strip() else None


def _unpushed(root: Path, branch: str, upstream: str) -> int:
    counted = _git(root, "rev-list", "--count", f"{upstream}..{branch}")
    try:
        return int(counted.stdout.strip())
    except ValueError:
        return 0


def sync(name: str, path: Path, branch: str | None, *, check: bool = False) -> Outcome:
    """Carry this bundle's commits to the shared branch, or say why not.

    The order of the questions is the order in which refusing is cheapest.
    Everything answerable from the checkout is asked first, so a tree that was
    never going to be pushed costs no fetch and no waiting.
    """
    if branch is None:
        return Outcome(name, NOTHING_TO_DO, "not shared (`sync` is not set), so nothing is fetched or pushed")
    if not path.is_dir():
        return Outcome(name, BLOCKED, f"the manifest points at {path}, which does not exist")

    refused = _refused_before_the_network(name, path, branch)
    if refused is not None:
        return refused

    upstream = _upstream(path, branch)
    if upstream is None:
        return Outcome(
            name,
            BLOCKED,
            f"`{branch}` tracks no remote branch here, so a commit has nowhere to go",
            remedy=(
                f"Set one up yourself once: `git -C {path} push -u origin {branch}`. Commits made "
                "in the meantime are kept and go with the first run after that."
            ),
        )
    if check:
        return Outcome(
            name,
            WOULD,
            f"would fetch `{upstream}`, rebase `{branch}` onto it and push",
            details=[f"{_unpushed(path, branch, upstream)} commit(s) not yet on {upstream}"],
        )
    return _move(name, path, branch, upstream)


def _refused_before_the_network(name: str, path: Path, branch: str) -> Outcome | None:
    """Every reason to stop that the checkout alone can give. None means carry on."""
    for question in (_is_a_repository, _is_between_operations, _is_on_the_shared_branch, _is_clean):
        answer = question(name, path, branch)
        if answer is not None:
            return answer
    return None


def _is_a_repository(name: str, path: Path, _: str) -> Outcome | None:
    if _git(path, "rev-parse", "--show-toplevel").returncode == 0:
        return None
    return Outcome(
        name,
        BLOCKED,
        f"{path} is not in a git repository, so there is nowhere to push",
        remedy="A shared bundle is a repository other people clone. Make it one, or drop `sync`.",
    )


def _is_between_operations(name: str, path: Path, _: str) -> Outcome | None:
    busy = _mid_operation(path)
    if busy is None:
        return None
    return Outcome(
        name,
        BLOCKED,
        f"{busy} is in progress in this checkout",
        remedy=f"Finish or abort {busy} yourself. Nothing was fetched, rebased or pushed.",
    )


def _is_on_the_shared_branch(name: str, path: Path, branch: str) -> Outcome | None:
    """No flag overrides this one, which is why the refusal names both branches.

    Both honest ways to contradict the manifest already exist - change the field,
    or use git directly - and a person deliberately preparing a pull request
    needs neither permission nor a warning.
    """
    head = _git(path, "symbolic-ref", "--quiet", "--short", "HEAD")
    if head.returncode != 0:
        return Outcome(
            name,
            BLOCKED,
            "HEAD is detached, so there is no branch to push",
            remedy=f"Check out `{branch}` when the work that detached it is finished.",
        )
    current = head.stdout.strip()
    if current == branch:
        return None
    return Outcome(
        name,
        BLOCKED,
        f"this checkout is on `{current}`; the manifest shares this bundle on `{branch}`",
        remedy=(
            f"Switch to `{branch}` when you are done on `{current}`, or change `sync` in the "
            "manifest if the shared branch has moved. There is no flag that overrides this."
        ),
    )


def _is_clean(name: str, path: Path, _: str) -> Outcome | None:
    outstanding = _dirty(path)
    if not outstanding:
        return None
    return Outcome(
        name,
        BLOCKED,
        "the working tree holds changes no commit does, so nothing was fetched or pushed",
        remedy=(
            "Commit or put aside the files below - through the bundle's own hooks, not with "
            "`--no-verify` - and run this again. Anything already committed is safe and goes "
            "with the next clean run."
        ),
        details=outstanding,
    )


def _move(name: str, path: Path, branch: str, upstream: str) -> Outcome:
    """Fetch, rebase, push."""
    remote, _, remote_branch = upstream.partition("/")
    fetched = _fetch(name, path, remote, remote_branch)
    if fetched is not None:
        return fetched
    rebased = _rebase(name, path, branch, upstream)
    if rebased is not None:
        return rebased
    if _unpushed(path, branch, upstream) == 0:
        return Outcome(name, UP_TO_DATE, f"up to date with `{upstream}`; nothing of this machine's to send")
    return _push(name, path, branch, upstream)


def _fetch(name: str, path: Path, remote: str, remote_branch: str) -> Outcome | None:
    fetched = _git(path, "fetch", remote, remote_branch)
    if fetched.returncode == 0:
        return None
    return Outcome(
        name,
        BLOCKED,
        f"could not reach `{remote}`, so nothing was rebased or pushed",
        remedy="The commits are kept and go with the next run that reaches the remote.",
        details=_lines(fetched.stderr),
    )


def _push(name: str, path: Path, branch: str, upstream: str) -> Outcome:
    """Push, and replay once more if a teammate got in first.

    A teammate pushing between the fetch and the push is routine rather than an
    error to report, so it is worth one retry. It is worth exactly one: a second
    rejection means the branch is moving faster than this can follow, and
    looping would be a program deciding to keep trying against a remote that
    keeps saying no.
    """
    remote, _, remote_branch = upstream.partition("/")
    refname = f"{branch}:{remote_branch}"
    if _git(path, "push", remote, refname).returncode == 0:
        return Outcome(name, PUSHED, f"pushed `{branch}` to `{upstream}`")

    fetched = _fetch(name, path, remote, remote_branch)
    if fetched is not None:
        return fetched
    rebased = _rebase(name, path, branch, upstream)
    if rebased is not None:
        return rebased

    again = _git(path, "push", remote, refname)
    if again.returncode == 0:
        return Outcome(name, PUSHED, f"pushed `{branch}` to `{upstream}`")
    return Outcome(
        name,
        BLOCKED,
        f"`{upstream}` moved again while pushing, so the push was given up after one retry",
        remedy="Run this again once the branch is quieter. The commits are kept.",
        details=_lines(again.stderr),
    )


def _rebase(name: str, path: Path, branch: str, upstream: str) -> Outcome | None:
    """Replay this checkout's commits onto the fetched tip. None means it worked.

    A conflict stops the machine every time. The append-only files are
    union-merged by the bundle's own git attributes, so a real conflict means
    two people wrote the same concept - a question about what is true, and the
    last thing to hand to an agent working quickly.
    """
    replayed = _git(path, "rebase", upstream)
    if replayed.returncode == 0:
        return None
    files = _conflicted(path)
    _git(path, "rebase", "--abort")
    if not files:
        # A rebase can fail without a conflict - no committer identity is the
        # one that actually happens - and calling that "two people wrote the
        # same concept" would send somebody looking for a disagreement that is
        # not there.
        return Outcome(
            name,
            BLOCKED,
            f"replaying `{branch}` onto `{upstream}` failed for a reason that is not a conflict",
            remedy="The rebase was aborted and your commits are untouched. Git's own words:",
            details=_lines(replayed.stdout + replayed.stderr),
        )
    return Outcome(
        name,
        BLOCKED,
        f"rebasing `{branch}` onto `{upstream}` conflicts, so the rebase was aborted and nothing pushed",
        remedy=(
            "Two people wrote the same thing, which is a question about what is true rather than "
            "a merge to perform. Resolve it by hand; your commits are untouched."
        ),
        details=files or _lines(replayed.stdout + replayed.stderr),
    )


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()][:5]


def checked_out_branch(path: Path) -> str | None:
    """The branch this checkout is on, or None if it is not on one.

    Used by `lint`, which answers the cheap half of the same question without a
    network call: a bundle filing into the wrong branch has stopped leaving the
    machine, and this is what says so before anyone wonders why.
    """
    if not path.is_dir():
        return None
    head = _git(path, "symbolic-ref", "--quiet", "--short", "HEAD")
    return head.stdout.strip() if head.returncode == 0 else None
