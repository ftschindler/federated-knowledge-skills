# Giving a bundle its infrastructure

`fkb add --new` writes the smallest bundle that passes its own lint: an index, a log, and a
floor. That is enough to file into and not much else. A bundle people actually live with
grows a few more layers - something that checks it, something that publishes it, something
that says how to write in it.

**This page does not contain that infrastructure.** It describes the shape and then sends
you to read a working example, because a file listing someone's site generator and their
hook versions is wrong within the year and looks authoritative the whole time. The shape
below has been stable since the beginning; every concrete answer to it belongs to whoever
currently maintains the bundle you copy from.

## Read the reference implementation

`ftschindler/knowledge` is the worked example, and onboarding already cloned it - it is the
bundle registered as `practice`. Its *repository root* is the interesting part here, not the
bundle inside it:

```text
uv run SKILLDIR/scripts/fkb list          # find where `practice` is checked out
ls -a <that path>/..             # the repository root, one level above the bundle
```

Read it as a whole before copying anything from it. The layers below are the questions to
read it for.

## The layers, and the question each one answers

A publishing bundle has all of these. A private one has the first three and nothing else.

| Layer | The question it answers | Where it lives |
| --- | --- | --- |
| **The floor** | What must every concept in this bundle carry? | `fkb.yaml` at the bundle root |
| **Conformance hooks** | What refuses a bad concept before it lands? | `.pre-commit-config.yaml` |
| **Conventions** | How is prose written here, and where does a newcomer read that? | A markdown page the floor points at |
| **Editing rules** | What does a markdown linter enforce, and what does a link checker check? | Per-tool config at the repository root |
| **The editor's view** | How does this look to a person opening it in an editor or vault? | Editor or vault configuration |
| **The site** | How do concepts become pages, and where is the navigation declared? | Site generator config, theme overrides, build hooks |
| **The gate** | What must pass before anything is published? | CI workflows |
| **Non-knowledge pages** | Where do "about this site" pages live, given a bundle holds only concepts? | A directory *outside* the bundle root |

The last three are what separates a public bundle from a private one. Everything above them
applies to both.

### The two hooks are ours, and are the one thing to copy exactly

Every other layer is somebody's choice. These are published from this skill's own repository
and a bundle pins them by revision:

```yaml
- repo: https://github.com/ftschindler/federated-knowledge-skills
  rev: <commit>
  hooks:
  - id: okf-concepts
    args: [--bundle-root, docs, --floor, docs/fkb.yaml]
  - id: okf-bundle
    args: [--bundle-root, docs, --floor, docs/fkb.yaml]
```

`okf-concepts` checks the whole bundle and fails only on findings in the files being
committed, so an unfinished concept elsewhere never blocks an unrelated commit. With
`--all-files` everything is in scope, which is how the same hook is strict in CI without a
second configuration. `okf-bundle` adds index coverage and sits on the manual stage, so it
stays off the commit path and CI calls it by name.

**Adjust both paths to where the bundle actually starts.** `--bundle-root docs` for a bundle
under `docs/`, `--bundle-root .` for one at the repository root. Getting this wrong is the
single most common way a copied configuration fails, and it fails by checking nothing rather
than by complaining.

**Name the floor file `fkb.yaml`.** The hook accepts any name because it is told the path,
but `fkb` finds the floor by that name and by no other. A bundle whose floor is called
something else is enforced by its own hook and *not* by `fkb lint`, which is two tools
disagreeing about what the bundle requires - and the disagreement is silent, because the
looser one is the one that says `ok`.

## Bootstrapping a public bundle

A bundle whose concepts are meant to be read by people who will never clone it.

1. **Create and register it**, publishable rather than sealed:

   ```text
   uv run SKILLDIR/scripts/fkb add mykb --new --writable --referenceable-by '*'
   ```

2. **Decide where the bundle sits in its repository.** A publishing bundle usually keeps
   concepts under `docs/` with build configuration above them, because a site generator wants
   a directory it can treat as its whole input. Move the scaffolded files there if so, and
   remember that every path in every config follows.

3. **Copy the layers from the reference checkout**, adapting as you go. Take the shape, not
   the contents.

4. **Tell `fkb` where it publishes**, once the site has a URL. The address of a page you can
   already open is the safest way to get both halves right:

   ```text
   uv run SKILLDIR/scripts/fkb add mykb --path <bundle root>  --publish-sample https://example.com/kb/topic/a-concept/  --publish-sample-path topic/a_concept.md
   ```

   It may also be declared before the site exists, since it is a promise about where the
   bundle will be reachable.

5. **Put non-knowledge pages outside the bundle root.** Every non-reserved markdown file
   inside a bundle is a concept and is checked as one, so a colophon or a contributing guide
   belongs in a sibling directory that the site includes and the bundle does not.

## Bootstrapping a private bundle

Simpler, and with one specific trap.

```text
uv run SKILLDIR/scripts/fkb add private --new --writable
```

Sealed by default, which is what you want: nothing may cite it, so nothing in it can surface
through a link from a bundle that publishes. It keeps its concepts at the repository root -
there is no site, so there is nothing to keep them out of the way of.

It still wants the first three layers. A private bundle with no hooks drifts faster than a
public one, because nothing else ever looks at it.

> **Do not clone the public bundle's repository to make a private one.** It has been done,
> and what arrives is a configuration written for a bundle rooted at `docs/` pointed at a
> bundle rooted at `.`, a copy of a helper script that is stale the moment the original
> changes, and none of the prose that makes the rules knowable - because the conventions page
> and the agent instructions live in directories the copy did not bring. Start empty and add
> layers deliberately. It is a shorter job than fixing the inherited one.

## What to adapt, and what never to copy

A scan of someone else's repository cannot tell you which of their files are about *them*.

**Always adapt:** the site URL and repository name; the licence and its holder; author
identity files; ownership and review configuration; the navigation, which lists their
sections; the floor, if your bundle requires different fields; every path argument, if your
bundle root differs from theirs.

**Never copy:** the concepts themselves - the whole point is that yours are yours; build
output, virtual environments, caches and lock files from their toolchain; anything under a
directory their tooling generates.

**Check afterwards**, in this order, because each catches what the previous one cannot:

```text
uv run SKILLDIR/scripts/fkb lint mykb     # conformance, and the floor as `fkb` discovers it
prek run --all-files             # the bundle's own hooks, which are the real gate
```

If those two disagree about the same file, the floor is not where `fkb` looks for it. See
above.
