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

## Run all tests (support scripts, and the disposable agent)
test: test_python_scripts test_agent

## Test the support scripts under .scripts/ (fast, deterministic, no network)
test_python_scripts: | guard-uvx
	uvx --with pytest pytest -v -m python_scripts

## Test the disposable agent by actually driving one (slow, needs network)
test_agent: | guard-node guard-npm guard-npx guard-uvx
	uvx --with pytest $(shell uv run .scripts/extract-deps.py skills) pytest -v -m agent

## Run the full pre-commit guard suite against all files
check: | guard-uvx
	uvx prek run --all-files

## Build a disposable agent and drop into a shell for inspection
agent:
	.scripts/disposable-agent.py

## Install the pre-commit hooks into this clone
bootstrap: | guard-git guard-uvx
	uvx prek install

.PHONY: help test test_python_scripts test_agent check agent bootstrap
