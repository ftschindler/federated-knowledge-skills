#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Build a disposable agent and drop into a shell inside its world — for
deliberate hands-on inspection of how an agent behaves with a set of skills.

Usage:
  .scripts/disposable-agent.py                 # install this repo's skills/, enter shell
  .scripts/disposable-agent.py --skills DIR    # install skill directories from DIR
  .scripts/disposable-agent.py --no-skills     # bare agent, nothing installed
  .scripts/disposable-agent.py --keep          # build and print, but do NOT spawn a shell
  .scripts/disposable-agent.py --dir DIR       # build under DIR instead of a fresh mktemp

Inside the spawned shell, `opencode` sees only this agent's skills and config.
Type `exit` to leave; the directory is left on disk so you can re-enter with the
printed command.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

# Import the shared builder from tests/ (single source of truth).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from disposable_agent import REPO_SKILLS_DIR, build_disposable_agent, have


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--skills", type=Path, help="install skill directories from here")
    source.add_argument("--no-skills", action="store_true", help="install opencode only, no skills")
    parser.add_argument("--keep", action="store_true", help="don't spawn a shell, just build + print")
    parser.add_argument("--dir", type=Path, help="build under this directory instead of mktemp")
    args = parser.parse_args()

    for tool in ("node", "npm", "npx"):
        if not have(tool):
            print(f"error: '{tool}' is required but not found on PATH", file=sys.stderr)
            return 1

    skills_dir = None if args.no_skills else (args.skills or REPO_SKILLS_DIR)
    if skills_dir is not None and not skills_dir.is_dir():
        print(
            f"note: no skills at {skills_dir} — building a bare agent.\n"
            "      This repo ships no skills yet; see DESIGN.md.",
            file=sys.stderr,
        )

    root = args.dir or Path(tempfile.mkdtemp(prefix="fkb-agent-"))
    root.mkdir(parents=True, exist_ok=True)
    print(f"Building a disposable agent under {root} (skills={skills_dir or 'none'})…", file=sys.stderr)

    agent = build_disposable_agent(root, skills_dir=skills_dir)

    print(agent.enter_hint(reason="Disposable agent ready."), file=sys.stderr)

    if args.keep:
        return 0

    # Spawn an interactive shell with the redirected environment.
    return subprocess.run(["bash"], cwd=agent.work, env=agent.env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
