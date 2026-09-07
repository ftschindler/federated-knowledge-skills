# federated-knowledge-skills

A federated, agent-agnostic knowledge base: privacy-tiered bundles of plain markdown, each
its own git repo, readable and writable by agents across harnesses and by humans in an
editor.

It is an implementation of the [LLM wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
idea over the [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format),
with the federation and access tiers that neither of those specifies.

> **Status: design stage.** The architecture is settled and written down. The
> implementation is not built yet. An earlier attempt was, and was retired - see
> [below](#history).

## Read this first

**[DESIGN.md](DESIGN.md) is the sole source of truth.** It specifies what gets built, what
was deliberately rejected, and which questions are still open.
[IMPLEMENTATION.md](IMPLEMENTATION.md) carries the order of work: tasks T1–T7, what "done"
means for each, and which open question each one settles. Together they are
self-contained - everything needed to start is either in them or listed in
IMPLEMENTATION.md's "before starting" section.

Three ideas carry most of the design:

- **The markdown file is the source.** No ingest pipeline, no generated copies. An agent
  writes the file you edit.
- **A skill may run a command; a skill never invokes another skill.** Prose calling prose
  through an LLM is not control flow.
- **The manifest is a guardrail, not a security boundary.** Access control is git remote
  permissions and the CI publish gate.

## What is in this repository today

| | |
| --- | --- |
| `DESIGN.md` | The design |
| `IMPLEMENTATION.md` | The plan: tasks T1–T7, in order |
| `tests/disposable_agent.py` | A throwaway agent: install skills into it, send it a message, throw it away |
| `tests/test_disposable_agent.py` | Keeps that machinery exercised while there is nothing else to test |
| `.scripts/` | Support scripts: build an agent by hand, extract dependencies, guard the mailmap and skill frontmatter |
| dotfiles, `.github/` | Pre-commit hooks, linters, CI |

No skills and no CLI. Those arrive with the tasks in [IMPLEMENTATION.md](IMPLEMENTATION.md).

## Working on it

See [CONTRIBUTING.md](CONTRIBUTING.md) for prerequisites, bootstrap and the test layers.

```bash
make bootstrap   # install the pre-commit hooks
make test        # support scripts, then a real agent run
make check       # the full guard suite over every file
make agent       # build a disposable agent and drop into a shell inside it
```

## History

The first attempt wrapped the single-bundle `kb-*` skills from
[stjbrown/agent-knowledge](https://github.com/stjbrown/agent-knowledge) in a federation
layer. It reached 20 commits and a green test suite, and it did not work: skills invoking
skills is not something an agent reliably carries out. That state is preserved on a tag,
and what it cost is recorded in DESIGN.md appendix A.

The disposable agent is what survived, because building a throwaway agent and talking to it
is independent of what is being tested.

## License

[MIT](LICENSE).
