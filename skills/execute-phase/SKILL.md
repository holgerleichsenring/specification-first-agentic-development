---
name: execute-phase
description: "Implement the active phase following the 10-step workflow. Triggers when the user references an active phase file, says 'implement this phase', 'execute the phase', 'start working on p{NN}', or has a phase in the active/ directory."
user-invocable: true
---

# Execute Phase

Implement the currently active phase following the Specification-First workflow. The spec is the contract — build exactly what it says, nothing more.

## Before You Start

1. Read context files in order:
   - **Every** `.{project}/contexts/<name>/context.yaml` — glob `contexts/*/context.yaml`. Each context describes one stack (single-stack projects have just `contexts/default/`). Read each one to know the architecture, stack, and what's been built per sub-tree.
   - **Every** `.{project}/contexts/<name>/coding-principles.md` — these are constraints per stack, not suggestions. Different contexts can have different conventions (C# vs. TypeScript).
   - The active phase spec in `phases/active/`.
   - Relevant past decisions: `decisions/<phase-id>-*.yaml` for the active phase and for any phase listed in `requires:`. Also glob `decisions/*.yaml` if you need to consult the broader history.

2. If there is no phase in `active/`, ask the user which planned phase to start. Move it from `planned/` to `active/`.

3. If the active phase has `applies_to:` set, prefer the matching context's `coding-principles.md` over others when there's a conflict. `applies_to:` is free text — interpret it against the context names in `contexts/`.

## The 10 Steps

### Step 1: Understand the spec

Read the phase spec completely. Identify:
- The goal (what and why)
- `applies_to:` (which stack(s)) — falls back to "all" if absent
- Each step and its deliverables (`new`, `modify`, `delete`)
- Test expectations
- Done criteria

If anything is unclear, ask the user before proceeding.

### Step 2: Plan the approach

Explore the codebase(s) the phase touches. For each context the phase affects:
- Where new code fits in the existing architecture
- What existing code will be modified
- What patterns are already established (follow them — per that context's coding-principles.md)

Present your plan to the user. Get approval before writing code.

### Step 3: Implement step by step

Follow the spec's `steps` array in order. For each step:
- Create or modify the files listed
- Follow the architecture patterns from the relevant `contexts/<name>/context.yaml`
- Follow the relevant context's coding principles strictly

**Order within each step**: contracts/interfaces first, then implementation, then DI wiring, then tests.

### Step 4: Build after each step

Run the build after completing each step. Fix errors immediately — don't accumulate broken state.

### Step 5: Run all tests

After implementation is complete, run the full test suite. Zero failures before moving on. If tests fail, fix them before proceeding.

### Step 6: Log decisions

For every non-obvious choice made during implementation, write a YAML file under `.{project}/decisions/`:

Filename: `<phase-id>-<slug>.yaml`. Multiple decisions per phase = multiple files all sharing the prefix.

```yaml
# yaml-language-server: $schema=../decision.schema.json
phase: p{NN}
category: Architecture     # | Tooling | Implementation | TradeOff | Security
chose: "<one-line>"
over: "<one-line alternative>"
reason: |
  Multi-line why.
alternatives:              # optional
  - "<other option — why rejected>"
```

Use the `/spec-first:log-decision` skill if you prefer interactive logging — it asks for the slug and writes the file for you.

### Step 7: Update context.yaml

Move the phase entry in the affected context(s):
- Remove from `state.active`
- Add to `state.done` with a one-line summary

If the phase touched multiple contexts, update each affected context's `context.yaml`. The phase ID is shared across contexts; the phase entry can live in whichever context owns it (often the one named in `applies_to:`).

### Step 8: Move phase file

Move the spec from `phases/active/` to `phases/done/`.

### Step 9: Verify done criteria

Go through every item in the spec's `done:` list. Confirm each one is satisfied. If any criterion is not met, address it before committing.

### Step 10: Commit

One commit per phase. Message format: `feat: {short description} (p{NN})`

## Rules During Execution

- **No scope creep** — if you notice something that should be fixed but isn't in the spec, note it for a future phase.
- **No premature abstraction** — three similar lines are better than a helper nobody asked for.
- **No silent decisions** — if you choose between alternatives, write a decision YAML.
- **Ask when stuck** — if the spec is ambiguous or the codebase contradicts the plan, ask the user rather than guessing.
- **Respect context boundaries** — when the phase touches one context (e.g. `applies_to: server`), don't drift into another (`client/`) "while you're there".
