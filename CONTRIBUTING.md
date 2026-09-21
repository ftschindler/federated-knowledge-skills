# Contributing

## Local Dev Environment

### Prerequisites

We require

- [uv](https://docs.astral.sh/uv/),
- [Node.js](https://nodejs.org),

and optionally [make](https://en.wikipedia.org/wiki/Make_(software)).

> Using make is actually an optional convenience.
> If not available: look up the raw uv or node calls in the [Makefile](Makefile)

Everything below works on Linux, macOS and Windows. Each make target is one
`uv run` line precisely so that the make-less path is not a second, rotting set
of instructions. See [Working on Windows](#working-on-windows) for the two
places the two worlds differ.

### Clone and bootstrap

```bash
git clone https://github.com/ftschindler/federated-knowledge-skills.git
cd federated-knowledge-skills
make bootstrap
```

### Using the development version of the skills globally

Link them into the location every harness reads, so edits in this clone are live:

```bash
mkdir -p ~/.agents/skills && \
for ii in $(cd skills && ls -d *); do ln -s "${PWD}/skills/${ii}" ~/.agents/skills/; done
```

On Windows, in PowerShell (a symlink needs developer mode or an elevated shell; without
either, use `Copy-Item -Recurse` and re-copy after each edit):

```powershell
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
Get-ChildItem -Directory skills | ForEach-Object {
  New-Item -ItemType SymbolicLink -Path "$HOME\.agents\skills\$($_.Name)" -Target $_.FullName
}
```

> Remove previously installed copies from the target location beforehand.

These links live in your home directory and are never committed. Symlinks *inside* the
repository are a different matter and are refused by a hook: see
[Working on Windows](#working-on-windows).

### Working on Windows

Two things the repository deliberately does not do, both because of how a Windows clone
differs from a Linux one:

**No committed symlinks.** Git stores a symlink as a blob holding the target path, and a
clone on Windows writes that path out as an ordinary text file unless `core.symlinks` is on,
which needs developer mode. The link does not break loudly - it becomes a one-line document
saying `../../JOURNAL.md`, and everything reading through it reads that string. The
`no-symlinks` pre-commit hook refuses one, and the Windows CI job checks the checkout it got.

The one this repo had was the journal placed beside the skill, so the skill's "the journal is
running on this machine" branch is reachable while working on it. Put your own copy there if
you want that branch live; `skills/*/JOURNAL.md` is gitignored:

```bash
cp JOURNAL.md skills/fkb/JOURNAL.md     # or: ln -s ../../JOURNAL.md skills/fkb/JOURNAL.md
```

**No shell in the tooling.** Test invocation goes through
[`.scripts/run-tests.py`](.scripts/run-tests.py) rather than a `$(shell ...)` in the
Makefile, so `make`, `bash` and command substitution are not prerequisites for running the
suite. Without make:

```powershell
uv run .scripts/run-tests.py python_scripts
uv run .scripts/run-tests.py federation
uv run .scripts/run-tests.py agent
```

The pre-commit suite (`uvx prek run --all-files`) runs on Windows too, but is only *gated* on
Linux in CI: several of its hooks are third-party binaries whose Windows builds we do not
control, and a formatting job is not worth pinning that on. If one of them misbehaves on your
machine, the Linux governance job is the authority.

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

Most of these run `fkb` inside a [fake home](#a-fake-home): a throwaway directory that `HOME`,
`USERPROFILE` and every `XDG_*` variable point into, with the skill installed in it. Nothing
they do can reach the workspace you actually use.

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

This layer installs a throwaway skill authored by the test and checks that the agent
discovers and follows it. That keeps every moving part exercised: the opencode install, the
permission grant, skill discovery, activation and transcript parsing.

What that skill says is deliberately dull. It asks for a house greeting and gets a nonsense
phrase back. An earlier version asked the model to "report the canary token", which reads as
an attempt to make it disclose a secret; it declined on exactly those grounds and the layer
went red. A test of skill discovery must not look like a test of anything else.

#### A disposable agent

A `DisposableAgent` is a real agent you can talk to, owned by the caller and thrown away
afterwards. Building one

- creates a `HOME` (and `USERPROFILE`) with all `XDG_*` redirected into it,
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

`USERPROFILE` is redirected alongside `HOME` because the fallback is `Path.home()`, which
reads `HOME` on Linux and `USERPROFILE` on Windows. Redirecting one of the two would make the
isolation hold on one operating system and silently fail on the other.

### Releasing

Every merge to `main` ships, and the size of the release comes from a label on the pull
request. Put exactly one of them on before merging:

| label | when |
| --- | --- |
| `major` | a setup that works today stops working, or needs a hand to keep working |
| `minor` | something new: a command, a field, a capability |
| `patch` | a fix, or prose that ships inside the skill |
| `no-release` | nothing that ships - CI, repository docs, this file |

The release job writes `skills/fkb/VERSION`, commits it and tags it. **Do not bump that file
in a pull request** - a hook and a CI check both refuse it. It is written in one place so a
tag and the version installed from it cannot disagree, and so two open pull requests do not
conflict over one line.

The job needs a `RELEASE_TOKEN` secret that may push to protected `main`. Without one it
falls back to the default token, which cannot, and the release fails visibly rather than
tagging a commit it could not push.

**If the change asks something of setups that already exist**, write the guide with it:
`skills/fkb/references/migrations/<next version>.md`, in the voice described by
[the README beside it](skills/fkb/references/migrations/README.md). You are naming a file
for a version that does not exist yet, which is the one awkward part of this: take the
current `VERSION`, apply your own label to it, and use that. Most changes need no guide, and
a gap in the series is normal.

### Before you push

Run the full pre-commit guard suite against every file (the same hooks that run on commit):

```bash
uvx prek run --all-files
```
