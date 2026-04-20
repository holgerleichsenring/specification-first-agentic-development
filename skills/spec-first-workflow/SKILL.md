---
name: spec-first-workflow
description: "Specification-First Agentic Development methodology guide. Triggers when a project has a .yourproject/ directory structure (context.yaml, phases/, decisions.md) or when the user mentions spec-first development."
user-invocable: true
---

# Specification-First Agentic Development

You are working in a project that follows the Specification-First Agentic Development methodology. This means documentation is a first-class development artifact — every feature starts as a specification, every decision gets logged, and you read context files in a defined order before writing code.

## Core Loop

```
Discuss → Write Spec → planned/ → active/ → done/ → decisions.md updated
```

## Context Read Order

Before starting any work, read these files in order:

1. `.yourproject/context.yaml` — architecture, stack, integrations, phase status
2. `.yourproject/coding-principles.md` — code quality rules (ALWAYS follow)
3. `.yourproject/phases/active/` — spec for the current phase
4. `.yourproject/decisions.md` — past architectural decisions (for consistency)

Replace `.yourproject/` with the actual project directory name (e.g., `.agentsmith/`, `.myapp/`).

## Available Skills

This plugin provides specialized skills for each part of the workflow:

| Skill | When to use |
|-------|-------------|
| `/spec-first:bootstrap-project` | Setting up the methodology in a new or existing project |
| `/spec-first:create-phase` | Planning a new feature, refactor, or task |
| `/spec-first:execute-phase` | Implementing the active phase |
| `/spec-first:log-decision` | Recording an architectural or design decision |
| `/spec-first:update-project` | Syncing methodology files with a newer plugin version |

## The 10-Step Implementation Workflow

For every phase, follow this order:

1. **Write phase spec first** — create `phases/planned/p{NN}-slug.yaml` with goal, steps, and done criteria. No code until the spec exists.
2. **Move to active** — move the phase file from `planned/` to `active/`.
3. **Plan first** — explore the codebase, design the approach, get human approval before coding.
4. **Implement step by step** — contracts/models first, then implementation, then wiring, then tests.
5. **Build after each step** — fix errors immediately, don't accumulate them.
6. **Run ALL tests** — zero failures before moving on.
7. **Log decisions** — append to `decisions.md` under `## p{NN}: Phase Title`.
8. **Update state** — move phase from `active` to `done` in `context.yaml`.
9. **Move phase file** — move from `active/` to `done/`.
10. **Commit** — one commit per phase, descriptive message.

## Key Rules

- **English only** — all code, comments, docs, exceptions, logs, commit messages.
- **No over-engineering** — only build what the phase requires, nothing more.
- **Tests** — every new public method gets at least one test.
- **Follow coding-principles.md** — these are constraints, not suggestions.
- **Specification is the contract** — the spec defines what gets built. No scope creep.
