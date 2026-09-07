# IMPLEMENTATION - federated-knowledge-skills

**Status:** the plan of record. [DESIGN.md](DESIGN.md) remains the sole source of truth for
*what* gets built; this document says *in which order* and *when* each open question is
answered. It was §10 of that document until it grew large enough to stand on its own.

**Section references.** A `§N` link points at the matching section of [DESIGN.md](DESIGN.md);
`OKF §N` refers to the Open Knowledge Format spec.

This is the implementation plan. It assumes nothing from this repository except
[DESIGN.md](DESIGN.md) and this file - a fresh session should be able to start here.

## How to use it

**Answer an open question only when a task forces it.** Deciding early trades away the
information the work itself produces. Every task below therefore names two things: which
questions it must settle, and which it must leave alone even when the answer feels obvious.
Leaving one alone is not procrastination; it is refusing to guess when the next task will know.

Tasks run in order. Each states what "done" means in terms someone else could check.

## Before starting

A fresh session needs four things, none of which live in this repository.

| What | Where | Why |
| --- | --- | --- |
| The OKF v0.2 spec | `GoogleCloudPlatform/open-knowledge-format` | Vendored verbatim ([§8](DESIGN.md#8-vendoring-from-okf-skills)) |
| `okf-skills` at a pinned commit | `scaccogatto/okf-skills` | Source of the validator, template and spec copy ([§8](DESIGN.md#8-vendoring-from-okf-skills)) |
| The publishing template | `~/Projects/public/running-linux` | MkDocs, prek, CI, Pages - reused, not rebuilt |
| The existing content | `~/.agents/wikis/{public,private}/docs` | ~60 concepts, ~100 transcripts |

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

**Goal.** A conformant, publishing bundle that is ready to be written into, before any content
is migrated. Hours, not days - [T2](#t2---minimum-capture-and-a-friction-journal) is blocked on
this and nothing else.

**Deliverable.** A git repo from the running-linux template, with the directory layout fixed,
the floor declaration written, publishing working, and a handful of concepts in it as proof.

**Steps.**

- Copy the template: MkDocs, prek, CI, Pages.
- Fix the top-level directory layout, and decide how the `meta/` pages satisfy OKF §11
  ([§9.4](DESIGN.md#94-non-knowledge-pages-inside-a-bundle)). Both are forced now, because
  everything written afterwards assumes them.
- Decide where markdown raw sources live
  ([§9.3](DESIGN.md#93-markdown-raw-sources-references-concepts-or-outside-the-bundle)). The
  ~100 transcripts are the concrete case; deciding does not mean moving them yet.
- Write the floor declaration file
  ([§9.2](DESIGN.md#92-where-a-bundle-declares-its-floor---a-yaml-file-at-the-bundle-root)).
  Nothing reads it until [T4](#t4---finish-the-cli).
- Write `index.md`, `log.md`, and three or four real concepts by hand.

**Done when.** `okf_validate.py --strict` passes, `mkdocs build --strict` passes, and the site
is live.

**Settles.**
[§9.2](DESIGN.md#92-where-a-bundle-declares-its-floor---a-yaml-file-at-the-bundle-root),
[§9.3](DESIGN.md#93-markdown-raw-sources-references-concepts-or-outside-the-bundle),
[§9.4](DESIGN.md#94-non-knowledge-pages-inside-a-bundle), and
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
- Convert `[[wikilinks]]` to relative markdown links using a filename-and-title map. Emit the
  unresolved ones as a list for manual review rather than guessing a target.
- Delete the `raw/` tree once the conversion validates.
- Move the transcripts wherever [T1](#t1---prepare-the-bundle-empty) decided
  ([§9.3](DESIGN.md#93-markdown-raw-sources-references-concepts-or-outside-the-bundle)).

**Done when.** `okf_validate.py --strict` and `mkdocs build --strict` both pass, internal links
resolve, and the unresolved-link list is empty or consciously accepted.

**Leave alone.** The conversion script is disposable and never becomes part of `fkb`.

## T4 - Finish the CLI

**Goal.** Add the commands the journal justified, and nothing else.

**Specified by DESIGN.md.** Manifest schema and resolution
([§4](DESIGN.md#4-bundles-and-the-manifest)), the reference rule
([§4](DESIGN.md#4-bundles-and-the-manifest)), what `resolve` reports
([§7](DESIGN.md#7-the-cli)), `lint`'s warning-versus-error behaviour
([§6.6](DESIGN.md#66-what-fkb-lint-does-across-bundles)).

**Steps.**

- Read `JOURNAL.md` first. A command with no entries against it does not get built.
- Implement the federation checks in `lint`: the reference rule, cross-bundle links, and
  demotion to warnings for non-writable bundles
  ([§6.6](DESIGN.md#66-what-fkb-lint-does-across-bundles)).
- Implement `search` if the journal earned it, in pure Python unless
  [§9.7](DESIGN.md#97-what-we-may-assume-is-installed) says otherwise. Output must be
  bundle-qualified, and a published bundle's hits must render as URLs.
- Add `resolve`'s vocabulary reporting if the journal shows style mismatches
  ([§7](DESIGN.md#7-the-cli)).
- Implement `fkb init` and `fkb add` with its three arrival paths ([§7](DESIGN.md#7-the-cli)).
  Until now the workspace was hand-written;
  [T7](#t7---second-bundle-then-retire-the-old-architecture) introduces a second bundle and a
  real user, so setup stops being a one-off.

**Done when.** Every built command runs against the migrated bundle and at least one read-only
upstream, and the tests drive the installed copy rather than the source tree.

**Settles.** [§9.7](DESIGN.md#97-what-we-may-assume-is-installed), and
[§9.1](DESIGN.md#91-ranking-once-rg-stops-being-enough) to the extent the journal decided it.

## T5 - Finish the skill

**Goal.** Extend the filing-only skill of [T2](#t2---minimum-capture-and-a-friction-journal)
into the full one, including onboarding.

**Steps.**

- Add the query workflow and the semantic lint checklist
  ([§6.5](DESIGN.md#65-two-lints-one-of-them-code)).
- Add the "new here?" branch to `SKILL.md` and write `references/getting-started.md`
  ([§6.7](DESIGN.md#67-the-skill-explains-itself)). Take the three arrival paths from the
  previous `README.md` before [T7](#t7---second-bundle-then-retire-the-old-architecture) deletes
  it.
- Add `references/house-style.md` and `references/federation.md`.
- Fold whatever the journal revealed about the filing instructions back into `SKILL.md`.

**Done when.** Three cold-session tests pass, each starting with no prior context:

1. Given a question, the agent finds the skill, reads a concept and cites it.
2. Given "note this down", it files a conformant concept that passes `fkb lint` uncorrected.
3. Given "what is this and how do I start?" on a machine with **no workspace configured**, it
   explains what a bundle is and gives a first command that runs
   ([§6.7](DESIGN.md#67-the-skill-explains-itself)).

The third test is the one that fails quietly. A plausible summary of the design is not a pass;
a next step the person can run is.

**Leave alone.** [§9.6](DESIGN.md#96-how-knowledge-is-structured-inside-a-bundle) - the skill
reads a bundle's style, it does not impose one.

## T6 - Ship the standalone pre-commit hook

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
- Fold `JOURNAL.md` into a decisions record and delete it.
- Update `README.md` to describe what now exists rather than what is planned.

**Done when.** The repository contains the design, this plan, the CLI, the skill, the hook and
their tests, and nothing describing the previous architecture except DESIGN.md appendix A.

## Already done

- **The stale AGENTS.md block is removed** from `~/.config/opencode/AGENTS.md` (2026-09-02).
  Cold sessions currently get no wiki instructions at all, which is correct until
  [T4](#t4---finish-the-cli) gives them something true to say.
- **The retired architecture is deleted** (2026-09-02): the six `fkb-*` skills, `manifest.py`,
  `install-glue`, the bundle commands and their tests. The last working state is preserved in
  git history, and what it cost is DESIGN.md appendix A. The disposable-agent test machinery
  was kept.
