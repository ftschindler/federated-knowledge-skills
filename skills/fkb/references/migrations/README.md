# Migration guides

One file per release that asks something of an existing setup, named for that release:
`0.2.0.md` covers the step from the release before it to `0.2.0`. `fkb migrate` finds the
ones a workspace still owes by comparing its recorded version against this skill's, and
prints their paths in order.

Most releases ask nothing and leave no file here. A gap in the series is the normal shape.

A guide is read by an agent and carried out as a conversation, so write it as instructions
to that agent, not as a changelog entry. It should say:

- **What changed**, in a sentence, from the point of view of somebody who has the old setup
  working and does not care what the release was called.
- **What to do**, concretely: the manifest field to add, the command to run, the question to
  put to the person. Name the fields and commands exactly.
- **What happens if they decline.** Most changes here are new capabilities rather than
  breakages, and "nothing, everything keeps working" is a common and useful answer.
- **How to tell it worked** - the output of `fkb list`, a file that now exists.

Do not tell the reader to stamp the version at the end. `fkb migrate --done` does that once,
after the last guide, and a guide that stamps on its own leaves the chain half recorded.
