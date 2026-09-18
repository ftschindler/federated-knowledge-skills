"""How a bundle arrives: the machinery behind `fkb init` and `fkb add`.

Three ways a bundle turns up - a remote repo, a checkout already on disk, and one
that does not exist yet - and all three end in the same place, a manifest entry
naming policy nobody can infer. Registration was mechanical enough to be a
command long before it was one, and doing it by hand cost three judgement calls
in a single session: the bundle root is not the repository root, a decoy sample
bundle looks exactly like a real one, and a checkout can sit outside the
workspace it is registered under.

Kept out of the command file because the rules here are about disk and URLs
rather than about output, and because they want testing directly.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from workspace import Publish

RESERVED = {"index.md", "log.md"}

TEMPLATE_INDEX = """---
okf_version: "0.2"
---

# {name}

An empty bundle. Concepts are linked from here as they are written.
"""

TEMPLATE_LOG = """# Update Log

## {date}

- The bundle was created.
"""

TEMPLATE_FLOOR = """# What a concept in this bundle must carry, beyond OKF's own `type`.
# The bundle's pre-commit hook and `fkb lint` both read this file, so it is the
# only place that decides. Add a field here and every concept must carry it.
required:
- type
- title
- description
- status
- generated
"""


TEMPLATE_ATTRIBUTES = """# The two files everybody appends to, merged by keeping both sides.
# A concept is one file one person wrote, so it never conflicts; the index and
# the log are where two people writing on the same day would collide over lines
# neither of them disagrees about. `union` keeps both, in order, and leaves a
# real conflict - two people writing the same concept - as the only one a person
# is asked about.
index.md merge=union
log.md merge=union
"""


def find_bundle_root(checkout: Path) -> Path:
    """The shallowest `index.md` in a checkout, or a refusal naming the candidates.

    A repository is usually infrastructure at the top with the bundle somewhere
    beneath, so the root has to be found rather than assumed. Depth is the signal
    and it is not a guess: an OKF bundle's index sits at its root, and anything
    deeper is a section index or, in the case that caused this function, a sample
    bundle shipped inside a repository about bundles. Registering that sample
    would have published an example as somebody's knowledge.

    A tie is refused rather than broken. Two indexes at one depth are two
    plausible bundles, and picking the first is the failure the journal recorded:
    inference presented as a decision.
    """
    found = [p for p in checkout.rglob("index.md") if p.is_file() and ".git" not in p.parts]
    if not found:
        sys.exit(
            f"fkb: no `index.md` anywhere under {checkout}, so there is no bundle root to find.\n"
            "An OKF bundle has an index at its root. Point `--path` at the bundle itself if "
            "this checkout holds one under another name."
        )
    shallowest = min(len(p.relative_to(checkout).parts) for p in found)
    candidates = sorted(p for p in found if len(p.relative_to(checkout).parts) == shallowest)
    if len(candidates) > 1:
        listed = "\n".join(f"  {p.parent.relative_to(checkout) or '.'}" for p in candidates)
        sys.exit(
            f"fkb: {checkout} holds more than one candidate bundle root:\n{listed}\n"
            "Name the one you mean with `--path`."
        )
    return candidates[0].parent


def derive_publish(sample_url: str, relative: str) -> Publish:
    """Recover `{url, style}` from one concept's published URL and its local path.

    Both halves of `publish` have a plausible wrong answer - a repository's
    landing page instead of the prefix its concepts hang under, and a style
    guessed from the presence of an `mkdocs.yml` - and a wrong one is silent
    forever after, because nothing fetches a URL. Asking instead for the address
    of a page the person can already open turns two abstract questions into one
    they answer by pasting from a browser, and it is the only moment in a
    bundle's life when the promise can be checked against something real.

    Each style is asked what suffix it would produce for this path; the one whose
    suffix the URL actually ends with is the answer, and what remains is the
    prefix. A URL that matches nothing is reported with what was expected, since
    at that point the sample and the path disagree and only the person knows
    which is wrong.
    """
    url = sample_url.strip()
    expectations = []
    for style in Publish.STYLES:
        probe = Publish("<sample>", {"url": "https://x.invalid/", "style": style})
        suffix = probe.published_path(relative)
        expectations.append((style, suffix))
        # An empty suffix means the concept is the bundle's own index, published
        # at the prefix itself; there is nothing to strip and the URL is it.
        if not suffix and url.endswith("/"):
            return Publish("<derived>", {"url": url, "style": style})
        if suffix and url.endswith(suffix):
            return Publish("<derived>", {"url": url[: -len(suffix)], "style": style})

    shapes = "\n".join(f"  {style:<9} would end in  {suffix or '/'}" for style, suffix in expectations)
    sys.exit(
        f"fkb: `{url}` is not how `{relative}` would be published under any known style.\n{shapes}\n"
        "Either the URL is not that concept's page, or the path is not what the site was built from."
    )


def clone(remote: str, into: Path) -> Path:
    """Clone a remote under the workspace, refusing to write over anything."""
    name = remote.rstrip("/").split("/")[-1].removesuffix(".git")
    destination = into / name
    if destination.exists():
        sys.exit(
            f"fkb: {destination} already exists. If it is the bundle you mean, register it "
            "with `--path` instead of cloning it again."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["git", "clone", remote, str(destination)], check=False)
    if result.returncode != 0:
        sys.exit(f"fkb: `git clone {remote}` failed; nothing was registered")
    return destination


def scaffold(root: Path, name: str, date: str) -> Path:
    """Write the smallest bundle that passes its own lint.

    An index, a log and a floor declaration, and no concepts: a bundle with a
    concept in it would be a bundle with an opinion about what belongs there,
    and the floor is the only opinion this is entitled to have. The floor it
    writes is the one the existing bundles converged on, which a new bundle is
    free to edit before filing anything.

    The `.gitattributes` beside them is written even for a bundle nobody shares,
    because the day it is shared is not the day anyone remembers to add it, and
    on a bundle of one it does nothing at all.
    """
    if root.exists() and any(root.iterdir()):
        sys.exit(f"fkb: {root} already exists and is not empty")
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.md").write_text(TEMPLATE_INDEX.format(name=name), encoding="utf-8")
    (root / "log.md").write_text(TEMPLATE_LOG.format(date=date), encoding="utf-8")
    (root / "fkb.yaml").write_text(TEMPLATE_FLOOR, encoding="utf-8")
    (root / ".gitattributes").write_text(TEMPLATE_ATTRIBUTES, encoding="utf-8")
    return root


def checkout(root: Path, branch: str) -> bool:
    """Put a registered bundle on the branch it is shared on. True if it now is.

    This is what makes leaving the reviewed branch as the repository's default
    safe (DESIGN §10). A clone lands on the default branch, which is the one
    protected against direct pushes, so a person who was never told would file
    into the branch their commits cannot leave - and would find out days later,
    from a teammate who never saw the concept.

    A branch that exists locally or on a remote is checked out; one that exists
    nowhere is created from where the checkout already is, since a bundle whose
    shared branch has not been cut yet is a bundle at the start of being shared
    rather than a mistake. Failure is reported to the caller rather than fatal:
    the registration is still correct, and `sync` refuses loudly until the
    checkout catches up.
    """
    if shutil.which("git") is None:
        return False
    quiet = {"GIT_TERMINAL_PROMPT": "0"}
    inside = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    if inside.returncode != 0:
        return False
    for attempt in (["checkout", branch], ["checkout", "-b", branch]):
        done = subprocess.run(
            ["git", "-C", str(root), *attempt],
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, **quiet},
        )
        if done.returncode == 0:
            return True
    return False


def git_init(root: Path) -> bool:
    """Make a scaffolded bundle a git repository. True if it now is one.

    This is here rather than in the skill because it has no judgement in it: a
    bundle that is a repository has history, hooks and a way to be shared, and a
    bundle that is not has none of those and no compensating advantage. Leaving
    it to prose meant every route to a new bundle had to remember, and the one
    that mattered most - somebody's first private bundle - is the one written by
    an agent that had just been told not to run git.

    What stays in the skill is the half that cannot be hardcoded: which hook
    revision to pin, which is a fact about a remote right now, and the first
    commit, which needs an author this program has no business inventing.

    A machine without git still gets a bundle. Every check here runs on a
    directory, and history is the only layer that can be added later without
    touching a single concept.
    """
    if shutil.which("git") is None:
        return False
    if (root / ".git").exists():
        return True
    done = subprocess.run(["git", "init", str(root)], capture_output=True, text=True, check=False)
    if done.returncode != 0:
        print(f"fkb: `git init` failed, leaving a plain directory\n{done.stderr}", file=sys.stderr)
        return False
    return True
