"""End-to-end tests of the fkb skill: four cold sessions, no prior context.

Everything else in this suite checks parts in isolation. Here a real agent is
given a sentence and has to find the skill, work out what it is being asked for,
and act. The checks are deliberately about what it left behind rather than what
it said: a file on disk, a manifest, a link in a concept. An agent can describe
any of these convincingly without having done them.

The four cover the two directions and the two edges: read from a bundle, write
into one, arrive at a machine where nothing exists, and link between two bundles
that do not know about each other.

Slow, needs network and node. Marked `agent`, like everything that drives one.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from disposable_agent import DisposableAgent
from git_environment import outside_any_repository

pytestmark = pytest.mark.agent

REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_LINT = REPO_ROOT / "skills" / "fkb" / "scripts" / "bundle_lint.py"
FKB = REPO_ROOT / "skills" / "fkb" / "scripts" / "fkb"
REPO_SKILLS = REPO_ROOT / "skills"

FLOOR = "required:\n- type\n- title\n- description\n- status\n- generated\n"
INDEX = '---\nokf_version: "0.2"\n---\n\n# Notes\n\nThings worth keeping.\n'
LOG = "# Log\n\n## 2026-01-01\n\n- created the bundle\n"

# A fact with no plausible source on the web, so a concept containing it can only
# have come from the message rather than from the model's own memory.
FACT = "the deploy key for the mesh-relay staging box rotates every 41 days"
MARKER = "mesh-relay"

# The same trick in the other direction, and it has to be sharper. A fact written
# here in plain text is a fact on this machine, and the agent runs with permission
# to read outside its own home so that it can load skills at all: the first
# version of this test was answered correctly out of this file, cited by line
# number. So the revision is minted per run and exists nowhere but the bundle the
# test just wrote.
KNOWN_MARKER = f"{uuid4().hex[:8]}-kestrel"
KNOWN_CONCEPT = f"""---
type: reference
title: Quillhaven toolchain pin
description: Which toolchain revision Quillhaven builds are pinned to, and why.
status: published
generated:
  by: "human:tester"
  at: 2026-01-01
---

# Quillhaven toolchain pin

Quillhaven builds are pinned to toolchain revision {KNOWN_MARKER}. The pin exists because
later revisions reorder link units, which makes build output non-reproducible.
"""


def _bundle(root: Path, concepts: dict[str, str] | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    entries = "".join(f"- [{name}]({name})\n" for name in (concepts or {}))
    (root / "index.md").write_text(INDEX + entries, encoding="utf-8")
    (root / "log.md").write_text(LOG, encoding="utf-8")
    (root / "fkb.yaml").write_text(FLOOR, encoding="utf-8")
    for relative, text in (concepts or {}).items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _manifest(agent: DisposableAgent, body: str) -> None:
    config = agent.home / ".config" / "fkb"
    config.mkdir(parents=True, exist_ok=True)
    (config / "workspace.yaml").write_text(body, encoding="utf-8")


def _seed_bundle(agent: DisposableAgent, concepts: dict[str, str] | None = None) -> Path:
    """One minimal writable bundle in the agent's own home, plus the manifest naming it."""
    bundle = _bundle(agent.home / "knowledge" / "notes", concepts)
    _manifest(agent, f"bundles:\n  notes:\n    path: {bundle}\n    writable: true\n")
    return bundle


def _concepts_in(bundle: Path) -> list[Path]:
    return [path for path in bundle.rglob("*.md") if path.name not in {"index.md", "log.md"}]


def _run_cli(agent: DisposableAgent, *args: str) -> subprocess.CompletedProcess[str]:
    """Run `fkb` against the agent's home, to check what it left is usable."""
    env = outside_any_repository(
        HOME=str(agent.home),
        XDG_CONFIG_HOME=str(agent.home / ".config"),
    )
    if importlib.util.find_spec("yaml") is None:
        command = ["uv", "run", "--script", str(FKB), *args]
    else:
        command = [sys.executable, str(FKB), *args]
    return subprocess.run(command, capture_output=True, text=True, check=False, env=env)


def _lint(bundle: Path) -> subprocess.CompletedProcess[str]:
    args = ["--bundle-root", str(bundle), "--floor", str(bundle / "fkb.yaml")]
    if importlib.util.find_spec("yaml") is None:
        command = ["uv", "run", "--script", str(BUNDLE_LINT), *args]
    else:
        command = [sys.executable, str(BUNDLE_LINT), *args]
    return subprocess.run(command, capture_output=True, text=True, check=False, env=outside_any_repository())


def test_a_cold_session_answers_from_the_bundle_and_cites_it(agent_factory) -> None:
    """Asked a question the bundle answers, the agent reads it rather than guessing.

    The fact exists nowhere but in the seeded concept, so an answer carrying it
    can only have come from the file. The citation is checked separately and
    matters as much: an answer without a path cannot be followed up, and a person
    has no way to tell it came from their own knowledge base rather than from the
    model.
    """
    agent: DisposableAgent = agent_factory(REPO_SKILLS)
    _seed_bundle(agent, {"quillhaven_toolchain_pin.md": KNOWN_CONCEPT})

    result = agent.run("What toolchain revision are Quillhaven builds pinned to, and why?")
    assert result.returncode == 0, f"opencode exited {result.returncode}\n{result.stderr}"

    answer = result.text
    assert KNOWN_MARKER in answer, (
        "the agent did not find the answer that was sitting in the bundle.\n"
        f"--- transcript ---\n{answer.strip() or '(empty)'}"
    )
    assert "quillhaven_toolchain_pin" in answer, (
        f"the answer cites no concept, so nobody can check it:\n{answer.strip()}"
    )


def test_a_cold_session_files_a_conformant_concept(agent_factory) -> None:
    """Given something worth keeping, the agent writes a file the bundle accepts.

    The bundle declares a floor of five fields, none of which the message
    mentions. Passing means the agent read the declaration rather than guessing,
    which is the property that keeps a single statement of what a concept must
    carry from quietly becoming two.
    """
    agent: DisposableAgent = agent_factory(REPO_SKILLS)
    assert (agent.agents_skills / "fkb" / "SKILL.md").is_file(), "the fkb skill was not installed"
    compiled = list((agent.agents_skills / "fkb").rglob("*.pyc"))
    assert not compiled, f"the install carries compiled files naming the developer's checkout: {compiled}"
    bundle = _seed_bundle(agent)

    result = agent.run(f"Note this down in the knowledge base: {FACT}.")
    assert result.returncode == 0, f"opencode exited {result.returncode}\n{result.stderr}"

    written = _concepts_in(bundle)
    assert written, f"no concept was written into the bundle.\n--- transcript ---\n{result.text.strip() or '(empty)'}"

    bodies = "\n".join(path.read_text(encoding="utf-8") for path in written)
    assert MARKER in bodies, f"the concept does not carry the fact it was given:\n{bodies}"

    linted = _lint(bundle)
    assert linted.returncode == 0, (
        f"the filed concept does not satisfy the bundle's own floor.\n{linted.stdout}{linted.stderr}"
    )

    index = (bundle / "index.md").read_text(encoding="utf-8")
    assert any(path.name in index for path in written), (
        f"the concept was written but never linked from the index:\n{index}"
    )


def test_a_cold_session_onboards_a_machine_with_nothing_on_it(agent_factory) -> None:
    """The question the skill has to answer out of its own pocket.

    Someone installs it, opens a session and asks what it is. No manifest, no
    bundles, no README within reach. A plausible summary of the design is the
    failure mode here, and it is easy to mistake for a pass, so the assertion is
    not about the words: a workspace has to exist afterwards and `fkb list` has
    to run against it.

    The agent is told to go ahead, because being asked to explain something is
    not the same as being asked to change the machine.
    """
    agent: DisposableAgent = agent_factory(REPO_SKILLS)
    manifest = agent.home / ".config" / "fkb" / "workspace.yaml"
    assert not manifest.exists(), "the fixture is not a cold machine"

    result = agent.run(
        "I just installed this fkb thing and I have no idea what it is or how to start. "
        "Explain it to me and get me set up."
    )
    assert result.returncode == 0, f"opencode exited {result.returncode}\n{result.stderr}"

    assert manifest.exists(), (
        "no workspace was left behind, so the answer was a description rather than a start.\n"
        f"--- transcript ---\n{result.text.strip() or '(empty)'}"
    )
    assert "workspace_root" in manifest.read_text(encoding="utf-8")

    listed = _run_cli(agent, "list")
    assert listed.returncode == 0, f"the workspace it created does not load:\n{listed.stdout}{listed.stderr}"

    stray = list((agent.home / "work").rglob("*.md")) if (agent.home / "work").is_dir() else []
    assert not stray, f"knowledge was scattered into the working directory: {stray}"


def test_a_cold_session_cites_across_bundles_with_a_real_url(agent_factory) -> None:
    """A link out of one bundle into another is absolute, and comes from the CLI.

    This is the only check that the federation's whole point is reachable. The
    bundles do not know about each other, so a relative path is a fact about one
    disk that dies on publication - and writing one is the natural thing to do,
    which is why it is worth failing the test over.
    """
    agent: DisposableAgent = agent_factory(REPO_SKILLS)
    public = _bundle(agent.home / "knowledge" / "public", {"quillhaven_toolchain_pin.md": KNOWN_CONCEPT})
    private = _bundle(agent.home / "knowledge" / "private")
    _manifest(
        agent,
        f"bundles:\n"
        f"  public:\n    path: {public}\n    writable: true\n"
        f"    referenceable_by: '*'\n"
        f"    publish:\n      url: https://kb.invalid/docs/\n      style: directory\n"
        f"  private:\n    path: {private}\n    writable: true\n",
    )

    result = agent.run(
        "File a note in the private bundle: our release checklist must confirm the toolchain "
        "pin before tagging. Link it to the existing Quillhaven toolchain pin concept in the "
        "public bundle."
    )
    assert result.returncode == 0, f"opencode exited {result.returncode}\n{result.stderr}"

    written = _concepts_in(private)
    assert written, f"nothing was filed.\n--- transcript ---\n{result.text.strip() or '(empty)'}"

    bodies = "\n".join(path.read_text(encoding="utf-8") for path in written)
    assert "https://kb.invalid/docs/quillhaven_toolchain_pin/" in bodies, (
        f"the cross-bundle link is not the URL `fkb url` produces for that concept.\n{bodies}"
    )
    assert "../" not in bodies, (
        f"a relative path was written across a bundle boundary, which cannot survive publishing:\n{bodies}"
    )
