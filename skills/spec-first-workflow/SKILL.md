---
name: spec-first-workflow
description: "Specification-First Agentic Development methodology guide. Triggers when a project has a .yourproject/ directory structure (contexts/, phases/, decisions/) or when the user mentions spec-first development."
user-invocable: true
---

# Specification-First Agentic Development

You are working in a project that follows the Specification-First Agentic Development methodology. This means documentation is a first-class development artifact — every feature starts as a specification, every decision gets logged, and you read context files in a defined order before writing code.

## Core Loop

```
Discuss → Write Spec → planned/ → active/ → done/ → decisions/<phase>-<slug>.yaml written per choice
```

## Directory Layout (v2.1)

```
.yourproject/
  contexts/<name>/
    context.yaml              # per-stack: stack, arch, quality, state, workdir
    coding-principles.md      # per-stack: language rules (AI reads every session)
  decisions/
    <phase-id>-<slug>.yaml    # one decision per file; phase ID prefix groups them
    <run-id>-<slug>.yaml      # run-attached decisions
  memory/
    MEMORY.md                 # experiential-memory index (one line per memory)
    <name>.md                 # one typed Markdown fact per file
  phases/
    planned/  active/  done/
      {id}-feature-slug.yaml
```

Single-stack projects have one context: `contexts/default/`. Monorepos add siblings — `contexts/server/`, `contexts/client/`, `contexts/docs/` — each with its own `workdir:` pointing at that stack's sub-tree of the repo.

## Context Read Order

Before starting any work, read these files in order:

1. **Every** `.yourproject/contexts/<name>/context.yaml` (glob `contexts/*/context.yaml`) — architecture, stack, integrations, phase status PER stack.
2. **Every** `.yourproject/contexts/<name>/coding-principles.md` — code quality rules per stack (ALWAYS follow). Different contexts can have different conventions.
3. `.yourproject/phases/active/` — spec for the current phase. Note its `applies_to:` field — it tells you which context's principles dominate when conflicts arise.
4. Relevant `.yourproject/decisions/<phase-id>-*.yaml` files — past decisions for the active phase and its `requires:` chain. Glob broader if you need historical context.
5. `.yourproject/memory/MEMORY.md` — the experiential-memory index, one line per recorded fact. Recall detail from `memory/<name>.md` on demand when an index line touches your task.

Replace `.yourproject/` with the actual project directory name (e.g., `.agentsmith/`, `.myapp/`).

**Decisions vs memory — the boundary:** a decision records a CHOICE made at a point in time (chose/over/reason — it lives in `decisions/`, written via `/spec-first:log-decision`); a memory records a transferable FACT or RULE that future work consults (it lives in `memory/`: `feedback` = ratified operator preference, `project` = goal/constraint/state not derivable from code or git, `reference` = external pointer). `log-decision` never writes `memory/`, and memory writes never land in `decisions/` — distil a decision's durable lesson into a memory entry when one exists, never copy the decision itself.

## Available Skills

This plugin provides specialized skills for each part of the workflow:

| Skill | When to use |
|-------|-------------|
| `/spec-first:bootstrap-project` | Setting up the methodology in a new or existing project |
| `/spec-first:create-phase` | Planning a new feature, refactor, or task |
| `/spec-first:execute-phase` | Implementing the active phase |
| `/spec-first:log-decision` | Recording an architectural or design decision |
| `/spec-first:update-project` | Syncing methodology files with a newer plugin version (and migrating v1 → v2) |

## The 10-Step Implementation Workflow

For every phase, follow this order:

1. **Write phase spec first** — create `phases/planned/{id}-slug.yaml` with goal, `applies_to:`, steps, done criteria. No code until the spec exists. The id is minted from the clock — today's UTC date plus four random hex digits, e.g. `2026-08-24-8a3f` — never from a count of what already exists, so it can be minted offline and in parallel. Counter ids (`p0042`) from older projects stay valid forever and are never renamed.
2. **Move to active** — move the phase file from `planned/` to `active/`.
3. **Plan first** — explore the codebase(s) the phase touches (filtered by `applies_to:`), design the approach, get human approval before coding.
4. **Implement step by step** — contracts/models first, then implementation, then wiring, then tests. Follow the relevant context's coding-principles.
5. **Build after each step** — fix errors immediately, don't accumulate them.
6. **Run ALL tests** — zero failures before moving on.
7. **Log decisions** — write one YAML per non-obvious choice to `decisions/<phase-id>-<slug>.yaml`. Multiple decisions per phase = multiple files sharing the prefix.
8. **Update state** — move phase from `active` to `done` in the relevant context's `context.yaml`.
9. **Move phase file** — move from `active/` to `done/`.
10. **Commit** — one commit per phase, descriptive message.

## Key Rules

- **English only** — all code, comments, docs, exceptions, logs, commit messages, decisions.
- **No over-engineering** — only build what the phase requires, nothing more.
- **Tests** — every new public method gets at least one test.
- **Follow the relevant context's coding-principles.md** — these are constraints, not suggestions.
- **Specification is the contract** — the spec defines what gets built. No scope creep.
- **Respect context boundaries** — a phase with `applies_to: server` doesn't drift into `client/`.
