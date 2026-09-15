# Federation: several bundles, and what may cross between them

One bundle needs none of this. The moment there are two at different privacy tiers, three
questions appear that a single directory never had to answer: which one does this belong in,
may this one mention that one, and what does a link between them even look like.

## Tiers are a property of the workspace, not of the content

Nothing inside a concept records how private it is. Sensitivity is carried by **which bundle
the file is in**, and the manifest is what says what each bundle allows:

```yaml
public:
  path: ./public/docs
  referenceable_by: "*"        # anyone may cite it
  writable: true
  publish:
    url: https://example.com/kb/
    style: directory

private:
  path: ./private
  referenceable_by: []         # sealed: nobody may cite it
  writable: true
```

This is why "which bundle?" is a real decision rather than filing paperwork. Moving a
concept later costs one commit. Putting it in the wrong bundle costs whatever it disclosed.

**In doubt, take the most private bundle you may write to.**

## The reference rule

> A concept in bundle **A** may reference a concept in bundle **B** if `A` is `B`, or if `A`
> is listed in `B.referenceable_by`.

`referenceable_by` is **inbound**. It lists who may point at this bundle, not who this bundle
may point at, because disclosure runs in that direction: a link from a published page into a
private one exposes the private one, and the published bundle is not who should get to decide
that.

Two consequences that look asymmetric and are not:

- A sealed bundle may still cite a public one. Linking *out* of a private bundle discloses
  nothing; linking *into* it is what would.
- A bundle needs a `publish` value to be linked **to**, and needs nothing at all to link
  **out**.

## Citing across bundles

Bundles do not know about each other. Two consequences follow, and the second is the useful
one:

- **A relative path cannot work.** `../../other-bundle/docs/thing.md` is a fact about one
  disk. It breaks when either bundle is published, cloned elsewhere, or checked out at a
  different depth, and it breaks silently.
- **Only the workspace can produce the link**, because only it sees both bundles at once.

So ask it:

```text
uv run SKILLDIR/scripts/fkb url <target-bundle> <path/inside/it.md> --from <bundle-you-are-writing-in>
```

It prints one absolute URL, and that is what goes in the markdown link.

**Never hand-write a cross-bundle URL**, even when you can see what it would be. The command
is not doing string concatenation on your behalf; it is checking that the link is allowed to
exist at all, and the URL is what you get *instead of* a refusal.

### The refusals, and what each means

| What it says | What happened | What fixes it |
| --- | --- | --- |
| `A` may not cite `B` | The reference rule refused. This is a policy answer, not a formatting one | `B`'s `referenceable_by`, if the link is genuinely meant to exist |
| `B` has no published location | `B` is real and citable, but nowhere for a URL to point | Give `B` a `publish` entry - it may name where it *will* live |
| not a file in `B` | The path does not exist in the target bundle | The path, usually a typo or a concept that moved |

A refusal is information. Do not route around it by writing the URL yourself, and do not
fall back to a relative path: both turn a checked link into an unchecked one, and the first
also turns a policy violation into a committed file.

`--from` is required and has no default. The rule is a question about a *pair* of bundles,
and the citing half is the one nothing on disk knows - you are the only one who knows which
bundle you are writing into.

## What lint sees that `url` cannot

`fkb url` refuses a bad link when someone asks for one. `fkb lint` reads the links that are
already there and applies the same rule to them, by matching each absolute URL against the
bundles it knows and working out which one it points into.

That covers the cases `url` never saw: a link pasted by hand, one written before the policy
existed, and one that became a violation when `referenceable_by` was tightened afterwards.

```text
uv run SKILLDIR/scripts/fkb lint            # every bundle
uv run SKILLDIR/scripts/fkb lint <bundle>   # one of them
```

Findings in a bundle this machine cannot write to are reported as warnings and never block.
An upstream written against an older version of the format is not a failure state, and a
check that fails on what nobody here can fix is one people learn to scroll past - along with
the finding that mattered.

## Which bundle does this belong in?

In order, stopping at the first that answers:

1. **The person named one.** Use it. If more than one could match what they said, ask which.
   If none matches, say what does exist.
2. **The content decides.** Anything about an employer, a client, a person's circumstances,
   or anything under an obligation not to share it, goes somewhere sealed. If you are
   weighing it, that is the answer.
3. **Still unsure.** Most private writable bundle.

Check `writable` before writing, not after. A bundle registered read-only on this machine is
someone else's, and filing into it is the one mistake here that is somebody else's problem to
discover.
