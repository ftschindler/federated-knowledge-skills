"""Unit tests for skills/fkb/scripts/fkb.

Fast and deterministic (no LLM, no network, no git). Each test builds a throwaway
bundle and a throwaway manifest under tmp_path, pointing `XDG_CONFIG_HOME` at it,
and runs the CLI as a subprocess the way a person or an agent would.

**The copy under test is an installed one.** The skill is copied out of the source
tree once per session and every subprocess runs from there, because the source
tree is not the arrangement anyone uses: a skill is installed into
`~/.agents/skills/fkb/` and runs from whatever went with it. Driving the sources
would pass happily on a file the install never ships, and the CLI now imports two
siblings rather than standing alone, so that failure is reachable.

The test that matters most is the last one. The design's constraint is one
implementation behind two entry points - a bundle's standalone pre-commit hook,
and this CLI - and a constraint nothing checks is a wish. So the two are run over
the same broken file and their findings compared.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Installed at import so the module-level paths below can point at it. The copy
# is what `npx skills add` or a symlink would leave on disk, minus the harness.
INSTALLED = Path(tempfile.mkdtemp(prefix="fkb-installed-")) / "fkb"
shutil.copytree(REPO_ROOT / "skills" / "fkb", INSTALLED)

SCRIPTS = INSTALLED / "scripts"
FKB = SCRIPTS / "fkb"
BUNDLE_LINT = SCRIPTS / "bundle_lint.py"

pytestmark = pytest.mark.python_scripts

INDEX = '---\nokf_version: "0.2"\n---\n\n# Bundle\n\n'
LOG = "# Update Log\n\n## 2026-01-01\n\n- created\n"
FLOOR = "required:\n- type\n- title\n- description\n- status\n- generated\n"


def _concept(title: str, *, omit: str = "") -> str:
    """A concept whose frontmatter is warning-free, minus the omitted field."""
    fields = {
        "type": "note",
        "title": title,
        "description": f"About {title}.",
        "tags": "[example]",
        "status": "draft",
    }
    fields.pop(omit, None)
    lines = [f"{key}: {value}" for key, value in fields.items()]
    if omit != "generated":
        lines.append('generated:\n  by: "human:tester"\n  at: 2026-01-01')
    return "---\n" + "\n".join(lines) + f"\n---\n\n# {title}\n"


def _bundle(root: Path, files: dict[str, str], conventions: str | None = None) -> Path:
    root.mkdir(parents=True)
    (root / "index.md").write_text(INDEX + "".join(f"- [{name}]({name})\n" for name in files), encoding="utf-8")
    (root / "log.md").write_text(LOG, encoding="utf-8")
    declaration = FLOOR if conventions is None else FLOOR + f"conventions: {conventions}\n"
    (root / "fkb.yaml").write_text(declaration, encoding="utf-8")
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _workspace(tmp_path: Path, bundles: dict[str, str]) -> dict[str, str]:
    """Write a manifest naming the given bundles, and return the env that finds it."""
    config = tmp_path / "config" / "fkb"
    config.mkdir(parents=True)
    lines = ["bundles:"]
    for name, path in bundles.items():
        lines += [f"  {name}:", f"    path: {path}", "    writable: true"]
    (config / "workspace.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"XDG_CONFIG_HOME": str(tmp_path / "config")}


def _run(script: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    # Same reasoning as the bundle_lint tests: the pytest interpreter often has
    # no pyyaml, in which case uv resolves the script's own inline metadata.
    if importlib.util.find_spec("yaml") is None:
        command = ["uv", "run", "--script", str(script), *args]
    else:
        command = [sys.executable, str(script), *args]
    return subprocess.run(command, capture_output=True, text=True, check=False, env={**os.environ, **(env or {})})


def test_list_speaks_the_manifests_own_field_names(tmp_path: Path) -> None:
    """`list` is read before choosing where to write, and must name the fields it read.

    A label of its own invention would give one policy two vocabularies, leaving
    an agent no way from what it sees back to the line that produced it.
    """
    _bundle(tmp_path / "open", {"alpha.md": _concept("Alpha")})
    _bundle(tmp_path / "shut", {"beta.md": _concept("Beta")})
    config = tmp_path / "config" / "fkb"
    config.mkdir(parents=True)
    (config / "workspace.yaml").write_text(
        f"bundles:\n"
        f"  open:\n    path: {tmp_path / 'open'}\n"
        f"    referenceable_by: '*'\n    writable: true\n"
        f"    publish:\n      url: https://example.invalid/kb\n      style: directory\n"
        f"  shut:\n    path: {tmp_path / 'shut'}\n",
        encoding="utf-8",
    )
    result = _run(FKB, "list", env={"XDG_CONFIG_HOME": str(tmp_path / "config")})
    assert result.returncode == 0, result.stdout + result.stderr
    for field in ("path", "referenceable_by", "writable", "publish"):
        assert field in result.stdout, f"`list` never names `{field}`"
    assert '"*"' in result.stdout, "the open bundle's permission is not shown as the manifest holds it"
    assert "https://example.invalid/kb" in result.stdout
    assert "style" in result.stdout, "`publish` has two halves and `list` shows one"


def test_a_bare_string_publish_is_refused_by_name(tmp_path: Path) -> None:
    """The field was a bare URL once, and the manifest is hand-written.

    Accepting the old spelling would mean guessing the transform, which is the
    half that was got wrong in the first place: one bundle's prefix concatenates
    verbatim and another's strips the extension, and both read plausibly. The
    error therefore names the new shape rather than saying the value is invalid.
    """
    _bundle(tmp_path / "kb", {"alpha.md": _concept("Alpha")})
    config = tmp_path / "config" / "fkb"
    config.mkdir(parents=True)
    (config / "workspace.yaml").write_text(
        f"bundles:\n  kb:\n    path: {tmp_path / 'kb'}\n    publish: https://example.invalid/kb\n",
        encoding="utf-8",
    )
    result = _run(FKB, "list", env={"XDG_CONFIG_HOME": str(tmp_path / "config")})
    assert result.returncode != 0
    assert "url" in result.stderr and "style" in result.stderr


def test_omitted_policy_fails_closed(tmp_path: Path) -> None:
    """A bundle added without policy must disclose nothing and accept no writes."""
    _bundle(tmp_path / "shut", {"beta.md": _concept("Beta")})
    env = _workspace(tmp_path, {})
    (tmp_path / "config" / "fkb" / "workspace.yaml").write_text(
        f"bundles:\n  shut:\n    path: {tmp_path / 'shut'}\n", encoding="utf-8"
    )
    result = _run(FKB, "list", env=env)
    assert "referenceable_by  []" in result.stdout
    assert "writable          false" in result.stdout


def test_missing_manifest_sends_you_to_init(tmp_path: Path) -> None:
    """The error has to name the command that fixes it, and that command changed.

    It used to teach the file's shape, because there was nothing to run and a
    hand-written manifest was the only way in. `fkb init` now exists, so telling
    someone to write YAML would be sending them the long way round.
    """
    result = _run(FKB, "list", env={"XDG_CONFIG_HOME": str(tmp_path / "empty")})
    assert result.returncode != 0
    assert "workspace.yaml" in result.stderr
    assert "fkb init" in result.stderr


def test_lint_picks_up_the_bundles_own_floor(tmp_path: Path) -> None:
    """The floor is the bundle's declaration; the CLI must read it rather than carry its own list."""
    _bundle(tmp_path / "kb", {"alpha.md": _concept("Alpha", omit="description")})
    env = _workspace(tmp_path, {"kb": str(tmp_path / "kb")})
    result = _run(FKB, "lint", env=env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "required field `description`" in result.stdout


def test_lint_names_one_bundle(tmp_path: Path) -> None:
    """Linting everything on every call gets ignored; naming one has to be possible."""
    _bundle(tmp_path / "good", {"alpha.md": _concept("Alpha")})
    _bundle(tmp_path / "bad", {"beta.md": _concept("Beta", omit="title")})
    env = _workspace(tmp_path, {"good": str(tmp_path / "good"), "bad": str(tmp_path / "bad")})
    result = _run(FKB, "lint", "good", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "beta.md" not in result.stdout


def test_unknown_bundle_lists_the_known_ones(tmp_path: Path) -> None:
    """A typo in a bundle name is the common case, so the error carries the alternatives."""
    _bundle(tmp_path / "kb", {"alpha.md": _concept("Alpha")})
    env = _workspace(tmp_path, {"kb": str(tmp_path / "kb")})
    result = _run(FKB, "lint", "kbb", env=env)
    assert result.returncode != 0
    assert "kb" in result.stderr


def test_cli_and_hook_report_the_same_finding(tmp_path: Path) -> None:
    """One implementation, two entry points.

    The standalone hook exists so a bundle can enforce itself without the
    federation installed, which is only safe if it and `fkb lint` agree. Run
    both over the same broken file and compare what they say about it.
    """
    root = _bundle(tmp_path / "kb", {"alpha.md": _concept("Alpha", omit="status")})
    env = _workspace(tmp_path, {"kb": str(root)})

    hook = _run(BUNDLE_LINT, "--bundle-root", str(root), "--floor", str(root / "fkb.yaml"))
    cli = _run(FKB, "lint", env=env)

    def findings(text: str) -> set[str]:
        return {line.strip() for line in text.splitlines() if line.strip().startswith("ERROR")}

    assert hook.returncode == cli.returncode == 1, hook.stdout + cli.stdout
    assert findings(hook.stdout) == findings(cli.stdout)
    assert "alpha.md: floor: required field `status` is absent or empty" in hook.stdout


def test_conventions_may_point_outside_the_bundle(tmp_path: Path) -> None:
    """The public bundle keeps its house rules beside the site, not inside the knowledge.

    A pointer that cannot leave the bundle root would force such a bundle to
    move the page or keep a second copy, which is the drift the key exists to
    avoid (DESIGN §9.2). `list` has to resolve it and report where it landed.
    """
    root = _bundle(tmp_path / "repo" / "docs", {"alpha.md": _concept("Alpha")}, conventions="../about/style.md")
    house = tmp_path / "repo" / "about" / "style.md"
    house.parent.mkdir(parents=True)
    house.write_text("# House rules\n", encoding="utf-8")

    env = _workspace(tmp_path, {"kb": str(root)})
    listed = _run(FKB, "list", env=env)
    assert listed.returncode == 0, listed.stdout + listed.stderr
    assert str(house.resolve()) in listed.stdout
    assert "MISSING" not in listed.stdout

    assert _run(FKB, "lint", env=env).returncode == 0


def test_a_broken_conventions_pointer_warns_and_does_not_block(tmp_path: Path) -> None:
    """A moved page leaves a pointer at nothing, and the agent silently reads no rules.

    Worth reporting, not worth failing a commit over: the key is optional and
    the path may leave the bundle, so a bundle vendored without its repository
    would block for no fault of its own.
    """
    root = _bundle(tmp_path / "kb", {"alpha.md": _concept("Alpha")}, conventions="about/gone.md")
    env = _workspace(tmp_path, {"kb": str(root)})

    result = _run(FKB, "lint", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "conventions: `about/gone.md` does not resolve to a file" in result.stdout
    assert "warn   fkb.yaml:" in result.stdout


def test_a_bundle_without_the_declaration_is_still_lintable(tmp_path: Path) -> None:
    """A third-party bundle carries no `fkb.yaml`, and must stay usable anyway.

    Conformance still applies; the floor simply has nothing to say, so a concept
    missing a field the floor would have required passes (DESIGN §9.2).
    """
    root = _bundle(tmp_path / "kb", {"alpha.md": _concept("Alpha", omit="description")})
    (root / "fkb.yaml").unlink()
    env = _workspace(tmp_path, {"kb": str(root)})

    result = _run(FKB, "lint", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "required field `description`" not in result.stdout
    assert "config            not declared" in _run(FKB, "list", env=env).stdout


def test_the_hook_accepts_a_declaration_under_any_name(tmp_path: Path) -> None:
    """Only `fkb` requires the filename, because only `fkb` discovers it.

    The hook is handed an explicit path, so a bundle may decline the canonical
    name and still enforce itself with no federation installed. Adopting the
    name is how a bundle opts into being found, not into being checked.
    """
    root = _bundle(tmp_path / "kb", {"alpha.md": _concept("Alpha", omit="status")})
    renamed = root / "house-floor.yaml"
    (root / "fkb.yaml").rename(renamed)

    hook = _run(BUNDLE_LINT, "--bundle-root", str(root), "--floor", str(renamed))
    assert hook.returncode == 1, hook.stdout + hook.stderr
    assert "alpha.md: floor: required field `status` is absent or empty" in hook.stdout


def _federation(tmp_path: Path, bodies: dict[str, str] | None = None) -> dict[str, str]:
    """Three bundles covering the cases `url` and the reference rule turn on.

    `site` publishes as a generated site and anything may cite it; `sealed`
    publishes too but lists nobody, which is the case where a URL exists and
    still must not be produced; `nowhere` may be cited by `site` and has no
    published location at all, which is the other refusal and the one that is
    not a policy violation.
    """
    _bundle(tmp_path / "site", {"guide.md": _concept("Guide"), "deep/inner.md": _concept("Inner")})
    _bundle(tmp_path / "sealed", {"secret.md": _concept("Secret")})
    _bundle(tmp_path / "nowhere", {"draft.md": _concept("Draft")})
    for rel, text in (bodies or {}).items():
        (tmp_path / rel).write_text(text, encoding="utf-8")

    config = tmp_path / "config" / "fkb"
    config.mkdir(parents=True)
    (config / "workspace.yaml").write_text(
        f"bundles:\n"
        f"  site:\n    path: {tmp_path / 'site'}\n    writable: true\n"
        f"    referenceable_by: '*'\n"
        f"    publish:\n      url: https://site.invalid/kb\n      style: directory\n"
        f"  sealed:\n    path: {tmp_path / 'sealed'}\n    writable: true\n"
        f"    referenceable_by: []\n"
        f"    publish:\n      url: https://sealed.invalid/kb/\n      style: raw\n"
        f"  nowhere:\n    path: {tmp_path / 'nowhere'}\n    writable: true\n"
        f"    referenceable_by: [site]\n",
        encoding="utf-8",
    )
    return {"XDG_CONFIG_HOME": str(tmp_path / "config")}


def test_url_applies_the_transform_the_target_declares(tmp_path: Path) -> None:
    """Two bundles, two URL shapes, and the caller does no string work.

    The reason this is a command rather than a prefix in `resolve`'s JSON: a
    caller handed the prefix has to know that one site strips the extension and
    another keeps it, and two callers knowing that is two readings of one field.
    """
    env = _federation(tmp_path)

    site = _run(FKB, "url", "site", "guide.md", "--from", "nowhere", env=env)
    assert site.returncode == 0, site.stdout + site.stderr
    assert site.stdout.strip() == "https://site.invalid/kb/guide/"

    nested = _run(FKB, "url", "site", "deep/inner.md", "--from", "nowhere", env=env)
    assert nested.stdout.strip() == "https://site.invalid/kb/deep/inner/"

    raw = _run(FKB, "url", "sealed", "secret.md", "--from", "sealed", env=env)
    assert raw.returncode == 0, raw.stdout + raw.stderr
    assert raw.stdout.strip() == "https://sealed.invalid/kb/secret.md"


def test_url_refuses_a_link_the_reference_rule_forbids(tmp_path: Path) -> None:
    """The refusal is the command's job as much as the URL is.

    An agent handed a string has been told the link is permitted, so the check
    and the formatting cannot come apart. `sealed` publishes, so a URL could be
    produced here and must not be.
    """
    env = _federation(tmp_path)
    result = _run(FKB, "url", "sealed", "secret.md", "--from", "site", env=env)
    assert result.returncode != 0
    assert "referenceable_by" in result.stderr
    assert "https://sealed.invalid" not in result.stderr, "the refusal leaked the URL it withheld"


def test_url_refuses_an_unpublished_target_without_calling_it_a_violation(tmp_path: Path) -> None:
    """No published location is not a policy failure, and the message must not say it is.

    `site` may cite `nowhere`; there is simply no URL yet. The fix is a
    `publish:` entry, which may name where the bundle *will* live, so the error
    has to say that rather than send someone to `referenceable_by`.
    """
    env = _federation(tmp_path)
    result = _run(FKB, "url", "nowhere", "draft.md", "--from", "site", env=env)
    assert result.returncode != 0
    assert "publish" in result.stderr
    assert "referenceable_by" not in result.stderr


def test_url_refuses_a_concept_that_is_not_there(tmp_path: Path) -> None:
    """Cheap now, impossible later: afterwards only fetching the site can tell you."""
    env = _federation(tmp_path)
    result = _run(FKB, "url", "site", "no/such.md", "--from", "nowhere", env=env)
    assert result.returncode != 0
    assert "no/such.md" in result.stderr


def test_lint_catches_a_forbidden_link_that_url_never_wrote(tmp_path: Path) -> None:
    """The same rule at the second place it can be broken.

    `url` covers links this federation produced. A link pasted by hand, or one
    that became a violation when `referenceable_by` was tightened, only ever
    meets lint.
    """
    body = _concept("Guide") + "\nSee [it](https://sealed.invalid/kb/secret.md).\n"
    env = _federation(tmp_path, {"site/guide.md": body})

    result = _run(FKB, "lint", "site", env=env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "reference rule" in result.stdout
    assert "sealed" in result.stdout


def test_lint_reads_the_reference_rule_out_of_an_index_too(tmp_path: Path) -> None:
    """An index that links into a sealed bundle has leaked it as surely as a concept.

    The rest of lint reads concepts, because that is what OKF constrains.
    Disclosure does not care which file did it, and in practice the indexes are
    where the cross-bundle links are.
    """
    index = '---\nokf_version: "0.2"\n---\n\n# Bundle\n\n- [out](https://sealed.invalid/kb/secret.md)\n'
    env = _federation(tmp_path, {"site/index.md": index})

    result = _run(FKB, "lint", "site", env=env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "index.md: reference rule" in result.stdout


def test_an_allowed_cross_bundle_link_is_checked_for_existing(tmp_path: Path) -> None:
    """A permitted link into a real bundle still has to land on a concept.

    Warns rather than blocks: the target is another repository, which may simply
    not have been pulled, and §6.1 tolerates a link to not-yet-written knowledge.
    """
    body = _concept("Draft") + "\nSee [gone](https://site.invalid/kb/vanished/).\n"
    env = _federation(tmp_path, {"nowhere/draft.md": body})

    result = _run(FKB, "lint", "nowhere", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "resolves to no concept" in result.stdout


def test_a_directory_style_url_resolves_either_spelling(tmp_path: Path) -> None:
    """`foo/bar/` is published by both `foo/bar.md` and `foo/bar/index.md`.

    The URL has forgotten which, so the checkout decides. Getting this wrong
    would report a working link as broken on every bundle that uses sections.
    """
    body = (
        _concept("Draft") + "\nSee [a](https://site.invalid/kb/deep/inner/) and [b](https://site.invalid/kb/deep/).\n"
    )
    env = _federation(tmp_path, {"nowhere/draft.md": body})
    (tmp_path / "site" / "deep" / "index.md").write_text("# Deep\n", encoding="utf-8")

    result = _run(FKB, "lint", "nowhere", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "resolves to no concept" not in result.stdout


def test_nested_publish_prefixes_are_refused_at_load(tmp_path: Path) -> None:
    """Two bundles under one site root leave a URL that belongs to both.

    Lint reads links backwards, so attribution has to have one answer. Refusing
    here is the only cheap place: afterwards the ambiguity is spread across
    every link already written.
    """
    _bundle(tmp_path / "outer", {"alpha.md": _concept("Alpha")})
    _bundle(tmp_path / "inner", {"beta.md": _concept("Beta")})
    config = tmp_path / "config" / "fkb"
    config.mkdir(parents=True)
    (config / "workspace.yaml").write_text(
        f"bundles:\n"
        f"  outer:\n    path: {tmp_path / 'outer'}\n"
        f"    publish:\n      url: https://example.invalid/kb/\n      style: directory\n"
        f"  inner:\n    path: {tmp_path / 'inner'}\n"
        f"    publish:\n      url: https://example.invalid/kb/team/\n      style: directory\n",
        encoding="utf-8",
    )
    result = _run(FKB, "list", env={"XDG_CONFIG_HOME": str(tmp_path / "config")})
    assert result.returncode != 0
    assert "outer" in result.stderr and "inner" in result.stderr


def test_findings_in_a_read_only_bundle_never_block(tmp_path: Path) -> None:
    """An upstream we cannot edit is not a failure state.

    A lint that fails on what nobody here can fix is one you learn to ignore,
    and the finding that mattered scrolls past with the rest.
    """
    root = _bundle(tmp_path / "kb", {"alpha.md": _concept("Alpha", omit="status")})
    config = tmp_path / "config" / "fkb"
    config.mkdir(parents=True)
    (config / "workspace.yaml").write_text(
        f"bundles:\n  kb:\n    path: {root}\n    writable: false\n", encoding="utf-8"
    )
    result = _run(FKB, "lint", env={"XDG_CONFIG_HOME": str(tmp_path / "config")})
    assert result.returncode == 0, result.stdout + result.stderr
    assert "warn   alpha.md: floor: required field `status`" in result.stdout
    assert "ERROR" not in result.stdout


def test_resolve_counts_the_vocabulary_it_reports(tmp_path: Path) -> None:
    """A bare list says a string exists; counts are what make a split visible.

    One subject spelled two ways sits in the tail, under the tags that carry the
    bundle. Noticing that two entries mean one thing is semantic work and
    belongs to the skill - what this command owes it is a legible input.
    """
    _bundle(
        tmp_path / "kb",
        {
            "a.md": _concept("A").replace("tags: [example]", "tags: [awiki, linux]"),
            "b.md": _concept("B").replace("tags: [example]", "tags: [agent-wiki]"),
            "c.md": _concept("C").replace("tags: [example]", "tags: [linux]"),
        },
    )
    env = _workspace(tmp_path, {"kb": str(tmp_path / "kb")})
    result = _run(FKB, "resolve", "kb", env=env)
    assert result.returncode == 0, result.stdout + result.stderr

    report = json.loads(result.stdout)
    assert report["tags"] == {"linux": 2, "agent-wiki": 1, "awiki": 1}
    assert list(report["tags"]) == ["linux", "agent-wiki", "awiki"], "counts are not the sort key"
    assert report["types"] == {"note": 3}
    assert report["writable"] is True
