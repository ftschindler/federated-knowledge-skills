"""Unit tests for `fkb init`, `fkb add`, and the arrival machinery behind them.

Separate from the command tests because these are about how a bundle *gets* into
the federation rather than what the federation then says about it, and because
almost every one of them encodes an incident: registration was done by hand once
and cost three judgement calls in a single session, each of which is a test here.

Every test runs inside a fake home (tests/fake_home.py) with the skill installed
into it, so nothing can reach the developer's real workspace and the install is
what gets exercised rather than the source tree.

Cloning is tested against a local repository over `file://`. What a clone has to
get right here is mechanics - where the checkout lands, what gets written, what
is refused - and mechanics do not need somebody else's server. Repository shapes
nobody here controls are a different question, and they are in
test_fkb_federation.py behind the `federation` marker.
"""

from __future__ import annotations

import json
import os
import subprocess

import pytest
from fake_home import FakeHome, have, local_remote

pytestmark = pytest.mark.python_scripts

CONCEPT = """---
type: note
title: A concept
description: Something a bundle knows.
status: draft
generated:
  by: "human:tester"
  at: 2026-01-01
---

# A concept
"""


def _registered(home: FakeHome, name: str) -> dict:
    """What the federation now believes about a bundle, read back through the CLI.

    Parsing the manifest would test that `add` can write YAML. Asking `resolve`
    tests the thing that matters, which is that the next command to read the file
    understands what was written into it.
    """
    result = home.run("resolve", name)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def _init(home: FakeHome) -> None:
    result = home.run("init", "--workspace-root", str(home.workspace_root))
    assert result.returncode == 0, result.stdout + result.stderr


def test_an_installed_skill_carries_no_build_artifacts(fake_home: FakeHome) -> None:
    """An install is source, and nothing that names the machine it was built on.

    A `.pyc` records the absolute path it was compiled from. Copying one puts the
    author's checkout into somebody else's skills directory, and in a test home it
    is worse than untidy: an agent that reads its own skill directory finds a path
    out of the sandbox and into the repository under test. That is not
    hypothetical - a cold-session test asking a question seeded in a bundle
    answered out of the test file instead, citing it by line number.
    """
    strays = [
        p
        for p in fake_home.skill.rglob("*")
        if p.suffix == ".pyc" or p.name in {"__pycache__", ".ruff_cache", ".pytest_cache"}
    ]
    assert not strays, f"the install carries build artifacts: {strays}"


def test_init_writes_a_manifest_add_can_use(fake_home: FakeHome) -> None:
    """Setup is two steps because they answer different questions.

    `init` asks only where bundles live on this machine, which has nothing to do
    with what is in any of them, and must leave a file `add` can append to.
    """
    _init(fake_home)
    written = fake_home.manifest.read_text(encoding="utf-8")
    assert f"workspace_root: {fake_home.workspace_root}" in written
    assert "bundles: {}" in written


def test_init_refuses_to_overwrite(fake_home: FakeHome) -> None:
    """The manifest on disk is the only record of policy decided rather than defaulted."""
    _init(fake_home)
    second = fake_home.run("init", "--workspace-root", str(fake_home.root / "elsewhere"))
    assert second.returncode != 0
    assert "already exists" in second.stderr


def test_the_manifest_is_found_through_home_when_xdg_is_unset(fake_home: FakeHome) -> None:
    """`~/.config` is the documented fallback, and nothing reached it before.

    It matters more than a fallback usually does: this is the branch that decides
    which machine's federation a command edits, and a bug in it writes to the
    developer's own manifest rather than to a test's. Running the whole of setup
    with the variable removed is the only way to know the house holds.
    """
    env = fake_home.env_without_xdg
    created = fake_home.run("init", "--workspace-root", str(fake_home.workspace_root), env=env)
    assert created.returncode == 0, created.stdout + created.stderr
    assert fake_home.manifest.is_file(), "init did not land under the fake HOME"

    added = fake_home.run("add", "notes", "--new", "--writable", env=env)
    assert added.returncode == 0, added.stdout + added.stderr
    assert fake_home.run("lint", "notes", env=env).returncode == 0


def test_add_scaffolds_a_bundle_that_passes_its_own_lint(fake_home: FakeHome) -> None:
    """A bundle that does not exist yet is the third arrival path.

    What it writes has to be conformant on the spot, because the next thing that
    happens to it is a commit, and the bundle's own hook runs then.
    """
    _init(fake_home)
    added = fake_home.run("add", "notes", "--new", "--writable")
    assert added.returncode == 0, added.stdout + added.stderr

    root = fake_home.workspace_root / "notes"
    assert (root / "index.md").is_file()
    assert (root / "log.md").is_file()
    assert (root / "fkb.yaml").is_file()
    assert fake_home.run("lint", "notes").returncode == 0


def test_add_fails_closed_on_policy_it_was_not_told(fake_home: FakeHome) -> None:
    """Both security-relevant defaults are the cautious ones.

    A bundle registered in a hurry discloses nothing and accepts no writes until
    someone opens it deliberately.
    """
    _init(fake_home)
    fake_home.run("add", "notes", "--new")

    entry = _registered(fake_home, "notes")
    assert entry["referenceable_by"] == []
    assert entry["writable"] is False
    assert entry["publish"] is None


def test_a_scaffolded_private_bundle_is_sealed_in_both_directions(fake_home: FakeHome) -> None:
    """The private case, end to end, because it is the one with something to lose.

    Sealed means two separate refusals and they fail for different reasons: a
    bundle that lists nobody cannot be cited, and a bundle with no published
    location has no URL to cite even where policy would allow it. Linking *out*
    of it stays permitted, which is the asymmetry the manifest exists to express
    and the easiest thing to get backwards.
    """
    _init(fake_home)
    fake_home.run("add", "private", "--new", "--writable")
    fake_home.run(
        "add",
        "public",
        "--new",
        "--writable",
        "--referenceable-by",
        "*",
        "--publish-url",
        "https://public.invalid/kb/",
        "--publish-style",
        "directory",
    )
    (fake_home.workspace_root / "private" / "secret.md").write_text(CONCEPT, encoding="utf-8")
    (fake_home.workspace_root / "public" / "open.md").write_text(CONCEPT, encoding="utf-8")

    inbound = fake_home.run("url", "private", "secret.md", "--from", "public")
    assert inbound.returncode != 0
    assert "referenceable_by" in inbound.stderr

    outbound = fake_home.run("url", "public", "open.md", "--from", "private")
    assert outbound.returncode == 0, outbound.stdout + outbound.stderr
    assert outbound.stdout.strip() == "https://public.invalid/kb/open/"

    assert fake_home.run("lint").returncode == 0


def test_an_unpublished_bundle_is_refused_for_a_different_reason(fake_home: FakeHome) -> None:
    """No published location is not a policy failure, and the message must not say it is.

    The fix is a `publish:` entry, which may name where the bundle *will* live,
    so sending someone to `referenceable_by` would send them to the wrong file.
    """
    _init(fake_home)
    fake_home.run("add", "draft", "--new", "--writable", "--referenceable-by", "*")
    fake_home.run("add", "other", "--new", "--writable")
    (fake_home.workspace_root / "draft" / "wip.md").write_text(CONCEPT, encoding="utf-8")

    refused = fake_home.run("url", "draft", "wip.md", "--from", "other")
    assert refused.returncode != 0
    assert "publish" in refused.stderr
    assert "referenceable_by" not in refused.stderr


@pytest.mark.skipif(not have("git"), reason="cloning needs git")
def test_add_clones_a_remote_under_the_workspace(fake_home: FakeHome) -> None:
    """The first arrival path: a bundle that is not on this machine yet.

    The checkout belongs under `workspace_root`. A bundle cloned somewhere else
    is how a checkout ends up outside the workspace it is registered under, which
    happened, and was noticed only because a path stopped resolving.
    """
    remote = local_remote(
        fake_home.root / "remotes" / "vault",
        {
            "README.md": "# Infrastructure\n",
            "docs/index.md": '---\nokf_version: "0.2"\n---\n\n# Vault\n',
            "docs/guide.md": CONCEPT,
        },
    )
    _init(fake_home)
    added = fake_home.run("add", "vault", "--clone", remote, "--writable")
    assert added.returncode == 0, added.stdout + added.stderr

    checkout = fake_home.workspace_root / "vault"
    assert (checkout / ".git").is_dir(), "the clone is not a repository anyone can commit into"
    assert _registered(fake_home, "vault")["path"] == str(checkout / "docs")


@pytest.mark.skipif(not have("git"), reason="cloning needs git")
def test_cloning_over_an_existing_directory_is_refused(fake_home: FakeHome) -> None:
    """Re-running `add` must not write over a checkout that may hold uncommitted work."""
    remote = local_remote(
        fake_home.root / "remotes" / "vault",
        {"index.md": '---\nokf_version: "0.2"\n---\n\n# Vault\n'},
    )
    _init(fake_home)
    assert fake_home.run("add", "vault", "--clone", remote).returncode == 0

    again = fake_home.run("add", "second", "--clone", remote)
    assert again.returncode != 0
    assert "--path" in again.stderr, "the refusal does not say how to register what is already there"


def test_add_finds_the_bundle_root_rather_than_the_repo_root(fake_home: FakeHome) -> None:
    """A repo is usually infrastructure at the top with the bundle underneath.

    Registering the checkout root would point the federation at a directory with
    no concepts in it, and nothing downstream would say so.
    """
    checkout = fake_home.root / "repo"
    (checkout / "docs" / "topic").mkdir(parents=True)
    (checkout / "README.md").write_text("# Repo\n", encoding="utf-8")
    (checkout / "docs" / "index.md").write_text("# Bundle\n", encoding="utf-8")
    (checkout / "docs" / "topic" / "index.md").write_text("# Topic\n", encoding="utf-8")

    _init(fake_home)
    added = fake_home.run("add", "kb", "--path", str(checkout))
    assert added.returncode == 0, added.stdout + added.stderr
    assert _registered(fake_home, "kb")["path"] == str(checkout / "docs")


def test_an_existing_checkout_is_registered_where_it_lies(fake_home: FakeHome) -> None:
    """The second arrival path moves nothing, including out of the workspace.

    A checkout that already lives somewhere gets adopted rather than relocated,
    which is what an absolute path in the manifest is for.
    """
    elsewhere = fake_home.root / "src" / "someones-kb"
    elsewhere.mkdir(parents=True)
    (elsewhere / "index.md").write_text('---\nokf_version: "0.2"\n---\n\n# KB\n', encoding="utf-8")

    _init(fake_home)
    assert fake_home.run("add", "kb", "--path", str(elsewhere)).returncode == 0
    assert _registered(fake_home, "kb")["path"] == str(elsewhere)
    assert elsewhere.is_dir(), "the checkout was moved"


def test_two_candidate_roots_are_refused_rather_than_ranked(fake_home: FakeHome) -> None:
    """The decoy case, and the reason this refuses instead of picking.

    A repository *about* bundles ships a sample bundle that looks exactly like a
    real one. Choosing the first would have registered an example as somebody's
    knowledge, and the failure would have been silent.
    """
    checkout = fake_home.root / "repo"
    (checkout / "knowledge").mkdir(parents=True)
    (checkout / "example").mkdir(parents=True)
    (checkout / "knowledge" / "index.md").write_text("# Real\n", encoding="utf-8")
    (checkout / "example" / "index.md").write_text("# Sample\n", encoding="utf-8")

    _init(fake_home)
    added = fake_home.run("add", "kb", "--path", str(checkout))
    assert added.returncode != 0
    assert "knowledge" in added.stderr and "example" in added.stderr
    assert "--path" in added.stderr, "the refusal does not say how to resolve it"


def test_add_refuses_a_name_already_in_the_manifest(fake_home: FakeHome) -> None:
    """Silently rebinding a name would repoint every existing link to it."""
    _init(fake_home)
    fake_home.run("add", "notes", "--new")
    again = fake_home.run("add", "notes", "--new")
    assert again.returncode != 0
    assert "already in the manifest" in again.stderr


def test_add_requires_an_arrival_route(fake_home: FakeHome) -> None:
    """The bundle's identity is the argument that must never be defaulted.

    Asked to add "a public read-only vault" with nothing named, the right move is
    to stop. Inferring it from the only candidate on disk was right once, and
    would have been wrong the moment a second one existed.
    """
    _init(fake_home)
    added = fake_home.run("add", "kb")
    assert added.returncode != 0
    assert "--clone" in added.stderr and "--path" in added.stderr and "--new" in added.stderr


def test_add_without_a_workspace_says_to_run_init(fake_home: FakeHome) -> None:
    """Setup is two steps, so the second one has to name the first."""
    added = fake_home.run("add", "kb", "--new")
    assert added.returncode != 0
    assert "fkb init" in added.stderr


def test_a_fresh_workspace_reads_as_empty_rather_than_broken(fake_home: FakeHome) -> None:
    """`init` writes no bundles, so the very next command must not call that an error.

    It did. The manifest was hand-written for long enough that "declares no
    bundles" could only mean a mistake, and `init` then made it the documented
    first state: the two steps the skill tells a newcomer to run produced a
    failure between them.
    """
    _init(fake_home)
    listed = fake_home.run("list")
    assert listed.returncode == 0, listed.stdout + listed.stderr
    assert "fkb add" in listed.stdout
    for route in ("--clone", "--path", "--new"):
        assert route in listed.stdout, "the empty state does not say how to leave it"


def test_the_script_resolves_its_own_dependencies(fake_home: FakeHome) -> None:
    """`fkb` is a PEP 723 script, and that has to keep being true.

    The rest of this suite runs it on an interpreter that already has its
    dependencies, because doing otherwise costs six times the wall clock. That
    speed hides something a bundle relies on: the standalone hook is pinned by
    revision and resolves its own environment through `uv`, so a machine with
    nothing but `uv` has to be able to run this. One test pays the cost on
    purpose, and it is this one.
    """
    _init(fake_home)
    result = subprocess.run(
        ["uv", "run", "--script", str(fake_home.fkb), "list"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, **fake_home.env},
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("sample", "relative", "style", "prefix"),
    [
        ("https://site.invalid/kb/guide/", "guide.md", "directory", "https://site.invalid/kb/"),
        ("https://site.invalid/kb/deep/inner/", "deep/inner.md", "directory", "https://site.invalid/kb/"),
        ("https://them.example/blob/main/docs/deep/x.md", "deep/x.md", "raw", "https://them.example/blob/main/docs/"),
        ("https://s.example/docs/a/b.html", "a/b.md", "html", "https://s.example/docs/"),
    ],
)
def test_publish_is_derived_from_a_page_someone_can_open(
    fake_home: FakeHome, sample: str, relative: str, style: str, prefix: str
) -> None:
    """Both halves of `publish` have a plausible wrong answer, and no feedback.

    Nothing fetches a URL, so a bad prefix or a guessed style is silent forever.
    Asking instead for the address of a page the person already has open turns
    two abstract questions into one they answer by pasting from a browser.
    """
    _init(fake_home)
    root = fake_home.bundle("vault", {relative: CONCEPT})
    added = fake_home.run(
        "add",
        "vault",
        "--path",
        str(root),
        "--publish-sample",
        sample,
        "--publish-sample-path",
        relative,
    )
    assert added.returncode == 0, added.stdout + added.stderr
    assert _registered(fake_home, "vault")["publish"] == {"url": prefix, "style": style}

    produced = fake_home.run("url", "vault", relative, "--from", "vault")
    assert produced.stdout.strip() == sample, "what `add` derived is not what `url` produces"


def test_a_sample_that_matches_no_style_says_what_was_expected(fake_home: FakeHome) -> None:
    """At that point the URL and the path disagree, and only the person knows which is wrong."""
    _init(fake_home)
    root = fake_home.bundle("vault", {"guide.md": CONCEPT})
    refused = fake_home.run(
        "add",
        "vault",
        "--path",
        str(root),
        "--publish-sample",
        "https://site.invalid/kb/something-else",
        "--publish-sample-path",
        "guide.md",
    )
    assert refused.returncode != 0
    assert "directory" in refused.stderr and "raw" in refused.stderr and "html" in refused.stderr
