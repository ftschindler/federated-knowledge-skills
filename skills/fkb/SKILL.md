---
name: fkb
description: Read from and write to privacy-tiered markdown knowledge bundles (the wiki, my notes, the team wiki). Use when something worth keeping is learned - a decision made, a principle extracted, a fix that cost time - or when asked to note something down, write it up, or add it to the knowledge base. Use also before searching the web, to check whether the bundles already answer the question, and when setting up a knowledge base for the first time, auditing one, or linking between them.
---

# Working with knowledge bundles

A bundle is an ordinary directory of markdown concepts, one idea per file, in the Open
Knowledge Format ([the spec](references/SPEC.md)). Several bundles sit side by side at
different privacy tiers. You write the file that a person then reads and edits.

## Commands

`SKILLDIR` below is the directory this file sits in - the path you read it from, which you
already have. Substitute it. The commands work from whatever directory you are already in, so
do not change directory first and do not chain two commands together: how that is written
differs between shells, and the one you are running in is not knowable from here.

```text
uv run SKILLDIR/scripts/fkb list                      # which bundles exist, and what each allows
uv run SKILLDIR/scripts/fkb lint [name]               # check a bundle, or all of them
uv run SKILLDIR/scripts/fkb resolve <name>            # one bundle as JSON: policy, tags, types
uv run SKILLDIR/scripts/fkb url <name> <path> --from <name>   # cite a concept in another bundle
uv run SKILLDIR/scripts/fkb sync [name]               # carry a shared bundle's commits, or refuse
uv run SKILLDIR/scripts/fkb init --workspace-root <dir>       # create the workspace, once per machine
uv run SKILLDIR/scripts/fkb add <name> ...            # bring a bundle in: --clone, --path or --new
uv run SKILLDIR/scripts/fkb version                   # this release, and the one this setup stands at
uv run SKILLDIR/scripts/fkb migrate [--done]          # what an upgrade asks of this setup
```

There is no search command yet. Reading is step 2 of
[answering from the bundles](#answering-from-the-bundles).

## Which way in

- **`fkb list` says there is no workspace manifest** - nothing is set up. Go to *Setting up*.
- **`fkb list` opens with a notice about versions** - this skill has been upgraded past the
  setup on this machine. Go to *Migrating*, then carry on with what was asked.
- **A question that the bundles might answer** - go to *Answering from the bundles*.
- **Something worth keeping** - go to *Filing*.
- **Asked to audit, review or tidy a bundle** - run `fkb lint` first, then work through
  [the semantic lint checklist](references/semantic-lint.md).

## Setting up

Nothing is configured, and the person may not know what this is. Do the work; explain as you
go, briefly, rather than delivering a lecture first.

[The full walkthrough is in getting-started](references/getting-started.md). The short form:

1. **Say what a bundle is** in two sentences. A directory of markdown files, one idea per
   file, that you and your agents both read and write. No database, no import step.
2. **Decide where the bundles should live, and say what you decided.** Run
   `fkb init --propose-roots`: it prints the roots that make sense on this machine and says
   what each is for, and writes nothing. Do not write a path of your own - which ones are
   sensible depends on the operating system, and that command is where that is known. **Take
   the one it recommends**, which keeps the bundles out of their home directory, unless they
   have said they mean to open and edit the files themselves. Then run `fkb init` with
   `--workspace-root` set to it.

   "Get me started", "set this up", "I have nothing configured" - that is the decision
   already made, and coming back with a question about directory layout spends their turn on
   the least interesting thing here. They can move it later; it is one line of a file.

   **Ask only when the setup was not what they asked for** - when they wanted something
   filed or answered and the missing workspace is in the way. Then the question is worth
   their turn, because you are about to create something they never mentioned.

3. **Add the two public bundles**, read-only, named for their owners:
   `stjbrown/agent-knowledge` is about the idea itself, `ftschindler/knowledge` is knowledge
   management and engineering practice. The exact commands, with their `publish` values, are
   in the walkthrough.
4. **Create their private bundle**: `fkb add private --new --writable`. Not a question -
   everybody needs somewhere for their own notes, and sealed is the right setting for that
   permanently. The name is what makes "note this in the private wiki" route without
   guessing.
5. **Ask whether they also want one to share.** This is the one decision in setup that nobody
   can make for them, and the reason to ask is that the answers cost different amounts. A
   shared bundle is the same directory with a remote other people can clone. A *published*
   one is that plus a site generator, its navigation and a CI gate - a project rather than a
   command, and not something to start because they said the word "public". The three shapes
   are in [the walkthrough](references/getting-started.md), and what the published one
   involves is in [bundle infrastructure](references/bundle-infrastructure.md).

   A bundle on a forge is already readable and already citable, with `publish` pointed at the
   blob URL and `--publish-style raw`. Say that before offering to build anything.
6. **Give each new bundle its gate, then commit it.** `add` has made it a git repository and
   written nothing else. Pin its pre-commit hooks - **look the revision up now rather than
   copying one from anywhere**, including from this skill; the command and the config are in
   [bundle infrastructure](references/bundle-infrastructure.md). Then install the hook and
   make the first commit. A bundle with no hooks is one nothing checks, and one of these is
   where they will keep their private notes.
7. **Show them `fkb list`, then hand over.** Three lines on what happens from here: ask a
   question and the bundles get checked before the web; say something is worth keeping and it
   gets filed; the two public bundles are worth reading a few concepts from to see what a
   good one looks like.

   **Do not invent a first concept to prove it works.** The bundle is empty because they have
   not told you anything yet, which is the correct state and not a gap to fill. A
   demonstration note is a real file that someone has to notice and delete later, and it
   teaches the bundle's first reader that this is where filler goes. If they want to watch
   filing happen, ask what they want kept - that is a real note, and they have one.

`writable` and `referenceable_by` are worth one sentence when a bundle of theirs is created: a
bundle is sealed unless they say otherwise, and sealed is right for anything private.

One thing this does *not* do: it never guesses that some directory it found is a bundle. A
bundle is registered because someone said so.

### While you are there: the AGENTS.md block

Without a line in the user's session instructions, nothing will make a future session reach
for the bundles at all. Check whether it is present and offer it if not:
[the block and how to check](references/agents-block.md). Propose it, do not write it - that
file loads into every session they run.

## Migrating

The skill is installed by copying, so an upgrade arrives without announcement and nothing on
the machine notices. `fkb list` notices, by comparing this copy's release against the one
recorded in the manifest, and says so when a change since then asks something of this setup.

1. **`fkb migrate`** names the guides that apply, oldest first. Read them in that order.
2. **Do what each says**, and put its decisions to the person rather than taking them. These
   are mostly new capabilities, not breakages - "there is now a way to share a bundle with
   your team; do you want that here" is the shape of it, and no is a complete answer.
3. **`fkb migrate --done`** once the last one is worked through. A change they declined is
   still migrated: the question was asked, and leaving it unrecorded asks it again next week.

Do it when the notice appears, before the work it interrupted, unless they are mid-question -
then answer them first and come back to it. Never edit the manifest's `version` by hand, and
never stamp guides you have not read: the field's only job is to be trustworthy about what
has been put to this person.

If they say to leave it, leave it. The notice returns, nothing breaks, and that is the
design - a version stamp is bookkeeping about capabilities, not a lock on the bundles.

## Answering from the bundles

Before searching the web, check what is already known. The bundles are the cheaper source and
the one that carries this person's own decisions.

1. **`fkb list`** for the bundles and their paths.

   If any bundle shows a `sync` branch, somebody else files into it too. Run
   `uv run SKILLDIR/scripts/fkb sync <that bundle>` before reading it, which is what stops you
   answering from a page a teammate corrected this morning. If it refuses, read the bundle anyway and repeat the
   refusal in your answer, so the person knows what they are reading may be behind.

   If they named a source and nothing is called that - "what does Felix say about this", with
   no `felix` in the list - take the bundle that is plainly meant and say which you took.
   Then offer the mapping a line in
   [the AGENTS.md block](references/agents-block.md), so the next session does not have to
   work it out again. A name that has to be re-derived every time is one that will eventually
   be derived wrongly.
2. **Search the concept files.** Use `rg` if it is available; if it is not, use your own
   file-reading and glob tools over the same paths - a bundle is markdown in a directory and
   needs nothing special to read. Search titles, `description` and body together; the useful
   hit is often in a description.
3. **Read the bundle's `index.md`** when a keyword search comes up empty. An index is
   written by a person and names things a grep cannot match - a page about "supersession"
   may never contain the word you searched.
4. **Name the file you read.** Every answer that came from a bundle ends with the bundle
   and the concept's path, like `(private: principles/pin_actions_by_sha.md)`. This is not a
   flourish and it is not optional: an answer with no path cannot be checked, corrected or
   followed up, and the person cannot tell their own knowledge base from something you
   recalled. Repeating the concept's content back without naming it is the failure mode
   here, and it reads perfectly well, which is what makes it worth a rule.

   If the bundle publishes and a link would help, `fkb url` turns that path into one.
5. **If the bundles do not answer it**, say so, then go to the web - and then file what you
   found. A question someone actually asked, that the bundles could not answer, is the
   strongest evidence there is that the answer belongs in one, and it will be asked again.
   Go to *Filing*; do not stop to ask whether it is worth keeping. **This is the step that
   makes the bundles worth having** - a knowledge base only grows where it was used and
   found wanting, and this is the only moment you know exactly where that was.

> **When you searched the bundles, found nothing, and the web had it** - that is worth a
> journal line. It is the evidence that decides whether a real search command gets built.

## Filing

1. **What am I holding?**
   - An *external artifact* - a page, a paper, a repository, a document. Continue at 2.
   - An *insight from this session* - a decision made, a principle extracted, a fix that
     cost time. **There is no raw source. Write the concept directly and skip to 3.**

   > The second branch is the one that gets mishandled. Do not invent a source, do not
   > archive the conversation, do not go looking for a URL that would justify the note.

2. **Is the artifact perishable?** A stable public URL archives nothing: record it as
   `resource:`. A perishable or access-gated source gets archived beside the bundle and
   recorded under `sources:`.

3. **Which bundle?**

   Run `fkb list` to see what exists and what each allows. Then:

   - **If the user named one** ("public wiki", "the private bundle"):
     - If exactly one bundle matches that name, use it.
     - If more than one could match, ask which they meant rather than guessing.
     - If none matches, say what *is* there and ask which they meant. This question earns
       the turn: they gave an explicit instruction and it cannot be carried out, and writing
       past that is how a note lands somewhere they did not choose.

       Then offer to stop it recurring, because the same phrase will come back next session.
       Either the manifest name is wrong for what they call it, which is a one-line edit, or
       the phrase is simply theirs and belongs in
       [the AGENTS.md block](references/agents-block.md), where one line maps it to a bundle
       for every future session. Propose it; that file is theirs to edit.
   - **Otherwise choose by sensitivity**:
     - Write only where `writable` is `true`.
     - `referenceable_by "*"` means any bundle may cite it, so treat it as published.
     - `referenceable_by []` means it is sealed: nothing may cite it, so nothing in it can
       surface through a link from somewhere that publishes.
     - **In doubt, take the most private bundle you may write to.** Moving a concept later
       costs one commit; disclosing it costs whatever it disclosed.

   [More on tiers and the reference rule](references/federation.md).

4. **Where in the bundle?**

   **Start at the bundle's own `index.md`.** A bundle that has grown directories usually says
   there what each one is for, and that is the answer to this question. Picking from
   directory names alone is guessing at a taxonomy someone already wrote down, and the names
   are the part most likely to mislead: two of them look interchangeable until the index says
   what separates them.

   Then take the directory that fits. If several could, take the most specific. If none fits,
   **put it at the bundle root** and say that is what you did; do not invent a directory for
   a single page, and do not stop to ask. A bundle with no directories yet is the ordinary
   case for a first note, not an ambiguity.

   > **Filing does not pause to confirm a default it already holds.** Stating the answer and
   > then asking for it anyway - "I'd default to root for a single note; where should it
   > go?" - ends the turn in a session that has no one to reply, and the note does not get
   > written. Say what you chose, in one clause, and keep going. Ask only about things that
   > are genuinely the person's to decide: which bundle, and how private it is.

   Then **read that directory's own index**, if it has one. The two indexes answer different
   questions and neither substitutes for the other: the bundle's says *which* directory, the
   directory's says what the category is, how its pages are written, and which neighbours are
   worth reading. A note going to the root has only one index, which has already done both.

   If what you read says the category is not what you took it for, **move the note now**. It
   is one path, changed before anything points at it.

5. **Read before you write.** [House style](references/house-style.md) is the procedure, and
   it is four things: the bundle's floor, the conventions it points at, the indexes from
   step 4, and **two existing concepts from that directory**. The first three give you
   the bundle's schema, but none of its voice which the latter carries.

   Skipping the last one is the most common way a concept comes out wrong in a way lint
   cannot see.

6. **Write the file** with the ordinary write tool.

   **The bundle decides what a concept must carry.** Read `fkb.yaml` at the bundle root and
   satisfy every field its `required:` list names. Do not carry a list of required fields in
   your head, and do not copy one from another bundle: that file is the only statement of
   what is required, and a second one would be free to drift. A bundle with no `fkb.yaml`
   requires nothing beyond the format itself.

   For everything beyond the floor, see [the concept template](references/concept-template.md)
   and [the specification](references/SPEC.md). Fill what is true and omit the rest rather
   than writing a field blank.

   Two rules about who did the writing, both easy to get subtly wrong:
   - `generated.by` names the harness and the model that produced the content, as
     `<harness>/<model>` - `opencode/claude-opus-5`, `codex/gpt-5.6-sol`. It is never `fkb`:
     this skill is prose you are reading, and you are what acts. A person is
     `human:<their_name>`, not a forge handle.
   - **Never write `verified:` about your own work.** Its absence is how the format records
     that nothing has confirmed the content, which is the truth at the moment you write it.
     If someone instructs you to write it anyway, do - and say in your reply that the
     attestation has not happened yet. [Why, and what to tell them](references/house-style.md).

   **Linking to another bundle?** Never write the URL yourself and never use a relative path:

   ```text
   uv run SKILLDIR/scripts/fkb url <target-bundle> <path/in/it.md> --from <this-bundle>
   ```

   It prints the URL, or refuses because the link is not allowed to exist. A refusal is an
   answer - do not route around it. Links *inside* one bundle stay ordinary relative markdown
   links.

7. **Connect it, then link it and log it.**

   **Connect it.** A concept that links to nothing is in the bundle without being part of it,
   and the whole value of one idea per file is what the files say about each other. Link out
   to the concepts you read in step 5 where they are genuinely related - you have already
   read them, so this costs nothing. **Only link to pages you have actually opened**: a
   plausible path to a page that does not exist is the one kind of link nobody notices is
   wrong.

   Inbound links are the other direction and want a lighter hand, because they edit pages
   this session did not write. Add one where the new concept makes an existing page
   incomplete - it answers a question that page leaves open, or supersedes part of it - and
   stop there. Say which pages you touched. Anything broader is an audit, not a filing, and
   belongs in [the semantic lint pass](references/semantic-lint.md).

   **Link it.** Add an entry to the nearest `index.md`, written in the bundle's
   own voice: say what the page is for rather than copying its `description`. Then append a
   line to `log.md` under today's date, matching the order the file already runs in.

   Log entries are **prose and carry no links**: the log is append-only and its subjects get
   renamed and moved, so a link there rots and cannot be repaired without rewriting history.
   A concept no index points at is one nobody finds.

8. **Lint it.** Run `fkb lint <bundle>` and fix what it calls an ERROR. Warnings are the
   format's guidance and do not have to be silenced.

9. **Commit it, if the bundle is a git repository.** Stage only the files you wrote this
   session and commit with a message naming the concept. An uncommitted note is one the
   person has to notice and finish, and they asked you to file it, not to leave it in the
   working tree.

   - **The hooks are the check, so let them run.** Never pass `--no-verify`. If a hook
     rejects the commit, fix what it reports and commit again; that is the gate working.
   - **Do not invent an author.** If git has no `user.name` or `user.email` here, stop and
     say so rather than configuring one - a commit attributed to a guess is worse than an
     uncommitted file.
   - **Do not push a bundle whose `list` entry shows `sync null`.** Publishing is theirs, and
     a stray staged file is how something private leaves a machine. Never commit anything you
     did not write, in any bundle.
   - **A bundle that shows a `sync` branch is shared with other people**, and getting the
     concept to them is part of filing there. Run
     `uv run SKILLDIR/scripts/fkb sync <bundle>` once the commit is made. If it refuses, say
     what it said and stop - the refusal carries its own remedy, and a way around it is not
     yours to find.
   - A bundle that is not a repository is left as written. Say so in one line.

## The journal

While this skill is being developed, `SKILLDIR/JOURNAL.md` sits beside it. **If it is not there,
but you encounter an incident or are asked to file one, offer to create it.**

Append one line whenever the work runs into a limit of the bundles or of this skill. Three
rules, all of which exist because an entry that breaks them is worse than no entry:

- **Record what happened, not what should exist.** "Searched the web for X; the bundle had
  it at `principles/y.md`" is evidence. "Search would be useful" is a wish.
- **Name the artifacts.** The actual query, the actual path, the actual tag you chose. An
  entry that names no file and no query did not happen, and must not be written.
- **Record what you did instead.** The workaround is the measurement. If there was none,
  say the task was abandoned.

**An artifact is a path, a query or a command. An identity is not one**, and neither is the
name or URL of a bundle that is not public. This file is committed to a public repository and
the federation it describes may contain private bundles, so an entry says what was done and
describes whose it was. Never paste `fkb list` output or the manifest into it.

One line per incident, dated, so the file greps:

```markdown
- **2026-09-08** search - asked "do we pin actions by SHA"; web-searched; bundle had
  `principles/pin_github_actions_to_full_commit_shas.md`. Read the whole index to find it.
- **2026-09-08** tags - filed `ci` where the bundle uses `ci-cd`; noticed only at lint.
```

**Do not write an entry because none has been written for a while.** Nothing happening is a
finding too, and a plausible invented incident destroys the only evidence this file exists
to collect.
