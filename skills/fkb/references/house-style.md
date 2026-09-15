# House style: how to write a concept the bundle will accept

**This page contains no house style.** It cannot: the bundles on one machine agree on almost
nothing. Concepts start at the repository root in one and under `docs/` in another. One
requires five frontmatter fields, one requires none at all. Prose conventions live in a
different place in every bundle that has any, and one bundle has none.

So what follows is the procedure for finding out, which is the only thing that generalises.
A rule copied from one bundle into this file would be wrong in three others and, worse,
would look authoritative.

## Read four things before writing

In this order. The first three are cheap and the fourth is the one that is usually skipped.

### 1. The floor: `fkb.yaml` at the bundle root

A flat `required:` list naming the frontmatter every concept in this bundle must carry.
Satisfy it exactly.

**Do not keep a list of required fields in your head, and do not copy one from another
bundle.** That file is the single statement of what this bundle requires; a second copy is
free to drift from it, and the bundle's own pre-commit hook reads the file, not your memory.

A bundle with no `fkb.yaml` requires nothing beyond the format itself. That is not an
oversight to correct - a third-party bundle will never have one - so write to the format and
do not invent a floor for it.

### 2. The conventions the bundle points at

If `fkb.yaml` carries a `conventions:` key, it is a path to that bundle's own prose rules.
Read what it points at. The path is relative to `fkb.yaml` and is allowed to leave the
bundle root, because a bundle may keep its conventions beside its website rather than inside
its knowledge.

No `conventions:` key means the bundle has not written its rules down. Fall through to the
next two, which are how you read them off the content instead.

### 3. The index of the directory you are writing into

Not the bundle's top-level index: the one in the directory the concept is going in, if there
is one. Bundles that have grown tend to move the definition of a category into that
category's own index, so `findings/index.md` is where a bundle says what a Finding is, what
its titles look like, and which order its list runs in.

Reading the top-level index instead costs a whole pass over the bundle and still misses
this. If the directory has no index, the top-level one is what there is.

### 4. Two existing concepts from that same directory

The floor and the indexes give you the bundle's *schema* and none of its *voice*. Concepts
written without opening a neighbour come out in whatever register the model defaults to, and
that has to be corrected by hand afterwards.

**Prose matches nearby prose far more reliably than it satisfies an adjective.** Two files
is enough. Read them for register, sentence length, how much hedging the bundle tolerates,
and whether it addresses a reader at all.

> One trap worth naming: if this session has already written several concepts, do not use
> those as the reference. A style drawn from your own recent output is internally consistent
> and can be collectively off-register, with nothing to catch it. Read pages that predate
> the session.

## Also: what the bundle's own hooks enforce

A bundle that is a git repository usually has a `.pre-commit-config.yaml`, and the rules in
it are as real as the floor - they will reject the commit. They commonly cover things the
format says nothing about: forbidden characters, heading structure, link checking, filename
casing.

Glance at it before writing a batch. Discovering at commit time that every file needs its
first heading removed is a re-run of the whole job.

## Frontmatter beyond the floor

The floor is the minimum. [The concept template](concept-template.md) has the full palette
and [the specification](SPEC.md) has the detail.

**Fill what is true and omit the rest.** A field written blank or null is worse than an
absent one: absence is meaningful in this format, and a validator will reject the empty
version of something it would have accepted missing.

### Who did the writing

Two fields carry identity, and both are easy to get subtly wrong.

`generated.by` names **the harness and the model**, as `<harness>/<model>`:

| Situation | Write | Not |
| --- | --- | --- |
| An agent in opencode wrote it | `opencode/claude-opus-5` | `fkb`, `opencode`, `claude`, an agent's persona name |
| An agent in Codex wrote it | `codex/gpt-5.6-sol` | `codex/codex` |
| A person wrote or reviewed it | `human:felix_schindler` | `human:felix`, `human:ftschindler`, `Human:…`, `human/…` |
| A scheduled job refreshed it | `process:wiki-nightly` | `process/wiki-nightly` |

**`fkb` is never the actor.** This skill is prose you are reading; you are what acts.
Recording the skill would write the same string regardless of which model produced the
content, which is the one thing the field exists to capture.

**A person's id is their name, not a forge handle.** A handle belongs to one forge and one
tenant - the same person has a different login at work - so it identifies an account rather
than a human. The name form also matches the filename of that person's own concept, so the
actor resolves inside the bundle by grep, with no forge involved.

### `verified` is not yours to write

Its absence is how the format records that nothing has confirmed the content, which is the
truth at the moment you write it. A person adds it when they have checked it.

**If someone instructs you to write it anyway**, that is their call to make and not a rule
to enforce over them. Write what they asked, and say plainly in your reply that the
attestation has not happened yet, naming who it claims and what would make it true. Two
specific things are worth telling them, because both are easy to miss:

- A timestamp written before the confirming act states a time the act did not happen at. If
  the confirmation is expected later - as a review approval, say - the `at` value is fiction
  until then.
- Nothing revalidates the field afterwards. A concept whose body changes keeps whatever
  `verified` block it had, so it degrades into decoration silently.

Neither is a reason to refuse. They are reasons to say it out loud once.

## Naming, tagging, placing

**Filenames** are lowercase with underscores unless the bundle plainly does otherwise. The
filename should track the `title` closely enough that someone who remembers the title can
find the file.

**Tags come from what the bundle already uses.** Ask it:

```text
uv run SKILLDIR/scripts/fkb resolve <bundle>
```

That reports every tag in use with the number of concepts carrying it. Prefer an existing
tag that is close enough over a new one that is exact: a tag used once retrieves one page,
and a second spelling of an existing subject is a silent retrieval failure, because searching
either spelling returns half the pages and gives no hint the other half exists.

If nothing fits, propose one or two and ask, or file without tags and say so. Do not invent
a tag silently.

**Directories** follow what is there. If one fits, use it. If several could, take the most
specific and say which you chose. If none fits, ask rather than creating a directory for a
single page.

## Where a concept is not the right shape

**A bundle holds concepts and nothing else.** Every non-reserved markdown file in it is a
concept, by the format's own rule, and will be checked as one. There is no sanctioned place
inside a bundle for a scratch file, a to-do list, or a draft that is not meant to be a page
yet - putting one there produces a handful of errors that are correct and pointless.

Put working notes outside the bundle root: beside it in the repository, or somewhere else
entirely.

**Knowledge that does not exist yet is a stub, not a dangling link.** A stub is a real file
carrying the floor and a one-line description of what it will contain, with
`status: draft`. The link resolves, the gap shows up in the index and in a search for
drafts, and what would have been an error becomes a first-class state. It costs six lines.
