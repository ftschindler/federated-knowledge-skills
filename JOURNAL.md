# Journal

Friction, recorded while filing knowledge with a deliberately incomplete toolset. `fkb` has
`list` and `lint` and nothing else; search, vocabulary reporting and setup commands are
withheld so that what gets built next answers an incident rather than a guess.

This file is temporary. It is folded into a decisions record and deleted once it has decided
the CLI's scope.

## How to write an entry

One line per incident, dated, so the file greps. Three rules:

- **Record what happened, not what should exist.** "Searched the web for X; the bundle had
  it at `principles/y.md`" is evidence. "Search would be useful" is a wish, and wishes are
  free.
- **Name the artifacts.** The actual query, the actual path, the actual tag chosen. An entry
  that names no file and no query did not happen, and must not be written.
- **Record what was done instead.** The workaround is the measurement. If there was no
  workaround, say the task was abandoned.

An empty week is a finding. Nothing is gained by inventing a plausible incident, and the
only evidence this file exists to collect is lost.

## What to watch for

The skill files one concept at a time and stops. It does not search for existing concepts,
update overviews, or change tags. That is deliberate: the gaps stay open long enough to be
measured. Notice these moments and record them:

- **Supersession** - you write something that makes an existing concept wrong. Did you notice
  mid-write? Did you search for it first? What did you do instead: file both, ask, or skip?
- **Impact sweep** - a concept you file touches others that cite the same thing. Did you look
  for them? Did you link back, or only outward?
- **Schema evolution** - no existing `type` or directory fits. Did you invent one, ask, or
  force it? Who should update `spec/types.md`?
- **Tag discipline** - you picked a tag without knowing what the bundle uses. Did you guess?
  Did lint catch it? What workaround did you use?
- **Cross-linking** - you filed a concept that others *should* link to. Did you find them and
  edit them, or leave it for later?
- **Re-synthesis** - an overview or roll-up now says something outdated. Did you notice? Did
  you update it, supersede it, or file a note?

Each of these is a decision the `kb-ingest` skill makes automatically. This design stops at
filing, so the journal decides whether integration mechanics belong in T5 or stay with a
person.

## Incidents

### 2026-09-09

We need a way to seamlessly share the knowledge across machines live. Taking a step back:
the main branch in the writable bundles is the one that is PR-gated and gets published.
We could therefore have another branch, say `staging`, that's checked out in the writable
bundles. The skill could then advise to commit + `git pull --rebase` + `git push` on the
staging branch automatically. That way, the knowledge is shared live across users, and we
manually do a PR to integrate that into main via a weekly/daily GH workflow trigger.

Did we not want to provide the fkb cli with a `--json` option so agents can read the structured output better?

- **2026-09-09** house style - the skill sends you to `okf-floor.yaml` for what a concept must
  carry, and that file is honest about the frontmatter. It says nothing about the bundle repo's
  *prose* rules, which are enforced by `.pre-commit-config.yaml`: `.scripts/check_markdown_style.py`
  forbids em dashes and thematic breaks, and `.markdownlint-cli2.jsonc` sets MD041
  `front_matter_title`, which makes a body `# Title` a second H1 under MD025. Wrote all 66
  concepts of an import first, hit both only at `uv run prek run --all-files`, and re-ran the
  whole migration to strip body H1s and replace `\u2014`. Step 4 ("read the structure first")
  should say to read the bundle's hook config too, not only its floor.
- **2026-09-09** scratch files - was asked to hold five concepts back in an uncommitted
  `TODO.md`. Put it at `docs/TODO.md`; `okf-bundle` failed it with six ERRORs, correctly, since
  §11.1 makes every non-reserved `.md` in a bundle a concept. Moved it to the repo root as
  `TODO.md`, outside `--bundle-root docs`. There is no sanctioned place inside a bundle for a
  note that is not a concept.
- **2026-09-09** bulk import - filed 66 concepts from an older awiki vault in one pass. The skill
  is written for one concept at a time, so nothing covers ordering an `index.md` that gains 61
  entries at once, or building index and log incrementally so that each of 61 commits is
  self-consistent. Wrote a throwaway script that re-rendered `index.md` and `log.md` before every
  commit; nothing in the skill suggested that shape.
- **2026-09-09** link check - `linkspector` blocked commit 15 of 61 on `https://excalidraw.com`
  returning 403, in `about/*.md` files the import never touched (`curl` gets 403 too, so not rate
  limiting). Added the pattern to `.linkspector.yml` alongside the four already there for the
  same reason, in its own commit. A bulk file is where a pre-existing external-link rot surfaces,
  and the skill's "leave the commit to the person" does not anticipate the person having asked
  for 61 of them.

### 2026-09-10

- **2026-09-10** log order - appended a day's entries to `ftschindler/docs/log.md` at the
  bottom, because the file ran oldest-first (`2026-09-07`, `2026-09-09`) and matching the file
  looked safer than matching the rule. The rule said the opposite: `about/editing_conventions.md`
  says "find today's heading or create one at the top; do not append at the bottom". The bulk
  import of 2026-09-09 had built the file ascending and nothing caught it, so the artifact had
  been contradicting its own convention for a day and the next writer inherited the error.
  Reversed the three day-sections with a throwaway script. No hook checks log order, so the
  only signal was reading a prose file the skill does not send you to. Same shape as the house
  style incident above: the skill points at `okf-floor.yaml`, and the bundle's actual writing
  rules live somewhere else. A `kb-lint` check that `log.md` headings descend would have caught
  both the import's mistake and mine.
- **2026-09-10** supersession, noticed and acted on - rewrote
  `decisions/building_an_agent_first_wiki_that_is_also_a_human_pkb.md` into
  `explorations/running_this_knowledge_base_on_awiki.md` because the decision recorded a tool
  choice that had since been abandoned. This is the supersession case the watch-list asks about,
  and it needed three things the skill has none of: finding every inbound reference (four, via
  `grep`, two of them prose-only mentions with no link that no link checker would have flagged),
  deciding that `status: deprecated` was the wrong marker for a *finished* piece of work, and
  inventing a directory. `explorations/` did not exist and no `type: Exploration` was in use.
  Invented both, then wrote a concept arguing for the layer so the invention has a rationale in
  the bundle rather than only in a commit message. Nothing asked whether `spec/types.md` should
  learn about it.
- **2026-09-10** log format, unspecified - wrote nine `log.md` entries for the day as markdown
  links, the way every other file in the bundle is written and the way OKF §9's own example
  shows (`Established the [Dataplex Playbook](/playbooks/dataplex.md)`). Then deleted two
  concepts in the same pass and found the log lines that had added them, which could be neither
  left (dangling, and `mkdocs build --strict` fails on it) nor deleted (the entry is a record
  that the thing happened). Degraded both to plain text. Nothing anywhere said which of these
  was right: `DESIGN.md` mentioned `log.md` once, in a blockquote about find-or-create ordering;
  `SKILL.md` step 6 says "append a line to `log.md` under today's date" and stops; `check_log`
  validates only that frontmatter is absent and the date headings are ISO. The rule is
  discoverable only by deleting something, which is the least frequent operation and the one the
  skill does not cover at all. Settled it in `DESIGN.md` §9.9 as prose-only, with a `check_log`
  warning and an appendix B deviation, both unbuilt.
- **2026-09-10** registering a bundle - asked to add a public read-only vault. `fkb` has `list`
  and `lint` and no `add`, and `SKILL.md` line 26 says not to create or guess a manifest, so the
  only route was hand-editing `~/.config/fkb/workspace.yaml`: added `stjbrown-agent-knowledge`
  with `path: ./stjbrown-agent-knowledge/knowledge`, `referenceable_by: "*"`, `writable: false`.
  Three things nothing told me to do. The **OKF root is not the repo root** - the clone has ten
  `index.md` files, and only `knowledge/index.md` is the top-most one; `skills/kb/example-bundle/`
  is a decoy that would have registered a sample as the bundle. The **checkout was in the wrong
  place**, at `~/.agents/knowledge/`, under a `workspace_root` of `~/knowledge`; checked
  `git check-ignore` before moving it, since `~/.agents` is itself a repo. And a **second, stale
  manifest** existed at `~/.config/federated-knowledge/workspace.okf.yaml`, listing this same
  bundle at a path that no longer resolved; `fkb list` cannot see it and so cannot report the
  divergence. The user deleted it. Registration is mechanical enough to be a command and was
  three judgement calls instead.
- **2026-09-10** lint on a bundle I may not write to - `fkb lint stjbrown-agent-knowledge`
  returned `ok (105 warning(s))`, all of them `okf_version: "0.1"` vintage: `timestamp` and
  `# Citations` per concept, checked against v0.2. Correct, and unactionable: the bundle is
  `writable: false`, so every one of the 105 is somebody else's to fix, and `lint` has no notion
  of that. Read them all to confirm none was a real defect, then left them. `--coverage` was not
  run for the same reason. A foreign bundle wants either a version-aware check or a quiet mode,
  or its warnings will be scrolled past every time and the one that matters will go with them.
- **2026-09-10** `publish`, undefined and got wrong - registered the bundle above with
  `publish: https://github.com/stjbrown/agent-knowledge`, the repo's landing page, as if the
  field named where the bundle lives. The user corrected it: `publish` is a **prefix**, so a
  concept at `<path>/foo/bar.md` is reachable at `<publish>foo/bar.md`. Mine resolved
  `concepts/memex.md` to `https://github.com/stjbrown/agent-knowledge/concepts/memex.md`, a 404.
  Corrected to `https://github.com/stjbrown/agent-knowledge/blob/main/knowledge/` (checked: 200),
  which for a bundle with no deployed site means the prefix has to carry the forge's
  `blob/<branch>/` and the OKF subdir, and must end in a slash to concatenate. Nothing states any
  of this: `grep -n publish references/SPEC.md` returns nothing at all, `SKILL.md` never mentions
  the field, and the only description anywhere is `fkb list`'s own help string, "publish URLs".
  The existing entries do not settle it either and cannot be copied from - `public` is
  `https://ftschindler.github.io/knowledge` with no trailing slash, and it is a MkDocs site where
  `foo/bar.md` publishes as `foo/bar/`, so the concatenation rule does not hold there at all.
  Two bundles, two incompatible readings of one field, and no error is possible: `lint` never
  fetches a URL, so a `publish` that resolves to nothing is indistinguishable from a correct one.
- **2026-09-10** which bundle, never asked - the request was "add a public non-writable OKF vault
  to my federated knowledge base" and named no repository. I wrote a plan whose step 2 was "get
  the vault on disk", noted in it that a remote-only vault meant stopping, and then never asked
  for a URL. I had asked one blocking question - which of the two manifests was authoritative -
  and the user answered it by deleting `~/.config/federated-knowledge/`; I treated that one
  answer as closing both gaps. Filled the second by `ls ~/.agents/knowledge`, found
  `stjbrown-agent-knowledge` as the only public read-only bundle present, and registered it.
  Right, as it happens: it was in the deleted manifest. But "only candidate on disk" was
  inference, not instruction, and a new third-party vault would have looked identical from here.
  Nothing in the skill could have caught this, because registration is not a skill operation at
  all - `SKILL.md` covers filing a concept into a bundle that already exists, and the one guard
  it does have (line 26, do not guess a path) fires on a *missing* manifest, not on a missing
  argument. If `fkb add` is ever built, the bundle's identity is the argument it must refuse to
  default, and the failure to imitate is a plan that names a step it has no input for and runs it
  anyway.

### 2026-09-13

- **2026-09-13** tone, unconditioned - wrote ten concepts into the `public` bundle across a
  session and never once opened an existing page to see how they were written. The skill's step
  4 says to read the structure first, and reading the structure gets you `okf-floor.yaml`, the
  directories and the index: the bundle's *schema* and none of its *voice*. Where the new pages
  matched the house register it was a side effect of research - `explorations/running_this_...md`
  came out right because six neighbouring pages were already in context for their content. Where
  nothing was in context, `tools/agent_wiki.md` and the genre notes, the default register showed
  up instead and Felix corrected it by hand. The fix is one line in the skill and it is cheap:
  **before writing, read two existing concepts from the target directory**, which the directory
  index now names. A rule describes a voice; the pages are one, and prose matches nearby prose
  more reliably than it satisfies an adjective. Written up in the bundle's
  `about/editing_conventions.md` under "Read before you write".
- **2026-09-13** tone, self-referential - the same session generated genre notes for 67 pages in
  one pass, each with a two-sentence gloss drawn from the directory indexes. Those indexes had
  been written an hour earlier, in the same session, by the same agent. So the style reference
  for 67 files was the agent's own recent output rather than the bundle, and any drift in the
  first artefact propagated to every page without a second opinion. Nothing flagged it; the
  result reads consistently, which is exactly the failure mode - internally consistent and
  possibly off-register as a whole. A bulk operation wants its reference pinned to pages that
  predate the session, and the skill has no notion of a bulk operation at all (see the
  2026-09-09 bulk import entry, which hit the same gap on a different axis).
- **2026-09-13** log format, applied - the `2026-09-10` entry settled `log.md` entries as prose
  with no links, and `DESIGN.md` §9.9 records it. Three sessions later the rule held without
  effort: the 2026-09-11 and 2026-09-13 entries were written as plain text first time, including
  across a restructure that renamed three files and moved them between directories. No log line
  needed touching during the moves, which is the property the rule was chosen for. Worth one line
  as positive evidence, since this file otherwise only records friction.

  that is what "rename" felt like. Three other things had to move with it and nothing said so.
  The **filename** still read `building_a_pkb_that_is_mine_forever_readable_and_visual.md`
  under a title of "Building my visual PKB", which is a slug that no longer describes its
  concept and that a `grep` for the new title does not find. Nine **inbound links** across
  seven files still carried the old title as their link text, so the bundle rendered a page
  under one name and referred to it by another everywhere else, and only the frontmatter knew
  which was current. The **index entry** was one of the nine. Nothing caught any of it:
  `mkdocs build --strict` and `linkspector` both passed the whole time, because every link
  still resolved - the target existed, it was only misnamed, and a stale link *text* is
  invisible to a link checker by construction. Found by grepping the old title by hand a day
  later, on a hunch. So the rule is: a rename is a title, a filename, and every inbound link's
  text and target, done as one edit. `fkb` has no rename operation, and this is the failure it
  should own, because it is entirely mechanical and entirely unenforceable after the fact -
  once the old title is gone from frontmatter there is nothing left to grep the stale link
  texts against. Historical `log.md` entries are the exception and keep the old name, which is
  the append-only rule of the entry above working as intended.
- **2026-09-10** deletion - dropped two concepts outright
  (`linux/kde_plasma_phantom_pointer_...`, and two `meta/` pages). Deleting a concept means
  editing at least three other files: the inbound link in a sibling concept, the `index.md`
  entry, and the historical `log.md` line that added it, which cannot simply be removed because
  it is a record that the thing happened. Degraded that line to plain text instead. The skill
  files concepts and has no notion of removing one, so nothing suggested the log needed handling
  differently from the index.
- **2026-09-11** onboarding a new unpublished private bundle - `~/knowledge/private` was a
  `git clone` of `~/knowledge/ftschindler` minus the publishing stack, so it inherited a
  `.pre-commit-config.yaml` written for a bundle rooted at `docs/` and an already-stale copy
  of `.scripts/check_no_horizontal_rules.py`, whilst inheriting none of the prose that makes
  the rules knowable: no `about/editing_conventions.md`, no `.github/copilot-instructions.md`.
  Setting it up meant diffing the two repositories by hand, then reading
  `skills/fkb/scripts/bundle_lint.py` in the pinned checker to answer the one question that
  decided the whole layout: `bundle.rglob("*.md")` descends into dot-directories, so with
  `--bundle-root .` there is no place to put a non-concept Markdown file at all. `about/` is
  not an option in a root-rooted bundle, and `exclude:` cannot rescue `.github/` either,
  because `okf-bundle` runs `pass_filenames: false, always_run: true`. Resolved by conforming:
  `editing_conventions.md` and a three-line pointer `AGENTS.md`, both carrying floor
  frontmatter, both listed under a `## Meta` heading in `index.md`, plus `AGENTS\.md` added to
  the `lowercase-no-whitespace-filenames` exclude. `prek run --all-files` and
  `prek run --hook-stage manual --all-files okf-bundle` both pass. None of that was written
  down anywhere; it was re-derived from the checker's source. The skill has no notion of
  creating a bundle, only of filing into one that exists, so a new private tier starts by
  cloning a public one and silently keeps every assumption the publishing stack had made. A
  `references/getting_started.md` covering exactly this - root-rooted versus `docs/`-rooted
  and what each implies, the floor file, which hooks to keep when nothing publishes, where
  conventions and agent instructions can legally live, and the two commands that prove it -
  would have replaced the clone-and-diff entirely, and `SKILL.md` should read it on request
  rather than carrying it inline.

- **2026-09-11** structure - filing a Finding in the `public` bundle, step 4 told me to read the
  bundle's directories and `index.md`. The directory listing was misleading: there is no
  `findings/`, and the two existing Findings sit in `tools/` and `linux/` beside concepts of
  other types, so the section is assembled by the index rather than by directory. I placed
  `tools/dependabot_declines_transitive_security_updates_in_uv_lock.md` next to
  `tools/awiki_title_extraction_breaks_on_frontmatter_led_source_files.md` only after reading
  the whole index. Step 4 leads with directories and mentions `index.md` second; for a bundle
  that groups by subject and sections by type, that order costs a read.
