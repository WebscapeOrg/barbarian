# Barbarian — agent notes

The bar-arranger panel for the Omarchy Quickshell bar (HYPER+B), with the former Reptile layouts panel merged in (HYPER+L). One plugin, one IPC id: `atlas.arrange`.

## Asking Dave for decisions

Questions go in `docs/open-questions.md` and Dave settles them through Pickle — read `docs/settled-questions.md` before asking anything. The contract lives in `~/.local/share/pickle/agent-instructions.md`.

## Work from Dave

```markdown
## Work from Dave: Carrot

Carrot is where Dave hands an agent a thing to pick up and run with. Before you start work in a
repository, read `~/.local/share/carrot/agent-instructions.md` and follow it: it says how to see what
waits for you (`carrot list --mine`), how to take one, and how the record of finishing it comes
back to Dave (`docs/agent-closed-tasks.md`). Do not copy its contents into this file or any other
file: it is kept in one place so that a change to it reaches every agent.

```

## Things Dave should open

```markdown
## Showing Dave your work: Peacock

A report, a review, a demo recording or a set of screenshots is something Dave should open, not
read in a chat window. Before you start work in a repository, read
`~/.local/share/peacock/agent-instructions.md` and follow it: it says how to publish one with
`peacock publish`, where it lands (`docs/published/`, never committed), and how Dave and other
agents see it. Do not copy its contents into this file or any other file: it is kept in one place
so that a change to it reaches every agent.

```
