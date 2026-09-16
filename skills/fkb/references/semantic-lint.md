# Semantic lint: the checks only a reader can make

`fkb lint` checks what a program can check: conformance to the format, the fields the bundle
requires, whether every concept is reachable from an index, whether a link crosses a tier it
may not. Run it first, and fix what it calls an ERROR.

This page is the other half, and it is the half that needs a reader. Every check here is one
a retrieval system structurally cannot perform: they are about what the bundle *means*, and
two files can each be perfectly valid while saying incompatible things.

**Use it when asked to audit, review, or tidy a bundle** - not on every filing. On a filing,
step 6 of the body covers the one case that matters in the moment.

## How to run a pass

Scope it. A whole bundle at once produces a list nobody acts on, and the checks below want
the concepts in context rather than one at a time.

1. Pick a directory, or a subject, or what changed recently.
2. Read `fkb resolve <bundle>` for the vocabulary, and the directory's own index for what
   the category claims to be.
3. Read the concepts. Actually read them; these checks do not survive skimming.
4. Report findings with paths, grouped by kind, and **propose rather than perform**. A
   contradiction between two pages usually needs the person who wrote them.

## The checks

### One subject tagged two ways

The most valuable check here, and the one no program will ever do for you.

Read the tag list from `fkb resolve` with its counts. Look for two entries that name the
same subject: an abbreviation beside the thing it abbreviates, a singular beside a plural, a
hyphenated form beside a compressed one, a synonym.

This happened, and sat undetected for weeks: `awiki` on four pages and `agent-wiki` on three.
Nothing caught it - not the bundle's hooks, not its site build, not `fkb lint` - and it was
found because a sentence happened to mention the tag.

It cannot be automated, and it is worth understanding why, because the reason generalises.
`awiki` and `agent-wiki` are five edits apart; no normalisation of case, hyphens or plurals
brings them together. A program can enforce a closed list of permitted tags, but it cannot
discover that two strings *outside* any list denote one thing. That is a judgement about
meaning, which is what you are for.

The damage is retrieval: a search for either spelling returns half the pages and gives no
signal that the other half exists. So the failure is silent on both sides.

**Look in the tail.** A split shows up as two low counts where one moderate one belongs.

### Contradiction

Two concepts that cannot both be true. Usually one is older and nobody noticed when the
second was written.

Report both paths and what they disagree about. Do not pick a winner unless the newer one
explicitly supersedes the older, and do not edit either without asking.

### Supersession left implicit

A newer concept makes an older one wrong or redundant, and the older one still reads as
current. The format has `status: deprecated` for exactly this, and a bundle that uses it
gets the finding for free next time, because deprecation is something deterministic lint can
see. When deprecating in favour of a newer concept, link to the newer from the deprecated one.

The tell is usually a date gap plus an overlapping subject.

### Orphans and gaps

- **Orphans**: a concept no index links to. `fkb lint --coverage` finds these mechanically;
  what it cannot say is whether the page should be linked or should not exist.
- **Gaps**: a subject several concepts refer to as if it had a page, and it does not. These
  are worth filing as `status: draft` stubs, since a stub turns an implied page into a
  visible one.

### Stale content that has not been marked stale

`stale_after` is checked by `fkb lint`; the concepts that never carried it are not. A
concept about a tool's behaviour, a version, a pricing page or an API is the kind that rots,
and a bundle full of unmarked rotting pages will not tell you which ones they are.

Propose `stale_after` for the ones that clearly expire. Leave principles alone - a principle
does not go stale on a date.

### Trust that was asserted rather than earned

`verified` should name a person who actually confirmed the content. Look for blocks naming
someone who did not, timestamps that predate the confirmation they claim, and concepts whose
body has moved on since the block was written. None of this is visible to a validator: the
YAML is well formed in every case.

### Index entries that have stopped describing their page

An index entry is written in the bundle's voice and says what the page is for. When a page
is rewritten, its entry usually is not. The entry is what a reader uses to decide whether to
open the file, so a stale one is a page that stops being found.

## What not to do in an audit

- **Do not rewrite prose you merely dislike.** The bundle's register is the bundle's, and
  the one thing this skill must not do is impose a style on a bundle that has its own.
- **Do not canonicalise tags across a whole bundle unasked.** It touches many files and it is
  a decision about vocabulary, not a fix.
- **Do not delete anything.** Removing a concept edits other files that point at it and the
  log line that announced it. Report it and let a person decide.
