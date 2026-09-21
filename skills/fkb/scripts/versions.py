"""What version this skill is, what version the setup on this machine is, and what lies between.

A skill is installed by copying `skills/fkb/` somewhere a harness reads. Nothing
of the repository survives that: no tags, no history, no remote. So the one
honest answer to "which version am I" is a file that travels with the copy, and
`VERSION` beside `SKILL.md` is it. Everything here reads that file rather than
asking git, because on the machines this actually runs on there is no git to ask.

The other half is the manifest. It is the only state this project owns that
outlives an upgrade - bundles belong to the person, and the skill directory is
replaced wholesale - so it is the only place a "what has this setup been through"
stamp can live. A manifest with no `version` is not an error and never becomes
one: it is every setup made before this field existed, and the baseline it gets
is `0.0.0` so that the guides written since all still apply to it.

The comparison is made here rather than in an agent's reading of a file, because
"is 0.10.0 newer than 0.9.0" is exactly the kind of question a model answers
confidently and wrongly.

Nothing in here writes anything except `stamp`, and `stamp` edits lines rather
than reserialising the manifest: that file is hand-edited and carries comments a
YAML round-trip would silently drop.
"""

from __future__ import annotations

import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = SKILL_ROOT / "VERSION"
MIGRATIONS = SKILL_ROOT / "references" / "migrations"

# What a manifest that predates the `version` field is taken to be. Not the
# current version: that would declare every existing setup already migrated and
# skip the first guide ever written, which is the one case this whole mechanism
# exists for.
BASELINE = (0, 0, 0)

_SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_VERSION_LINE = re.compile(r"^version:.*$", re.MULTILINE)


def parse(text: str) -> tuple[int, int, int] | None:
    """A version as three numbers, or None if it is not one.

    Returning None rather than raising because both callers have somewhere
    better to go than a traceback: an unreadable `VERSION` means an install that
    was tampered with, and an unreadable manifest stamp means a hand-edit, and
    both are reported as text to a person.
    """
    match = _SEMVER.match(text.strip())
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def render(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def skill_version() -> tuple[int, int, int]:
    """The version of this installed copy, from the file that travelled with it."""
    try:
        text = VERSION_FILE.read_text(encoding="utf-8")
    except OSError:
        return BASELINE
    return parse(text) or BASELINE


def manifest_version(data: dict) -> tuple[int, int, int]:
    """The version this workspace was last brought up to.

    Absent is the common case for a while yet, and means the baseline. A present
    but unparseable value is also treated as the baseline rather than refused:
    the cost of being wrong is that guides already applied get offered twice,
    which a person can decline, and the cost of refusing is a machine that
    cannot read its own bundles over a typo in a field none of them use.
    """
    declared = data.get("version")
    if declared is None:
        return BASELINE
    return parse(str(declared)) or BASELINE


def guides(after: tuple[int, int, int], through: tuple[int, int, int]) -> list[Path]:
    """The migration guides that apply, oldest first.

    A guide is named for the release that introduced the change, and covers the
    step from the release before it. So the ones a setup still owes are those
    strictly newer than where it stands and no newer than the skill reading it -
    the skill cannot honour a guide it does not carry.

    Releases mostly change nothing a setup has to do, and those leave no file
    here. A gap in the series is the normal shape, not a missing page.
    """
    if not MIGRATIONS.is_dir():
        return []
    found = []
    for guide in MIGRATIONS.glob("*.md"):
        version = parse(guide.stem)
        if version and after < version <= through:
            found.append((version, guide))
    return [guide for _, guide in sorted(found)]


def stamp(path: Path, version: tuple[int, int, int]) -> None:
    """Record in the manifest that this setup now stands at `version`.

    Line surgery rather than `yaml.safe_dump`, because the manifest is a file
    people edit: it opens with four lines of comment explaining what `path`
    means, and a round-trip through the parser returns the data without them.
    Losing a comment is worse here than anywhere else in the CLI - it is the
    only documentation of a policy decision that sits where the decision does.
    """
    text = path.read_text(encoding="utf-8")
    line = f"version: {render(version)}"
    if _VERSION_LINE.search(text):
        path.write_text(_VERSION_LINE.sub(line, text, count=1), encoding="utf-8")
        return
    # Under the opening comment rather than above it: that comment introduces the
    # file as a whole, and a stamp wedged in front of it reads as a heading for
    # prose it has nothing to do with.
    lines = text.splitlines(keepends=True)
    at = 0
    while at < len(lines) and (lines[at].startswith("#") or not lines[at].strip()):
        at += 1
    lines.insert(at, line + "\n")
    path.write_text("".join(lines), encoding="utf-8")
