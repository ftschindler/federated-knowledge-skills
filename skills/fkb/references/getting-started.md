# Getting started

You have the `fkb` skill installed and no knowledge base yet, or one you did not set up
yourself. This page is the long form of that: what these things are, and the exact commands
that turn an empty machine into a working one.

Nothing here has to be done by hand. The agent reading this can run every command on the
page, and should say what it is doing as it goes.

## What a bundle is

A **bundle** is a directory of markdown files, one idea per file. Each file is a *concept*:
a few lines of YAML frontmatter and then prose. That is the whole format. There is no
database, no index to rebuild, no ingest step. The file an agent writes is the file a person
opens in an editor.

It follows the [Open Knowledge Format](SPEC.md), which asks for very little: every concept
declares a `type`, and everything else the format merely recommends. A bundle may require
more of itself, and says so in a file at its own root - see [house style](house-style.md).

A bundle is almost always a git repository, so it has history, it can be shared, and its own
pre-commit hooks can refuse a concept that does not hold up. None of that is required to
start.

## What the federation is

Several bundles, side by side, at different privacy tiers. Something you would publish goes
in one; something that must never leave the machine goes in another; a bundle somebody else
wrote is read but never written to.

One file on this machine knows about all of them: the **workspace manifest**, at
`$XDG_CONFIG_HOME/fkb/workspace.yaml`. It records, per bundle, where it is checked out and
what may be done with it. `fkb` reads it; nothing else does.

The bundles themselves know nothing about each other. That is deliberate, and it is why
linking between them goes through a command rather than through a relative path - see
[federation](federation.md).

## Step 1: do you already have one?

```text
uv run SKILLDIR/scripts/fkb list
```

Three things it can say:

- **A list of bundles.** There is a workspace. Skip to [what to do next](#what-to-do-next).
- **"No bundles yet."** The workspace exists and is empty. Go to step 3.
- **"no workspace manifest at ..."** Nothing is set up. Start at step 2.

## Step 2: create the workspace

This happens once per machine, and asks nothing about knowledge - only where bundles are
kept on disk.

```text
uv run SKILLDIR/scripts/fkb init --workspace-root WORKSPACE
```

**Write `WORKSPACE` out in full**, as an absolute path. A leading `~` is expanded by some
shells and left as a literal directory name by others, and a workspace in a folder called
`~` is a puzzle to find later.

The root is worth one moment's thought, because moving it later means re-registering every
bundle. Two answers, and the choice is about how you expect to work rather than about
correctness:

| Root | Pick it when |
| --- | --- |
| `knowledge` in their home directory | They intend to open these files themselves, in an editor or in Obsidian. They are theirs, and putting them where they can be seen is the point. |
| `knowledge` under their agent directory | They would rather their home directory stayed as it is, and expect to reach the content through an agent or a published site. |

Any path works, and a bundle that already lives somewhere else is registered where it lies
rather than moved.

**If they asked to be set up, pick `~/knowledge` and say so in one line.** The decision is
already made and this is the least interesting part of it; the root lives on one line of the
manifest, and changing it later means re-registering the bundles rather than losing anything.

**Ask only when setup was not what they asked for** - when they wanted something filed or
answered, and the missing workspace is what is in the way. Then you are about to create
something they never mentioned, and the question earns its turn.

## Step 3: add the two public bundles

These are read-only: you cite them, you never write into them. Both are worth having from
the first day, and between them they answer most of "what is this and how should I use it".

```text
uv run SKILLDIR/scripts/fkb add llm-wiki  --clone https://github.com/stjbrown/agent-knowledge  --referenceable-by '*'  --publish-url https://github.com/stjbrown/agent-knowledge/blob/main/knowledge/  --publish-style raw

uv run SKILLDIR/scripts/fkb add practice  --clone https://github.com/ftschindler/knowledge  --referenceable-by '*'  --publish-url https://ftschindler.github.io/knowledge/  --publish-style directory
```

`llm-wiki` is about the idea itself: what an agent-maintained wiki is, why one idea per file,
what the format is for. `practice` is applied knowledge - knowledge management, and
engineering practice from someone using this daily. Read a few concepts from each before
writing your own; it is the fastest way to see what a good concept looks like.

Neither is `--writable`, which is the default, so nothing can author into them by accident.

> These two also happen to demonstrate both ways a bundle publishes. The first has no
> deployed site, so its concepts are reachable as files on a branch and keep their `.md`
> extension: that is `--publish-style raw`. The second is a generated site where
> `foo/bar.md` is served at `foo/bar/`: that is `directory`. The distinction matters when
> something links to them, and it is why the style is declared rather than guessed.

## Step 4: a bundle of your own

Somewhere to actually write. One command, and it exists:

```text
uv run SKILLDIR/scripts/fkb add notes --new --writable
```

That scaffolds a conformant bundle under the workspace root - an index, a log, and a file
declaring what a concept in it must carry - and registers it as writable and **sealed**:
nothing may cite it, so nothing in it can surface through a link from somewhere that
publishes. That is the cautious default, and for a private bundle it is also the right one
permanently.

If you want it published, or citable by another bundle, say so when you add it:

```text
uv run SKILLDIR/scripts/fkb add team --new --writable --referenceable-by '*'
```

It is a git repository as soon as you make it one, which `fkb` deliberately does not do for
you: `git init` and the first commit are yours.

What it is **not** is a bundle with hooks checking it, a site publishing it, or a page saying
how to write in it. Those are worth having and none of them is scaffolded, because each is a
choice. [Bundle infrastructure](bundle-infrastructure.md) describes the shape and sends you
to read the reference implementation you have just cloned - which is the only copy of it that
cannot go out of date.

## The three ways a bundle arrives

Step 3 cloned one and step 4 created one. The third case is a bundle already sitting on this
machine, perhaps without anyone having called it a bundle:

```text
uv run SKILLDIR/scripts/fkb add kb --path PATH/TO/THE/CHECKOUT --writable
```

| Arrival | Command | What happens |
| --- | --- | --- |
| Remote repository | `--clone <url>` | Cloned under the workspace root, its bundle root found inside it, registered |
| Already on disk | `--path <dir>` | Registered exactly where it is, absolute, nothing moved |
| Does not exist yet | `--new` | A minimal conformant bundle is written and registered |

**The bundle root is not always the repository root.** A repository that publishes usually
keeps concepts under `docs/`, with build configuration above them, so `add` looks for the
shallowest `index.md` rather than assuming. If two candidates sit at the same depth it stops
and asks, because one of them may be an example bundle shipped as documentation, and
registering that would quietly turn a sample into your knowledge base.

## What the manifest records

Four things per bundle. Both of the security-relevant ones fail closed, so a bundle added
carelessly discloses nothing until it is opened deliberately.

| Field | Question it answers | Default |
| --- | --- | --- |
| `path` | Where the bundle is checked out here | required |
| `referenceable_by` | Who may point *at* me | `[]`, meaning nobody |
| `writable` | May an agent author into me on this machine | `false` |
| `publish` | Where my concepts are reachable from outside | none |

`referenceable_by` is inbound: it lists who may cite this bundle, not who it may cite. Two
bundles that should cite each other name each other. `"*"` means anyone.

**`writable` is a property of this machine**, not of the bundle. The same repository can be
writable on your laptop and read-only on a colleague's.

### Getting `publish` right

`publish` has two halves, and both have a plausible wrong answer:

```yaml
publish:
  url: https://ftschindler.github.io/knowledge/
  style: directory
```

The `url` is the prefix its *concepts* hang under, not the repository's landing page. The
`style` says how a local path becomes a URL: `directory` for a generated site that serves
`foo/bar.md` at `foo/bar/`, `html` for one that serves `foo/bar.html`, `raw` for a forge or
file server that keeps `foo/bar.md`.

Nothing ever fetches this value, which means a wrong one is silent forever - it was wrong
once for weeks, producing links that 404ed and looked perfectly reasonable. So rather than
answer two abstract questions, hand over one page you can already open and let `add` work
backwards:

```text
uv run SKILLDIR/scripts/fkb add kb --path PATH/TO/THE/CHECKOUT --publish-sample https://example.com/kb/topic/some-concept/ --publish-sample-path topic/some_concept.md
```

If the URL is not how that path would be published under any known style, it says so and
tells you what each style would have produced. That is the only moment in a bundle's life
when this can be checked against something real.

A bundle with no `publish` is not a problem: it simply cannot be linked to from elsewhere,
which for a private bundle is exactly right. It may also be declared before the site exists,
because it is a promise about where the bundle *will* be reachable rather than a claim about
where it is now. That is what lets two unpublished bundles link to each other.

## What to do next

```text
uv run SKILLDIR/scripts/fkb list          # what you now have, and what each allows
uv run SKILLDIR/scripts/fkb lint          # every bundle, checked where it lies
```

Then read three or four concepts from `practice`, and file something of your own. The skill
body carries the filing steps; this page is only about getting to the point where they make
sense.

Two things that will save a puzzled moment later:

- **Warnings from a read-only bundle are not yours to fix.** An upstream written against an
  older version of the format reports a hundred of them and blocks nothing.
- **`fkb` never commits.** The bundle is a git repository with its own hooks, and those
  hooks are the real gate. Committing stays with the person unless they ask otherwise.
