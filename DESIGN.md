# DESIGN - federated knowledge

**Status:** settled direction, not yet implemented. This document is the **sole source of
truth** for the design. Change it here first; `README.md`, `DECISIONS.md` and the current
`skills/` tree describe an earlier architecture until they are rewritten to match.

**Date:** 2026-09-01

## 1. What we build

A federated, agent-agnostic, human-friendly system for capturing and sharing knowledge,
following the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
pattern.

- Each knowledge bundle is its own git repo, optionally published to GitHub Pages.
- Bundles sit at different privacy tiers: public, team, private, plus read-only upstreams.
- Content is [OKF v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format)
  markdown - plain files, edited directly in an editor, in Obsidian, or in the GitHub web
  UI.
- Agents read and write it as a first-class consumer, across harnesses.

We do not build a knowledge platform. OKF is a file format; this stays a thin layer over
git. We do not build a security mechanism - access control is git remote permissions and
the CI publish gate, and everything here is an agent guardrail that prevents accidents,
not attackers.

### Open questions

Detail in §9. None of them blocks the first task; [IMPLEMENTATION.md](IMPLEMENTATION.md)
says which task settles each, and answering earlier than that trades away what the work
would have told us.

| # | Question | Settled by |
| --- | --- | --- |
| 9.1 | How `fkb search` ranks once bundles outgrow lexical matching | T8, with `search` itself |
| 9.2 | The floor's exact content, and the config file's name | T1, renamed in T2 |
| 9.3 | Whether markdown raw sources become `references/` concepts or stay outside the bundle | T1 |
| 9.4 | How non-knowledge pages in a bundle satisfy OKF §11 | T1 |
| 9.5 | How a bundle lints standalone, without knowing it is federated | T6 |
| 9.6 | How knowledge is structured inside a bundle - directories, `tags`, publishing nav | T1, per bundle |
| 9.7 | Whether we may assume more than `uv` is installed | T4 |

§9.10 records what is settled.

## 2. Invariants

These bound every decision below. Each was paid for once already (appendix A).

1. **The knowledge file is the source.** Nothing generates it from a shadow copy. No ingest
   pipeline stands between an agent and the file it means to write.
2. **A skill may instruct an agent to run a deterministic command. A skill never instructs
   an agent to invoke another skill.** Prose to command works; prose to prose does not.
3. **Deterministic behaviour lives in the CLI, never in prose.** The skill body says
   `run fkb list`; it does not describe what the output looks like.
4. **Everything ships self-contained.** No cross-skill dependencies, no post-install
   configuration, no assumption that another package is present.
5. **Every command justifies itself** against "git or an editor already does this clearly".

## 3. Architecture

Three layers, each doing one thing.

| Layer | Carries | Loads |
| --- | --- | --- |
| **AGENTS.md block** (~5 lines) | that fkb exists here, and when to reach for it | always |
| **The `fkb` skill** | conventions, workflow, OKF reference, house style | on activation, then on demand |
| **The `fkb` CLI** | bundle resolution, lint, policy checks | on invocation |

The skill is the portable artifact. `~/.agents/skills/` is read natively by Codex, Cursor,
Gemini CLI, Zed and Goose; Claude Code reaches it through a symlink from
`~/.claude/skills/`. Every harness names its instruction file differently, so the block is
the harness-specific part.

The block exists for **activation**. The failure it prevents is an agent that never reaches
for the skill and writes a markdown file wherever it happens to be. It carries the two
triggers an agent does not infer: check fkb before web-searching, and file durable
knowledge when you learn it.

## 4. Bundles and the manifest

One file couples otherwise-independent repos: `$XDG_CONFIG_HOME/fkb/workspace.yaml`. Four
fields per bundle.

| field | question it answers | default |
| --- | --- | --- |
| `path` | where the bundle is checked out locally | (required) |
| `referenceable_by` | who may point *at* me | `[]` (no one) |
| `writable` | may an agent author into me here | `false` |
| `publish` | where my concepts are reachable from outside, if anywhere | `null` |

Both security-relevant defaults fail closed, so a new bundle discloses nothing until you
open it deliberately.

### `publish` is how one bundle links to another

Bundles do not know about each other, which makes a cross-bundle link the one thing neither
side can write on its own. A relative path is a fact about one disk and does not survive
either publication or a clone elsewhere, so the link has to be an absolute URL, and only
`fkb` can produce it: it is the sole component that sees both bundles at once.

So `publish` is not a note about hosting. It is **the function that turns a concept's local
path in bundle B into a URL that works from anywhere**, and it carries two things, because
a prefix alone underdetermines the answer:

```yaml
publish:
  url: https://ftschindler.github.io/knowledge/
  style: directory
```

`url` is a prefix, normalised to a trailing slash when read so the manifest cannot get that
half wrong. `style` names the transform applied to the path beneath it:

| `style` | `foo/bar.md` becomes | `foo/index.md` becomes | who publishes this way |
| --- | --- | --- | --- |
| `directory` | `foo/bar/` | `foo/` | MkDocs by default, Hugo, Docusaurus |
| `html` | `foo/bar.html` | `foo/index.html` | MkDocs with `use_directory_urls: false`, Sphinx |
| `raw` | `foo/bar.md` | `foo/index.md` | forge blob URLs, any plain file server |

The two keys nest so that `style` cannot exist without `url`: the invalid state is
unrepresentable rather than caught by a check. Absence of the whole key means the bundle has
no published home.

> The enum is closed, and lives in `fkb` rather than in the manifest as a template string.
> It is a list of *transforms* and not of tools, which is why it is three entries long and
> has been that shape for a decade; a generator we have not met is near-certain to be
> `directory`. A template would never need extending, but it puts a mini-language in a
> hand-edited file with no feedback, cannot express the `index.md` case without a second
> placeholder, and makes the reverse direction below a parsing problem instead of a suffix
> strip. Meeting a fourth URL shape is a commit, and wants a journal entry behind it like
> anything else here.

**`url` is a promise, not an observation.** Nothing fetches it, so it may be declared before
the site exists - which is what makes two unpublished bundles able to interlink: declare
where each *will* live, then link. The cost is that a wrong promise is baked silently into
every inbound link, and only an opt-in fetch ever catches it.

**Two refusals, both hard.** `fkb` will not invent a URL where it cannot produce a true one.
Citing a bundle that does not list the citer is a policy violation; citing a bundle with no
`publish` is a bundle with no published location. Different messages, because the fixes
differ, but neither degrades to a relative path.

**Prefixes must be mutually non-prefixing.** Lint reads links in the other direction - given
an absolute URL in a concept, which bundle is that? - and two bundles under one site root
make the question unanswerable. The manifest is checked for this when it is loaded.

**The reference rule.** A concept in bundle **A** may reference a concept in bundle **B**
iff `A = B` or `A ∈ B.referenceable_by`. `referenceable_by` is inbound-only, which is the
disclosure axis: it lists who may point at a bundle. Two bundles that may cite each other
list each other.

> Inbound allow-lists express unranked symmetric peers, which a ranked sensitivity lattice
> cannot, and reduce the leak check to one dictionary lookup.

We keep this policy in the manifest rather than in each repo, because `path` and `writable`
are properties of *this machine* and a bundle cannot usefully self-describe them. If bundles
are ever distributed across many independently-administered workspaces, move only
`referenceable_by` into the target bundle, since it is an inbound permission the target
owns.

### A worked manifest

```yaml
# $XDG_CONFIG_HOME/fkb/workspace.yaml
workspace_root: ~/.agents/knowledge   # relative bundle paths resolve under this

bundles:
  # Published foundation. Anyone may cite it.
  public:
    path: ./public/docs
    referenceable_by: "*"
    writable: true
    publish:
      url: https://example.com/kb/
      style: directory

  # Two unranked peers: each names the other. Symmetric, order-free. Neither is
  # published yet, and `team` has already declared where it will be, so `peer`
  # can link into it today.
  peer:
    path: ./peer/docs
    referenceable_by: [team]
    writable: true
  team:
    path: ./team/docs
    referenceable_by: [peer]
    writable: true
    publish:
      url: https://team.example/kb/
      style: directory

  # Sealed. Nothing may point at it, so its content cannot surface elsewhere,
  # and with no `publish` there is no URL to surface through either.
  private:
    path: ./private/docs
    referenceable_by: []
    writable: true

  # Someone else's bundle: read and cite freely, never author into. No deployed
  # site, so the prefix reaches into the forge and concepts keep their `.md`.
  upstream:
    path: /home/felix/src/their-kb/docs
    referenceable_by: "*"
    writable: false
    publish:
      url: https://github.com/them/their-kb/blob/main/docs/
      style: raw
```

An absolute `path` ignores `workspace_root` and stays where it is, which is how a checkout
that already lives somewhere gets adopted without moving. With no `workspace_root`, every
path must be absolute.

Both defaults are the cautious ones: omit `referenceable_by` and nothing may cite the
bundle; omit `writable` and no agent may author into it.

`peer` is the case worth reading twice. It may cite `team` and has nowhere to publish
itself, which is fine: `publish` describes how *others* reach a bundle, so a bundle needs
one to be linked *to* and needs nothing to link *out*. `private` shows the same asymmetry at
its limit - it may link into `public` while nothing can ever link back.

### Where policy is enforced

| Concern | Enforced by |
| --- | --- |
| Who can read or write a bundle | git remote permissions |
| What reaches the public site | CI publish gate, `mkdocs build --strict` |
| Accidental agent writes | `writable` in the manifest (guardrail) |
| Accidental cross-tier links | `referenceable_by` lint check (guardrail) |

The README says this plainly. The last two are guardrails, not access control: a direct
write bypasses any skill, so the enforceable guards are each bundle's own pre-commit hooks
and its publish gate. `fkb` makes the right thing easy; the bundle's hooks make the wrong
thing fail.

## 5. Content model

Three layers, from the LLM Wiki pattern.

### 5.1 The wiki

OKF concept documents, authored directly and edited directly.

**Reading:** the agent reads `index.md` first, then follows links into the concepts it
needs. `fkb search` (§7) covers the case where the right index is not obvious.

**Writing:** there is no `fkb ingest`. An agent has a write tool and knows markdown.

1. `fkb list` - which bundles exist, which are writable, what the tiers are
2. the agent writes the `.md` file directly
3. `fkb lint` - did that violate anything

`fkb` answers *where* and *is this legal*. It never touches a concept body, renders, or
hashes.

### 5.2 Assets

Images, screenshots and Excalidraw sketches - whether clipped or drawn by us - live
**beside the concept that references them**, named after it:

```text
principles/autofix-in-the-hook.md
principles/autofix-in-the-hook-prek-output-20260827.png
```

not in an `assets/` or `images/` subtree. A concept and its pictures move together and read
together, and a relative link survives Obsidian, MkDocs and the GitHub web UI unchanged.

> Neither Git LFS nor OKF argues for a separate directory. LFS matches on extension
> (`*.png filter=lfs`), not location. OKF §11 only ever treats `.md` files as concepts, so a
> `.png` beside a concept is invisible to conformance.

The cost is real and accepted: renaming or moving a concept means moving its assets too.

### 5.3 Raw sources

External artifacts you did not author and cannot change: clipped articles, PDFs,
transcripts, recordings.

**Non-markdown raw sources** (PDFs, images, audio) follow the asset rule above - beside the
concept that draws on them.

**Markdown raw sources** cannot, and this is a spec constraint rather than a preference:
OKF §3.1 makes every non-reserved `.md` in the tree a concept document requiring `type:`. A
clipped article dropped beside a concept becomes a concept. OKF §6.3 anticipates exactly
this and gives it a home:

> A `references/` subdirectory conventionally mirrors external material, run instructions,
> or code **as first-class concepts within the bundle**. […] It is a naming convention, not
> a requirement.

So the spec's answer is not to hide external material from the validator but to admit it as
a concept with its own `type` (`Source`, `Transcript`, `Article`). See §9.3, which is the
one part of this still open.

Whatever the location, two rules hold:

1. **The archive is not a pipeline stage.** You write the concept directly and archive the
   source alongside only when it is perishable. The archive is never an input an agent must
   manufacture before it is allowed to write.
2. **Provenance is a pointer, not a copy.** OKF links the layers natively through
   `sources: [{ id, resource, title, author, last_modified }]` and `resource:`. **A concept
   points at its source rather than shadowing it.** A stable public URL stores nothing and
   records `resource:`; a perishable or access-gated source gets archived, with
   `sources[].resource` pointing at the archived copy.

> Licensing does not choose a directory - it chooses whether to **publish**. Verbatim
> third-party content is the same obligation in `references/` as beside a concept, and the
> real decision is whether the publish gate emits it at all. Private bundles carry no such
> question.
>
> The ~100 opencode session transcripts currently in the private vault are legitimate raw
> sources under this reading, and are the concrete case §9.3 has to settle.

### 5.4 The schema

The AGENTS.md block and the skill. This is where "how we do it" lives, and it is the layer
we co-evolve.

#### The AGENTS.md block

It loads on every session, so it stays at roughly this length. Its only job is to make an
agent reach for the skill; everything else lives one hop away.

```markdown
## Knowledge bundles (fkb)

Durable knowledge — decisions, research, fixes worth keeping — lives in privacy-tiered
markdown bundles managed by the `fkb` skill. When the user says "the wiki", "my notes"
or "the team wiki", they mean these.

- Before searching the web, check the bundles.
- When something durable is learned, file it.
- Load the `fkb` skill for how; it carries the conventions and the commands.

If the `fkb` skill is not installed, skip this silently.
```

Three properties matter more than the wording. It names the trigger phrases, because an
agent will not guess that "my notes" means a bundle. It defers everything procedural to the
skill, so the two cannot drift. It fails silent, so a machine without fkb loses nothing.

## 6. The skill

**One skill.** Triggers differ - "what do we know about X", "note this down", "audit the
wiki" - and splitting sharpens the routing descriptions. We keep one anyway, because
`references/` is scoped to a single skill directory: three skills means duplicating the OKF
reference three times or symlinking it, and both drift. Split later if activation proves
unreliable; siblings would then call the CLI, never each other.

### 6.1 What goes where

> If it is a branch the agent takes, it belongs in `SKILL.md`. If it is a table the agent
> consults, it belongs in `references/`.

Progressive disclosure sets the economics: name and description load at startup, the body
loads on activation, `references/` loads only when a task reaches for it. The body stays
short and almost entirely control flow, well under 500 lines.

### 6.2 Layout

```text
~/.agents/skills/fkb/
├── SKILL.md                    # decisions / control flow
├── scripts/
│   ├── fkb                     # our CLI (PEP 723, uv)
│   ├── bundle_lint.py          # ours — conformance, floor, coverage (§9.5)
│   └── okf_validate.py         # vendored, unmodified (§8)
└── references/
    ├── SPEC.md                  # vendored verbatim OKF v0.2 (§8)
    ├── APACHE-2.0.txt           # vendored — licence for SPEC.md
    ├── MIT-okf-skills.txt       # vendored — licence for the validator and template
    ├── concept-template.md      # vendored, lightly adapted
    ├── getting-started.md       # ours — onboarding (§6.7)
    ├── bundle-infrastructure.md # ours — the shape a bundle grows into
    ├── house-style.md           # ours
    ├── federation.md            # ours
    ├── semantic-lint.md         # ours — the audit checklist (§6.5)
    └── agents-block.md          # ours — the block, and how to check for it (§5.4)
```

Three of those were not in the original list, and each is a lookup that would otherwise have
sat in the body. `semantic-lint.md` is the checklist §6.5 places in "`SKILL.md` prose": the
trigger stays in the body and the checklist moves here, because §6.1's rule is that a table
an agent consults belongs in `references/`. `agents-block.md` carries the §5.4 text plus the
instruction to look for it in whatever user-level file the *harness* loads, which is
knowledge the agent has and this repository cannot. `bundle-infrastructure.md` describes the
layers a bundle grows - hooks, conventions, a site, a publish gate - as a shape rather than
as files, and sends the reader to a working example instead of reproducing one.

> **That last one is a deliberate refusal to write something down.** Infrastructure is the
> fastest-rotting thing here: name a site generator and a hook revision and the page is wrong
> within a year while still reading as authoritative. Onboarding already clones a bundle that
> has all of it, so the durable half is the list of questions to read that checkout for, plus
> the one thing a scan cannot tell you - which of its files are about *its owner* rather than
> about being a bundle.

Shipping the CLI inside the skill as `scripts/` means one `npx skills add …` installs both,
and there is no separate step to forget. The manifest lives outside, in
`$XDG_CONFIG_HOME/fkb/`, because it is machine-local user data rather than code.

**Nothing installs anything.** Installation is a one-time human command. The skill's
contract is: present, use it; absent, stay quiet; present but broken, tell the human and
install nothing.

> A skill that installs runs at unpredictable moments during unrelated work.

### 6.3 Filing knowledge - the decision tree

This is the body's spine.

1. **What am I holding?**
   - an *external artifact* - a raw source, continue at 2
   - an *insight from this session*, such as a decision made or a principle extracted -
     **there is no raw source. Write the concept directly.**
2. **If external, is it perishable?** A stable public URL archives nothing and records
   `resource:`. A perishable or access-gated source gets archived, recorded in `sources[]`.
3. **Which bundle?** `fkb list`, then pick by sensitivity. In doubt, the most-private
   writable bundle.
4. **Write the file directly** with the normal write tool.
5. **Frontmatter:** the required floor inline; `references/concept-template.md` and
   `SPEC.md` §5 for the optional palette. Set `generated:`; never self-assert `verified:`
   (§6.4).
6. **Update `index.md`, append to `log.md`.**
7. **Run `fkb lint`.**

Seven steps, no lookups, no other skill invoked.

> Step 1's second branch is stated as an explicit prohibition rather than left as an
> omission - it is the one an ingest-shaped tool gets wrong.

### 6.4 Actors and trust

OKF §7 gives one convention for every identity field (`generated.by`, `verified[].by`):

| Shape | For | Spec's example |
| --- | --- | --- |
| `<producer>/<version>` | agents and tools | `reference_agent/gemini-2.5-pro` |
| `human:<id>` | a person | `human:ahormati` |
| `process:<id>` | an automated process | `process:finance-nightly` |

**Producer is the program that did the writing; version is the model it ran on.** The
spec's own example pairs a program (`reference_agent`) with a model (`gemini-2.5-pro`), so
ours pairs the harness with the model:

```yaml
generated: { by: opencode/claude-opus-5,  at: 2026-09-01T14:22:00Z }
verified:  { by: human:felix_schindler,   at: 2026-09-02T08:10:00Z }
```

| Situation | `by` | Not |
| --- | --- | --- |
| An agent in opencode wrote the concept | `opencode/claude-opus-5` | `fkb`, `claude`, `Sisyphus`, `opencode` |
| An agent in Codex wrote it | `codex/gpt-5.6-sol` | `codex/codex` |
| Felix wrote or reviewed it | `human:felix_schindler` | `human:felix`, `human:ftschindler`, `Human:…`, `human/…` |
| A scheduled job refreshed it | `process:wiki-nightly` | `process/wiki-nightly` |

**A person's `<id>` is their name, not an account handle.** A forge handle is scoped to one
forge and one tenant - an Enterprise Managed User is a different login from the same person's
personal account - so it identifies a login rather than a human, and the same author would
carry different ids in different bundles. `verified` exists to say *who* confirmed something,
and the trust tier it feeds (§5.3) is worthless if one person has three ids.

The form pays for itself twice over: it matches the filename of that person's own concept
(`people/felix_schindler.md`), so an actor resolves inside the bundle, by grep, with no forge
and no git. That holds in a bundle that was never a repository.

> **The skill is not an actor.** `fkb` is prose an agent reads; the agent is what acts.
> Naming the skill would record the same string no matter which harness or model produced
> the content, which is precisely the information the field exists to carry.

Two consequences worth stating in the skill body:

- `generated.by` is **required** whenever `generated` is present (OKF §5.2). Half a
  `generated` block is malformed.
- OKF §5.3 derives the trust tier from `verified` alone: absent ⇒ **unverified**,
  non-`human:` actors only ⇒ **machine-confirmed**, any `human:<id>` ⇒ **human-reviewed**. A
  near-miss such as `Human:felix` or `human/felix` silently downgrades a reviewed concept to
  machine-confirmed, which earns a dedicated lint check rather than a note in a guide.

### 6.5 Two lints, one of them code

| | Lives in | Checks |
| --- | --- | --- |
| **Deterministic** | `bundle_lint.py`, called by the CLI and by the standalone hook (§9.5) | OKF §11 conformance, **the bundle's declared floor**, actor shapes, index coverage, links resolve *as a warning*, `stale_after` passed, the reference rule |
| **Semantic** | `SKILL.md` prose | contradictions between pages, claims superseded by newer sources, orphans, concepts mentioned but lacking a page, gaps, **one subject tagged two ways** |

**A tag vocabulary splits semantically, so it is caught semantically.** One subject carried
by two spellings is a silent retrieval failure: searching either returns half the pages and
gives no sign the other half exists. The case that happened was `awiki` on four pages and
`agent-wiki` on three, and it is worth stating why it sits in the right-hand column. The two
strings are five edits apart and no normalisation of case, hyphens or plurals collides them,
because an abbreviation is lexically distant from what it abbreviates and identical in
meaning. Deterministic lint can enforce a closed set of tags; it cannot discover that two
strings outside any set denote one thing. Reading the tag list of §7's `resolve` output and
noticing that two entries name one subject is the operation §6.6 calls the payoff of the
whole pattern, and this is an instance of it.

> **A singleton-tag warning was specified here and then measured away.** The idea was that
> a tag used by exactly one concept is where typos and one-off inventions live, and it cost
> almost nothing. Running the finished `resolve` over the public bundle answered it: 29 of
> 76 tags are used once. A check that fires on 38% of a healthy bundle is not a signal, it
> is a second warning stream to learn to ignore, and the tail it would flag is the same tail
> `resolve` already prints for a reader who can tell an abbreviation from a typo. Recorded
> rather than dropped silently, because it looks like an obvious win until someone counts.

**A broken internal link is never an error.** OKF §6.1 requires consumers to tolerate one -
it "may simply represent not-yet-written knowledge" - so lint reports it and continues.

> **A bundle that publishes cannot carry one anyway.** `mkdocs build --strict` aborts on a
> link whose target is not among the built files, which is stricter than the spec demands.
> The warning is therefore what a bundle that does *not* publish gets instead, and the
> private bundle is exactly that case.

**Not-yet-written knowledge is a `status: draft` stub, not a dangling link.** A stub is a
real file carrying the floor and a one-line `description` saying what it will contain. The
link resolves, so the site builds; the gap appears in the index, in search and in
`rg 'status: draft'`; and what was an error state becomes a first-class one that semantic
lint can reason about. It costs six lines of frontmatter to promise something.

**The floor is what the bundle requires beyond OKF's `type`.** OKF deliberately makes
everything else optional and requires consumers to tolerate absence, so the floor is ours
to impose, not the spec's.

The floor holds **fields that are always knowable when the file is written**, not every
field we would like to see:

| Field | In the floor | Why |
| --- | --- | --- |
| `type` | yes | OKF §11 requires it anyway |
| `title`, `description` | yes | Always knowable; they feed `index.md` and search snippets (OKF §4.1) |
| `status` | yes | Always knowable; an input to deterministic lint |
| `generated` | yes | Always knowable, and the field that makes provenance real rather than encouraged |
| `verified` | **no** | Its absence *is* the signal |
| `stale_after` | no | Only meaningful for content that expires; a principle does not |
| `sources`, `resource` | no | Only when the concept derives from something |

> **`verified` cannot default to empty.** OKF §5.3 derives the trust tier from absence:
> no key ⇒ unverified. Writing `verified: null` says the same thing a second way, and the
> vendored validator rejects it outright - it warns unless the value is a `{by, at}` mapping
> or a list of them. Requiring the field would also push an agent toward self-asserting it,
> which §6.4 forbids. Absence is the encoding; leave it absent.

Enforcing an optional field converts a meaningful absence into noise. That is the limit on
"as rich as possible".

Two properties follow from bundles we do not control, and from a bundle needing to lint
itself without knowing it is federated:

- **The floor is per-bundle, not global.** A read-only upstream is held to OKF conformance
  and nothing more.
- **The bundle declares its own floor**, so its standalone pre-commit hook and `fkb lint`
  read one declaration and cannot disagree. Where that declaration lives is §9.2.

### 6.6 What `fkb lint` does across bundles

It iterates every bundle in the manifest and checks each one in place. It does not assume a
bundle carries a floor declaration or a pre-commit config - a bundle that declares nothing
is held to OKF conformance, which every bundle can meet.

**Findings in a non-writable bundle are reported as warnings, never errors.** An upstream we
cannot edit is not a failure state, and a lint that fails on what you cannot fix is a lint
you learn to ignore.

**The reference rule is checked by reading `publish` backwards.** A cross-bundle link is an
absolute URL in a concept body (§4), so lint matches each one against every bundle's
declared prefix, recovers the local path by undoing that bundle's `style`, and applies the
rule to the pair. This is the direction that makes §4's non-prefixing constraint load
bearing: two bundles under one site root leave a URL belonging to both, and a leak check
that cannot name the target cannot run.

It catches what `fkb url` cannot. `url` refuses a forbidden link at the moment an agent asks
for one, which covers links this federation wrote; lint covers the rest - a link pasted by
hand, one that predates the policy, and one that became a violation because
`referenceable_by` was tightened afterwards. The same rule, at the two points where it can
be broken.

Semantic lint is the operation a retrieval system structurally cannot perform, and it is
the payoff of the whole pattern rather than a formality. It is also the second reason the
skill exists.

`status: deprecated` and `stale_after` are the *inputs* to deterministic lint. That is why
the optional OKF fields earn their keep: without them, lint has nothing to check.

### 6.7 The skill explains itself

Someone runs `npx skills add …`, opens a fresh session and asks "what is this, and how do I
start?". That question must be answerable from the skill alone, with no README, no web page
and no prior context. A skill that needs documentation elsewhere has failed the one job that
distinguishes it from a library.

**The user story, from the previous README.** Someone wants their agent to read from and
write into any combination of:

1. bundles that live in remote git repos, readable or writable;
2. bundles already checked out somewhere on disk, possibly without realising they are
   bundles;
3. bundles that do not exist yet, to share or to keep private.

Those three are how a bundle arrives, and they map onto the setup commands (§7).

**What the skill answers.** `SKILL.md` carries a short "new here?" branch that explains what
a bundle is, checks whether a workspace exists, and routes to the right first step.
`references/getting-started.md` carries the long form: the three arrival paths worked
through, what each manifest field means, and what to do first when nothing is configured.

> The split follows §6.1. "Do you have a workspace yet?" is a branch and belongs in the
> body. "Here is each arrival path in full" is a lookup and belongs in the reference.

**The acceptance test is behavioural**, and worth writing down because it is easy to fake:
a session with no prior context, given only the question, produces an accurate explanation
and a first command that works. Not a summary of the design - a next step the person can
run.

## 7. The CLI

Six commands, and we stay suspicious of the seventh. Single-file PEP 723 Python, run through
`uv`.

```text
fkb list                    # bundles, paths, tiers, publish URLs
fkb search <query>          # ripgrep across bundles, bundle-qualified hits
fkb lint [bundle]           # vendored OKF validator plus the bundle's floor
fkb resolve <bundle>        # one bundle as JSON: policy plus observed vocabulary
fkb url <bundle> <path> --from <bundle>   # one concept's cross-bundle URL, or a refusal
fkb init                    # create the workspace manifest — once per machine
fkb add <what>              # bring a bundle into the workspace — once per bundle
```

`can-reference` folds into `lint`, being a check rather than a workflow. Clone, pull, commit
and file creation get no command, since git and the editor already do them clearly.

### `fkb url` is the whole of cross-bundle linking

An agent filing into **A**, told to cite a concept in **B**, needs one call that returns a
string it can paste. That is this command, and the reason it is a command rather than a
field in `resolve`'s JSON is that the alternative hands every caller the prefix and the
style and asks it to do the concatenation itself. Two callers doing that is two readings of
one field, which is the failure this design already had once.

It applies §4's transform, and it refuses rather than approximating:

| situation | what happens |
| --- | --- |
| `A ∈ B.referenceable_by`, `B` publishes | the URL, on stdout, nothing else |
| `A ∉ B.referenceable_by` | refuses: a policy violation, named as one |
| `B` declares no `publish` | refuses: `B` has no published location |
| `path` names no file in `B` | refuses: linking at a concept that is not there |

Refusal is the point of the command as much as the URL is. An agent that gets a string back
has been told the link is permitted, so the check and the formatting cannot come apart - and
a forbidden link fails at the moment it is asked for, rather than surviving in a file until
lint sees it.

`--from` is required and has no default. The reference rule is a question about a pair of
bundles, and the citing half is the one the command cannot see: an agent knows which bundle
it is filing into, and nothing on disk does. Defaulting it would mean answering a policy
question by assumption, which is the failure this whole command exists to prevent.

> The last row is cheap here and impossible later. `fkb` has the target bundle on disk, so
> it can confirm the concept exists before it is cited; once the link is a URL in a committed
> file, only fetching the site can tell you the same thing.

### Setup is two steps, because they answer different questions

`fkb init` creates the workspace: the manifest file, with `workspace_root` and no bundles.
It runs once per machine and asks nothing about knowledge.

`fkb add` brings one bundle in, and covers the three ways a bundle arrives (§6.7):

| Arrival | What `add` does |
| --- | --- |
| A remote git repo | Clone it under `workspace_root`, find the bundle root inside it, register it |
| An existing local checkout | Register the path as-is, absolute, moving nothing |
| A bundle that does not exist yet | Scaffold a minimal conformant bundle, register it writable and sealed |

Each asks for the policy it cannot infer - `referenceable_by`, `writable`, `publish` - and
ends by printing the manifest line it wrote, so what entered the federation is visible
before it is used.

> `publish` is the one it must ask carefully, because both halves have a plausible wrong
> answer: a repo's landing page rather than the prefix its concepts hang under, and a
> `style` guessed from the fact that the checkout contains an `mkdocs.yml`. Ask for the URL
> of one concept the person can already open, and derive both halves from it against the
> local path - that turns two abstract questions into one the person can answer by pasting
> from a browser, and it is the only point in the lifecycle where a promise can be checked
> against something real.
>
> Finding the bundle root matters more than it sounds. A repo is often infrastructure at the
> top with the bundle in `docs/`, so `add` inspects the checkout for the shallowest
> `index.md` and asks when the answer is ambiguous rather than guessing.

### `fkb resolve` reports what a bundle *does*, not only what it declares

Alongside the manifest fields, `resolve` returns the vocabulary in use: the `tags` and
`type` values that appear across the bundle, **each with the number of concepts carrying
it**, and its top-level directories. The skill already calls `resolve` before writing (§6.3
step 3), so choosing a tag that matches its neighbours costs no extra call.

The counts are not decoration. A bare list of tags says only that a string exists; a list
with frequencies is the difference between forty equal-looking options and a shape in which
`awiki: 4` and `agent-wiki: 3`, sitting under `linux: 22`, read as one subject spelled two
ways. Splits live in the tail, and a tail is only visible once something is counted.

This half of house style is **derived**, which is why it is the half in the CLI: it cannot
drift, needs no declaration, and works on read-only upstreams that will never adopt our
conventions. The *declared* half - casing rules, prohibitions, intent - lives in the bundle
beside its floor declaration, which §9.2's `conventions:` key points at, never in the
manifest (§9.6).

**Vocabulary is derived per bundle, and is never declared.** The alternative is a vocabulary
file with a hook that fails on any tag outside it, which is a stronger check and is what the
tool this design replaces had. We decline it for three reasons: it is a second declaration
free to drift from the files it describes, which is the failure the derived half exists to
avoid; it cannot apply to a read-only upstream, so it would hold for half the federation;
and a bundle that declares none must still be filable into, which makes it optional, and an
optional gate is not a gate. What is knowingly given up is recorded in §9.10 rather than
left to be rediscovered.

**Vocabulary is also per bundle rather than federation-wide.** The same subject spelled two
ways in two bundles is the same failure one level up, and there is no evidence of it: the
journal raises it as a question and records no incident. It degrades exactly one thing,
federated search, which does not exist yet and is itself waiting on evidence. Coupling
independent repos to a shared vocabulary is also the one piece of coupling that would make
an upstream non-compliant by construction. It moves to T8 with `search`.

The scan is the one `lint` already performs over frontmatter.

### `fkb search` is in scope, and it is not a search engine

**What it adds over plain `rg` is the bundle set, not the ranking.** It knows which bundles
exist and where they are checked out, and it emits each hit qualified by bundle and, where
`publish` is set, as a real URL. An agent that greps a directory it happened to guess gets
neither. That value holds at 40 concepts and at 4000, so we build it now.

The engine underneath stays deliberately dull: ripgrep over concept bodies and frontmatter,
deterministic and dependency-free. Ranking is §9.1.

> We do not dispatch to a better engine when one happens to be installed. Identical queries
> would return different results on different machines, and a search whose behaviour depends
> on what a laptop has lying around is not one you can reason about. Adopting a heavier
> engine is an explicit, recorded choice.

`fkb lint` shells out to the vendored `okf_validate.py` for OKF conformance and adds its own
passes: the bundle's declared floor, actor shapes, the reference rule, no-copied-state. It
does not reimplement conformance checking.

## 8. Vendoring from okf-skills

[scaccogatto/okf-skills](https://github.com/scaccogatto/okf-skills) is MIT-licensed, 353
stars, actively maintained, and independently arrived at this architecture: a 151-line
decision-flow SKILL.md, a 1012-line verbatim spec in `reference/`, templates, and
deterministic Python in `scripts/`. It is a personal project, not an Anthropic one, despite
its "for Claude Code" tagline.

> Their ADR `self-contained-skills.md` states invariant 4 in their own words: "Each skill
> ships its script inside its own directory… No absolute paths, no post-install
> configuration."

### What we take

| Artifact | Size | Why |
| --- | --- | --- |
| `reference/SPEC.md` | 1012 lines | The verbatim spec. Our current excerpt is 43 lines - enough to check conformance, not enough to author against. Loads on demand only. |
| `templates/concept.md` | 38 lines | Every optional field present and commented, which makes filling them the default rather than an act of recall. |
| Actor convention (§7) | ~10 lines | See §6.4. |
| `okf_validate.py` | 571 lines | PEP 723 plus pyyaml, `--json`, `--strict`, `--max-warnings N`. We do not write an OKF linter. |

### What we skip

- **Attested Computations (OKF §10)** - sanctioned SQL and metric concepts for data
  catalogues. It rides along inertly inside `SPEC.md`; the house guide leaves it out.
- **MCP server, visualizer, GitHub Action, stop hooks, `backfill`** - ~1400 LOC of
  Claude Code plugin scaffolding. Our publishing stack renders and gates already.
- **`agents/` subagents** - harness-specific.
- **`--migrate`** (v0.1 to v0.2) - we have no v0.1 content.
- **`.okf/` as the default bundle root** - our MkDocs layout owns `docs/`.

### Mechanics

Every vendored file carries a provenance header naming its upstream commit, which makes a
later re-pull a diff:

```text
Vendored verbatim from the Open Knowledge Format v0.2 specification.
Source:  https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
Commit:  ad30107c31c06aec8a7d5636e0d1058118604e6f
License: Apache-2.0 (c) Google LLC — included verbatim under its terms.
```

| Vendored file | Upstream | Pin | Licence text |
| --- | --- | --- | --- |
| `references/SPEC.md` | `GoogleCloudPlatform/open-knowledge-format` | `ad30107` | `references/APACHE-2.0.txt` |
| `scripts/okf_validate.py` | `scaccogatto/okf-skills` | `d8393f3` | `references/MIT-okf-skills.txt` |
| `references/concept-template.md` | `scaccogatto/okf-skills` | `d8393f3` | `references/MIT-okf-skills.txt` |

Both licence texts sit in `references/`, beside what they cover, because the skill is
installed standalone (§6.2) and a copy that leaves this repository has to carry its own
notices.

`concept-template.md` is adapted rather than verbatim: it drops `verified:` so the template
cannot invite a self-assertion (§6.5), carries the actor spelling of §6.4, and marks which
fields are the floor.

Timestamps follow the validator rather than the spec: `stale_after`,
`sources[].last_modified` and `usage_window` are written as `YYYY-MM-DD` dates. The
canonical spec makes every timestamp-valued key an ISO 8601 datetime, but the vendored
validator predates that and rejects the datetime form under `--strict`. All three fields
sit outside the floor (§6.5), so what the simplification costs is day precision on
staleness.

Two adaptations are required:

1. **Replace `${CLAUDE_SKILL_DIR}`.** It appears in every invocation line, and Codex,
   Gemini, Zed and Cursor do not set it. Cross-harness portability is why we use a skill at
   all.
2. **Vendor the validator unmodified.** House rules live in `fkb`, which calls it. Editing
   their file turns every future re-pull into a merge.

> We reject two alternatives. Depending on `okf-skills` reproduces the dependency breakage
> in appendix A. A git submodule pins versions but adds clone friction, and agents handle
> submodules badly.

## 9. Open decisions

### 9.1 Ranking, once `rg` stops being enough

`fkb search` ships ripgrep-backed (§7). The open part is what replaces the engine when
lexical matching stops finding things - not whether the command exists.

Karpathy reports index-first navigation working "surprisingly well at moderate scale (~100
sources, ~hundreds of pages)". Two days of capture produced ~40 concepts, so team-wide
rollout crosses that band quickly and the question is when, not if.

[qmd](https://github.com/tobi/qmd) is the named candidate: local hybrid BM25 and vector
search over markdown, with both a CLI and an MCP server. It is also heavy - an index to
build, keep fresh, and reason about per bundle.

**Revisit when** a query an agent should have answered from the bundles gets answered from
the web instead. Record the query when it happens; a handful of real misses is what should
justify an index, not a projection.

### 9.2 Where a bundle declares its floor - `fkb.yaml` at the bundle root

**Settled: a small YAML file, not the bundle-root `index.md`.** The vendored validator
warns on any root-index key outside `okf_version` and its own `upkeep`:

```python
extra = set(meta) - {"okf_version", "upkeep"}
# → warn "§12 root index.md frontmatter may only carry `okf_version`"
```

Putting our floor there means our own linter warning about our own config on every run, and
silencing it would mean editing the vendored file (§8). A YAML file also parses without a
markdown-frontmatter reader, which the standalone hook (§9.5) wants.

The file is `fkb.yaml` at the bundle root. It carries a flat `required:` list of the five
fields §6.5 argues for - `type`, `title`, `description`, `status`, `generated` - and an
optional `conventions:` path, below. `tags` is deliberately absent from `required:`, which
keeps §9.6's question open: add one line to require it, the day the vocabulary is decided.

**That list is the whole of what a bundle demands beyond the format's own hard rules.** The
standalone hook reads this file and nothing else, so a field it does not name is reported
and never enforced (§9.5). The file is therefore the bundle's declaration and the hook's
configuration at once, which is why the hook takes it as an explicit argument rather than
discovering it.

#### Why not `okf-floor.yaml`

It was called that through T1, and the name was wrong twice over.

**`okf-` claims the wrong provenance.** The specification does not define this file:
`grep -n floor references/SPEC.md` returns nothing, and the paragraph above says plainly
that the floor is ours. The prefix invites the inference that any OKF bundle carries one,
and a third-party OKF bundle registered in this workspace carries none at all. An agent
reasoning from the name reasons correctly and concludes something false.

**`floor` names one of the file's two jobs.** It already holds a declaration *and* a hook
configuration, and with `conventions:` it holds a pointer as well. A name naming the first
of three stops describing the file the moment it grows, which is the state it was already
in.

The name that is left has to answer: who requires it to be *this* string? Not the bundle,
and not the hook, which is handed an explicit path and would accept any filename. Only
`fkb` does, because only `fkb` discovers the file rather than being told where it is. So
contents and filename have different owners, and that is ordinary rather than awkward:

| | owned by | meaningful without `fkb`? |
| --- | --- | --- |
| contents - `required:`, `conventions:` | the bundle | yes, the hook enforces them standalone |
| filename and location | `fkb`'s discovery contract | no, only within a federation |

`.editorconfig` and `package.json` hold project-owned content under an ecosystem-owned
filename and nobody finds them mis-named. Naming the file for the tool that has to find it
is the honest form, so `fkb.yaml` it is, and the name is a federation-level decision rather
than a per-bundle one.

**What the name does not buy.** A bundle is not required to adopt it. The hook goes on
taking an explicit path (§9.5), so a bundle may call the file anything, pin the hook, and
be fully checked with no `fkb` installed anywhere. What the canonical name buys is
*discovery*: `fkb lint` finds the file by convention because it has the manifest and does
not need telling. Adopting the filename is how a bundle opts into being found, and the cost
sits there rather than on the bundle that never federates.

#### `conventions:` - where the bundle's house rules live

**Settled: one optional key holding a path to the bundle's house rules.**

```yaml
required: [type, title, description, status, generated]
conventions: ../about/editing_conventions.md
```

The floor says what a concept must *carry*. It says nothing about how a concept is
*written*, and §9.6 records what that costs: an agent reads the floor, the directories and
the index, which is the bundle's schema and none of its voice. The rules exist in every
bundle that has been worked in; they are simply in a different place each time. Across the
four bundles in this workspace they sit at `docs/about/editing_conventions.md`, at the
repository root beside `AGENTS.md`, in an `about/` directory outside the OKF root entirely,
and nowhere at all.

So the skill cannot carry a path, and each bundle must state its own. The value is resolved
relative to the file that declares it and **may escape the bundle root**, which is the point:
§9.6 notes that the public bundle deliberately keeps its conventions outside the bundle,
where the people editing the site can find them, and that a tool given only the manifest's
`path` therefore cannot see the file. A pointer inside the bundle to a file outside it costs
no second copy, no restructuring, and no drift, and it is strictly cheaper than the three
options §9.6 had.

**Declaration, not enforcement.** The value is prose for an agent to read. Nothing parses
it, and `lint` checks only that a declared path resolves, because a pointer to a file that
does not exist is a defect the bundle can fix and a silent one otherwise.

**Everything degrades, and absence is never an error.** The three rows are all present in
this workspace today, and the third must stay filable:

| the bundle has | the skill does |
| --- | --- |
| `fkb.yaml` with `conventions:` | read it, then two concepts from the target directory |
| `fkb.yaml`, no `conventions:` | derive the vocabulary (§9.6), read two concepts |
| no `fkb.yaml` at all | conformance only (§6.6), derive, read two concepts |

**Not in the manifest, for the same reason as house style.** A bundle must be
self-describing to someone who has never heard of the federation (§9.5). A bundle whose
conventions are locatable only through one machine's manifest is not, and a manifest
pointer would be a second answer to a question the bundle already answers, free to be wrong
the moment the bundle is edited elsewhere.

### 9.3 Markdown raw sources live beside the bundle, not inside it

**Settled: `raw/` sits at the repository root, next to `docs/` and outside the bundle.**
Nothing in it is a concept, nothing in it is published, and the validator never sees it.

OKF §6.3 sanctions `references/` as the home for mirrored external material, as first-class
concepts, and that option was available. It was declined for two reasons. Raw sources would
appear in the index, in search and on the published site; and it blurs Karpathy's boundary,
where raw sources are the thing the wiki is *distilled from* rather than part of it.

The cost the spec-aligned option would have avoided is real and accepted: the archive sits
somewhere a bundle `path` does not reach, so federation tooling cannot see it.

This is one instance of a general shape. **The bundle root holds concepts and nothing else;
everything else is a sibling directory at the repository root.** `about/` is the other
instance, holding pages that describe the site (§9.4). The two differ only in whether they
are published: `about/` is, through the build hook; `raw/` is not, by never being added.

> The task list frames this as a decision for the first migration, on the grounds that
> "~100 transcripts need a home". That count came from the previous architecture and does
> not survive inspection: the public wiki holds 65 `raw/` files, which are shadows of
> published concepts that the migration deletes, and an empty `sessions/` directory. What
> the archive will actually contain is worth establishing before moving anything.

### 9.4 Non-knowledge pages sit outside the bundle root

**Settled: the bundle root is `docs/`, it holds concepts only, and pages describing the site
live in `about/` at the repository root.** OKF §3.1 is absolute - every non-reserved `.md`
is a concept - so a page carrying only `title:` cannot live inside the bundle, and a
skip-list is not available to us.

Three answers were on the table: accept such pages as concepts with `type: Document`; move
them above the bundle root; or narrow the bundle root to a subdirectory of `docs/`. The
second is what we took, inverted - rather than burying the knowledge deeper, the site pages
were lifted out.

That inversion is what keeps the published site readable. `docs/` is simultaneously the
bundle root and the MkDocs `docs_dir`, so every concept sits at a top-level URL and the
knowledge directories appear in the navigation as siblings of `about/`, at one level rather
than nested under a container.

A build hook of about twenty lines reconciles the two: it publishes `about/` from outside
`docs_dir`, and moves the bundle's own `index.md` off the site root so a landing page can
take it. No file is copied or generated - only the mapping from file to URL changes, and
MkDocs rewrites relative links through the same mapping, so nothing needs editing when the
index moves.

> A skip-list is not an option. okf-skills is explicit that one "would put the checker out
> of conformance", and vendoring their validator means inheriting that stance.

### 9.5 How a bundle lints standalone

**Settled: this repository publishes `pre-commit` hooks, and a bundle pins them by
revision.** A bundle is a normal git repo that does not know it belongs to a federation, so
its own hooks enforce OKF conformance and its floor without `fkb` present. The federation
layer then adds only the checks that need the manifest: the reference rule and cross-bundle
links.

`skills/fkb/scripts/bundle_lint.py` is the single implementation, and `fkb lint` calls the
same file rather than a copy of it. Two hook ids differ only in blocking policy:

| Hook | Blocks on | For |
| --- | --- | --- |
| `okf-concepts` | conformance and floor findings **in the files being committed** | every commit |
| `okf-bundle` | any finding anywhere, plus index coverage | CI |

**Blocking scope is what makes a whole-bundle check bearable per commit.** The vendored
validator only takes a bundle directory, so a genuinely per-file check would mean writing a
second conformance implementation, which §8 forbids. Instead the whole bundle is checked and
only findings in the author's own files fail. A half-finished concept elsewhere in the tree
never blocks an unrelated commit - the failure mode that teaches people to pass
`--no-verify`.

The floor declaration is passed explicitly as `--floor`, which makes it this hook's config
file as well as the bundle's declaration (§9.2). Omitted, the floor check does not run and
the bundle is held to conformance alone (§6.6); named but missing, it is an error, so a typo
cannot silently disable it. `fkb lint` finds the same file by convention at the bundle root,
because it has the manifest and does not need telling.

### 9.6 How knowledge is structured inside a bundle

*Deferred by agreement; recorded so it is not rediscovered.*

Nothing in this design dictates a bundle's internal shape, and OKF deliberately declines to
either:

> The directory structure is independent of the domain: producers organize concepts however
> makes sense for the knowledge being captured. (§3)

OKF gives exactly one classification key, `tags` - "a YAML list of short strings for
cross-cutting categorization" (§4.1) - and no file format for aggregating by it: "a consumer
that wants a tag-browsing view can synthesize one at consumption time by scanning
frontmatter" (§3.1). So there are two axes, directories and `tags`, and no third.

awiki introduced a third, `topic:`, whose value duplicated the top-level directory
(`topic: principles` inside `principles/`). That is copied state under our own no-copied-
state rule: the path already carries it, and the two can drift. **Drop `topic:` during
migration.**

The live tension is that top-level directories carry publishing meaning - nav sections, URL
prefixes - which pulls toward deciding them up front, while structure-emerges-over-time
pulls the other way. Both existing principles in the public bundle,
`split-orthogonal-classification-axes-across-folders-and-tags` and
`categorize-by-what-content-is-not-why-you-made-it`, already bear on this.

**This is per-bundle house style, not federation policy**, so it can differ between bundles
and does not belong in `fkb`. Pick it up when the first bundle's layout is fixed.

#### How an agent learns a bundle's style

Distinct styles across bundles create a real cost: the skill must decide *where* to write
(§6.3 step 3) and then *how* to write for that bundle. Three answers, ranked.

1. **Converge the bundles we own on one house style.** The cheapest fix by a distance.
   Better discovery tooling makes ten vocabularies cheaper to endure; one vocabulary makes
   the problem absent. Discovery then only matters for upstreams we do not control.
2. **Derive the rest.** `fkb resolve` reports the tags, types and top-level directories a
   bundle actually uses (§7). Derived facts cannot drift, need no declaration, and work on
   an upstream that will never adopt our conventions - which is exactly the case a
   declaration cannot reach.
3. **Declare what derivation cannot see** - casing rules, prohibitions, intent - in the
   bundle, pointed at by `conventions:` in its `fkb.yaml` (§9.2). One key, one answer, and
   the page may live wherever the bundle already keeps it.

> **Not in the manifest.** §4 admits machine-local facts and federation policy, and house
> style is neither. It belongs to the bundle, must travel with the repo, and must work when
> nobody knows the federation exists (§9.5). A manifest pointer would be a second home for
> something the bundle owns, drifting the moment the bundle is edited on another machine.

**Where the first bundle actually put it, and how that is resolved.** Option 3 says
"beside its floor declaration", which means inside the bundle. `ftschindler/knowledge` put
its house style in `about/editing_conventions.md` instead, outside the bundle, because the
rules are read by people editing the site as much as by anything else and a second copy
would drift.

That is defensible and it cost something specific: the manifest's `path` points at the
bundle root, so a tool given only that path could not see the file. It travelled with the
repository but not with the bundle.

**Settled by `conventions:` in §9.2**, which is a fourth option none of the three above
reached: the bundle declares *where* its rules are, and the path may escape the bundle
root. The page stays where humans edit it, no copy is made, and the skill dereferences a
pointer instead of guessing a path. This matters more than one bundle's layout, because
across the four bundles in this workspace the file sits in four different places and one of
them does not exist, so any hardcoded path in the skill is right once and wrong three
times.

What remains for [T5](IMPLEMENTATION.md#t5---finish-the-skill) is narrower than it was: the
skill ships a `references/house-style.md` and must not restate what a bundle already says.
The split to draw there is that the skill teaches what is true of writing concepts in
general, and `conventions:` answers what is true of writing them *here*.

### 9.7 What we may assume is installed

**`uv` is assumed, and by a bundle as well as by us.** The standalone hook (§9.5) is a PEP
723 script that resolves its own dependencies through it, so a bundle that pins the hook
inherits the assumption. That is a wider claim than this section originally made, and it was
taken deliberately: the alternative, packaging the checker so `pre-commit` builds its own
environment, buys a bundle nothing it does not already have, since the skill needs `uv`
regardless.

Whether `fkb search` may additionally assume `ripgrep`, or must scan in pure Python, is
still open.

Pure Python keeps the dependency floor at `uv` alone and stays comfortably fast at the scale
of §9.1. Shipping `rg` as a conditional fast path reintroduces the machine-dependence §7
rejects, unless results are provably identical.

Largely an implementation question, recorded here because it bounds what §7 can promise.

**A shell is not assumed, and neither is an operating system.** `uv` is the floor and it is
the whole floor: everything this repository ships has to work on Linux, macOS and Windows,
because a skill is installed onto whatever machine the person has and a bundle pins the hook
from whatever machine its owner has. Four rules follow, and each of them is a mistake already
made.

- **What the skill prints is a command, not a shell sentence.** `SKILL.md` is read by an
  agent that types what it says into a shell nobody here chose. So: one command per line, no
  `cd`, no `&&`, no `~`, no `$(...)`, and no fence tagged with a shell. A command that needs
  a working directory is a command with a precondition, and the only way to write that
  precondition down is in somebody's shell syntax. The CLI therefore works from any
  directory, and paths into the skill are given in full.
- **The tooling is Python where it would otherwise be shell.** A `$(shell ...)` in a Makefile
  or a `bash -c` in a hook makes `make` and a POSIX shell prerequisites of running the tests,
  which is a thing to discover rather than to assume. `make` stays an optional convenience by
  being a thin wrapper over commands that run without it.
- **No symlinks in the tree.** Git stores one as a blob holding the target path, and a clone
  on Windows writes that path out as an ordinary file. Nothing fails loudly; a link becomes a
  one-line document whose content is a relative path, and every reader downstream reads that
  string as the document.
- **Encoding and line endings are named, never inherited.** Text is read and written as
  UTF-8 explicitly, because the default is the machine's locale. Line endings are LF by
  `.gitattributes`.

The cost is that these are invisible from the machine that breaks them: each one looks
correct on Linux and fails somewhere else, so none of them can be left to review. Every test
layer therefore runs on both Linux and Windows, including the one that drives a real agent -
which is the only layer that reads `SKILL.md`, and so the only one that can catch an
instruction that parses in one shell and not another.

### 9.8 Index files are authored, not generated

**Settled: `fkb` never writes an index.** OKF §8 says an entry SHOULD carry the description
from the linked concept's frontmatter, which reads like an invitation to generate the file.
The reference bundle declines it, and the reason is instructive.
[stjbrown/agent-knowledge](https://github.com/stjbrown/agent-knowledge) truncates one
description, compresses a second to a fragment and rewrites a third, because an index entry
is read while scanning a list and a `description` is written to stand alone. Its index also
carries a statement of the bundle's purpose, a blurb under each section heading, and an order
that follows how the ideas build rather than the alphabet.

None of that is recoverable from frontmatter. A generator would not bend §7's promise so much
as produce a worse file, so the SHOULD is best read as guidance about *what an entry is
about*, not an instruction to copy a string (appendix B).

What deterministic lint may do instead is check **coverage rather than wording**: every
concept reachable from some index, every index entry resolving to a file. That catches the
failure worth catching - a concept filed and never linked - while touching no prose, so §7's
promise and invariant 1 both hold.

**Still open: whether an index sits in every directory or only at the bundle root.** OKF §8
allows one anywhere and the reference bundle puts one in each folder, which is progressive
disclosure working as intended. Ours has no folders yet. **Decide during the first
migration**, when there are directories to disclose.

### 9.9 Log entries are prose, and carry no links

**Settled: an entry in `log.md` names a concept in plain text; it never links to one.**

OKF §9's own example does the opposite, linking each entry at the concept it reports:

```markdown
* **Creation**: Established the [Dataplex Playbook](/playbooks/dataplex.md).
```

That works for as long as nothing is ever deleted or moved. `log.md` is the one file in a
bundle that is **append-only by nature**: an entry records that something happened on a
date, and that remains true after the concept it mentions is renamed, moved to another
directory, promoted to another bundle or dropped. A link, however, does not remain true, and
there are only bad ways to react to that. Rewriting the old entry falsifies the record.
Deleting it loses the history. Leaving it dangling breaks a strict site build, and does so
from a line nobody is editing.

Every other file in a bundle links freely, because every other file describes the present
tense. `index.md` must link, and its links must resolve, which is exactly why a deleted
concept has to be removed from the index and *not* from the log. The two reserved files have
opposite obligations, and that is not obvious enough to leave implicit.

The cost is real and small: a reader of the log cannot click through. They can search, and
the entry names the title, so a title given in full is worth more here than in a file where
a link would carry the reader anyway. This is a deviation from §9's example rather than from
its prose, which requires only date-grouped entries in ISO form (appendix B).

Two consequences for the tooling:

- `check_log` currently validates the absence of frontmatter and the date headings. It should
  also **warn on a markdown link in a log entry**, since this is a rule an author breaks by
  doing the obvious thing, and the breakage surfaces later in an unrelated commit.
- The rule should hold for **historical** entries too. An entry written before this was
  settled and pointing at a concept since removed is degraded to plain text, not deleted.

> A second point about `log.md`, for the skill rather than the design: appending to it is a
> find-or-create edit, not a blind append. The newest day goes first, so the agent has to
> locate today's `## YYYY-MM-DD` heading or insert one at the top. It is the only step of
> §6.3 that is not a plain write, and it needs saying in the skill body. Ordering has already
> been got wrong once in a real bundle, in the direction the file's existing content
> suggested rather than the direction the rule requires, so the skill saying it is not enough
> on its own: `check_log` should also verify that the date headings descend.

### 9.10 Settled

- **Canonical OKF home** is `GoogleCloudPlatform/open-knowledge-format`. The
  `knowledge-catalog` path in the okf-skills header is stale; pin from the former.
- **Claude Code discovery** is not our problem - no Claude Code in use here. If it ever is,
  a `~/.claude/skills/fkb` symlink covers it.
- **Assets live beside their concept** (§5.2).
- **The floor declaration is a YAML file**, not the bundle-root `index.md` (§9.2).
- **`verified` is never required and never nulled** - absence is how OKF encodes
  unverified (§6.5).
- **Indexes are authored, never generated by `fkb`**; deterministic lint may check that
  every concept is covered, never how an entry is worded (§9.8).
- **Log entries are prose with no links**, because `log.md` is append-only and its subjects
  move (§9.9).
- **A bundle lints itself through pinned `pre-commit` hooks** published from this
  repository, wrapping the one implementation `fkb lint` also calls (§9.5).
- **A broken internal link warns, never fails**; not-yet-written knowledge is a
  `status: draft` stub (§6.5).
- **The floor file is the only thing that decides what a concept must carry** beyond OKF's
  own hard rules; a field it does not name is reported and never enforced (§9.2, §9.5).
- **The bundle root holds concepts and nothing else.** Site pages live in `about/` and raw
  sources in `raw/`, both siblings of `docs/` at the repository root (§9.3, §9.4).
- **`uv` is assumed by a bundle too**, because the hook it pins runs through it (§9.7).
- **`publish` is a `{url, style}` promise**, not an observation, and it is what makes a
  cross-bundle link possible at all. `fkb url` produces the link or refuses; lint reads the
  transform backwards to police links it did not write (§4, §7, §6.6).
- **A bundle's vocabulary is derived and never declared**, and belongs to the bundle rather
  than to the federation (§7). A declared vocabulary with a hook that fails outside it is
  rejected, knowingly: it is what the tool this design replaces had, and losing it is the
  price of a federation whose members include bundles we do not own. Splitting one subject
  across two spellings is given to semantic lint instead, because no string comparison
  detects an abbreviation (§6.5).

### 9.11 A new bundle is a repository, and the agent commits into it

**Settled: `fkb add --new` runs `git init`; the skill pins the hooks and makes every commit,
including the first.** The earlier rule was that `fkb` creates no repository and the agent
commits nothing, on the reasoning that a bundle is a git repository with its own hooks and
those hooks are the real gate. Both halves were wrong, and they were wrong together.

The gate argument assumed the hooks exist. `--new` wrote an index, a log and a floor, so the
one bundle this design creates itself was the one bundle nothing checked - and that bundle is
somebody's first private one, the least supervised content on the machine. "A person adds the
layers later" is not a gate; it is a hope about a directory that already has notes in it.

The split follows invariant 3, and the seam is sharper than it first looks:

| What | Who does it | Why there |
| --- | --- | --- |
| `git init` | the CLI | No judgement in it. A bundle with history, hooks and a way to be shared beats one without, in every case, and a rule with no exceptions is not prose's to remember. |
| The hook revision | the skill | It is a fact about a remote *right now*. A revision shipped in a file is stale the week after, and stale invisibly: the hooks run, they pass, and they are not the hooks anyone thinks they are. An agent can read `git ls-remote` as it writes the config; this repository cannot. |
| Every commit, including the first | the skill | A commit needs an author. `fkb` inventing one would write a name no human chose into history that outlives the session. |

**Committing is part of filing, not a favour.** A concept left in the working tree is a task
handed back to the person who delegated it, and hooks only refuse what is actually committed -
so not committing is itself how a bad concept evades the check. Three rules bound it: never
`--no-verify`, never invent a git identity, never push. The first keeps the gate, the second
keeps provenance honest the way §6.4 does for `generated.by`, and the third leaves disclosure
with the person.

> **This gives `fkb` no `commit` command** (§7). Nothing here wraps git: the CLI creates a
> repository as part of creating a bundle, and everything after that is the agent using git
> directly, which it already knows how to do.

A machine without git still gets a bundle. Every check here runs over a directory, and
history is the only layer that can be added afterwards without touching a single concept.

## 10. The way forward

The implementation plan lives in [IMPLEMENTATION.md](IMPLEMENTATION.md): the tasks T1–T7 in
order, what "done" means for each, and which of the open questions in §9 each one settles.
It assumes this document and nothing else from this repository.

## Appendix A - what the invariants cost

Kept short, and only to argue §2.

**agent-wiki (awiki)** produced the ~60 concepts we still consider our best content, and
three properties made it untenable. Every concept carried a shadow `docs/raw/<slug>.md`
plus a `.meta.yaml`; `raw/autofix-in-hook.md` and its published concept are byte-identical
apart from frontmatter, so an agent wrote a fake source purely to feed a pipeline that
re-emitted the file it already had (invariant 1). Backlinks track `[[wikilinks]]` only,
against our own blueprint and OKF §6.1. Nothing knew about tiers.

**fkb over the `kb-*` skills** reached 20 commits and 56 green tests. `fkb-query` called
`skill(name="kb-query")` per bundle and then executed the returned prose, which is control
flow through prompt obedience; the SKILL.md accumulated three shouted warnings against an
indirection we had introduced ourselves (invariant 2). `create-bundle` already bypassed
`kb-init` to hand-roll its scaffold, because a skill is prose rather than a callable binary.
The `kb-*` skills are not installed on this machine while the global AGENTS.md advertises
fkb, because skills have no dependency resolution - `npx skills add` copies a directory and
verifies no "requires" (invariant 4).

The conclusion this design returns to was reached on 2026-08-27 in
`public/docs/research/substrate-options-…md`, ranked first among the options considered:

> OKF plain-markdown files + thin pre-commit scripts + an AGENTS.md contract, no engine

## Appendix B - deliberate deviations

| Source | Says | We do | Why |
| --- | --- | --- | --- |
| Karpathy | "You never (or rarely) write the wiki yourself - the LLM writes and maintains all of it" | Felix co-authors and edits concepts directly | Karpathy's vault is private, single-reader, optimised for compounding synthesis. Ours is published, multi-tier and human-facing, with a house voice, prek hooks and GitHub web editing as a deliberate entry point. |
| OKF §11 | Consumers tolerate every missing optional field | `fkb lint` enforces a per-bundle floor above `type` | Provenance that is merely encouraged does not get written. The floor is ours, not the spec's, and applies only to bundles we own (§6.5). |
| okf-skills | `.okf/` at the repo root | `docs/` | The publishing stack owns that directory. Consequences for non-knowledge pages are §9.4. |
| awiki | `[[wikilinks]]` | standard markdown links | Our blueprint mandates them, OKF §6.1 specifies them, and Obsidian and MkDocs both support them. |
| OKF §5 | Every timestamp-valued key is "an ISO 8601 datetime with an explicit UTC offset" | `YYYY-MM-DD` dates for `stale_after`, `sources[].last_modified` and `usage_window` | The vendored validator predates the change and rejects the datetime form under `--strict` (§8). All three fields sit outside the floor, so the simplification costs day precision on staleness. |
| OKF §6.1 | Absolute, bundle-relative links (leading `/`) are the recommended form; relative links are also supported | Relative links throughout | Only the relative form resolves in an editor, on the GitHub web UI and in a rendered site at once - the reason §5.2 already keeps assets beside their concept. MkDocs rewrites relative links when a page moves and leaves absolute ones untouched, so a moved target breaks silently. |
| OKF §9 | Its example log entries link at the concept they report | Log entries name a concept in plain text, never a link | `log.md` is append-only: an entry stays true after its subject moves or is deleted, whilst a link does not, and every way of reacting to that either falsifies the record, loses history or breaks a strict build from a line nobody is editing (§9.9). |
| OKF §8 | An index entry SHOULD carry the description from the linked concept's frontmatter | Entries are written in index voice: shorter than the description, tuned to being scanned in a list | The reference bundle `stjbrown/agent-knowledge` truncates, compresses or rewrites every one of its own, and its index additionally carries a purpose statement, per-section blurbs and an order that follows how the ideas build. Copying the descriptions would duplicate state and produce a worse file (§9.8). |

## Sources

- [Karpathy, LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format)
- [scaccogatto/okf-skills](https://github.com/scaccogatto/okf-skills) - MIT
- [stjbrown/agent-knowledge](https://github.com/stjbrown/agent-knowledge) - the `kb-*` skills
- [TacoTakumi/agent-wiki](https://github.com/TacoTakumi/agent-wiki)
- [Agent Skills specification](https://agentskills.io) - `SKILL.md`, `references/`,
  `scripts/`, progressive disclosure
- Local: `~/.agents/wikis/public/docs/research/substrate-options-…md`,
  `blueprints/mkdocs-material-pkb-publishing-stack.md`
- Local: `~/Projects/public/running-linux` - the working publishing stack
