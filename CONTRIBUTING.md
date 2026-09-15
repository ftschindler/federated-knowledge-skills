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
git clone https://github.com/ftschindler/federated-knowledge-skills.git
cd federated-knowledge-skills
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

Three layers, all run by:

```bash
make test
```

#### Support scripts

Fast and deterministic, no network:

```bash
make test_python_scripts
```

Most of these run `fkb` inside a [fake home](#a-fake-home): a throwaway directory that `HOME`
and every `XDG_*` variable point into, with the skill installed in it. Nothing they do can
reach the workspace you actually use.

#### Real published bundles

Needs the network and `git`, and no LLM:

```bash
make test_federation
```

These clone two real bundles and run the CLI against them. They exist for the one thing a
fixture cannot honestly provide - the shape of a repository nobody here controls - and they
can therefore fail without anyone changing anything here. That is not a false alarm: a
bundle that moved is a true statement about the federation, and the belief in this code is
what needs correcting.

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
- drops every `OPENCODE*` variable from the inherited environment,
- installs a pinned `opencode` (an agent runtime plus free access to its default model),
- copies skill directories from a given source into `~/.agents/skills`.

> Dropping those variables matters more than it looks. `OPENCODE_CONFIG_DIR` overrides
> config lookup outright, so a developer who has one set would otherwise re-attach every
> disposable agent to their real profile - reading their models and plugins while looking
> for credentials in an empty home. What surfaces is an opaque provider error, nowhere near
> the cause.

A test never needs to know opencode is in there: it installs skills, calls `run()`, and
reads the transcript.

Build one by hand and drop into a shell inside its world:

```bash
make agent                                    # this repo's skills, if any
.scripts/disposable-agent.py --skills DIR     # skills from elsewhere
.scripts/disposable-agent.py --no-skills      # a bare agent
```

On a test failure the agent is preserved and the command to enter it is printed.

### A fake home

`tests/fake_home.py` builds the smaller sibling of the disposable agent: a directory with the
skill installed into it and every path variable redirected inside, but no opencode and no
LLM. Tests that only need to run a command take it.

It exists because `fkb` finds its manifest at `$XDG_CONFIG_HOME/fkb/workspace.yaml` and falls
back to `~/.config` when that is unset. Both roads lead somewhere real on your machine, and
one of them is your live federation, so redirecting only `XDG_CONFIG_HOME` would leave a bug
one missing variable away from rewriting the manifest you use. Redirecting `HOME` as well
makes that unreachable, and turns the fallback into something a test can exercise on purpose.

### Before you push

Run the full pre-commit guard suite against every file (the same hooks that run on commit):

```bash
uvx prek run --all-files
```
