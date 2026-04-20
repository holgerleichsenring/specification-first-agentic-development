---
name: execute-phase
description: "Implement the active phase following the 10-step workflow. Triggers when the user references an active phase file, says 'implement this phase', 'execute the phase', 'start working on p{NN}', or has a phase in the active/ directory."
user-invocable: true
---

# Execute Phase

Implement the currently active phase following the Specification-First workflow. The spec is the contract — build exactly what it says, nothing more.

## Before You Start

1. Read context files in order:
   - `context.yaml` — know the architecture, stack, and what's been built
   - `coding-principles.md` — these are constraints, not suggestions
   - The active phase spec in `phases/active/`
   - `decisions.md` — maintain consistency with past decisions

2. If there is no phase in `active/`, ask the user which planned phase to start. Move it from `planned/` to `active/`.

## The 10 Steps

### Step 1: Understand the spec

Read the phase spec completely. Identify:
- The goal (what and why)
- Each step and its deliverables (`new`, `modify`, `delete`)
- Test expectations
- Done criteria

If anything is unclear, ask the user before proceeding.

### Step 2: Plan the approach

Explore the codebase to understand:
- Where new code fits in the existing architecture
- What existing code will be modified
- What patterns are already established (follow them)

Present your plan to the user. Get approval before writing code.

### Step 3: Implement step by step

Follow the spec's `steps` array in order. For each step:
- Create or modify the files listed
- Follow the architecture patterns from `context.yaml`
- Follow the coding principles strictly

**Order within each step**: contracts/interfaces first, then implementation, then DI wiring, then tests.

### Step 4: Build after each step

Run the build after completing each step. Fix errors immediately — don't accumulate broken state.

### Step 5: Run all tests

After implementation is complete, run the full test suite. Zero failures before moving on. If tests fail, fix them before proceeding.

### Step 6: Log decisions

For every non-obvious choice made during implementation, append to `decisions.md`:

```markdown
## p{NN}: Phase Title

- [Category] What was chosen -- why, and what alternatives existed
```

Categories: `Architecture`, `Tooling`, `Implementation`, `TradeOff`, `Security`

Use the `/spec-first:log-decision` skill if you prefer interactive logging.

### Step 7: Update context.yaml

Move the phase entry:
- Remove from `active`
- Add to `done` with a one-line summary
- Update `done-recently` if the project uses that section

### Step 8: Move phase file

Move the spec from `phases/active/` to `phases/done/`.

### Step 9: Verify done criteria

Go through every item in the spec's `done:` list. Confirm each one is satisfied. If any criterion is not met, address it before committing.

### Step 10: Commit

One commit per phase. Message format: `feat: {short description} (p{NN})`

## Rules During Execution

- **No scope creep** — if you notice something that should be fixed but isn't in the spec, note it for a future phase.
- **No premature abstraction** — three similar lines are better than a helper nobody asked for.
- **No silent decisions** — if you choose between alternatives, log it.
- **Ask when stuck** — if the spec is ambiguous or the codebase contradicts the plan, ask the user rather than guessing.
