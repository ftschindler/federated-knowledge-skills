"""A fake home: a house with `fkb` installed in it, and nothing of yours inside.

`fkb` reads its manifest from `$XDG_CONFIG_HOME/fkb/workspace.yaml`, falling back
to `~/.config` when that variable is unset. Both roads lead somewhere real on a
developer's machine, and one of them is the live federation, so a test that
redirects only `XDG_CONFIG_HOME` leaves a bug one missing variable away from
rewriting the manifest a person actually uses. Everything here exists to make
that unreachable: `HOME` and every `XDG_*` point inside the given directory, and
the fallback branch becomes something a test can exercise on purpose rather than
something it must avoid.

The skill is installed into the house rather than run from the source tree,
because the source tree is not an arrangement anyone has. A skill is copied into
`~/.agents/skills/fkb/` and runs from whatever went with it, so shipping a file
the install would not carry is a failure this catches and a source-tree run does
not.

Sibling of `disposable_agent.py` and deliberately much smaller: that one builds an
agent because it needs an LLM to drive the skill's prose, this one needs only a
shell and the commands.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_SKILL = REPO_ROOT / "skills" / "fkb"


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


@dataclass
class FakeHome:
    """One throwaway machine: a home directory, a skill installed in it, a workspace."""

    root: Path
    skill: Path

    @property
    def env(self) -> dict[str, str]:
        """The environment that makes this house the only one a subprocess can see.

        `XDG_CONFIG_HOME` is set explicitly rather than left to the fallback,
        because that is how a real session runs. The test that cares about the
        fallback removes it deliberately with `env_without_xdg`.
        """
        home = str(self.root)
        return {
            "HOME": home,
            "XDG_CONFIG_HOME": str(self.root / ".config"),
            "XDG_DATA_HOME": str(self.root / ".local" / "share"),
            "XDG_CACHE_HOME": str(self.root / ".cache"),
            "XDG_STATE_HOME": str(self.root / ".local" / "state"),
        }

    @property
    def env_without_xdg(self) -> dict[str, str]:
        """The same house with `XDG_CONFIG_HOME` unset, to reach the `~/.config` fallback."""
        stripped = self.env
        del stripped["XDG_CONFIG_HOME"]
        return stripped

    @property
    def fkb(self) -> Path:
        return self.skill / "scripts" / "fkb"

    @property
    def manifest(self) -> Path:
        return self.root / ".config" / "fkb" / "workspace.yaml"

    @property
    def workspace_root(self) -> Path:
        return self.root / "knowledge"

    def run(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        """Run `fkb` inside this house, as a person or an agent would.

        The pytest interpreter often has no pyyaml - the pre-commit hook that
        runs these deliberately installs nothing - in which case `uv` resolves
        the script's own inline metadata instead.
        """
        if importlib.util.find_spec("yaml") is None:
            command = ["uv", "run", "--script", str(self.fkb), *args]
        else:
            command = [sys.executable, str(self.fkb), *args]
        chosen = self.env if env is None else env
        # The parent environment is carried for PATH and the like, then the
        # house overrides every variable that could lead out of it. A variable
        # the house deletes is deleted here too, or the fallback test would
        # silently keep reading the developer's own config.
        merged = {k: v for k, v in os.environ.items() if k not in {"XDG_CONFIG_HOME", "HOME"}}
        merged.update(chosen)
        if "XDG_CONFIG_HOME" not in chosen:
            merged.pop("XDG_CONFIG_HOME", None)
        return subprocess.run(command, capture_output=True, text=True, check=False, env=merged)

    def bundle(self, name: str, files: dict[str, str] | None = None) -> Path:
        """A minimal bundle on disk, for the cases that do not want a real one."""
        root = self.workspace_root / name
        root.mkdir(parents=True, exist_ok=True)
        (root / "index.md").write_text(f'---\nokf_version: "0.2"\n---\n\n# {name}\n', encoding="utf-8")
        for relative, text in (files or {}).items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return root


def build_fake_home(root: Path) -> FakeHome:
    """Install the skill into a new house and hand it back."""
    skill = root / ".agents" / "skills" / "fkb"
    skill.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE_SKILL, skill)
    (root / ".config").mkdir(parents=True, exist_ok=True)
    return FakeHome(root=root, skill=skill)


def local_remote(path: Path, layout: dict[str, str]) -> str:
    """A real git repository on disk, to be cloned over `file://`.

    Cloning is mostly mechanics - does the checkout land under `workspace_root`,
    is the entry written, is an existing directory refused - and mechanics do not
    need somebody else's server. What a real remote is for is repository *shapes*
    nobody here controls, which is a different test and a different marker.
    """
    path.mkdir(parents=True, exist_ok=True)
    for relative, text in layout.items():
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    quiet = {"GIT_TERMINAL_PROMPT": "0"}
    identity = [
        "-c",
        "user.email=test@invalid",
        "-c",
        "user.name=Test",
        "-c",
        "commit.gpgsign=false",
    ]
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True, env={**os.environ, **quiet})
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True, env={**os.environ, **quiet})
    subprocess.run(
        ["git", "-C", str(path), *identity, "commit", "-qm", "initial"],
        check=True,
        env={**os.environ, **quiet},
    )
    return f"file://{path}"
