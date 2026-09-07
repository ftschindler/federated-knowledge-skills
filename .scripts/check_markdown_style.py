#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Forbid two markdown constructs this repo does not use.

- `---` thematic breaks. Headings already separate sections; a rule line adds a
  second, redundant separator that the rendered page shows as noise. YAML
  frontmatter delimiters are exempt, as are table delimiter rows (`| --- |`).
- The em dash `—`. Use `-` instead, so prose is typeable on any keyboard and
  greps the same way everywhere.

Both checks skip fenced code blocks: a snippet quotes something else's syntax.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s{0,3}(?:```|~~~)")
THEMATIC_BREAK = re.compile(r"^\s{0,3}-{3,}\s*$")
EM_DASH = "\u2014"


def check(path: Path) -> list[str]:
    """Return one message per offending line in `path`."""
    lines = path.read_text(encoding="utf-8").splitlines()
    frontmatter_close = None
    if lines and lines[0].strip() == "---":
        for number, line in enumerate(lines[1:], start=2):
            if line.strip() == "---":
                frontmatter_close = number
                break

    problems: list[str] = []
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if number == 1 and frontmatter_close is not None:
            continue
        if number == frontmatter_close:
            continue
        if THEMATIC_BREAK.match(line):
            problems.append(f"{path}:{number}: `---` separator - delete it, headings already separate sections")
        if EM_DASH in line:
            problems.append(f"{path}:{number}: em dash `{EM_DASH}` - use `-` instead")
    return problems


def main(argv: list[str]) -> int:
    problems = [message for name in argv for message in check(Path(name))]
    for message in problems:
        print(message)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
