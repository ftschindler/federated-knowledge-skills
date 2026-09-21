# federated-knowledge-skills

Durable knowledge, in plain markdown, that your agents read before the web and write back to
when they learn something worth keeping. Several bundles sit side by side at different
privacy tiers, each its own git repository, each readable and writable by agents across
harnesses and by you in an editor.

It is an implementation of the [LLM wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
idea over the [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format),
with the federation and access tiers that neither of those specifies.

You get a skill, a CLI it runs, and two pre-commit hooks each bundle pins for itself.
[ftschindler.github.io/knowledge](https://ftschindler.github.io/knowledge/) is one of these
bundles, published: what a bundle looks like when it has been lived in for a while.

## What to use it for

**Keep what a session learned.** A decision and why, a principle you would want true in any
repository, a fix that cost an afternoon. One idea per file, linked to the ones it rests on.
The agent files it, indexes it, logs it and commits it.

**Answer from what you already know.** A question the bundles hold is answered from them and
cited by path, rather than re-derived from a web search that does not know what you decided
last month.

**Keep work, clients and private notes apart without thinking about it.** A bundle declares
who may cite it. A sealed bundle cannot be linked to from one that publishes, and the CLI
refuses to write such a link rather than leaving it to an agent's judgement.

**Publish a bundle, or do not.** The same directory serves as a private vault, a repository
you share with a team, or a static site. Nothing about the files changes.

Use something else if you want a search engine over everything you have ever read, an
automatic transcript ingest, or a single vault with no privacy tiers. The first two are
deliberately absent, and the third is more machinery than one tier is worth.

## How to use it

**Requirements:** [uv](https://docs.astral.sh/uv/), git, and an agent that loads skills.
Nothing else, on Linux, macOS or Windows.

**1. Install the skill.** Copy `skills/fkb/` into wherever your harness keeps skills, or let
a skill installer do it:

```text
npx skills add ftschindler/federated-knowledge-skills
```

The CLI ships inside the skill as `scripts/fkb`, so there is no second install step. Nothing
here ever installs anything itself.

**2. Open a session and say what you want.** "Set up my knowledge base", or just "note this
down". The skill takes it from there: it proposes where the bundles should live, creates
your private one, adds the public bundles worth reading, and shows you the result. The
[getting-started reference](skills/fkb/references/getting-started.md) is what it follows.

**3. Add the block to your user-level instructions.** Without one line in the file your
harness loads every session, nothing will make an agent reach for the bundles at all. The
skill offers it and lets you place it; the text is in
[agents-block.md](skills/fkb/references/agents-block.md).

From then on you mostly do not type commands. When you want to, they are:

```text
uv run <skill>/scripts/fkb list                  # which bundles exist, and what each allows
uv run <skill>/scripts/fkb lint [name]           # check a bundle, or all of them
uv run <skill>/scripts/fkb resolve <name>        # one bundle as JSON: policy, tags, types
uv run <skill>/scripts/fkb url <name> <path> --from <name>   # cite a concept in another bundle
uv run <skill>/scripts/fkb add <name> --clone <url>          # bring a bundle in
uv run <skill>/scripts/fkb version               # this release, and the one your setup is on
uv run <skill>/scripts/fkb migrate               # what an upgrade asks of an existing setup
```

**Upgrading.** Copy the new `skills/fkb/` over the old one; that is the whole of it. A
release that needs something of a setup already on disk says so the next time you run
`fkb list`, and `fkb migrate` names the page to read. Nothing is blocked while you have not:
a version stamp here is bookkeeping about capabilities, not a lock on your bundles.

**4. Give each bundle its gate.** A bundle is checked by its own pre-commit hooks, pinned by
revision, so it holds up whether or not the federation layer is anywhere near it:

```yaml
- repo: https://github.com/ftschindler/federated-knowledge-skills
  rev: <commit>
  hooks:
  - id: okf-concepts
    args: [--bundle-root, docs, --floor, docs/fkb.yaml]
```

`okf-concepts` checks the whole bundle and fails only on the files being committed, so an
unfinished page elsewhere never blocks an unrelated commit; with `--all-files` the same hook
is strict in CI. `okf-bundle` adds index coverage and sits on the manual stage. Only two
layers can fail a run: the format's hard rules, and the fields your own `fkb.yaml` declares.

## How it is put together

Three ideas carry most of it.

- **The markdown file is the source.** No ingest pipeline, no generated copies, no drift
  guard between two versions of one note. An agent writes the file you edit.
- **A skill may run a command; a skill never invokes another skill.** Prose calling prose
  through an LLM is not control flow.
- **A copy of the skill can tell you how old it is.** It ships with a `VERSION` file,
  because nothing else survives being copied into a skills directory, and the manifest
  records which release your setup was last brought up to.
- **The manifest is a guardrail, not a security boundary.** It is one machine-local file
  saying which bundles exist and what each allows. The boundary that holds is git remote
  permissions and each bundle's own publish gate, so a bundle stays safe when an agent
  bypasses the federation layer entirely.

**[DESIGN.md](DESIGN.md) is the source of truth** for what this is, what was deliberately
rejected and which questions are still open, including the ones that cost the most to
answer. [IMPLEMENTATION.md](IMPLEMENTATION.md) is the order of work and what remains.

The reasoning behind it, written from the outside, is on the bundle it produced:
[the decision](https://ftschindler.github.io/knowledge/decisions/federating_my_knowledge_base_as_privacy_tiered_okf_bundles/),
[the architecture](https://ftschindler.github.io/knowledge/research/federated_okf_knowledge_bases_a_workspace_manifest_architecture/)
and [what the first attempt taught](https://ftschindler.github.io/knowledge/explorations/wrapping_the_kb_skills_in_a_federation_layer/).

## Working on it

See [CONTRIBUTING.md](CONTRIBUTING.md) for prerequisites, bootstrap and the test layers.

```bash
make bootstrap   # install the pre-commit hooks
make test        # support scripts, real bundles, then a real agent run
make check       # the full guard suite over every file
make agent       # build a disposable agent and drop into a shell inside it
```

Two things are worth knowing before changing anything. The skill is tested by installing it
into a throwaway agent and asking that agent to do the thing, because prose is what regresses
here and no unit test reads it. And `JOURNAL.md` records what the tooling could not do, one
line per incident with the actual paths and queries: it is the evidence that decides what
gets built next, which is why `fkb search` does not exist yet.

## License

[MIT](LICENSE). The vendored OKF specification and validator carry their own, beside them in
`skills/fkb/references/`.
