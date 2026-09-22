"""An environment for running `git` in, with the repository it was started from taken out.

`git` tells its hooks where the repository is by putting it in the environment:
`GIT_DIR`, `GIT_INDEX_FILE`, `GIT_WORK_TREE` and friends are exported for the
duration of a hook and inherited by everything it starts. A test suite run from
a hook - which is how the `support-script-tests` hook runs this one - therefore
begins inside somebody's commit, and every `git` command it issues without
thinking about it operates on **this** repository rather than on the throwaway
one the test just built.

The symptom is not a failure, which is what makes it worth a module. A test that
commits into a temporary repository succeeds, and the commit lands in the
developer's own history; `git init` in a fixture re-initialises nothing and the
fixture's first commit is written against the outer index, taking whatever the
developer had staged with it. This was found as three commits by "Ada Lovelace"
on a working branch and a file staged out of a test fixture.

So every `git` this suite runs, directly or through `fkb`, is handed an
environment with the whole `GIT_` namespace removed. Wholesale rather than by a
list of the variables known to cause it: the list is long, git is free to add to
it, and nothing this suite runs wants a `GIT_` variable it did not set itself.
"""

from __future__ import annotations

import os

GIT_PREFIX = "GIT_"


def outside_any_repository(**overrides: str) -> dict[str, str]:
    """The current environment, minus every `GIT_` variable, plus what is passed.

    The rest of the environment is carried rather than built from scratch, for
    the reason `_commit` gave before this existed: a hand-built environment
    listing `PATH` and `HOME` is enough on Linux and not on Windows, where git
    needs `SYSTEMROOT` to resolve anything at all.

    Overrides are applied after the scrub, so a caller that means to set
    `GIT_AUTHOR_NAME` still can. Setting one deliberately is the opposite of
    inheriting it by accident.
    """
    return {**without_git_variables(os.environ), **overrides}


def without_git_variables(env: dict[str, str] | os._Environ[str]) -> dict[str, str]:
    """The given environment with the `GIT_` namespace taken out."""
    return {key: value for key, value in env.items() if not key.startswith(GIT_PREFIX)}
