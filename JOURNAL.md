# Journal

Friction, recorded while filing knowledge with a deliberately incomplete toolset. `fkb` has
`list` and `lint` and nothing else; search, vocabulary reporting and setup commands are
withheld so that what gets built next answers an incident rather than a guess.

This file is temporary. It is folded into a decisions record and deleted once it has decided
the CLI's scope.

## How to write an entry

One line per incident, dated, so the file greps. Three rules:

- **Record what happened, not what should exist.** "Searched the web for X; the bundle had
  it at `principles/y.md`" is evidence. "Search would be useful" is a wish, and wishes are
  free.
- **Name the artifacts.** The actual query, the actual path, the actual tag chosen. An entry
  that names no file and no query did not happen, and must not be written.
- **Record what was done instead.** The workaround is the measurement. If there was no
  workaround, say the task was abandoned.

An empty week is a finding. Nothing is gained by inventing a plausible incident, and the
only evidence this file exists to collect is lost.

## What to watch for

The skill files one concept at a time and stops. It does not search for existing concepts,
update overviews, or change tags. That is deliberate: the gaps stay open long enough to be
measured. Notice these moments and record them:

- **Supersession** - you write something that makes an existing concept wrong. Did you notice
  mid-write? Did you search for it first? What did you do instead: file both, ask, or skip?
- **Impact sweep** - a concept you file touches others that cite the same thing. Did you look
  for them? Did you link back, or only outward?
- **Schema evolution** - no existing `type` or directory fits. Did you invent one, ask, or
  force it? Who should update `spec/types.md`?
- **Tag discipline** - you picked a tag without knowing what the bundle uses. Did you guess?
  Did lint catch it? What workaround did you use?
- **Cross-linking** - you filed a concept that others *should* link to. Did you find them and
  edit them, or leave it for later?
- **Re-synthesis** - an overview or roll-up now says something outdated. Did you notice? Did
  you update it, supersede it, or file a note?

Each of these is a decision the `kb-ingest` skill makes automatically. This design stops at
filing, so the journal decides whether integration mechanics belong in T5 or stay with a
person.

## Incidents
