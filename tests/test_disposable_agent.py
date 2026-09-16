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
from disposable_agent import LEAKY_ENV_PREFIX, LEAKY_ENV_VARS, DisposableAgent

pytestmark = pytest.mark.agent

# Deliberately odd so it cannot plausibly appear by chance in a model's output,
# and deliberately mundane in what it says. An earlier version asked the agent to
# "report the canary token", which reads as an attempt to make a model disclose a
# secret: it declined on those grounds and the whole layer went red. The string a
# skill carries has to be boring, or the test measures safety training instead of
# skill discovery.
HOUSE_PHRASE = "PURPLE-OTTER-4417"


def test_a_bare_agent_runs_and_touches_nothing_real(bare_agent: DisposableAgent) -> None:
    """The agent is runnable, and everything it reads or writes is its own."""
    assert bare_agent.opencode_bin.is_file(), "no opencode binary was located"

    # The whole point is that nothing reaches the developer's real home.
    assert bare_agent.env["HOME"] == str(bare_agent.home)
    for var in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"):
        assert bare_agent.env[var].startswith(str(bare_agent.home)), var

    # Redirecting HOME is not enough: OPENCODE_CONFIG_DIR overrides config lookup
    # outright, so a developer who has one set would silently re-attach this agent
    # to their real profile. Nothing opencode-specific may survive from outside.
    leaked = sorted(k for k in bare_agent.env if k.startswith(LEAKY_ENV_PREFIX))
    assert not leaked, f"environment reaches outside the agent: {leaked}"

    # `PWD` and `OLDPWD` arrive naming wherever pytest was started, which is the
    # repository under test. The agent may read outside its home - it has to, to
    # load skills - so an inherited absolute path is a route out of the sandbox
    # rather than a cosmetic leak.
    for var in LEAKY_ENV_VARS:
        assert var not in bare_agent.env, f"{var} points the agent at the directory the tests ran from"

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
    greeting = skills_dir / "house-greeting"
    greeting.mkdir(parents=True)
    (greeting / "SKILL.md").write_text(
        textwrap.dedent(f"""\
        ---
        name: house-greeting
        description: >-
          Give the house greeting. Use when the user asks for the house greeting,
          or asks which greeting this project uses.
        ---

        # House greeting

        When this skill is active, reply with exactly this phrase and nothing else:

        {HOUSE_PHRASE}
        """),
        encoding="utf-8",
    )

    agent = agent_factory(skills_dir)
    assert (agent.agents_skills / "house-greeting" / "SKILL.md").is_file()

    result = agent.run("What is the house greeting for this project?")

    assert result.returncode == 0, f"opencode exited {result.returncode}\n{result.stderr}"
    assert HOUSE_PHRASE in result.text, (
        "the house-greeting skill did not reach the model, or its instruction was not followed.\n"
        f"--- transcript ---\n{result.text.strip() or '(empty)'}"
    )
