# The AGENTS.md block

A skill is only loaded once something makes an agent reach for it. That is what this block
does: it sits in the user-level instructions a harness loads at the start of every session,
names the phrases a person actually uses, and hands off everything procedural to the skill.

Without it, a session has no reason to consider the bundles. The person says "what do we
know about X", the agent searches the web, and the bundle that held the answer is never
opened. Nothing appears to go wrong, which is what makes it worth checking for.

## Checking whether it is there

**Look in the user-level instructions file your own harness loads for every session.** You
know which file that is and where it lives. In opencode it is
`AGENTS.md` under the user config directory; other harnesses use their own name and their
own location.

The block is present if that file has a section about knowledge bundles naming `fkb`. If the
file exists and has no such section, it is missing. If there is no such file at all, the
person has never had user-level instructions, and creating one is a bigger suggestion than
this - say so rather than writing it silently.

## Propose, do not write

**This file is one a person curates.** It loads into every session they run, for every
project, so an uninvited edit changes the behaviour of work that has nothing to do with
knowledge bundles.

Show them the block, say which file it goes in and why, and let them place it. If they ask
you to add it, append it as its own section and change nothing else in the file.

## The block

```markdown
## Knowledge bundles (fkb)

Durable knowledge — decisions, research, fixes worth keeping — lives in privacy-tiered
markdown bundles managed by the `fkb` skill. When the user says "the wiki", "my notes"
or "the team wiki", they mean these.

- Before searching the web, check the bundles.
- When something durable is learned, file it.
- Load the `fkb` skill for how; it carries the conventions and the commands.

If the `fkb` skill is not installed, skip this silently.
```

Three properties matter more than the exact wording, and are worth preserving if it is
adapted:

- **It names the trigger phrases.** An agent will not guess that "my notes" means a bundle.
- **It defers everything procedural to the skill**, so the two cannot drift apart. Anything
  about how to file, what a concept must carry, or which bundle to choose belongs in the
  skill and not here.
- **It fails silent.** A machine without the skill installed loses nothing and sees no error.

It is also deliberately short. It loads on every session, including the overwhelming
majority that never touch a bundle, so its only job is to make the skill reachable.

## Their own words for their own bundles

The phrases above are the generic ones. Someone who regularly calls a bundle something the
manifest does not - "my notes" for the bundle registered as `private`, "work" for the team
one - is describing a mapping nothing on disk knows, and a session that has to ask about it
will have to ask again tomorrow. One line in their section settles it:

```markdown
- "my notes" is the `private` bundle; "the work wiki" is `team`; "what does Felix say" means
  `ftschindler`.
```

**Upstreams attract this more than anything else.** They are registered under their owner's
name, because a subject is never exclusive and an owner is - but people then refer to them by
person ("what does Felix think"), by subject ("the engineering practice one"), or by project,
and only one of those is what the manifest says. The mapping is one line and it is stable for
as long as the bundle is registered.

This is where it goes because it is the only file that outlives the session the phrase was
learned in. The other honest answer is to rename the bundle, which is the better one when the
manifest name is simply *wrong* rather than merely different from what they say out loud.
Offer both and let them choose; as above, propose rather than write.
