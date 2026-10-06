---
name: spec-first-workflow
description: "Specification-First Agentic Development methodology guide. Triggers when a project has a .yourproject/ structure (contexts/, specs/, decisions/) or the user mentions spec-first."
user-invocable: true
---

# Specification-First Agentic Development

You are working in a project that follows the Specification-First Agentic Development methodology. This means documentation is a first-class development artifact — every feature starts as a specification, every decision gets logged, and you read context files in a defined order before writing code.

## Core Loop

```
Discuss → Write Spec → worktree + commit → review-spec → active/ → build → done/ → deliver-spec (verify, commit, PR)
```

## Directory Layout (v2.5)

```
.yourproject/
  contexts/<name>/
    context.yaml              # per-stack: stack, arch, quality, state, workdir
    coding-principles.md      # per-stack: language rules (AI reads every session)
  decisions/
    <spec-id>-<slug>.yaml    # one decision per file; spec ID prefix groups them
    <run-id>-<slug>.yaml      # run-attached decisions
  memory/
    MEMORY.md                 # experiential-memory index (one line per memory)
    <name>.md                 # one typed Markdown fact per file
  specs/
    planned/  active/  done/
      {id}-feature-slug.yaml  # plus same-stem companions ({id}-feature-slug.md, …)
  series/
    {base}.yaml               # optional, written by tools: one manifest per series
```

Single-stack projects have one context: `contexts/default/`. Monorepos add siblings — `contexts/server/`, `contexts/client/`, `contexts/docs/` — each with its own `workdir:` pointing at that stack's sub-tree of the repo.

`series/{base}.yaml` is written by a tool (agent-smith, for one) that cuts a series `{base}a`, `{base}b`, … from a ticket or a conversation: it names the source and lists the series' spec ids in order. The specs themselves stay in `specs/`. A series written by hand needs no manifest — its shared base already shows the kinship.

## Context Read Order

Before starting any work, read these files in order:

1. **Every** `.yourproject/contexts/<name>/context.yaml` (glob `contexts/*/context.yaml`) — architecture, stack, integrations, spec status PER stack.
2. **Every** `.yourproject/contexts/<name>/coding-principles.md` — code quality rules per stack (ALWAYS follow). Different contexts can have different conventions.
3. `.yourproject/specs/active/` — the current spec. Note its `applies_to:` field — it tells you which context's principles dominate when conflicts arise.
4. Relevant `.yourproject/decisions/<spec-id>-*.yaml` files — past decisions for the active spec and its `requires:` chain. Glob broader if you need historical context.
5. `.yourproject/memory/MEMORY.md` — the experiential-memory index, one line per recorded fact. Recall detail from `memory/<name>.md` on demand when an index line touches your task.

Replace `.yourproject/` with the actual project directory name (e.g., `.agentsmith/`, `.myapp/`).

**Decisions vs memory — the boundary:** a decision records a CHOICE made at a point in time (chose/over/reason — it lives in `decisions/`, written via `/spec-first:log-decision`); a memory records a transferable FACT or RULE that future work consults (it lives in `memory/`: `feedback` = ratified operator preference, `project` = goal/constraint/state not derivable from code or git, `reference` = external pointer). `log-decision` never writes `memory/`, and memory writes never land in `decisions/` — distil a decision's durable lesson into a memory entry when one exists, never copy the decision itself.

## Available Skills

This plugin provides specialized skills for each part of the workflow:

| Skill | When to use |
|-------|-------------|
| `/spec-first:bootstrap-project` | Setting up the methodology in a new or existing project |
| `/spec-first:create-spec` | Planning a new feature, refactor, or task; commits the spec on a spec branch in its own worktree |
| `/spec-first:review-spec` | Checking a spec's evidence and getting a fresh reviewer's verdict before any code |
| `/spec-first:apply-spec` | Implementing the active spec, up to its done criteria |
| `/spec-first:deliver-spec` | Running the verify stages, committing, pushing and opening the pull request |
| `/spec-first:log-decision` | Recording an architectural or design decision |
| `/spec-first:update-project` | Syncing methodology files with a newer plugin version (and migrating v1 → v2) |

## The 12-Step Implementation Workflow

For every spec, follow this order:

1. **Write spec first** — create `specs/planned/{id}-slug.yaml` with goal, `applies_to:`, steps, done criteria. No code until the spec exists. The id is minted from the clock — today's UTC date plus four random hex digits, e.g. `2026-08-24-8a3f` — never from a count of what already exists, so it can be minted offline and in parallel. Counter ids (`p0042`) from older projects stay valid forever and are never renamed.
2. **A worktree per spec** — commit the spec and its planned entry on branch `spec/{id}` in a new worktree cut from the default branch (create-spec does this). All work on the spec happens there.
3. **Review the spec** — `/spec-first:review-spec`: the evidence script resolves every cited file and line, then a fresh reviewer answers BUILD, BUILD WITH CUTS or REFUSE. No code before BUILD, or BUILD WITH CUTS with the cuts applied.
4. **Move to active** — move the spec file from `planned/` to `active/`.
5. **Plan first** — explore the codebase(s) the spec touches (filtered by `applies_to:`), design the approach, get human approval before coding.
6. **Implement step by step** — contracts/models first, then implementation, then wiring, then tests. Follow the relevant context's coding-principles.
7. **Build after each step** — fix errors immediately, don't accumulate them.
8. **Run ALL tests** — the contexts' `verify:` stages and every other check; zero failures before moving on.
9. **Log decisions** — one YAML per spec at `decisions/<spec-id>.yaml`, every non-obvious choice an entry in its `decisions:` list.
10. **Update state** — move spec from `active` to `done` in the relevant context's `context.yaml`.
11. **Move spec file** — move from `active/` to `done/`.
12. **Deliver** — `/spec-first:deliver-spec`: runs the `verify:` stages, commits once as `feat: {short description} ({id})`, pushes and opens the pull request.

## Key Rules

- **English only** — all code, comments, docs, exceptions, logs, commit messages, decisions.
- **No over-engineering** — only build what the spec requires, nothing more.
- **Tests** — every new public method gets at least one test.
- **Follow the relevant context's coding-principles.md** — these are constraints, not suggestions.
- **Specification is the contract** — the spec defines what gets built. No scope creep.
- **Respect context boundaries** — a spec with `applies_to: server` doesn't drift into `client/`.
