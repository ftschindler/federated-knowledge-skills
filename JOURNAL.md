# Journal

Friction, recorded while filing knowledge with a deliberately incomplete toolset. `fkb` has
`list` and `lint` and nothing else; search, vocabulary reporting and setup commands are
withheld so that what gets built next answers an incident rather than a guess.

This file is temporary, and runs in windows. The first one decided T4's scope and is folded
into a decisions record at T7; the file stays open for T8's window, which is the retrieval
half the first one could not reach, and is deleted when that has decided `search`.

**An artifact is a path, a query or a command.** An identity is not one, and neither is the
name or URL of a bundle that is not public. This file is committed to a public repository and
the federation it describes contains a private work bundle, so an entry names what was done
and describes whose it was. Do not paste `fkb list` output or the manifest.

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

## Proposals raised while journaling

Not incidents, and they break the first rule of this file: both are wishes, neither names a
path or a query. They are kept here rather than deleted because they were raised in the course
of the work and have nowhere else to live yet. Both belong in DESIGN's open questions, and
should be moved there rather than answered here.

- **Live sharing across machines.** The main branch in the writable bundles is the one that is
  PR-gated and gets published. There could be a second branch, say `staging`, checked out in
  the writable bundles, with the skill advising commit, `git pull --rebase` and `git push` on
  it automatically. Knowledge is then shared live across machines, and a weekly or daily GitHub
  workflow raises the PR that integrates `staging` into main.
- **`--json` output on the CLI**, so an agent parses structured output rather than prose.

## Incidents

### 2026-09-09

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
- **2026-09-10** renaming a concept - changed one `title` in frontmatter and stopped, because
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

### 2026-09-11

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

### 2026-09-14

Backfilled after the fact, on 2026-09-14, having noticed that this file had recorded nothing
since the morning of 2026-09-13 while the `public` bundle went from 66 concepts to 76 and had
its whole taxonomy rebuilt. The gap is the subject of the third entry below.

- **2026-09-14** tag vocabulary - the agent-wiki subject had been split across two spellings,
  `awiki` on four pages and `agent-wiki` on three, for several weeks. Searching either spelling
  returned one half and gave no indication the other existed, which makes a misspelt tag a
  silent retrieval failure rather than a cosmetic one, because tags carry the subject axis per
  `knowledge_management/split_orthogonal_classification_axes_across_folders_and_tags.md`.
  Nothing caught it: not the bundle's hooks, not `mkdocs build --strict`, not `fkb lint`. It was
  found by reading a sentence that happened to mention the tag, and canonicalised by hand across
  four files in `ccf9812`. The workaround is that there is no workaround: a `grep` for one
  spelling cannot tell you that a second exists, and the only reliable check is a declared
  vocabulary with a hook that fails on a tag outside it. awiki had exactly that (`tag add`,
  `tag suggest`, `tag fix`, and a `lint --strict` gate) and it is one of the capabilities lost
  in the move off that tool. This is the first concrete evidence for `fkb resolve`'s vocabulary
  reporting, which T2 withheld. It also raises a question only this layer can answer: a tag
  split *across* bundles is the same failure one level up, and a per-bundle vocabulary cannot
  see it, so whether the vocabulary is a bundle artifact or a federation one is a design
  question and not a bundle one. Either way it has to be optional: no bundle in the manifest
  declares a vocabulary today, and a bundle that declares none must still be filable into.
- **2026-09-14** navigation reachability - `c912bf5` made the `docs/.pages` nav list explicit to
  fix section ordering, which replaced a `...` wildcard that turned out to be the only thing
  pulling the `about/` pages into the site navigation. All of them silently left the nav:
  editing conventions, the dev environment, Obsidian, the tech stack, and the tags page added
  the day before. Nothing failed; the pages still built, still rendered, and every link to them
  still resolved. They were simply unreachable by browsing, found by a person noticing a gap in
  the nav bar days later, and restored in `2cd39a5` with a comment recording that the wildcard
  is load-bearing. `fkb lint` checks that every concept is reachable from an index, which covers
  `docs/` only; there is no equivalent for the built site, so a page can be published and
  unreachable, which is the same defect the reachability rule exists to prevent, one layer out.
- **2026-09-14** where an incident gets filed - the three findings of this session were written
  up as issues on the bundle's own repository (`ftschindler/knowledge` numbers 8, 9 and 10) and
  not here, and `TODO.md` was rewritten with a routing rule that makes this deliberate: repo and
  site to issues, single-page debt to `status: draft`. The rule is right for the bundle and
  wrong for this file, because two of those three issues are evidence about `fkb` rather than
  about the bundle: the tag vocabulary is the case for `resolve`, and nav reachability is a
  claim about what `fkb lint` does not cover. So the evidence base this journal exists to
  collect is now split across two trackers with nothing routing between them, and the split runs
  along exactly the axes T2 withheld commands to measure. Nothing in `SKILL.md` mentions the
  journal as a destination once a repository with an issue tracker is in reach, and an issue is
  the more natural place to put something when the bundle is the thing in front of you. The
  workaround was to read the three issues back and write the two relevant ones into this file by
  hand, which only happened because someone went looking.
- **2026-09-14** per-directory indexes, and what step 4 should read - the bundle moved from one
  `index.md` to eleven. The top-level index is now four lines of orientation and a list of
  eleven section links, and each directory carries its own `index.md` which *defines the
  category* and then lists its pages: `findings/index.md` states what a Finding is, its four
  conventions (the title names the symptom in the words you would have searched for, the
  filename leads with the date found, the list runs newest first, a finding about a tool carries
  `stale_after`) and links to the knowledge-management concepts carrying the reasoning. Genre
  definitions moved out of per-page genre notes into those indexes in `6c73c8f` and `c912bf5`,
  and `findings/` became a real directory in `7853326`. This answers the 2026-09-11 structure
  entry directly: the complaint there was that the directory listing was misleading and the
  whole index had to be read to place one page, and that cost disappears if step 4 reads the
  *target directory's* index rather than the bundle's. It also answers most of the 2026-09-13
  tone entry, since that index names the neighbouring pages to read before writing. Two things
  follow that nothing currently enforces. A directory index is now a normative artifact, and no
  lint knows it exists, so a directory can gain concepts that its own index never lists and a
  new directory can appear with no definition at all. And `okf-floor.yaml` is no longer the
  whole schema story, which matters because an agent that reads `SKILL.md`, the floor and the
  top-level index still never opens a single concept. All of which is a fact about *this*
  bundle, and the entry below is the reason that distinction has to be carried forward rather
  than collapsed into a rule.
- **2026-09-14** one bundle's conventions are not the skill's rules - the entry above, and the
  house style and tone entries before it, were all written from the `public` bundle, and every
  one of them ends in a sentence of the form "the skill should read X". That generalises a
  single bundle's conventions into a rule for all of them, and the manifest on this machine
  already contains four bundles that agree on almost nothing. Checked all four rather than
  assuming. **Where concepts start** differs: two are rooted at `docs/`, one at the repository
  root, one in `knowledge/`. **The floor** is not universal: the read-only third-party bundle
  has no `okf-floor.yaml` anywhere, so the skill's central instruction, satisfy the bundle's
  floor rather than carrying your own list of fields, has no referent there at all and nothing
  says what an agent should do instead. **The prose conventions** are in a different place in
  every bundle that has them, at `docs/about/editing_conventions.md`, at the repository root
  beside `AGENTS.md`, in an `about/` directory that sits outside the OKF root entirely, and
  absent in the fourth. **Indexes** differ in kind, not just in count: eleven category-defining
  ones in the bundle above, two in the flat private bundle, six in the third-party one that
  index by subject rather than by genre. And one bundle carries a **stale duplicate floor in a
  build output directory**, which is the same shape of trap as the `example-bundle/` decoy in
  the 2026-09-10 registering entry: a naive walk that looks for the floor finds two and has no
  basis for choosing. There is no workaround yet because nothing has failed yet; all four were
  handled by a person who knew each one. The correction this makes to the rest of this file is
  that the fixes proposed in those entries have a generic form and a specific one, and only the
  generic form belongs in `SKILL.md`: **read the conventions the bundle declares, wherever it
  declares them, and read two neighbouring concepts before writing**, rather than "read
  `about/editing_conventions.md`" or "read the target directory's index". Which implies the
  thing none of these bundles has: a declared place for a bundle to say where its own
  conventions live, next to the floor that already says what a concept must carry, so that the
  skill dereferences a pointer instead of guessing a path. A bundle that declares nothing must
  still be filable into, and the third-party one is the proof that this case is not theoretical.
- **2026-09-14** the read path was never exercised - worth recording as a property of the
  window rather than as an incident, because it changes how the rest of this file should be
  read. Every session so far has been onboarding: importing an existing vault, restructuring it,
  and filing new concepts into it. Nothing in five sessions asked the bundle a question it might
  already have answered. So the absence of any `search` entry in this file is a gap in coverage
  and not a finding about `search`, and T4 cannot decide the command either way from what is
  here. The scheduling made this inevitable: T3's migration runs alongside T2's observation
  window by design, and a migration is all writes. Retrieval pressure only starts once the
  bundle is the thing being consulted rather than the thing being built.
- **2026-09-14** the work account - filing the issues above required `gh`, which was authed as
  an employer-issued account holding only `READ` on the target repository; creating an issue
  would have failed, or would have succeeded under the wrong identity had permissions differed.
  Checked first, switched to the personal account, filed, and switched back. The incident worth
  recording is not the switch but what this file would have done with it: the rules at the top
  say to name the artifacts and record the actual command, and following them literally would
  have written an employer-identifying account name into a public repository. The rule that
  needs stating, in `SKILL.md` and at the top of this file, is that an artifact is a path, a
  query or a command, and an identity is not one. Nothing currently says so, and the exposure is
  wider than an account name: the manifest itself now registers a bundle whose name and
  `publish` URL are an employer's, so any entry that pastes `fkb list` output, or quotes the
  manifest to make a point about bundle shapes, discloses it. Both of those are things the
  entries above genuinely wanted to do. Names of bundles and their URLs are as redactable as
  identities, and a journal kept in a public repository about a federation containing a private
  work bundle needs that said once, at the top, rather than remembered each time.

- **2026-09-15** verified - asked to add `verified: { by: human:<name>, at: ... }` to six concepts
  I had just authored in a private work bundle, naming two colleagues who had not yet confirmed
  anything; the confirmation was expected to arrive as a pull request approval on the very commit
  that carries the claim. `SKILL.md` says never to write `verified:` about my own work, and the
  bundle's own conventions say the same, so I wrote the fields as instructed, flagged in the reply
  that the attestations had not happened, and did not commit until told to. Three things this
  exposed. First, `verified.at` written ahead of the confirming act states a time before the act,
  which is false by construction; a plain date, or reading it from the history the way creation
  and revision dates already are, would not be. Second, the field is content-at-a-commit, so it
  cannot land after the review without the attestation living in a forge's review API instead of
  the bundle, which is the one place the format can carry it; a check pairing a changed
  `verified.by` with an approval from that same person is what would make the pairing evidence
  rather than convention. Third, and the one that outlives the forge question: nothing fails when
  a concept's body changes whilst `verified` stays put, so the field decays into decoration on its
  own. The rule as written tells an agent not to write the field and says nothing about what to do
  when a person instructs it to anyway, which is the case that actually came up.
  Both checks are candidates to ship from this repository rather than to be rebuilt per bundle:
  the staleness one as a pre-commit hook beside the linter, since it needs only the diff and the
  frontmatter, and the approval pairing as a reusable GitHub workflow or composite action, since
  it needs the forge's review API and a mapping from a person slug to an account. A bundle would
  then get both by referencing them, which is also what would keep the person-to-handle mapping
  in one place per bundle instead of one per check.

- **2026-09-15** the shell in the instructions - a user reported the skill failing under
  opencode on Windows. `SKILL.md` §Commands said "Paths are relative to this skill's own
  directory, not to the working directory you happen to be in. Run them from here", in a
  fence tagged `bash`, so an agent that follows it writes
  `cd ~/.agents/skills/fkb && uv run scripts/fkb list` - and in the shell that is default on
  that machine `&&` is not valid and `~` does not expand. The requirement was never real:
  `scripts/fkb` puts its own directory on `sys.path` itself, so `uv run <dir>/scripts/fkb
  list` has always worked from anywhere, and running `uv run scripts/fkb list` from
  `/tmp` confirmed it. The instruction recorded how the author happened to invoke the CLI and
  promoted that to a precondition the reader had to satisfy first, and the only way to satisfy
  it in one line is a shell sentence. Replaced with a `SKILLDIR/scripts/fkb` form in a `text`
  fence that says the working directory does not matter and not to chain two commands, and
  pinned by two tests under the `python_scripts` marker: one runs the CLI with `cwd` set to a
  directory unrelated to both the skill and the bundle, one reads the installed `SKILL.md` and
  fails on a `bash` fence, a `cd`, a `~` or an `&&` among the commands it prints. What let it
  through is that no test read `SKILL.md`: the CLI is exercised everywhere as an argument
  list, which is not how anybody meets it. The agent layer is the only one that reads the
  prose and it ran on one operating system, so it could only ever have caught half of what it
  is for; it now runs on both.

- **2026-09-15** a question is the end of the session - `test_a_cold_session_files_a_conformant_concept`
  gave an agent a fact to keep and a writable bundle holding only `index.md`, `log.md` and
  `fkb.yaml`. It read the manifest, chose the bundle correctly, and then answered "It has no
  directories and no concepts yet, so before I write: place this note at the bundle root (no
  new directory for a single page), and file it without tags since none exist yet? Or do you
  want a directory/tag setup to start?" - and wrote nothing. `opencode run` is
  non-interactive, so the question was the last thing that happened and the bundle stayed
  empty. Both choices it raised are ones §9.6 already answers by refusing to have an opinion,
  which means an empty bundle offers nothing to read and the skill says what to read rather
  than what to do when there is nothing there. The failure is not platform-specific and not
  new: it is red on `main` today on Linux, in the same test, with the same assertion. Nothing
  was done instead - the test is left failing rather than relaxed, because what it reports is
  a gap in the filing instructions and not a flaky harness. Worth pairing with the setup
  branch being written for T5, which already tells the agent that "get me started" is the
  decision made and not a question to ask back; the same instinct fires one step later, in
  filing, and is not yet answered there.
