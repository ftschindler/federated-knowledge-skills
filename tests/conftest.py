"""Shared fixtures for the tests that drive a real agent.

Tests marked `agent` are true end-to-end tests: they build a disposable agent
(see tests/disposable_agent.py), install skills into it exactly as a user would,
send it a message and inspect the transcript and the files it left behind.

On failure the agent is preserved and a copy-pasteable command to enter its world
is printed, so a run can be inspected by hand.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from disposable_agent import DisposableAgent, build_disposable_agent


@pytest.fixture
def bare_agent(tmp_path: Path) -> DisposableAgent:
    """A disposable agent with no skills installed at all."""
    # pytest keeps the last few `tmp_path` roots on disk by default, so a failing
    # run's agent survives long enough to inspect (path is printed on failure).
    return build_disposable_agent(tmp_path, skills_dir=None)


@pytest.fixture
def agent_factory(tmp_path: Path):
    """Build a disposable agent with skills from a caller-supplied directory.

    Lets a test author a skill on the fly and install it, so the machinery can be
    exercised without depending on whichever skills this repo currently ships.
    """
    built: list[DisposableAgent] = []

    def _build(skills_dir: Path | None) -> DisposableAgent:
        agent = build_disposable_agent(tmp_path / f"agent{len(built)}", skills_dir=skills_dir)
        built.append(agent)
        return agent

    _build.built = built  # type: ignore[attr-defined]
    return _build


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """On failure of a test that used a disposable agent, print how to enter it."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    funcargs = getattr(item, "funcargs", {}) or {}
    candidates: list[DisposableAgent] = [v for v in funcargs.values() if isinstance(v, DisposableAgent)]
    factory = funcargs.get("agent_factory")
    candidates.extend(getattr(factory, "built", []))
    for agent in candidates:
        report.sections.append(
            (
                "Disposable agent (inspect it)",
                agent.enter_hint(reason=f"Test {item.name!r} failed."),
            )
        )
        break
