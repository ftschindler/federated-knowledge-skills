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
    """
    if root.exists() and any(root.iterdir()):
        sys.exit(f"fkb: {root} already exists and is not empty")
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.md").write_text(TEMPLATE_INDEX.format(name=name), encoding="utf-8")
    (root / "log.md").write_text(TEMPLATE_LOG.format(date=date), encoding="utf-8")
    (root / "fkb.yaml").write_text(TEMPLATE_FLOOR, encoding="utf-8")
    return root
