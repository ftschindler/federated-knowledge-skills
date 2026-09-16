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

One file on this machine knows about all of them: the **workspace manifest**. It records, per
bundle, where it is checked out and what may be done with it. `fkb` reads it; nothing else
does, and it is the file to edit by hand when you want to change policy.

**Ask where it is rather than assuming.** Its location is a property of the machine - the
user configuration directory, wherever that turns out to be here - so `fkb list` prints the
path before the bundles, and every message about a missing manifest names it in full.

The bundles themselves know nothing about each other. That is deliberate, and it is why
linking between them goes through a command rather than through a relative path - see
[federation](federation.md).

### Where this comes from

The skill, the `fkb` CLI and the pre-commit hooks a bundle pins are all published from
<https://github.com/ftschindler/federated-knowledge-skills>.

Worth naming, because everything on this page is the short answer. The repository carries the
design and why each part is shaped the way it is, the implementation plan, and a journal of
the incidents that produced the rules here - which is the honest account of what went wrong
before a rule existed. Go there to understand a decision, to disagree with one, or to file an
issue; nothing on this page needs you to.

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

Run it with no root first. It proposes the ones that make sense here and says what each is
for, which is not the same list on every operating system. It writes nothing:

```text
uv run SKILLDIR/scripts/fkb init --propose-roots
```

Then run it again with the one you picked:

```text
uv run SKILLDIR/scripts/fkb init --workspace-root WORKSPACE
```

The proposals come out as absolute paths, which is what to pass back. **Write `WORKSPACE`
out in full** if you write one yourself: a leading `~` is expanded by some shells and left
as a literal directory name by others, and a workspace in a folder called `~` is a puzzle to
find later.

The root is worth one moment's thought, because moving it later means re-registering every
bundle. The proposals differ by machine; the choice between them does not, and it is about
how you expect to work rather than about correctness:

| Root | Pick it when |
| --- | --- |
| `knowledge` under their agent directory **(recommended)** | The usual case. The content is reached through an agent or a published site, and a knowledge base is not something most people open by hand often enough to earn a visible directory in their home. |
| `knowledge` in their home directory | They intend to open these files themselves, in an editor or in Obsidian. Then being able to see them is the whole point. |

Any path works, and a bundle that already lives somewhere else is registered where it lies
rather than moved.

**If they asked to be set up, take the recommended one and say so in one line.** The decision
is already made and this is the least interesting part of it; the root lives on one line of
the manifest, and changing it later means re-registering the bundles rather than losing
anything.

**Ask only when setup was not what they asked for** - when they wanted something filed or
answered, and the missing workspace is what is in the way. Then you are about to create
something they never mentioned, and the question earns its turn.

## Step 3: add the two public bundles

These are read-only: you cite them, you never write into them. Both are worth having from
the first day, and between them they answer most of "what is this and how should I use it".

```text
uv run SKILLDIR/scripts/fkb add stjbrown  --clone https://github.com/stjbrown/agent-knowledge  --referenceable-by '*'  --publish-url https://github.com/stjbrown/agent-knowledge/blob/main/knowledge/  --publish-style raw

uv run SKILLDIR/scripts/fkb add ftschindler  --clone https://github.com/ftschindler/knowledge  --referenceable-by '*'  --publish-url https://ftschindler.github.io/knowledge/  --publish-style directory
```

`stjbrown` is about the idea itself: what an agent-maintained wiki is, why one idea per file,
what the format is for. `ftschindler` is applied knowledge - knowledge management, and
engineering practice from someone using this daily. Read a few concepts from each before
writing your own; it is the fastest way to see what a good concept looks like.

**An upstream is named for whose it is, not for what it is about.** Its subject is never
exclusive - a second bundle of engineering practice will want the same name as the first, and
then neither can have it - whereas there is exactly one `ftschindler`. The name is also what
a person's words have to match, and "what does Felix say about this" names an author rather
than a topic.

Neither is `--writable`, which is the default, so nothing can author into them by accident.

> These two also happen to demonstrate both ways a bundle publishes. The first has no
> deployed site, so its concepts are reachable as files on a branch and keep their `.md`
> extension: that is `--publish-style raw`. The second is a generated site where
> `foo/bar.md` is served at `foo/bar/`: that is `directory`. The distinction matters when
> something links to them, and it is why the style is declared rather than guessed.

## Step 4: a private bundle, always

Somewhere to actually write. This one is not a question - everybody needs a place for their
own notes, and sealed is the right setting for it permanently:

```text
uv run SKILLDIR/scripts/fkb add private --new --writable
```

That scaffolds a conformant bundle under the workspace root - an index, a log, and a file
declaring what a concept in it must carry - and registers it as writable and **sealed**:
nothing may cite it, so nothing in it can surface through a link from somewhere that
publishes.

**The name is part of how it gets used.** A bundle is chosen by what the person called it, so
`private` is what makes "note this in the private wiki" land here rather than somewhere that
publishes. Call it something else and that phrase matches nothing, and the choice falls back
to reading sensitivity off the manifest - which arrives at the same bundle, but by inference
rather than by being told.

It is a git repository from the moment `add` creates it: `git init` runs as part of
scaffolding, because a bundle with history, hooks and a way to be shared beats one without
and there is no judgement in that. What `fkb` does *not* do is pin the hooks or make the
first commit - the revision to pin is a fact about a remote right now, and a commit needs an
author no program should invent. Both are the next thing to do, and
[bundle infrastructure](bundle-infrastructure.md) has the config and the lookup.

A machine with no git still gets a bundle; it is then a plain directory, every check here
still runs, and history can be added whenever.

## Step 5: a shared one, if they want it

**Ask this one.** A private bundle is a directory; a shared one is a commitment to other
people reading it, and the work is not the same. It is also the only question in this whole
setup whose answer nobody can infer.

Three shapes, and each is the previous one plus something:

| Shape | What it needs | `add` |
| --- | --- | --- |
| **Private** | The bundle, and hooks so nothing bad lands in it | `--new --writable` |
| **Shared, no site** | The same, plus a remote the other people can clone | `--new --writable --referenceable-by '<them>'` |
| **Published** | The same, plus a site generator, its navigation, and CI that gates the publish | as above, plus `publish` once the site has an address |

```text
uv run SKILLDIR/scripts/fkb add team --new --writable --referenceable-by '*'
```

**The middle row is the one people skip past, and it is often the right answer.** A bundle on
a forge is already readable and already citable - point `publish` at the blob URL with
`--publish-style raw`, which is exactly how `stjbrown` is registered above. No site, no
generator, no deploy, and cross-bundle links work. Build the site when someone who will not
clone the repository needs to read it, which is a real reason and a later one.

The published row is a project rather than a command: a generator to choose, navigation to
declare, a theme, a build that has to keep passing. None of it is scaffolded, because each
part is a choice. [Bundle infrastructure](bundle-infrastructure.md) describes the shape and
sends you to read the reference implementation you have just cloned in `ftschindler` - which
is the only copy of it that cannot go out of date.

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

Then read three or four concepts from `ftschindler` to see what a good one looks like. The
bundle you made is empty, and it stays empty until you have something real to put in it -
that is the correct state, not a setup step left unfinished. The skill body carries the
filing steps; this page is only about getting to the point where they make sense.

Two things that will save a puzzled moment later:

- **Warnings from a read-only bundle are not yours to fix.** An upstream written against an
  older version of the format reports a hundred of them and blocks nothing.
- **`fkb` never commits, but the agent does.** The bundle's own hooks are the real gate, so
  a concept is written, linted and committed in one go, and the hooks get to refuse it.
  Pushing stays with you.
