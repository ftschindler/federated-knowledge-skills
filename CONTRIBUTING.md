# Contributing

## Local Dev Environment

### Prerequisites

We require

- [uv](https://docs.astral.sh/uv/),
- [Node.js](https://nodejs.org),

and optionally [make](https://en.wikipedia.org/wiki/Make_(software)).

> Using make is actually an optional convenience.
> If not available: look up the raw uv or node calls in the [Makefile](Makefile)

### Clone and bootstrap

```bash
git clone https://github.com/ftschindler/federated-knowledge.git
cd federated-knowledge
make bootstrap
```

### Using the development version of the skills globally

This repo ships no skills yet (see [DESIGN.md](DESIGN.md)). Once it does, symlink them into
the location every harness reads:

```bash
mkdir -p ~/.agents/skills && \
for ii in $(cd skills && ls -d *); do ln -s "${PWD}/skills/${ii}" ~/.agents/skills/; done
```

> Remove previously installed copies from the target location beforehand.

### Running the tests

Two layers, both run by:

```bash
make test
```

#### Support scripts

Fast and deterministic, no network:

```bash
make test_python_scripts
```

#### The disposable agent

Slower and non-deterministic, because it drives a real agent:

```bash
make test_agent
```

These tests

- build a [disposable agent](#a-disposable-agent),
- send it a message (the non-deterministic part),
- assert deterministically on the transcript it returns and the files it leaves.

While the repo has no skills of its own, this layer installs a canary skill authored by the
test and checks that the agent discovers and follows it. That keeps every moving part
exercised: the opencode install, the permission grant, skill discovery, activation and
transcript parsing.

#### A disposable agent

A `DisposableAgent` is a real agent you can talk to, owned by the caller and thrown away
afterwards. Building one

- creates a `HOME` with all `XDG_*` redirected into it,
- installs a pinned `opencode` (an agent runtime plus free access to its default model),
- copies skill directories from a given source into `~/.agents/skills`.

A test never needs to know opencode is in there: it installs skills, calls `run()`, and
reads the transcript.

Build one by hand and drop into a shell inside its world:

```bash
make agent                                    # this repo's skills, if any
.scripts/disposable-agent.py --skills DIR     # skills from elsewhere
.scripts/disposable-agent.py --no-skills      # a bare agent
```

On a test failure the agent is preserved and the command to enter it is printed.

### Before you push

Run the full pre-commit guard suite against every file (the same hooks that run on commit):

```bash
uvx prek run --all-files
```
