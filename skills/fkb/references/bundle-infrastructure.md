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
bundle registered as `ftschindler`. Its *repository root* is the interesting part here, not the
bundle inside it:

```text
uv run SKILLDIR/scripts/fkb list          # find where `ftschindler` is checked out
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

### The two hooks are ours, and their wiring is the one thing not to improvise

Every other layer is somebody's choice. These are published from this skill's own repository
and a bundle pins them by revision:

```yaml
- repo: https://github.com/ftschindler/federated-knowledge-skills
  rev: <commit>
  hooks:
  - id: okf-concepts
    args: [--bundle-root, BUNDLEROOT, --floor, BUNDLEROOT/fkb.yaml]
  - id: okf-bundle
    args: [--bundle-root, BUNDLEROOT, --floor, BUNDLEROOT/fkb.yaml]
```

The repository, the two ids and the argument names are fixed. `BUNDLEROOT` is not: it is
where this bundle's concepts start, relative to the repository root, and it follows from the
shape the bundle ended up with.

| Bundle shape | `BUNDLEROOT` | The floor path beside it |
| --- | --- | --- |
| Private, or shared with no site | `.` | `fkb.yaml` |
| Published | `docs` | `docs/fkb.yaml` |

A publishing bundle keeps its concepts under `docs/` because a site generator wants a
directory it can treat as its whole input; a bundle with no site has nothing to keep them out
of the way of, so they sit at the root. **Both values move together.** A `--bundle-root` that
points at the wrong place fails by checking nothing rather than by complaining, which is the
single most common way a copied configuration goes wrong - and a `--floor` left behind when
the root moved means the hook enforces OKF and quietly stops enforcing what the bundle
declared.

**Look `<commit>` up, do not copy one.** A revision written into a page is stale the week
after it is written, and a stale pin is invisible: the hooks run, they pass, and they are not
the hooks anyone thinks they are. There are no tags to name, so the revision is a commit on
`main`:

```text
git ls-remote https://github.com/ftschindler/federated-knowledge-skills main
```

Use the SHA it prints. Do not put a branch name there instead - the whole reason a hook is
pinned is that it must not change under the bundle without someone deciding it should.

Then make it run, and check it does:

```text
uvx prek install
uvx prek run --all-files
```

That second command is also how the paths get checked: a run that reports no files is a
`--bundle-root` pointing somewhere with no concepts in it, not a clean bundle.

`okf-concepts` checks the whole bundle and fails only on findings in the files being
committed, so an unfinished concept elsewhere never blocks an unrelated commit. With
`--all-files` everything is in scope, which is how the same hook is strict in CI without a
second configuration. `okf-bundle` adds index coverage and sits on the manual stage, so it
stays off the commit path and CI calls it by name.

**Name the floor file `fkb.yaml`.** The hook accepts any name because it is told the path,
but `fkb` finds the floor by that name and by no other. A bundle whose floor is called
something else is enforced by its own hook and *not* by `fkb lint`, which is two tools
disagreeing about what the bundle requires - and the disagreement is silent, because the
looser one is the one that says `ok`.

## Bootstrapping a bundle that publishes

A site exists for **readers who will not clone the repository** - someone who wants to read a
page, not check one out. It says nothing about how the owner works: a published bundle is
cloned, edited in an editor or a vault, and committed like any other repository, every day.
The site is an additional output, not a replacement for the checkout.

**Publishing is not the same as being public.** `publish` says where the concepts are
reachable from outside the checkout; who can actually reach that address is a property of the
hosting - an internal site behind a company login, a repository a dozen colleagues can read,
or the open web. And neither of those is `referenceable_by`, which is this federation's own
policy about which bundles may point here. Three separate questions, and answering the first
tells you nothing about the other two.

1. **Ask what it should be called, and do not answer for them.** The private bundle was not a
   question; this one is. A bundle is found by what the person calls it, so the name is what
   their own words have to match later - and one created under a name invented here is one
   they will not think to ask for. If they have no preference, `public` pairs with `private`
   and both match the words people actually use. If they are not ready to decide, **stop and
   say what is outstanding**: a bundle that does not exist yet costs nothing, and a bundle
   under the wrong name costs a rename in the manifest plus every link already pointing into
   it.

2. **Ask which bundles may cite it.** `'*'` means every bundle on this machine, now and in
   future, which is right for something on the open web and wrong for a bundle whose readers
   are one team. Name them instead when the answer is narrower, and remember the value is
   inbound: it says who may point *here*, not where this bundle may point.

   ```text
   uv run SKILLDIR/scripts/fkb add NAME --new --writable --referenceable-by '*'
   uv run SKILLDIR/scripts/fkb add NAME --new --writable --referenceable-by private,team
   ```

   If this bundle also needs to cite existing ones, that is a change to *their* entries and
   `add` does not make it - see [federation](federation.md).

3. **Decide where the bundle sits in its repository.** A publishing bundle usually keeps
   concepts under `docs/` with build configuration above them, because a site generator wants
   a directory it can treat as its whole input. Move the scaffolded files there if so, and
   remember that every path in every config follows - including the hook arguments above.

4. **Copy the layers from the reference checkout**, adapting as you go. Take the shape, not
   the contents.

5. **Tell `fkb` where it publishes**, once the site has a URL. The address of a page you can
   already open is the safest way to get both halves right:

   ```text
   uv run SKILLDIR/scripts/fkb add NAME --path <bundle root>  --publish-sample https://example.com/kb/topic/a-concept/  --publish-sample-path topic/a_concept.md
   ```

   It may also be declared before the site exists, since it is a promise about where the
   bundle will be reachable.

6. **Put non-knowledge pages outside the bundle root.** Every non-reserved markdown file
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

## Sharing a bundle with several people

A bundle several people file into has two clocks: what has been written, and what has been
reviewed. **Two branches, and neither weakens the other.** The repository's default branch
holds what has been reviewed and is what the site is built from; a long-lived shared branch -
`staging`, conventionally - holds that plus everything not ready yet, and is where every
checkout sits and every agent files.

The manifest half is one field, and `fkb` does the rest:

```text
uv run SKILLDIR/scripts/fkb add NAME --clone <remote> --writable --sync staging
```

It checks the branch out, `fkb sync` moves commits to and from it, and `fkb lint` says so when
a checkout has drifted onto another one. A bundle without the field behaves exactly as before:
commit, never push, nothing fetched.

The repository half is configuration, per bundle, and **none of it is enforced from here.**
Four properties, each of which fails quietly rather than loudly when it is missing:

| Load-bearing | What | Why, if it is missing |
| --- | --- | --- |
| yes | The default branch is protected: pull request and review | The careless web edit publishes unreviewed work; the review gate is decoration |
| yes | Merge commits only - no squash, no rebase merging | The branches stop sharing ancestry, the next release re-displays everything, and the merge back conflicts content against a copy of itself |
| yes | The merge back runs on **every** change to the default branch | The branches drift, every working copy goes stale, and the first symptom is a concept filed twice |
| yes | CI runs the bundle's own checks on pushes to the shared branch | A web edit has no working copy, so the pre-commit hooks never ran on it |

The third one ships from here as a reusable workflow, because it is the only one whose
absence nobody sees. Call it from the bundle, **pinned at the same commit the bundle already
pins for its hooks**, by full SHA and never by tag - it needs write access to the shared
branch, which is a larger trust step than a hook that only ran on a machine already holding
the files:

```yaml
name: Merge back
on:
  push:
    branches: [main]
jobs:
  merge_back:
    uses: ftschindler/federated-knowledge-skills/.github/workflows/merge-back.yml@<commit>
    with:
      branch: staging
    permissions:
      contents: write
      pull-requests: write
```

It merges rather than squashes, and opens a pull request against the shared branch when the
merge conflicts rather than failing a run somebody has stopped reading. It is GitHub Actions
and therefore about one forge; a bundle elsewhere reproduces the behaviour in four lines of
its own CI, and everything else here still holds.

That pull request is the one part of it with a repository setting behind it. The run opens it
with its own token, so **Workflow permissions, under Settings > Actions > General, has to
allow GitHub Actions to create pull requests.** Left off, the conflict path ends in a
permission error rather than in a page somebody is assigned - in the one situation where this
workflow is the only thing still watching the two branches.

**Give the bundle a `.gitattributes`.** `fkb add --new` writes one; a bundle that predates it
wants these two lines, at the bundle root:

```text
index.md merge=union
log.md merge=union
```

Both files are append-only, so the common concurrent edit stops being a conflict at all: two
people filing on the same day append different lines and both are kept. What remains is two
people writing the same concept, which is a question about what is true and the only case
worth a person's attention.

**Releases are a pull request from the shared branch to the default one**, cut on a cadence
you choose. Nothing here creates it: that is `gh pr create`, and a shorter cadence is also the
cheapest answer to the one thing this shape gives up - a concept is on every teammate's disk
as soon as it is pushed, and on the site only after the next release.

**A check that forbids merge commits on pull requests has to exempt these two branches.** It
is a common guard and it is right for the branches a person opens, but the release pull
request carries every merge the workflow above pushed onto the shared branch, and the conflict
one carries whatever the default branch merged. Both have multi-parent commits by
construction, so a guard that reads every commit rejects precisely the two pull requests this
shape is made of. Exempt them by head branch rather than dropping the guard.

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
uv run SKILLDIR/scripts/fkb lint NAME     # conformance, and the floor as `fkb` discovers it
prek run --all-files             # the bundle's own hooks, which are the real gate
```

If those two disagree about the same file, the floor is not where `fkb` looks for it. See
above.
