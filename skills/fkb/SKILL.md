---
name: fkb
description: File durable knowledge into privacy-tiered markdown bundles (the wiki, my notes, the team wiki). Use when something worth keeping is learned - a decision made, a principle extracted, a fix that cost time, a source worth remembering - or when asked to note something down, write it up, or add it to the knowledge base.
---

# Filing knowledge into a bundle

A bundle is an ordinary directory of markdown concepts, one idea per file, in the Open
Knowledge Format ([the spec](references/SPEC.md)). Several bundles sit side by side at
different privacy tiers. You write the file that a person then reads and edits: there is no
ingest step and no generated copy.

**This skill currently covers filing only.** Reading is `rg` and the ordinary file tools.
There is no search command and no audit workflow yet, on purpose.

## Commands

Paths are relative to this skill's own directory, not to the working directory you happen
to be in. Run them from here.

```bash
uv run scripts/fkb list          # which bundles exist, and what each allows
uv run scripts/fkb lint [name]   # check a bundle, or all of them
```

If `list` reports no manifest, say so and stop. Do not create one, do not guess a path, and
do not write a concept into a directory you found by looking around.

## File it

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

   Run `uv run scripts/fkb list` to see what exists and what each allows. Then:

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

4. **Where in the bundle?** Read the bundle's own `index.md` and its directory names first,
   and follow what is already there. A bundle's structure is its own; this skill does not
   impose one. If nothing fits, put the file at the bundle root rather than inventing a
   directory for a single page.

   Filenames are lowercase with underscores unless the bundle plainly does otherwise.

5. **Write the file** with the ordinary write tool.

   **The bundle decides what a concept must carry.** Read `okf-floor.yaml` at the bundle
   root and satisfy every field it lists. Do not carry a list of required fields in your
   head, and do not copy one from another bundle: the floor file is the only statement of
   what is required, and a second one would be free to drift from it.

   For everything beyond the floor, see [the concept template](references/concept-template.md)
   for the palette and [the specification](references/SPEC.md) for the detail. Fill what is
   true and omit the rest rather than writing a field blank.

   Two rules about who did the writing, both easy to get subtly wrong:
   - `generated.by` names the harness and the model that produced the content, as
     `<harness>/<model>` - `opencode/claude-opus-5`, `codex/gpt-5.6-sol`. It is never
     `fkb`: this skill is prose you are reading, and you are what acts. A person is
     `human:<their_name>`, not a forge handle.
   - **Never write `verified:` about your own work.** Its absence is how the format records
     that nothing has confirmed the content, which is the truth at the moment you write it.
     A person adds it when they have checked it.

6. **Link it and log it.** Add an entry to the nearest `index.md`, written in the bundle's
   own voice: say what the page is for rather than copying its `description`. Then append a
   line to `log.md` under today's date. A concept no index points at is one nobody finds.

7. **Lint it.** Run `uv run scripts/fkb lint <bundle>` and fix what it calls an ERROR.
   Warnings are the format's guidance and do not have to be silenced.

8. **Leave the commit to the person**, unless they asked for it. The bundle is a git
   repository with its own hooks, and those hooks are the real gate.

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

One line per incident, dated, so the file greps:

```markdown
- **2026-09-08** search - asked "do we pin actions by SHA"; web-searched; bundle had
  `principles/pin_github_actions_to_full_commit_shas.md`. Read the whole index to find it.
- **2026-09-08** tags - filed `ci` where the bundle uses `ci-cd`; noticed only at lint.
```

**Do not write an entry because none has been written for a while.** Nothing happening is a
finding too, and a plausible invented incident destroys the only evidence this file exists
to collect.
