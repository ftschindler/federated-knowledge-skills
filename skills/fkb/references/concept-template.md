---
# The five floor fields, required in bundles we own.
type: <Concept type, e.g. Principle, Decision, Reference, Playbook, Service>
title: <Human-readable display name>
description: <Single sentence summarizing the concept.>
status: stable                    # draft | stable | deprecated; absent means stable
generated: { by: <actor>, at: <2026-06-14T10:00:00Z> }

# Not part of the floor, but the key must be present: the validator warns when
# it is missing. The list may be empty `[]`.
tags: [<tag>, <tag>]

# Optional below. Fill what is true; omit the rest rather than writing a blank.
resource: <Canonical URI of the underlying asset — omit for abstract concepts>
stale_after: <YYYY-MM-DD>         # omit when the content does not expire
sources:                          # what this was derived from; omit if nothing
  - id: <short-key>
    resource: <URL, bundle path, or scope descriptor>
    title: <Human-readable label>
    author: <actor>               # optional credibility signal
    last_modified: <YYYY-MM-DD>   # when the source itself last changed
---

<!--
  Actors (SPEC.md §7). `by` names what did the writing, never the skill:

    <harness>/<model>    an agent           opencode/claude-opus-5, codex/gpt-5.6-sol
    human:<id>           a person           human:felix
    process:<id>         a scheduled job    process:wiki-nightly

  Not `fkb`, not `claude`, not a bare `opencode` - the field exists to record
  which harness and model produced the content.

  `generated.by` is required whenever `generated` is present; half a block is
  malformed. Spelling is load-bearing: `Human:felix` or `human/felix` silently
  downgrades a human-reviewed concept to machine-confirmed.

  Do not write `verified:`. Its absence is how OKF encodes "unverified", and it
  is added by whoever confirms the content against its sources - never by the
  author asserting it of their own work.
-->

# <Title>

## Overview

<What this concept is and why it matters. Attribute a sourced claim with a
footnote whose label is a `sources[].id`.[^short-key]>

## Schema

<Use for assets with fields/columns; delete this section otherwise.>

| Field | Type | Description |
|-------|------|-------------|
|       |      |             |

[^short-key]: <Human-readable label of the source>
