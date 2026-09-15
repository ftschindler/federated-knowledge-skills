.DEFAULT_GOAL := help

## Show available targets
help:
	@grep -B1 '^[a-z][a-z_-]*:' $(MAKEFILE_LIST) \
		| grep -A1 '^##' \
		| awk '/^##/{d=substr($$0,4)} /^[a-z]/{split($$0,a,":"); printf "  %-20s %s\n", a[1], d}'

# Fail early with an actionable message when a required tool is missing, rather
# than letting a recipe die halfway with a cryptic "command not found". Each
# target lists the binaries it assumes as `guard-<tool>` order-only prereqs.
guard-%:
	@command -v $* >/dev/null 2>&1 || { \
		printf 'error: required tool %s not found on PATH.\n' '$*' >&2; \
		printf 'See CONTRIBUTING.md > System requirements for how to install it.\n' >&2; \
		exit 1; \
	}

## Run all tests (support scripts, real bundles, and the disposable agent)
test: test_python_scripts test_federation test_agent

# Each layer is one call into .scripts/run-tests.py, which composes the `uvx`
# invocation in Python. That composition used to be a `$(shell ...)` here, which
# made `make` and a POSIX shell prerequisites of running the tests at all; the
# script runs the same on Windows, where make usually is not installed.

## Test the support scripts under .scripts/ (fast, deterministic, no network)
test_python_scripts: | guard-uv
	uv run .scripts/run-tests.py python_scripts

## Test `fkb` against real published bundles (needs network + git)
test_federation: | guard-git guard-uv
	uv run .scripts/run-tests.py federation

## Test the disposable agent by actually driving one (slow, needs network)
test_agent: | guard-node guard-npm guard-npx guard-uv
	uv run .scripts/run-tests.py agent

## Run the full pre-commit guard suite against all files
check: | guard-uvx
	uvx prek run --all-files

## Build a disposable agent and drop into a shell for inspection
agent: | guard-uv
	uv run .scripts/disposable-agent.py

## Install the pre-commit hooks into this clone
bootstrap: | guard-git guard-uvx
	uvx prek install

.PHONY: help test test_python_scripts test_federation test_agent check agent bootstrap
