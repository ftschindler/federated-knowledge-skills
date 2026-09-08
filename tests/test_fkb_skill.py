"""End-to-end test of the fkb skill: a cold session files a concept.

This is the acceptance test for filing. Everything before it checks parts in
isolation; here a real agent, with no prior context, is given a fact worth
keeping and has to find the skill, choose a bundle, write a conformant concept
and link it. The check is not what the agent said but what it left on disk, run
through the same linter the bundle's own pre-commit hook runs.

Slow, needs network and node. Marked `agent`, like everything that drives one.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest
from disposable_agent import DisposableAgent

pytestmark = pytest.mark.agent

REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_LINT = REPO_ROOT / "skills" / "fkb" / "scripts" / "bundle_lint.py"
REPO_SKILLS = REPO_ROOT / "skills"

FLOOR = "required:\n- type\n- title\n- description\n- status\n- generated\n"
INDEX = '---\nokf_version: "0.2"\n---\n\n# Notes\n\nThings worth keeping.\n'
LOG = "# Log\n\n## 2026-01-01\n\n- created the bundle\n"

# A fact with no plausible source on the web, so a concept containing it can only
# have come from the message rather than from the model's own memory.
FACT = "the deploy key for the mesh-relay staging box rotates every 41 days"
MARKER = "mesh-relay"


def _seed_bundle(agent: DisposableAgent) -> Path:
    """A minimal writable bundle in the agent's own home, plus the manifest naming it."""
    bundle = agent.home / "knowledge" / "notes"
    bundle.mkdir(parents=True)
    (bundle / "index.md").write_text(INDEX, encoding="utf-8")
    (bundle / "log.md").write_text(LOG, encoding="utf-8")
    (bundle / "okf-floor.yaml").write_text(FLOOR, encoding="utf-8")

    config = agent.home / ".config" / "fkb"
    config.mkdir(parents=True, exist_ok=True)
    (config / "workspace.yaml").write_text(
        f"bundles:\n  notes:\n    path: {bundle}\n    writable: true\n",
        encoding="utf-8",
    )
    return bundle


def _lint(bundle: Path) -> subprocess.CompletedProcess[str]:
    args = ["--bundle-root", str(bundle), "--floor", str(bundle / "okf-floor.yaml")]
    if importlib.util.find_spec("yaml") is None:
        command = ["uv", "run", "--script", str(BUNDLE_LINT), *args]
    else:
        command = [sys.executable, str(BUNDLE_LINT), *args]
    return subprocess.run(command, capture_output=True, text=True, check=False, env=os.environ.copy())


def test_a_cold_session_files_a_conformant_concept(agent_factory) -> None:
    """Given something worth keeping, the agent writes a file the bundle accepts.

    The bundle declares a floor of five fields, none of which the message
    mentions. Passing means the agent read the declaration rather than guessing,
    which is the property that keeps a single statement of what a concept must
    carry from quietly becoming two.
    """
    agent: DisposableAgent = agent_factory(REPO_SKILLS)
    assert (agent.agents_skills / "fkb" / "SKILL.md").is_file(), "the fkb skill was not installed"
    bundle = _seed_bundle(agent)

    result = agent.run(f"Note this down in the knowledge base: {FACT}.")
    assert result.returncode == 0, f"opencode exited {result.returncode}\n{result.stderr}"

    written = [path for path in bundle.rglob("*.md") if path.name not in {"index.md", "log.md"}]
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


def test_the_skill_refuses_to_invent_a_workspace(agent_factory) -> None:
    """With no manifest, filing has to stop rather than guess a directory.

    Setup is hand-written for now, so an agent that helpfully creates a workspace
    would be inventing the one thing nobody has decided yet - and would scatter
    knowledge into a path the person never chose.
    """
    agent: DisposableAgent = agent_factory(REPO_SKILLS)
    result = agent.run(f"Note this down in the knowledge base: {FACT}.")

    assert result.returncode == 0, f"opencode exited {result.returncode}\n{result.stderr}"
    manifest = agent.home / ".config" / "fkb" / "workspace.yaml"
    assert not manifest.exists(), "the agent created a workspace manifest it was told not to create"
    stray = [p for p in (agent.home / "work").rglob("*.md")] if (agent.home / "work").is_dir() else []
    assert not stray, f"the agent filed knowledge into its working directory instead of stopping: {stray}"
