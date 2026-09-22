"""The workspace manifest: which bundles this machine can see, and their policy.

Split from the `fkb` command file because it is the half that has no opinions
about output. `fkb` turns these objects into lines a person reads; everything
here is what the manifest says and what follows from it, which is also what the
tests want to reach without going through a subprocess.

Nothing in here talks to a network. `publish` is a promise about where a bundle
will be reachable, and the whole design rests on it never being checked by
fetching, so that a bundle can be linked to before its site exists.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import yaml

CONFIG_FILE = "fkb.yaml"


def invocation() -> str:
    """How this program was started, written so a reader can type it back.

    A message that names a command has to name one that works on the machine
    reading it, and there are three ways in: a `PATH` entry, `uv run` with a
    path, and the shebang. A hardcoded `fkb` is right only for the first, and the
    skill's `uv run SKILLDIR/scripts/fkb` form is wrong for anyone who installed
    the CLI on its own - which is supported, and is exactly the case a hardcoded
    string fails without saying so.

    The wrapper is not reconstructed, because it cannot be: `sys.argv[0]` carries
    the script and never the `uv run` in front of it, and no environment variable
    reliably reports that uv was used. So the question asked instead is whether
    the bare name resolves, on `PATH`, to this same file. If it does, that is
    what the caller typed and what will work again. If it does not, `uv run` with
    an absolute path is the form that runs from any directory and does not rely
    on the shebang, which is also why it is the one that works on Windows.

    Lives here rather than in the command file because both this module and `fkb`
    print commands, and two answers to "what am I called" is how they drift.
    """
    called = Path(sys.argv[0])
    try:
        resolved = called.resolve()
    except OSError:
        return f"uv run {called}"
    on_path = shutil.which(called.name)
    if on_path and Path(on_path).resolve() == resolved:
        return called.name
    return f"uv run {_quoted(resolved)}"


def _quoted(path: Path) -> str:
    """A path a shell will read as one argument, if it needs the help.

    Not an edge case: the default home on Windows is `C:\\Users\\First Last`, so
    an unquoted path there is a hint that silently runs the wrong thing for a
    large share of that platform. Double quotes are the one form `sh`, PowerShell
    and `cmd` all read the same way, which is what makes this affordable where
    `&&` and `~` were not - those have no portable spelling at all.

    Quoted only when there is whitespace, so the ordinary case stays copyable
    without decoration.
    """
    text = str(path)
    return f'"{text}"' if any(character.isspace() for character in text) else text


def manifest_path() -> Path:
    config = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(config) / "fkb" / "workspace.yaml"


def read_manifest() -> dict:
    """The manifest as data, or an empty mapping if there is none yet.

    Silent about absence, unlike `load_bundles`, because the callers differ in
    what absence means to them. A command asked about bundles has nothing to say
    without a manifest and stops; a command asked what version this setup is has
    an answer either way, and "there is no setup here" is one of the useful ones.
    """
    path = manifest_path()
    if not path.is_file():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        sys.exit(f"fkb: cannot read {path}: {exc}")


class Publish:
    """Where a bundle's concepts are reachable from outside, and under what shape.

    This is the whole of cross-bundle linking. Bundles do not know about each
    other, so a link between two of them is the one thing neither side can write
    alone, and a relative path is a fact about one disk that survives neither
    publication nor a clone. Only this layer sees both bundles, so the URL is
    made here or not at all.

    `url` is a prefix and `style` is the transform applied beneath it. The two
    are one object because `style` is meaningless without `url`: nesting them
    makes the invalid half-declaration unrepresentable rather than something a
    check has to catch.

    The value is a promise, never an observation. Nothing here fetches anything,
    which is deliberate: a bundle may declare where it *will* live and be linked
    to before its site exists, which is what lets two unpublished bundles cite
    each other. The cost is that a wrong promise is silent until someone opens
    the link.
    """

    STYLES = ("directory", "html", "raw")

    def __init__(self, bundle: str, entry: dict) -> None:
        url = entry.get("url")
        if not isinstance(url, str) or not url.strip():
            sys.exit(f"fkb: bundle `{bundle}` declares `publish` without a `url`")
        style = entry.get("style")
        if style not in self.STYLES:
            sys.exit(
                f"fkb: bundle `{bundle}` declares publish.style `{style}`; expected one of {', '.join(self.STYLES)}"
            )
        # Normalised on read, so the manifest cannot get this half wrong: a
        # prefix that does not end in a separator silently concatenates into the
        # first path segment, and the mistake renders as a plausible URL.
        self.url = url.strip().rstrip("/") + "/"
        self.style = style

    def to_url(self, relative: str) -> str:
        """The published URL of a concept, given its path beneath the bundle root."""
        return self.url + self.published_path(relative)

    def published_path(self, relative: str) -> str:
        stem = relative[: -len(".md")] if relative.endswith(".md") else relative
        if self.style == "raw":
            return relative
        if self.style == "html":
            return f"{stem}.html"
        # `directory`: the page is served as a directory, so an index is its own
        # parent and everything else gains one.
        if stem == "index":
            return ""
        if stem.endswith("/index"):
            return stem[: -len("index")]
        return f"{stem}/"

    def to_paths(self, url: str) -> list[str] | None:
        """The local paths a published URL could name, or None if it is not ours.

        The reverse direction, which is how lint finds cross-bundle links: a
        concept body carries absolute URLs and nothing else says which bundle
        each one belongs to. It is also why §4 forbids one bundle's prefix from
        containing another's - a URL under two prefixes has two answers, and a
        leak check that cannot name the target cannot run.

        A list rather than a path, because `directory` is not injective: MkDocs
        publishes both `foo/bar.md` and `foo/bar/index.md` at `foo/bar/`, and the
        URL has forgotten which. Only the checkout can say, so the candidates are
        returned in the order they should be tried and the caller looks. Which
        bundle the URL belongs to is never ambiguous, and that is the part the
        reference rule needs.
        """
        if not url.startswith(self.url):
            return None
        rest = url[len(self.url) :].split("#", maxsplit=1)[0].split("?", maxsplit=1)[0]
        if self.style == "raw":
            return [rest] if rest.endswith(".md") else None
        if self.style == "html":
            return [f"{rest[: -len('.html')]}.md"] if rest.endswith(".html") else None
        # `directory` again, inverted. A trailing slash is what the generator
        # emits and what a person copies from a browser; without one the site
        # still serves the page, so both spellings resolve here.
        stem = rest.rstrip("/")
        if not stem:
            return ["index.md"]
        return [f"{stem}.md", f"{stem}/index.md"]


class Bundle:
    """One bundle as this machine sees it, with the manifest's cautious defaults.

    Omitting `referenceable_by` means nothing may cite the bundle; omitting
    `writable` means no agent may author into it. Both fail closed, so a bundle
    that was added carelessly discloses nothing until someone opens it on
    purpose.
    """

    def __init__(self, name: str, entry: dict, workspace_root: Path | None) -> None:
        self.name = name
        raw = entry.get("path")
        if not raw:
            sys.exit(f"fkb: bundle `{name}` declares no path")
        path = Path(raw).expanduser()
        if not path.is_absolute():
            if workspace_root is None:
                sys.exit(f"fkb: bundle `{name}` has a relative path but no workspace_root is set")
            path = workspace_root / path
        self.path = path
        self.referenceable_by = entry.get("referenceable_by", [])
        self.writable = bool(entry.get("writable", False))
        self.sync = self._sync_branch(name, entry)
        raw_publish = entry.get("publish")
        if raw_publish is None:
            self.publish: Publish | None = None
        elif isinstance(raw_publish, dict):
            self.publish = Publish(name, raw_publish)
        else:
            sys.exit(
                f"fkb: bundle `{name}` declares `publish` as a bare string. "
                "It is a mapping now: `url:` and `style:` "
                f"({', '.join(Publish.STYLES)})."
            )

    @staticmethod
    def _sync_branch(name: str, entry: dict) -> str | None:
        """The branch this bundle is shared on, if anyone else writes into it.

        Absent is the default and means what it has always meant: commits stay
        on the machine that made them, and nothing is ever fetched. Present, it
        asserts three things at once (DESIGN §10) - the checkout belongs on that
        branch, commits made here may leave the machine, and somebody else is
        filing into this bundle too.

        A non-writable bundle declaring one is a contradiction rather than a
        harmless surplus: nothing here may author into it, so there is nothing
        of ours to push, and the reading that would make the field useful -
        "fetch, do not push" - is not what the field means. Refused on load
        beside the prefix check, so a bad manifest fails before the first push
        rather than during one.
        """
        branch = entry.get("sync")
        if branch is None:
            return None
        if not isinstance(branch, str) or not branch.strip():
            sys.exit(f"fkb: bundle `{name}` declares `sync` as `{branch!r}`; it is a branch name")
        if not entry.get("writable", False):
            sys.exit(
                f"fkb: bundle `{name}` declares `sync: {branch}` but is not writable.\n"
                "`sync` says commits made here may leave the machine, and nothing here may "
                "make one. Either set `writable: true` or drop `sync`."
            )
        return branch.strip()

    def may_be_cited_by(self, other: str) -> bool:
        """The reference rule, as §4 states it: inbound, and failing closed.

        A bundle may always cite itself, which is what makes an ordinary
        relative link inside one bundle none of this layer's business.
        """
        if other == self.name:
            return True
        if self.referenceable_by == "*":
            return True
        return other in (self.referenceable_by or [])

    @property
    def citation(self) -> str:
        """`referenceable_by` as the manifest holds it, with a reading of what it means.

        The value is printed verbatim so what `list` shows can be found in the
        file it came from. The gloss is there because `[]` looks like an omission
        and is in fact the whole point: a bundle nothing may cite cannot surface
        through a link from one that publishes.
        """
        if self.referenceable_by == "*":
            return '"*"  (any bundle may cite this one)'
        if not self.referenceable_by:
            return "[]   (sealed: no bundle may cite this one)"
        listed = ", ".join(self.referenceable_by)
        return f"[{listed}]  (only these may cite this one)"

    @property
    def config(self) -> Path | None:
        """The bundle's own declaration, found by convention rather than told.

        Only `fkb` needs the filename to be this exact string: the standalone
        hook is handed an explicit path and would accept any name (DESIGN §9.2).
        A bundle that does not carry the file is held to conformance alone.
        """
        candidate = self.path / CONFIG_FILE
        return candidate if candidate.is_file() else None

    @property
    def floor(self) -> Path | None:
        """The floor declaration, which is the config file when there is one."""
        return self.config

    @property
    def conventions(self) -> Path | None:
        """The bundle's house rules, if it declares where they are.

        Resolved against the declaring file and permitted to escape the bundle
        root, because a bundle may keep its conventions beside the site rather
        than inside the knowledge (DESIGN §9.2). Returned whether or not it
        resolves: reporting a broken pointer is the point, and `lint` is what
        calls it a defect.
        """
        config = self.config
        if config is None:
            return None
        try:
            declared = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            return None
        relative = declared.get("conventions") if isinstance(declared, dict) else None
        if not isinstance(relative, str) or not relative.strip():
            return None
        return (config.parent / relative.strip()).resolve()


def load_bundles(*, allow_empty: bool = False) -> list[Bundle]:
    path = manifest_path()
    me = invocation()
    if not path.is_file():
        sys.exit(
            f"fkb: no workspace manifest at {path}.\n"
            f"Run `{me} init` to create one, then `{me} add` to bring a bundle into it."
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        sys.exit(f"fkb: cannot read {path}: {exc}")

    raw_root = data.get("workspace_root")
    root = Path(raw_root).expanduser() if raw_root else None
    bundles = data.get("bundles") or {}
    # An empty workspace is what `fkb init` deliberately writes, so it is a
    # state to report rather than an error. It stays an error for the commands
    # that were asked about a particular bundle, because there the answer is
    # that the named one does not exist.
    if not bundles and not allow_empty:
        sys.exit(f"fkb: {path} declares no bundles yet. Add one with `{me} add`.")
    loaded = [Bundle(name, entry or {}, root) for name, entry in bundles.items()]
    check_publish_prefixes(loaded)
    return loaded


def check_publish_prefixes(bundles: list[Bundle]) -> None:
    """Refuse a manifest in which one bundle's publish URL contains another's.

    Reading a link forwards never needs this; reading one backwards always does.
    Given an absolute URL in a concept, lint asks which bundle published it, and
    two bundles sharing a site root leave that question with two answers - so a
    link into the more specific one also matches the broader one, and the
    reference rule would be applied against whichever happened to be checked
    first. Refusing at load is the only place this is cheap: afterwards the
    ambiguity is spread across every link already written.
    """
    published = [(b.name, b.publish.url) for b in bundles if b.publish]
    for name, url in published:
        for other, other_url in published:
            if name != other and url.startswith(other_url):
                sys.exit(
                    f"fkb: bundle `{name}` publishes under `{url}`, which sits inside "
                    f"bundle `{other}`'s `{other_url}`. A URL under both cannot be "
                    "attributed to one of them, so links between bundles cannot be checked. "
                    "Give them separate prefixes."
                )
