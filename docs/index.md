# starcheck docs

The README is the pitch. This folder is the reference.

- [SCORECARD.md](SCORECARD.md) — every check, its weight, and the exact evidence it reads
- [LAUNCH.md](LAUNCH.md) — how this repo itself was launched (the playbook, unedited)

## The one idea

Star count is not a code-quality metric. It is:

```
stars  ≈  exposure  ×  first-screen conversion  ×  reuse frequency
```

`starcheck` can only measure the middle term honestly, and it is the one you
control completely. The other two are distribution work, which is why the tool
refuses to give you a "viral" score and stops at 100.

## Why weights, not a checklist

A checklist tells you 20 things are wrong and you fix none of them. Weights
force an order. A `fail` on a weight-5 check (README hook, install command, GIF)
costs more than four weight-1 checks, because that is how a stranger's attention
actually works: they leave in the first screen.

## Why some checks are `skip`

Local mode cannot know your repo description, topics, or homepage — those live
on GitHub, not on disk. `skip` removes the item from the denominator instead of
pretending it failed, so a local score stays comparable with a remote one.

Run `starcheck owner/repo` (or `starcheck . --remote owner/repo`) to fill them in.

## Limits

- It cannot see stars, traffic, or conversion. It scores *readiness*, not results.
- It cannot judge whether your project is interesting. A 100 here with a boring
  idea is still a boring idea.
- It has no opinion about your architecture, and it never will.
