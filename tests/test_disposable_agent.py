"""Tests for the disposable agent itself.

This repository currently ships no skills: the previous architecture was removed
and its replacement is specified in DESIGN.md but not yet built. The machinery
that drove those skills survived, because building a throwaway agent and talking
to it is independent of what is being tested.

Without a test it would rot silently — a bumped opencode, a changed npm layout or
a new permission prompt would only surface once someone needed it. These two
tests keep it exercised. They also document the contract the next skill tests
build on: author a skill directory, install it, send a message, read the reply.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from disposable_agent import DisposableAgent

pytestmark = pytest.mark.agent

# Deliberately odd so it cannot plausibly appear by chance in a model's output.
CANARY = "AGENT-CANARY-7F3A"


def test_a_bare_agent_runs_and_touches_nothing_real(bare_agent: DisposableAgent) -> None:
    """The agent is runnable, and everything it reads or writes is its own."""
    assert bare_agent.opencode_bin.is_file(), "no opencode binary was located"

    # The whole point is that nothing reaches the developer's real home.
    assert bare_agent.env["HOME"] == str(bare_agent.home)
    for var in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"):
        assert bare_agent.env[var].startswith(str(bare_agent.home)), var

    # The permission grant is what lets a run reach ~/.agents/skills at all.
    config = bare_agent.home / ".config" / "opencode" / "opencode.json"
    assert config.is_file(), "opencode config was not written"
    assert "external_directory" in config.read_text(encoding="utf-8")

    assert bare_agent.agents_skills.exists() is False or not any(bare_agent.agents_skills.iterdir()), (
        "a bare agent must have no skills installed"
    )


def test_an_installed_skill_reaches_the_model_and_is_followed(
    tmp_path: Path,
    agent_factory,
) -> None:
    """A skill installed into the agent changes what it answers.

    This is the full chain the future fkb tests need: skill authored on disk,
    installed as a user would install it, discovered by the agent, activated by
    description match, and its instruction reflected in the transcript.
    """
    skills_dir = tmp_path / "skills"
    canary = skills_dir / "canary"
    canary.mkdir(parents=True)
    (canary / "SKILL.md").write_text(
        textwrap.dedent(f"""\
        ---
        name: canary
        description: >-
          Report the canary token. Use when the user asks for the canary, the
          canary token, or to verify that skills are wired up.
        ---

        # Canary

        When this skill is active, reply with exactly this token and nothing else:

        {CANARY}
        """),
        encoding="utf-8",
    )

    agent = agent_factory(skills_dir)
    assert (agent.agents_skills / "canary" / "SKILL.md").is_file()

    result = agent.run("Use the canary skill and report the canary token.")

    assert result.returncode == 0, f"opencode exited {result.returncode}\n{result.stderr}"
    assert CANARY in result.text, (
        "the canary skill did not reach the model, or its instruction was not followed.\n"
        f"--- transcript ---\n{result.text.strip() or '(empty)'}"
    )
