# IMPLEMENTATION - federated-knowledge-skills

**Status:** the plan of record. [DESIGN.md](DESIGN.md) remains the sole source of truth for
*what* gets built; this document says *in which order* and *when* each open question is
answered. It was §10 of that document until it grew large enough to stand on its own.

**Section references.** A `§N` link points at the matching section of [DESIGN.md](DESIGN.md);
`OKF §N` refers to the Open Knowledge Format spec.

This is the implementation plan. It assumes nothing from this repository except
[DESIGN.md](DESIGN.md) and this file - a fresh session should be able to start here.

## Status

- [x] **[T1](#t1---prepare-the-bundle-empty)** - Prepare the bundle, empty
- [x] **[T2](#t2---minimum-capture-and-a-friction-journal)** - Minimum capture, and a friction journal
- [x] **[T3](#t3---migrate-the-60-public-concepts)** - Migrate the ~60 public concepts
- [x] **[T4](#t4---finish-the-cli)** - Finish the CLI
- [x] **[T5](#t5---finish-the-skill)** - Finish the skill
- [x] **[T6](#t6---ship-the-standalone-pre-commit-hook)** - Ship the standalone pre-commit hook, *built early, verified in T4*
- [ ] **[T7](#t7---second-bundle-then-retire-the-old-architecture)** - Second bundle, then retire the old architecture
- [ ] **[T8](#t8---iterate-on-the-cli-and-the-skill)** - Iterate on the CLI and the skill, *open-ended, keeps discovering*
- [ ] **[T9](#t9---share-one-bundle-between-several-people)** - Share one bundle between several people

## How to use it

**Answer an open question only when a task forces it.** Deciding early trades away the
information the work itself produces. Every task below therefore names two things: which
questions it must settle, and which it must leave alone even when the answer feels obvious.
Leaving one alone is not procrastination; it is refusing to guess when the next task will know.

Tasks run in order, and each states what "done" means in terms someone else could check.
The order is a default rather than a rule: [T6](#t6---ship-the-standalone-pre-commit-hook)
was built during [T1](#t1---prepare-the-bundle-empty), because content started arriving
before anything checked it.

## Before starting

A fresh session needs four things, none of which live in this repository.

| What | Where | Why |
| --- | --- | --- |
| The OKF v0.2 spec | `GoogleCloudPlatform/open-knowledge-format` | Vendored verbatim ([§8](DESIGN.md#8-vendoring-from-okf-skills)) |
| `okf-skills` at a pinned commit | `scaccogatto/okf-skills` | Source of the validator, template and spec copy ([§8](DESIGN.md#8-vendoring-from-okf-skills)) |
| The publishing template | `~/Projects/public/running-linux` | MkDocs, prek, CI, Pages - reused, not rebuilt |
| The existing content | `~/.agents/wikis/{public,private}/docs` | ~60 concepts, and a `raw/` tree of shadows the migration deletes |

Everything else - the manifest schema ([§4](DESIGN.md#4-bundles-and-the-manifest)), the
AGENTS.md block ([§5.4](DESIGN.md#54-the-schema)), the skill layout
([§6.2](DESIGN.md#62-layout)), the command set ([§7](DESIGN.md#7-the-cli)) - is specified in
[DESIGN.md](DESIGN.md).

One thing this repository *does* provide: `tests/disposable_agent.py` builds a throwaway
agent (a pinned opencode in a redirected HOME) that you install skills into, send a message
to, and read a parsed transcript back from. It survived the previous architecture because it
is independent of what it drives. Use it for
[T2](#t2---minimum-capture-and-a-friction-journal)'s skill tests rather than rebuilding it;
`tests/test_disposable_agent.py` shows the shape.

## T1 - Prepare the bundle, empty

**Done.** `ftschindler/knowledge`, published at
<https://ftschindler.github.io/knowledge>. `okf_validate.py --strict` and
`mkdocs build --strict` both pass, and the site is live.

What it settled, and where the shape came from:

- The bundle root is `docs/`, which is also the MkDocs `docs_dir`, so concepts sit at
  top-level URLs. Pages describing the site live in `about/` and raw sources will live in
  `raw/`, both siblings at the repository root. A build hook publishes `about/` and moves
  the bundle index off the site root.
- The bundle declaration is `docs/fkb.yaml`, a flat `required:` list of five fields, plus
  the optional `conventions:` pointer at the bundle's house rules (DESIGN §9.2).
- The whole running-linux stack was taken, Obsidian vault config included, so the bundle is
  editable by a person in an editor, in Obsidian or on GitHub as readily as by an agent.

Two departures from the plan below, both deliberate. The bundle holds one hand-written
concept rather than three or four, because real content started arriving before the proof
was needed. And [§9.5](DESIGN.md#95-how-a-bundle-lints-standalone) was settled here rather
than left alone: content was landing with nothing checking it, which is the case that
section was written for.

Three fixes went into infrastructure copied from running-linux, each a latent fault there
too: `check_mailmap.py` crashed on a repository with no commits, `copilot-instructions.md`
pointed at pages that do not exist here, and two governance steps assumed a pull request
payload.

**Goal.** A conformant, publishing bundle that is ready to be written into, before any content
is migrated. Hours, not days - [T2](#t2---minimum-capture-and-a-friction-journal) is blocked on
this and nothing else.

**Deliverable.** A git repo from the running-linux template, with the directory layout fixed,
the floor declaration written, publishing working, and a handful of concepts in it as proof.

**Steps.**

- Copy the template: MkDocs, prek, CI, Pages.
- Fix the top-level directory layout, and decide how the `meta/` pages satisfy OKF §11
  ([§9.4](DESIGN.md#94-non-knowledge-pages-sit-outside-the-bundle-root)). Both are forced now, because
  everything written afterwards assumes them.
- Decide where markdown raw sources live
  ([§9.3](DESIGN.md#93-markdown-raw-sources-live-beside-the-bundle-not-inside-it)).
  Deciding does not mean moving anything yet.
- Write the floor declaration file
  ([§9.2](DESIGN.md#92-where-a-bundle-declares-its-floor---fkbyaml-at-the-bundle-root)).
  Nothing reads it until [T4](#t4---finish-the-cli).
- Write `index.md`, `log.md`, and three or four real concepts by hand.

**Done when.** `okf_validate.py --strict` passes, `mkdocs build --strict` passes, and the site
is live.

**Settles.**
[§9.2](DESIGN.md#92-where-a-bundle-declares-its-floor---fkbyaml-at-the-bundle-root),
[§9.3](DESIGN.md#93-markdown-raw-sources-live-beside-the-bundle-not-inside-it),
[§9.4](DESIGN.md#94-non-knowledge-pages-sit-outside-the-bundle-root), and
[§9.6](DESIGN.md#96-how-knowledge-is-structured-inside-a-bundle) for this bundle.

**Leave alone.** [§9.1](DESIGN.md#91-ranking-once-rg-stops-being-enough),
[§9.5](DESIGN.md#95-how-a-bundle-lints-standalone),
[§9.7](DESIGN.md#97-what-we-may-assume-is-installed). Migrate no bulk content - that is
[T3](#t3---migrate-the-60-public-concepts).

## T2 - Minimum capture, and a friction journal

**Goal.** Agent sessions file knowledge from today, while still producing honest evidence about
which commands are worth building.

**The bargain.** Building before observing risks the journal recording friction with the
tooling rather than with the task. That risk attaches to the commands, not to the instructions,
so this task builds every part whose necessity is not in question and deliberately withholds
the rest.

| Build now | Withhold |
| --- | --- |
| The skill, scoped to *filing* ([§6.3](DESIGN.md#63-filing-knowledge---the-decision-tree), [§6.4](DESIGN.md#64-actors-and-trust)) | Query and audit workflows |
| `fkb list` | `fkb search` ([§9.1](DESIGN.md#91-ranking-once-rg-stops-being-enough)) |
| `fkb lint`, conformance and floor only | `fkb resolve`'s vocabulary reporting ([§7](DESIGN.md#7-the-cli)) |
| The AGENTS.md block ([§5.4](DESIGN.md#54-the-schema)) | Semantic lint ([§6.5](DESIGN.md#65-two-lints-one-of-them-code)) |
| Vendored spec, template, validator ([§8](DESIGN.md#8-vendoring-from-okf-skills)) | `fkb init`, `fkb add` |

Withholding `search` and `resolve` is the entire point: reaching for the web when the bundle
knew the answer, or picking a tag that fits nothing, are the observations that decide whether
those commands exist.

**Deliverable.** `~/.agents/skills/fkb/` per [§6.2](DESIGN.md#62-layout) but filing-only, the
two commands, the AGENTS.md block, and `JOURNAL.md` in this repository beside this file.

**What [T6](#t6---ship-the-standalone-pre-commit-hook) already did for this task.**
`fkb lint` is not written from scratch: `skills/fkb/scripts/bundle_lint.py` exists, checks
conformance and the declared floor, and is what the first bundle already runs on every
commit. `fkb lint` becomes its second entry point, adding what needs the manifest. Confirm
while wiring it that both report the same finding on the same file, which is the half of
T6's "done when" that could not be checked at the time.

Two constraints on the skill body that were settled while building
[T1](#t1---prepare-the-bundle-empty), and are easy to breach without noticing:

- **The skill may not cite this design.** It ships standalone, so every rule it depends on
  is stated in it or in its `references/`, never referred to by section number.
- **The floor decides what a concept must carry**, so the skill tells an agent to satisfy
  the bundle's floor rather than carrying its own list of required fields, which would be a
  second declaration free to drift.

**The journal.** The skill instructs the agent to append to `JOURNAL.md` whenever the work runs
into a limit. Three rules keep it worth reading:

- **Record what happened, not what should be built.** "Searched the web for X; the bundle had
  it at `principles/y.md`" is evidence. "Search would be useful" is a wish, and wishes are
  free.
- **Record only concrete incidents, with the artifacts.** The actual query, the actual path,
  the actual tag chosen. An entry that names no file and no query did not happen.
- **Record what was done instead.** The workaround is the measurement. If there was no
  workaround, say the task was abandoned.

One line per incident, dated, so the file greps:

```markdown
- **2026-09-04** search — asked "do we pin actions by SHA"; web-searched; bundle had
  `principles/pin-github-actions-to-full-commit-shas.md`. Read the whole index to find it.
- **2026-09-05** tags — filed `ci` where the bundle uses `ci-cd`; noticed only at lint.
```

> Agents asked to report problems will invent plausible ones. The three rules exist to make
> a fabricated entry obviously empty: no path, no query, nothing done instead.

**Done when.** Filing works end to end from a cold session, and the journal has run for seven
days or accumulated enough entries to decide [T4](#t4---finish-the-cli) without waiting.

**Settles.** Nothing formally. It supplies the evidence for
[§9.1](DESIGN.md#91-ranking-once-rg-stops-being-enough) and for [T4](#t4---finish-the-cli)'s
scope.

**Leave alone.** Everything in the withhold column, however obvious it looks mid-week. The
whole value of this task is that the gaps stay open long enough to be measured.

## T3 - Migrate the ~60 public concepts

**Goal.** Move the existing content into the [T1](#t1---prepare-the-bundle-empty) bundle. Runs
alongside [T2](#t2---minimum-capture-and-a-friction-journal)'s observation window; capture does
not wait for it.

**Steps.**

- Copy from `~/.agents/wikis/public/docs`. The published files are canonical; the `raw/`
  shadows carry nothing extra.
- Frontmatter: add `type:`; drop `sources: [raw/…]`, `render_hash` and `topic:` (the directory
  already carries the topic, [§9.6](DESIGN.md#96-how-knowledge-is-structured-inside-a-bundle)).
  Add the rest of the floor the bundle declares, which the incoming files do not carry:
  `description`, `status` and `generated`. The bundle's own hook rejects them otherwise.
- Rename to the bundle's convention: the incoming files are hyphenated, the bundle uses
  underscores. The filename-and-title map the wikilink conversion already builds is where
  this belongs, so it costs nothing extra.
- Strip the body `# Title` from every concept. The vault repeats the frontmatter title as a
  first-level heading; here that is a second `h1` and fails `MD025` on all ~60 files.
- Convert `[[wikilinks]]` to relative markdown links using a filename-and-title map. Emit the
  unresolved ones as a list for manual review rather than guessing a target.
- Delete the `raw/` tree once the conversion validates.
- Move whatever raw sources survive into `raw/`, beside `docs/` and outside the bundle
  ([§9.3](DESIGN.md#93-markdown-raw-sources-live-beside-the-bundle-not-inside-it)). Establish
  first what the archive actually holds: the public wiki's `raw/` is 65 shadows of published
  concepts, which this task deletes, and its `sessions/` directory is empty.
- Write the index as the concepts arrive, in index voice rather than by copying each
  `description` (appendix B). Sixty entries is the point at which the section headings and
  their order start doing real work.

**Done when.** The bundle's own `okf-concepts` hook passes, `mkdocs build --strict` passes,
internal links resolve, and the unresolved-link list is empty or consciously accepted.

> The hook is the check that matters now, not `okf_validate.py` alone: it enforces the floor
> as well as conformance, and it is what a commit will run.

**Leave alone.** The conversion script is disposable and never becomes part of `fkb`.

## T4 - Finish the CLI

**Goal.** Add the commands the journal justified, and nothing else.

**Specified by DESIGN.md.** Manifest schema and resolution
([§4](DESIGN.md#4-bundles-and-the-manifest)), the reference rule
([§4](DESIGN.md#4-bundles-and-the-manifest)), `publish` and the transform it names
([§4](DESIGN.md#publish-is-how-one-bundle-links-to-another)), what `resolve` reports and what
`url` refuses ([§7](DESIGN.md#7-the-cli)), `lint`'s warning-versus-error behaviour
([§6.6](DESIGN.md#66-what-fkb-lint-does-across-bundles)).

**Steps.**

- Read `JOURNAL.md` first. A command with no entries against it does not get built.
- Migrate the manifest to `publish: {url, style}` and implement `fkb url <bundle> <path>`
  ([§4](DESIGN.md#4-bundles-and-the-manifest), [§7](DESIGN.md#7-the-cli)). The journal earned
  this twice over: `publish` was registered as a repo landing page and resolved to a 404,
  and the field is described nowhere but its own `--help` string. Settled before the work
  started, because it is a schema change three of the four commands below depend on.
- Implement the federation checks in `lint`: the reference rule, cross-bundle links, and
  demotion to warnings for non-writable bundles
  ([§6.6](DESIGN.md#66-what-fkb-lint-does-across-bundles)). Cross-bundle links means reading
  the `publish` transform backwards, so the non-prefixing constraint on the manifest is
  checked here too.
- Implement `resolve`'s vocabulary reporting ([§7](DESIGN.md#fkb-resolve-reports-what-a-bundle-does-not-only-what-it-declares)).
  The journal earned it: two spellings of one subject tag sat in the public bundle for
  weeks, invisible to the hooks, to `mkdocs build --strict` and to `fkb lint`, and were
  found only because a sentence happened to mention the tag. Report counts alongside the
  values; the tail is where a split shows, and a bare list has no tail. Detecting the split
  itself is semantic lint's job in [T5](#t5---finish-the-skill)
  ([§6.5](DESIGN.md#65-two-lints-one-of-them-code)), so what this step owes that task is an
  input it can read. Deterministic lint takes nothing from this: the singleton-tag warning
  that was specified alongside it was measured away once `resolve` could count, at 29
  singletons in the public bundle's 76 tags ([§6.5](DESIGN.md#65-two-lints-one-of-them-code)).
- Implement `fkb init` and `fkb add` with its three arrival paths ([§7](DESIGN.md#7-the-cli)).
  Until now the workspace was hand-written;
  [T7](#t7---second-bundle-then-retire-the-old-architecture) introduces a second bundle and a
  real user, so setup stops being a one-off.

**Leave alone.** `search`, which moves to [T8](#t8---iterate-on-the-cli-and-the-skill). The
observation window it was withheld for never exercised the read path: [T3](#t3---migrate-the-60-public-concepts)
ran alongside [T2](#t2---minimum-capture-and-a-friction-journal) by design, a migration is all
writes, and nothing in six days asked the bundle a question it might already have answered. So
the journal carries no entry against `search`, and the rule above would refuse it on a
technicality rather than on evidence. Withholding it costs nothing now that there is a bundle
worth querying, and it is the last command whose shape is still a guess.

Also `rename`, which the 2026-09-10 journal entry earns and which moves to
[T8](#t8---iterate-on-the-cli-and-the-skill) with it. The evidence is real, but it is a
single incident on the write path, and this task builds the commands the first window
argued for rather than every command it mentioned.

**Done when.** Every built command runs against the migrated bundle and at least one read-only
upstream, and the tests drive the installed copy rather than the source tree.

**Settles.** [§9.7](DESIGN.md#97-what-we-may-assume-is-installed) for everything built here:
the CLI is pure Python over `uv` and assumes nothing further, so a bundle and this machine
need the same one tool they already needed. The half of that section that asks about
`ripgrep` cannot be settled here, because it is a question about `search`, and moves to
[T8](#t8---iterate-on-the-cli-and-the-skill) with it.
[§9.1](DESIGN.md#91-ranking-once-rg-stops-being-enough) stays open and moves with `search`.

## T5 - Finish the skill

**Goal.** Extend the filing-only skill of [T2](#t2---minimum-capture-and-a-friction-journal)
into the full one, including onboarding.

**What [T4](#t4---finish-the-cli) changed about this task.** It was written when the CLI had
two commands and a workspace was hand-written YAML, which made onboarding a description of a
file someone had to author. There are six commands now, four of them unreachable because
nothing tells an agent they exist, and setup is something a session can carry out. So the
onboarding branch stops explaining a format and starts running commands, and
[§6.7](DESIGN.md#67-the-skill-explains-itself)'s acceptance test - a next step the person can
run, not a summary of the design - becomes something the skill can actually pass.

**Steps.**

- Add the query workflow and the semantic lint checklist
  ([§6.5](DESIGN.md#65-two-lints-one-of-them-code)). The query path may not assume `ripgrep`:
  it tries it and falls back to the agent's own read and glob tools, so the skill needs
  nothing a bundle does not already need. That constraint is the same question
  [§9.7](DESIGN.md#97-what-we-may-assume-is-installed) leaves open for `search`, met here by
  not depending on the answer.
- Add the "new here?" branch to `SKILL.md` and write `references/getting-started.md`
  ([§6.7](DESIGN.md#67-the-skill-explains-itself)). Take the three arrival paths from the
  previous `README.md` before [T7](#t7---second-bundle-then-retire-the-old-architecture) deletes
  it. **The skill carries onboarding out rather than describing it**: a person who has just
  installed it and knows nothing gets a working federation, with each step explained as it
  happens. It offers a choice of workspace root, `~/knowledge` when they mean to hand-edit
  and `~/.agents/knowledge` when they would rather not clutter `$HOME`, and recommends the
  two public bundles - `stjbrown/agent-knowledge` for what an LLM wiki is, and
  `ftschindler/knowledge` for knowledge-management and engineering practice. Registering
  those two also demonstrates both `publish` transforms, since one is a forge and one is a
  site.
- Teach the commands [T4](#t4---finish-the-cli) built. `fkb url` is the one that changes what
  an agent can do rather than how it does it: a cross-bundle link is absolute, comes from
  that command, and is never hand-written or relative.
- Check for the AGENTS.md block ([§5.4](DESIGN.md#54-the-schema)) and propose it when it is
  missing, shipping its text in `references/`. The skill does not carry a list of paths: it
  asks the agent to look in the user-level instructions file its own harness loads, which is
  a thing the agent knows and this repository cannot.
- Add `references/house-style.md` and `references/federation.md`. House style states the
  generic procedure only - read what the bundle declares, wherever it declares it, and read
  two neighbouring concepts before writing - never one bundle's rules, because the four
  bundles on the machine that produced the journal agree on almost nothing.
- Fold whatever the journal revealed about the filing instructions back into `SKILL.md`.
- Every command the skill prints has to satisfy [§9.7](DESIGN.md#97-what-we-may-assume-is-installed):
  one command per line, no `cd`, no `&&`, no `~`, no shell-tagged fence. The commands block
  grows from two entries to six here, which is six chances to reintroduce the invocation a
  user already reported; two tests in `tests/test_fkb_cli.py` fail if one does.

**Done when.** Four cold-session tests pass, each starting with no prior context:

1. Given a question, the agent finds the skill, reads a concept and cites it.
2. Given "note this down", it files a conformant concept that passes `fkb lint` uncorrected.
3. Given "what is this and how do I start?" on a machine with **no workspace configured**, it
   explains what a bundle is and leaves a workspace behind that works
   ([§6.7](DESIGN.md#67-the-skill-explains-itself)).
4. Given two bundles and a reason to cite across them, the link it writes is the absolute URL
   `fkb url` produces, not a relative path.

The third test is the one that fails quietly. A plausible summary of the design is not a pass;
a workspace the person can use is. The fourth exists because a capability nothing reaches for
is indistinguishable from one that was never built.

**Leave alone.** [§9.6](DESIGN.md#96-how-knowledge-is-structured-inside-a-bundle) - the skill
reads a bundle's style, it does not impose one. Bulk filing and deletion both move to
[T8](#t8---iterate-on-the-cli-and-the-skill): the journal has three incidents between them and
each wants a shape, not a paragraph, and this task is already the one that teaches four
commands and onboards from nothing.

## T6 - Ship the standalone pre-commit hook

**Built during [T1](#t1---prepare-the-bundle-empty), and verified in
[T4](#t4---finish-the-cli).** `skills/fkb/scripts/bundle_lint.py` ships behind two hook ids
in `.pre-commit-hooks.yaml`, and `ftschindler/knowledge` pins them by revision. Nine tests
cover it under the existing `python_scripts` marker.

Two properties are worth carrying forward, because neither is obvious from the code:

- **Only the floor decides.** Two layers may fail a run and no others: the format's hard
  rules, and the fields `fkb.yaml` declares. Everything OKF marks as recommended is
  reported and left alone, so a field the floor does not name is never enforced.
- **Blocking scope is what makes it bearable per commit.** The vendored validator accepts a
  bundle, never a file list, so the whole bundle is checked and only findings in the files
  being committed fail. An unfinished concept elsewhere never blocks an unrelated commit.
  With `--all-files` every file is in scope, so the same hook is strict in CI without a
  second configuration.

`okf-bundle` adds index coverage and nothing else, and sits on pre-commit's manual stage so
it stays off the commit path; the bundle's governance workflow invokes it by name.

**Done.** The second half of "done when" was unverifiable while `fkb lint` did not exist.
It now does, and `test_cli_and_hook_report_the_same_finding` runs both entry points over one
broken concept and compares what each says about it, so the constraint below is checked
rather than asserted. A companion test keeps the other property honest: the hook accepts a
floor declaration under any filename, because only `fkb` needs to *discover* the file.

**Goal.** A bundle enforces its own conformance and floor without `fkb` present.

**Deliverable.** This repository publishes a `pre-commit` hook that a bundle pins by revision,
wrapping the same checker `fkb lint` calls.

**Constraint.** One implementation, two entry points. If the hook and the skill's copy can
drift, the design has failed.

**Done when.** A bundle with no knowledge of the federation rejects a non-conformant commit,
and `fkb lint` reports the same finding on the same file.

**Settles.** [§9.5](DESIGN.md#95-how-a-bundle-lints-standalone).

## T7 - Second bundle, then retire the old architecture

**Goal.** Prove federation on more than one bundle, and remove what this design replaces.

**Steps.**

- Migrate the private bundle as in [T1](#t1---prepare-the-bundle-empty) and
  [T3](#t3---migrate-the-60-public-concepts).
- Populate the manifest with both bundles plus at least one read-only upstream.
- Exercise the reference rule: confirm a private-to-public link is refused and a
  public-to-public link is allowed.
- Fold the entries that decided [T4](#t4---finish-the-cli) into a decisions record. The file
  itself stays: [T8](#t8---iterate-on-the-cli-and-the-skill) runs a second window against it,
  so distil what has been spent and leave the file open rather than deleting it.
- Update `README.md` to describe what now exists rather than what is planned.

**Done when.** The repository contains the design, this plan, the CLI, the skill, the hook and
their tests, and nothing describing the previous architecture except DESIGN.md appendix A.

## T8 - Iterate on the CLI and the skill

**Goal.** Keep discovering against a knowledge base that is now used rather than built, and
build what that use earns. Open-ended by construction: it has no completion date, and its
first output is evidence rather than code.

**Why there is an eighth task.** [T2](#t2---minimum-capture-and-a-friction-journal) withheld
`search` so that an incident would justify it, and the incident never came - not because the
command is unnecessary, but because nothing in the window could have produced one. Every
session was onboarding: importing a vault, restructuring it, filing into it. A migration is
all writes. The evidence `search` needs comes from consulting a bundle, which only starts
being possible once there is one worth consulting, and that is true from
[T3](#t3---migrate-the-60-public-concepts) onward rather than during it.

So the bargain that made T2 work is re-struck rather than abandoned, on the half of the CLI
the first window could not reach.

**Steps.**

- Keep the journal running, under the rules at the top of `JOURNAL.md`. This time the
  incidents that matter are retrieval ones: a question answered from the web that the bundle
  already held, an index read end to end because nothing else would find a page, a concept
  filed twice because the first was not found.
- Record where an incident is filed. Findings about `fkb` belong in `JOURNAL.md`; findings
  about a bundle belong in that bundle's tracker. The 2026-09-14 entry exists because the
  distinction was not drawn and the evidence split in two.
- Implement `search` when the journal earns it, in pure Python unless
  [§9.7](DESIGN.md#97-what-we-may-assume-is-installed) says otherwise. Output must be
  bundle-qualified, and a published bundle's hits must render as URLs.
- Give **bulk filing** a shape. Two incidents on different axes: 66 concepts filed in one
  pass, where nothing covered ordering an index that gains 61 entries or keeping index and
  log self-consistent across 61 commits; and a session that generated genre notes for 67
  pages against indexes it had itself written an hour earlier, so the style reference was its
  own recent output and any drift propagated unchallenged. The second is the harder one, and
  what it wants is a rule that a bulk operation pins its reference to pages predating the
  session.
- Give **deletion** one too. Removing a concept edits at least three other files - the
  inbound link, the index entry, and the `log.md` line that announced it, which is a record
  that the thing happened and so degrades to plain text rather than disappearing. The skill
  files and has no notion of removing.
- Watch for a **vocabulary split across bundles**, which [T4](#t4---finish-the-cli) declined
  to address. `resolve` reports one bundle's tags, so one subject spelled two ways in two
  bundles is invisible to it. The failure it would cause is a federated search returning
  half its hits, which is why it waits for the command that could suffer it. A second
  incident, this time spanning bundles, is what would move the vocabulary up a level; the
  question until then is open and the coupling is not worth paying for in advance.
- Fold back into `SKILL.md` and the CLI whatever else the window turns up, one change per
  incident.
- **Propose workspace roots per operating system.** `fkb init --propose-roots` is the only
  statement of those defaults, now that the skill asks rather than carrying its own copy, and
  both of the two it offers are Unix habits: a visible `knowledge` directory and one under
  the agent directory. `Path.home()` gets the separators right, so nothing is broken; what is
  wrong is the advice. It is one function, deliberately, and it wants somebody who works on
  Windows rather than a guess from here.
- **Add the fifth cold-session test: a new bundle ends up with a gate.**
  [§9.11](DESIGN.md#911-a-new-bundle-is-a-repository-and-the-agent-commits-into-it) splits
  scaffolding between the CLI and the skill - `add --new` runs `git init`, and the agent pins
  the hooks at a revision it looks up in the session and makes the first commit. Only the CLI
  half is tested. The other half is prose, and prose is what regressed the last two times: a
  cold session given a new bundle should leave behind a `.pre-commit-config.yaml` pinned to a
  real SHA rather than a branch, an installed hook, and one commit that passed it.

  It waits here rather than joining [T5](#t5---finish-the-skill)'s four because it is the
  most expensive test in the suite to write honestly - it needs a network lookup and a real
  hook run inside the disposable agent's redirected `HOME` - and because the decision it
  checks was made at the end of T5 rather than designed into it. The gap it leaves is worth
  naming: until it exists, "the agent pins the hooks" is a claim this repository makes about
  itself and does not verify, which is the same shape as the `SKILL.md` instruction that no
  test read.

**Carried here from [T4](#t4---finish-the-cli): `fkb rename`.** The 2026-09-10 entry is a
complete incident and argues for a command - a rename is a title, a filename, and every
inbound link's text and target, done as one edit - but it is a *write*-path finding, and
[T4](#t4---finish-the-cli)'s step list is what the first window earned. It waits here rather
than being smuggled in, for one reason worth stating: the operation is unenforceable after
the fact. Once the old title is gone from frontmatter there is nothing left to grep the
stale link texts against, so neither a hook nor a lint can ever find what a rename left
behind. `mkdocs build --strict` and `linkspector` both passed over nine misnamed links,
because a stale link *text* is invisible to a link checker by construction. If a second
incident lands in this window, build it; if none does, the first one still stands and the
absence needs writing down rather than assuming.

**Done when.** Nothing, in the sense the other tasks mean it. The check is that `search`
either exists with journal entries behind it, or is still absent for a reason written down.

**Settles.** [§9.1](DESIGN.md#91-ranking-once-rg-stops-being-enough), when there is ranking
pressure to settle it with.

**Leave alone.** Anything the journal has not asked for. The failure mode of an open-ended
task is building the obvious thing, and the obvious thing is what the first window already
declined to confirm.

## T9 - Share one bundle between several people

**Goal.** Make one bundle writable by several people at once, without weakening the review
that guards what it publishes. Specified in
[§11](DESIGN.md#11-collaboration-and-syncing): one optional manifest field, one command, and
a branch shape that lives in the bundle's repository rather than here.

**It does not wait for [T8](#t8---iterate-on-the-cli-and-the-skill)**, which has no end by
construction. It needs [T7](#t7---second-bundle-then-retire-the-old-architecture) only for
the manifest to hold more than one writable bundle, and its first real test needs a bundle
that a second person actually files into.

**Why it is not part of [T5](#t5---finish-the-skill).** Filing was specified for one person
on one machine, and "never push" was a rule the skill could state absolutely because nothing
contradicted it. Sharing makes pushing part of filing for exactly one class of bundle, and
that is a change to the CLI's contract rather than to the skill's prose - which is the whole
argument for building it as a command.

**Steps.**

- **Add `sync` to the manifest schema**, optional, a branch name, meaningful only on a
  writable bundle. A non-writable bundle that declares one is a manifest error, raised where
  the mutually-non-prefixing `publish` check is raised, so a bad manifest fails on load
  rather than at the first push.
- **Teach `fkb add` to check the branch out**, when the bundle is registered with one. This
  is the step that makes the reviewed branch safe to leave as the repository's default:
  nobody has to remember that a fresh clone lands in the wrong place.
- **Implement `fkb sync [bundle]`** against the refusal table in
  [§11](DESIGN.md#11-collaboration-and-syncing). Fetch, rebase, push; no stashing, no branch
  switching, no conflict resolution, no flag that overrides the manifest. `--check` is a dry
  run of the same code path.
- **Have `fkb lint` report a checkout on the wrong branch** for a bundle that declares one.
  It is the cheap half of the same fact, available without a network call, and it is what
  tells somebody why their filing has stopped leaving the machine.
- **Narrow the skill's push rule rather than deleting it.** It becomes *never push a bundle
  with no `sync` branch*; for one that has it, filing runs the command on the way in and on
  the way out. The skill must not inspect what the command prints - it relays the refusal and
  stops, which is why the refusal text has to carry its own remedy.
- **Publish the merge back as a reusable workflow**, in `.github/workflows/`, called by a
  bundle with the shared branch as its one input. It merges the default branch in after every
  change to it, never squashing, and opens a pull request against the shared branch when the
  merge conflicts rather than failing a run nobody reads. A concurrency group keeps two rapid
  changes to the default branch from racing each other.

  It is built here rather than left to the recipe because it is the one part of the shape
  whose absence is silent: the branches drift, every working copy goes stale, and the first
  symptom is a concept filed twice. Bundles must pin it at the same commit they pin the hooks
  at, by full SHA, since it needs write access to the shared branch.

  **Name the test gap rather than closing it.** A workflow is infrastructure no test in this
  repository reads, which is the same shape as the `SKILL.md` instructions that regressed
  twice. Exercising it honestly needs a fixture repository with two branches and a real run,
  and until that exists "the merge back works" is a claim this repository makes about itself.
- **Write the rest of the repository recipe once**, in
  [`bundle-infrastructure.md`](skills/fkb/references/bundle-infrastructure.md): reviewed
  branch as the default and protected, shared branch open to push, merge commits only, the
  call to the workflow above, and the bundle's own checks in CI on pushes to the shared
  branch. None of that is enforced from here, and the reference is the only place it is
  stated. Mark which lines are load-bearing, so a bundle on another forge reproducing them by
  hand knows what it cannot drop.
- **Give the bundle `.gitattributes`.** `index.md` and `log.md` are append-only and get a
  union merge, which is what makes the common concurrent edit a non-event. A real conflict
  then means two people wrote the same concept, which is the only case worth a human.
- **Test the refusal table, one case per row**, over fixture repositories with a local bare
  remote. These are unit tests and cheap; the table is the whole product and an untested row
  is a row that will be wrong.
- **Add one cold-session test**: an agent files into a bundle registered with a `sync` branch
  and the concept arrives at the bare remote, with the hooks having run. It is the same shape
  as [T5](#t5---finish-the-skill)'s tests and for the same reason - the instruction to run
  the command is prose, and prose is what regresses.
- **Keep the journal on refusals.** The entry that matters here is a refusal that was wrong:
  the command declined, the person looked, and pushing would have been fine. Each of those
  argues for removing a row, and nothing else should.

**Done when.** Two machines share one bundle. A concept filed on the first is read by an
agent on the second without either person running a git command by hand, the reviewed branch
has only ever been changed through a pull request, the merge back has run unattended, and
every row of the refusal table has a test.

**Where it stands.** Everything except the last two clauses is built: `sync` in the manifest
and in `resolve`, `fkb sync [bundle] [--check]` against the refusal table, `add --sync` which
checks the branch out, the drifted-checkout warning in `lint`, union-merge `.gitattributes`
in every scaffolded bundle, the narrowed push rule in the skill, the recipe in
[`bundle-infrastructure.md`](skills/fkb/references/bundle-infrastructure.md), and the
merge-back workflow in `.github/workflows/merge-back.yml`. Each row of the table has a test
over real repositories with a bare remote, and one cold-session test files into a shared
bundle and checks the concept reached that remote.

**Two claims this repository still makes about itself.** The merge-back workflow is read by
no test here - exercising it honestly needs a fixture repository with two branches and a real
run - and no two machines have shared a bundle yet, so the branch shape is argued rather than
lived. Both were named as gaps when the task was written and neither is closed by building
the thing.

**Settles.** Nothing in [§9](DESIGN.md#9-open-decisions) on its own. It is what produces the
evidence for [§9.12](DESIGN.md#912-the-window-in-which-a-shared-concept-has-no-url), which
needs a bundle being cited across the window rather than an argument about one.

**Leave alone.** Conflict resolution, release pull request creation, and a second published
site for the shared branch. The first is a human's decision about what is true; the second is
`gh`; the third is the answer [§11](DESIGN.md#11-collaboration-and-syncing) declined, and
taking it early would settle
[§9.12](DESIGN.md#912-the-window-in-which-a-shared-concept-has-no-url) by assumption in the
one direction that cannot be walked back.

## Already done

Work that belongs to no task, recorded so it is not looked for.

- **The project is versioned and every merge releases** (2026-09-21). `skills/fkb/VERSION`
  travels with an installed copy because nothing else does, the manifest records which
  release a setup was last brought up to, and `fkb migrate` walks the guides in between.
  The size of each release comes from a label on the pull request and the version file is
  written by CI, never by hand. Reasoning in [§10](DESIGN.md#10-versioning-and-migration);
  the first guide, `0.1.0.md`, asks nothing but walks the chain once while nothing is at
  stake.

- **The AGENTS.md block was removed and later rewritten** in `~/.config/opencode/AGENTS.md`
  (removed 2026-09-02 because it described the retired architecture; the
  [§5.4](DESIGN.md#54-the-schema) text is in place again). One line of it is a promise the
  skill cannot yet keep - "before searching the web, check the bundles" - because filing is
  all the skill does. [T5](#t5---finish-the-skill) is what makes that line true, and also
  what teaches the skill to notice the block missing on somebody else's machine.
- **The retired architecture is deleted** (2026-09-02): the six `fkb-*` skills, `manifest.py`,
  `install-glue`, the bundle commands and their tests. The last working state is preserved in
  git history, and what it cost is DESIGN.md appendix A. The disposable-agent test machinery
  was kept.
- **The OKF material is vendored** (2026-09-07): the specification from its canonical
  repository, the validator and concept template from `okf-skills`, each pinned and with its
  licence beside it. The validator is byte-identical so a re-pull stays a diff; the template
  is adapted. Details in [§8](DESIGN.md#8-vendoring-from-okf-skills).
- **Six decisions made while building [T1](#t1---prepare-the-bundle-empty) were written back
  into DESIGN.md** (2026-09-07). They had been recorded only in commit messages, which say why
  a change happened and not what is currently true, leaving four sections describing questions
  as open that were in fact answered.
