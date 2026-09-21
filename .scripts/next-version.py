#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""The next version, given the one that shipped and how big the change was.

Its own file rather than three lines of `awk` in the workflow, for the reason the
test invocation is its own file: what the release does should be runnable, and
readable, without a CI run to see it. `uv run .scripts/next-version.py 0.4.2
minor` answers the question on a laptop.

The bump level comes from a label on the merged pull request, which is the one
place a human already looks at the change as a whole. Reading it from commit
messages was the alternative and is rejected: the commit subjects here are
sentences about the work ("Let several people file into one bundle"), and turning
those into a machine's opinion about severity means writing them for the machine
instead.
"""

from __future__ import annotations

import argparse
import re
import sys

LEVELS = ("major", "minor", "patch")
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def next_version(current: str, level: str) -> str:
    match = SEMVER.match(current.strip())
    if not match:
        sys.exit(f"next-version: {current!r} is not a version of the form 1.2.3")
    major, minor, patch = (int(part) for part in match.groups())
    if level == "major":
        # Zero the ones beneath, always: 0.4.2 major is 1.0.0, never 1.4.2. The
        # mistake is invisible in the tag and permanent in the history.
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("current", help="the version that shipped last, as 1.2.3")
    parser.add_argument("level", choices=LEVELS, help="how big the change was")
    args = parser.parse_args()
    print(next_version(args.current, args.level))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
