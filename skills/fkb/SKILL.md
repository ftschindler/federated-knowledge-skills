---
name: fkb
description: Read from and write to privacy-tiered markdown knowledge bundles (the wiki, my notes, the team wiki). Use when something worth keeping is learned - a decision made, a principle extracted, a fix that cost time - or when asked to note something down, write it up, or add it to the knowledge base. Use also before searching the web, to check whether the bundles already answer the question, and when setting up a knowledge base for the first time, auditing one, or linking between them.
---

# Working with knowledge bundles

A bundle is an ordinary directory of markdown concepts, one idea per file, in the Open
Knowledge Format ([the spec](references/SPEC.md)). Several bundles sit side by side at
different privacy tiers. You write the file that a person then reads and edits: there is no
ingest step and no generated copy.

## Commands

`SKILLDIR` below is this skill's own directory, the one holding this file. Substitute its
path. The commands work from whatever directory you are already in, so do not change
directory first and do not chain two commands together: how that is written differs between
shells, and the one you are running in is not knowable from here.

```text
uv run SKILLDIR/scripts/fkb list                      # which bundles exist, and what each allows
uv run SKILLDIR/scripts/fkb lint [name]               # check a bundle, or all of them
uv run SKILLDIR/scripts/fkb resolve <name>            # one bundle as JSON: policy, tags, types
uv run SKILLDIR/scripts/fkb url <name> <path> --from <name>   # cite a concept in another bundle
uv run SKILLDIR/scripts/fkb init --workspace-root <dir>       # create the workspace, once per machine
uv run SKILLDIR/scripts/fkb add <name> ...            # bring a bundle in: --clone, --path or --new
```

There is no search command yet. Reading is step 2 below.

## Which way in

- **`fkb list` says there is no workspace manifest** - nothing is set up. Go to *Setting up*.
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
2. **Ask where the bundles should live.** Two answers people pick, for different reasons: a
   `knowledge` directory in their home if they mean to open the files themselves, or one
   under their agent directory if they would rather keep home tidy. Then run `fkb init`
   with `--workspace-root` set to that path, **written out in full** - a leading `~` is a
   shell feature and not every shell has it.
3. **Add the two public bundles**, read-only. `stjbrown/agent-knowledge` is about the idea
   itself; `ftschindler/knowledge` is knowledge management and engineering practice. The
   exact commands, with their `publish` values, are in the walkthrough.
4. **Offer a bundle of their own**: `fkb add notes --new --writable`. It is sealed by
   default, which is right for anything private. If they want one that publishes, or one
   carrying the hooks and conventions a bundle lives with rather than the bare minimum,
   [bundle infrastructure](references/bundle-infrastructure.md) is the shape and points at a
   working example already on disk.
5. **Show them `fkb list`** and file something small, so the first concept exists.

**If they asked you to set it up, set it up.** "Get me started", "set this up", "I have
nothing configured" - that is the decision already made, and coming back with a question
about directory layout spends their turn on the least interesting thing here. Use a
`knowledge` directory in their home, tell them in one line that you did and that one under
the agent directory is the other common answer, and carry on to the end. They can move it later; it is one line of a file.

**Ask only when the setup was not what they asked for** - when they wanted something filed or
answered and the missing workspace is in the way. Then the question is worth their turn,
because you are about to create something they never mentioned.

Either way, `writable` and `referenceable_by` on a bundle of their own are worth one
sentence: a bundle is sealed unless they say otherwise, and sealed is right for anything
private.

Two things this does *not* do. It never guesses that some directory it found is a bundle: a
bundle is registered because someone said so. And it never commits: the bundle is a git
repository with its own hooks, and those hooks are the real gate.

### While you are there: the AGENTS.md block

Without a line in the user's session instructions, nothing will make a future session reach
for the bundles at all. Check whether it is present and offer it if not:
[the block and how to check](references/agents-block.md). Propose it, do not write it - that
file loads into every session they run.

## Answering from the bundles

Before searching the web, check what is already known. The bundles are the cheaper source and
the one that carries this person's own decisions.

1. **`fkb list`** for the bundles and their paths.
2. **Search the concept files.** Use `rg` if it is available; if it is not, use your own
   file-reading and glob tools over the same paths - a bundle is markdown in a directory and
   needs nothing special to read. Search titles, `description` and body together; the useful
   hit is often in a description.
3. **Read the bundle's `index.md`** when a keyword search comes up empty. An index is
   written by a person and names things a grep cannot match - a page about "supersession"
   may never contain the word you searched.
4. **Name the file you read.** Every answer that came from a bundle ends with the bundle
   and the concept's path, like `(notes: principles/pin_actions_by_sha.md)`. This is not a
   flourish and it is not optional: an answer with no path cannot be checked, corrected or
   followed up, and the person cannot tell their own knowledge base from something you
   recalled. Repeating the concept's content back without naming it is the failure mode
   here, and it reads perfectly well, which is what makes it worth a rule.

   If the bundle publishes and a link would help, `fkb url` turns that path into one.
5. **If the bundles do not answer it**, say so, then go to the web. Do not pretend the gap
   is not there: what is missing is worth filing afterwards.

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
     - If none matches, tell them what *is* available and ask again.
   - **Otherwise choose by sensitivity**:
     - Write only where `writable` is `true`.
     - `referenceable_by "*"` means any bundle may cite it, so treat it as published.
     - `referenceable_by []` means it is sealed: nothing may cite it, so nothing in it can
       surface through a link from somewhere that publishes.
     - **In doubt, take the most private bundle you may write to.** Moving a concept later
       costs one commit; disclosing it costs whatever it disclosed.

   [More on tiers and the reference rule](references/federation.md).

4. **Where in the bundle?**

   Look at the top-level directories and pick the one that fits. If several could, take the
   most specific. If none fits, **put it at the bundle root** and say that is what you did;
   do not invent a directory for a single page, and do not stop to ask. A bundle with no
   directories yet is the ordinary case for a first note, not an ambiguity.

   > **Filing does not pause to confirm a default it already holds.** Stating the answer and
   > then asking for it anyway - "I'd default to root for a single note; where should it
   > go?" - ends the turn in a session that has no one to reply, and the note does not get
   > written. Say what you chose, in one clause, and keep going. Ask only about things that
   > are genuinely the person's to decide: which bundle, and how private it is.

   Then **read the target directory's own `index.md`** if it has one. That is where a bundle
   defines what the category is and how its pages are written, and it names the neighbours
   worth reading. The bundle's top-level index is a poor substitute: it costs a whole pass
   and still will not tell you what a Finding is in this bundle.

5. **Read before you write.** [House style](references/house-style.md) is the procedure, and
   it is four things: the bundle's floor, the conventions it points at, the directory index
   from step 4, and **two existing concepts from that directory**. The first three give you
   the bundle's schema and none of its voice.

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

7. **Link it and log it.** Add an entry to the nearest `index.md`, written in the bundle's
   own voice: say what the page is for rather than copying its `description`. Then append a
   line to `log.md` under today's date, matching the order the file already runs in.

   Log entries are **prose and carry no links**: the log is append-only and its subjects get
   renamed and moved, so a link there rots and cannot be repaired without rewriting history.
   A concept no index points at is one nobody finds.

8. **Lint it.** Run `fkb lint <bundle>` and fix what it calls an ERROR. Warnings are the
   format's guidance and do not have to be silenced.

9. **Leave the commit to the person**, unless they asked for it.

## The journal

While this skill is being developed, `JOURNAL.md` sits beside it. **If it is not there, the
journal is not running on this machine: skip this section entirely.**

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
