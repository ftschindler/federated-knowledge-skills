"""`fkb` against real published bundles, cloned from where they actually live.

These exist for the one thing a fixture cannot honestly provide: the shape of a
repository nobody here controls. Every other property of `add` is mechanics and
is tested offline in test_fkb_arrival.py; what is tested here is that the rules
hold against two bundles as they really are, including one that is not ours and
never will be.

Two bundles, chosen because they disagree with each other in every way that
matters:

- `ftschindler/knowledge` publishes through MkDocs, so its bundle sits under
  `docs/` with infrastructure above it and its concepts are served as
  directories with the extension stripped.
- `stjbrown/agent-knowledge` publishes nothing, so its concepts are reachable
  only as files on a branch and keep their `.md`. It also ships a sample bundle
  inside itself, which is the decoy that `find_bundle_root` exists to survive.

They are cloned once per session and registered into one fake home, so the whole
module costs two clones and then asks a lot of cheap questions of them.

**These tests can fail without anyone here changing anything.** A bundle may be
restructured, or renamed, or a site may move. That is not a false alarm: it is a
true statement that the federation is not shaped the way this code believes, and
the belief is what needs correcting.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from fake_home import FakeHome, build_fake_home, have

pytestmark = [
    pytest.mark.federation,
    pytest.mark.skipif(not have("git"), reason="cloning real bundles needs git"),
]

PUBLISHING = "https://github.com/ftschindler/knowledge"
PUBLISHING_SITE = "https://ftschindler.github.io/knowledge/"
UPSTREAM = "https://github.com/stjbrown/agent-knowledge"
UPSTREAM_BLOB = "https://github.com/stjbrown/agent-knowledge/blob/main/knowledge/"

RESERVED = {"index.md", "log.md"}


@pytest.fixture(scope="session")
def federation(tmp_path_factory: pytest.TempPathFactory) -> FakeHome:
    """One fake home holding both real bundles, cloned and registered.

    Session-scoped because a clone is the expensive part and none of the
    assertions below write to the checkouts. The policy each bundle is
    registered with mirrors how it is really held: ours is writable and
    published, theirs is readable and never authored into.
    """
    home = build_fake_home(tmp_path_factory.mktemp("federation") / "home")
    created = home.run("init", "--workspace-root", str(home.workspace_root))
    assert created.returncode == 0, created.stdout + created.stderr

    ours = home.run(
        "add",
        "public",
        "--clone",
        PUBLISHING,
        "--writable",
        "--referenceable-by",
        "*",
        "--publish-url",
        PUBLISHING_SITE,
        "--publish-style",
        "directory",
    )
    assert ours.returncode == 0, ours.stdout + ours.stderr

    theirs = home.run(
        "add",
        "upstream",
        "--clone",
        UPSTREAM,
        "--referenceable-by",
        "*",
        "--publish-url",
        UPSTREAM_BLOB,
        "--publish-style",
        "raw",
    )
    assert theirs.returncode == 0, theirs.stdout + theirs.stderr
    return home


def _registered(home: FakeHome, name: str) -> dict:
    result = home.run("resolve", name)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def _a_concept_of(bundle_root: Path) -> str:
    """One concept path taken from the checkout itself, so content drift cannot break it.

    Naming a file here would be betting on somebody else's bundle keeping it.
    Asking the clone what it holds asks the same question of whatever is there
    today, which is the question worth asking.
    """
    concepts = sorted(
        p for p in bundle_root.rglob("*.md") if p.is_file() and p.name not in RESERVED and ".git" not in p.parts
    )
    assert concepts, f"{bundle_root} holds no concepts, so it is not the bundle root"
    return concepts[0].relative_to(bundle_root).as_posix()


def _reachable(url: str) -> int:
    request = urllib.request.Request(url, headers={"User-Agent": "fkb-tests"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return int(response.status)
    except urllib.error.HTTPError as refused:
        return int(refused.code)


def test_a_publishing_bundle_arrives_at_its_docs_directory(federation: FakeHome) -> None:
    """Infrastructure at the top, bundle underneath, which is the common shape.

    Registering the checkout root would point the federation at a directory of
    build config, and every command afterwards would agree that the bundle is
    empty rather than misplaced.
    """
    entry = _registered(federation, "public")
    assert Path(entry["path"]).name == "docs"
    assert (Path(entry["path"]) / "index.md").is_file()


def test_an_upstream_bundle_arrives_past_its_own_decoy(federation: FakeHome) -> None:
    """The repository that motivated `find_bundle_root`, tested against the real thing.

    It carries ten indexes, one of which belongs to a sample bundle shipped as
    documentation. Picking that one would publish an example as somebody's
    knowledge, and nothing downstream would notice: a sample bundle lints
    perfectly, because it was written to.
    """
    entry = _registered(federation, "upstream")
    root = Path(entry["path"])
    assert root.name == "knowledge"
    assert "example-bundle" not in str(root)
    assert (root / "index.md").is_file()


def test_ours_lints_clean_and_theirs_cannot_block(federation: FakeHome) -> None:
    """The asymmetry that makes a federated lint bearable.

    An upstream is held to the same checks and none of them may fail the run.
    Theirs is an older OKF vintage and reports a hundred findings that are
    nobody's here to fix; a lint that failed on them is a lint that gets
    ignored, taking the one finding that mattered with it.
    """
    result = federation.run("lint")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "read-only: nothing here can block" in result.stdout

    lines = result.stdout.splitlines()
    upstream_section = lines[lines.index(next(x for x in lines if x.startswith("upstream "))) :]
    assert not any(line.strip().startswith("ERROR") for line in upstream_section)


def test_each_bundle_publishes_under_the_transform_it_declares(federation: FakeHome) -> None:
    """The promise, checked against the only thing that can falsify it.

    `publish` is never fetched in normal use, so a wrong prefix or a guessed
    style is silent forever: the URL that resolved to a 404 for weeks was
    indistinguishable from a correct one. Here, once, the promise is opened.
    """
    for name, expected_suffix in (("public", "/"), ("upstream", ".md")):
        entry = _registered(federation, name)
        concept = _a_concept_of(Path(entry["path"]))
        produced = federation.run("url", name, concept, "--from", "public")
        assert produced.returncode == 0, produced.stdout + produced.stderr

        url = produced.stdout.strip()
        assert url.startswith(entry["publish"]["url"])
        assert url.endswith(expected_suffix), f"{name} produced {url}, which is not its declared shape"
        assert _reachable(url) == 200, f"{name} promises {url}, which does not resolve"


def test_a_real_bundles_vocabulary_is_reported_with_counts(federation: FakeHome) -> None:
    """Derived house style, on a bundle that never agreed to any of our conventions.

    This is the argument for deriving rather than declaring: the upstream will
    never adopt a vocabulary file, and `resolve` still has something true to say
    about what it uses.
    """
    entry = _registered(federation, "upstream")
    assert entry["tags"], "no tags were found in a bundle that has them"
    assert all(isinstance(count, int) and count > 0 for count in entry["tags"].values())
    assert list(entry["tags"].values()) == sorted(entry["tags"].values(), reverse=True)
    assert entry["types"], "no `type` values were found, which OKF requires of every concept"


def test_the_reference_rule_holds_across_two_real_bundles(federation: FakeHome, fake_home: FakeHome) -> None:
    """Both bundles are public and cite each other freely; a sealed one does not.

    The sealed half is built in its own house rather than added to the shared
    one, because a session fixture that tests mutate is a suite whose result
    depends on the order it ran in.
    """
    entry = _registered(federation, "upstream")
    concept = _a_concept_of(Path(entry["path"]))
    allowed = federation.run("url", "upstream", concept, "--from", "public")
    assert allowed.returncode == 0, allowed.stdout + allowed.stderr

    fake_home.run("init", "--workspace-root", str(fake_home.workspace_root))
    fake_home.run("add", "sealed", "--new", "--writable")
    fake_home.run("add", "elsewhere", "--new", "--writable")
    refused = fake_home.run("url", "sealed", "index.md", "--from", "elsewhere")
    assert refused.returncode != 0
    assert "referenceable_by" in refused.stderr
