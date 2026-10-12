# Being reached for at all

A skill is only loaded once something makes an agent reach for it, and nothing inside a
skill can do that. What does it is a few lines in the user-level instructions a harness
loads at the start of every session, naming the phrases a person actually uses and handing
off everything procedural to the skill. Those lines are a *rule*, and this skill ships with
one.

Without it, a session has no reason to consider the bundles. The person says "what do we
know about X", the agent searches the web, and the bundle that held the answer is never
opened. Nothing appears to go wrong, which is what makes it worth checking for.

## Checking whether it is there

**Look in the user-level instructions file your own harness loads for every session.** You
know which file that is and where it lives. In opencode it is `AGENTS.md` under the user
config directory; other harnesses use their own name and their own location.

The rule is present if that file has a section about knowledge bundles naming `fkb`. How it
got there does not matter and there is nothing to do. If the file exists and has no such
section, it is missing. If there is no such file at all, the person has never had
user-level instructions, and the subscription below creates one.

## The rule is subscribed to, not pasted in

**This skill does not carry the text of its own rule.** A pasted copy is one that nothing
can update: it would sit in a file no release reaches, while the authoritative wording moved
on, and neither copy would know about the other. So the rule lives beside this skill in the
repository, at `rules/fkb.md`, and `akit` is what carries it to the file your harness reads.

`akit` subscribes to skills and rules from ordinary git repositories and writes them where
each harness looks. One command takes both halves of this one:

```sh
uvx --from federated-agent-kits akit add --global ftschindler/federated-knowledge-skills fkb
```

The skill and the rule carry one name, so that is one kit, and `akit` renders both: the
skill into the skills directory every harness reads, the rule into whichever shape each
harness it detects wants. It needs `uv`, which this skill's own CLI needs anyway, and it
installs nothing permanently.

**Ask before running it, once.** Everywhere else this skill proposes a command and runs it,
because the thing it writes is a bundle somebody asked for. This one writes into the file
that loads on every session they run, for every project, including the work that has nothing
to do with knowledge bundles - and it starts a manifest of subscriptions they have not asked
for either. One sentence saying what it does, then run it when they say yes.

Three things to say once it has run:

- **What it wrote**, which `uvx --from federated-agent-kits akit list` reports.
- **How to undo it**: `uvx --from federated-agent-kits akit remove --global fkb` drops the
  subscription and deletes the copies it wrote, leaving anything the person wrote themselves
  alone.
- **That the hand-placed copy of this skill is now a second one**, if there is one, and an
  offer to delete it. You are still running from that old copy until the session reloads, so
  say that too rather than letting the next answer come from a file that was deleted.

## When it cannot run

Three cases end here: they say no, `uv --version` fails and they decline to install it, or
`akit` has no adapter for the harness they use and renders nothing for it.

**Then say where the text is rather than reciting it.** The rule is `rules/fkb.md` in
[this skill's repository](https://github.com/ftschindler/federated-knowledge-skills): its
body, without the frontmatter, goes into their instructions file as its own section. Say
plainly that a copy placed this way is theirs from then on, and that no upgrade will touch
it.

Three properties matter more than the exact wording, and are worth preserving if it is
adapted:

- **It names the trigger phrases.** An agent will not guess that "my notes" means a bundle.
- **It defers everything procedural to the skill**, so the two cannot drift apart. Anything
  about how to file, what a concept must carry, or which bundle to choose belongs in the
  skill and not here.
- **It fails silent.** A machine without the skill installed loses nothing and sees no error.

It is also deliberately short. It loads on every session, including the overwhelming
majority that never touch a bundle, so its only job is to make the skill reachable.

## Their own words for bundles

The phrases in the rule are the generic ones. Someone who regularly calls a bundle something
the manifest does not - "my notes" for the bundle registered as `private`, "work" for the
team one - is describing a mapping nothing on disk knows, and a session that has to ask about
it will have to ask again tomorrow. One line in the same file settles it:

```markdown
- "my notes" is the `private` bundle; "the work wiki" is `team`; "what does Felix say" means
  `ftschindler`.
```

**It goes in their own part of the file, outside anything `akit` marked as its own.** A
rendered rule is a disposable copy: `akit` rewrites it whole on every render, so a line added
inside its markers survives until the next render and then is gone without a message. Their
own section of the same file is never touched.

**Upstreams attract this more than anything else.** They are registered under their owner's
name, because a subject is never exclusive and an owner is - but people then refer to them by
person ("what does Felix think"), by subject ("the engineering practice one"), or by project,
and only one of those is what the manifest says. The mapping is one line and it is stable for
as long as the bundle is registered.

This is where it goes because it is the only file that outlives the session the phrase was
learned in. The other honest answer is to rename the bundle, which is the better one when the
manifest name is simply *wrong* rather than merely different from what they say out loud.
Offer both and let them choose; as above, propose rather than write.
