---
name: apply-spec
description: "Implement the active spec in its worktree, up to its done criteria. Triggers on 'implement this spec' (or phase), 'execute the spec', 'start working on {id}', or a spec in active/."
user-invocable: true
---

# Apply Spec

Implement the currently active spec following the Specification-First workflow. The spec is the contract — build exactly what it says, nothing more. Work in the spec's worktree (branch `spec/{id}`, created by create-spec); the commit, push and pull request belong to `/spec-first:deliver-spec`.

## Before You Start

1. Read context files in order:
   - **Every** `.{project}/contexts/<name>/context.yaml` — glob `contexts/*/context.yaml`. Each context describes one stack (single-stack projects have just `contexts/default/`). Read each one to know the architecture, stack, and what's been built per sub-tree.
   - **Every** `.{project}/contexts/<name>/coding-principles.md` — these are constraints per stack, not suggestions. Different contexts can have different conventions (C# vs. TypeScript).
   - The active spec in `specs/active/`.
   - Relevant past decisions: `decisions/<spec-id>.yaml` for the active spec and for any spec listed in `requires:`. Glob `decisions/*.yaml` if you need to consult the broader history.

2. If there is no spec in `active/`, ask the user which planned spec to start. Move it from `planned/` to `active/`.

3. Work in the spec's worktree: `git worktree list` shows it on branch `spec/{id}`. If there is none, create it as create-spec step 7 does. Its spec must have passed `/spec-first:review-spec`.

4. If the active spec has `applies_to:` set, prefer the matching context's `coding-principles.md` over others when there's a conflict. `applies_to:` is free text — interpret it against the context names in `contexts/`.

## The 9 Steps

### Step 1: Understand the spec

Read the spec completely. Identify:
- The goal (what and why)
- `applies_to:` (which stack(s)) — falls back to "all" if absent
- Each step and its deliverables (`new`, `modify`, `delete`)
- Test expectations
- Done criteria

If anything is unclear, ask the user before proceeding.

### Step 2: Plan the approach

Explore the codebase(s) the spec touches. For each context the spec affects:
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

### Step 5: Verify, then review

After implementation is complete, run the **full** verification — not just the unit tests, but every deterministic check the project defines — the contexts' `verify:` stages first, then unit tests, CLI/pipeline dry-runs, and any separate integration/harness executable. Zero failures before moving on. A project may enforce these as a blocking commit gate (e.g. a PreToolUse hook on `git commit`); treat that as the floor, not the ceiling, so the commit is never the first time they run.

Then check the green code is *good* — a judgment pass, best delegated to a fresh-eyes subagent, because a separate context catches what the author's does not:

1. **Principles** — walk the diff against each affected context's `coding-principles.md`; list every violation with file:line and fix it.
2. **Spec adherence** — the diff does what the spec says and nothing it doesn't.
3. **Refactoring** — surface what *should* improve; apply what is in scope, name a follow-up spec for the rest rather than dropping it.

Report the outcome to the user before moving on.

### Step 6: Log decisions

For every non-obvious choice made during implementation, append an entry to the spec's decision YAML at `.{project}/decisions/<spec-id>.yaml`.

**One file per spec.** All decisions for {id} live in `decisions/{id}.yaml` as entries in its `decisions:` array. Create the file on the first decision; append to it on subsequent decisions.

```yaml
# yaml-language-server: $schema=../decision.schema.json
spec: {id}

decisions:
  - category: Architecture     # | Tooling | Implementation | TradeOff | Security | Scope
    chose: "<one-line>"
    over: "<one-line alternative>"   # optional
    reason: |
      Multi-line why.
    alternatives:                    # optional
      - "<other option — why rejected>"
  - category: Implementation
    chose: "..."
    ...
```

Use the `/spec-first:log-decision` skill if you prefer interactive logging — it handles file creation, appending, and YAML formatting.

### Step 7: Update context.yaml

Move the spec entry in the affected context(s):
- Remove from `state.active`
- Add to `state.done` with a one-line summary

If the spec touched multiple contexts, update each affected context's `context.yaml`. The spec ID is shared across contexts; the spec entry can live in whichever context owns it (often the one named in `applies_to:`).

### Step 8: Move spec file

Move the spec from `specs/active/` to `specs/done/`.

### Step 9: Verify done criteria

Go through every item in the spec's `done:` list. Confirm each one is satisfied. If any criterion is not met, address it before handing over.

Then stop: do not commit. Run `/spec-first:deliver-spec` — it runs the project's verify stages, commits, pushes and opens the pull request.

## Rules During Execution

- **No scope creep** — if you notice something that should be fixed but isn't in the spec, note it for a future spec.
- **No premature abstraction** — three similar lines are better than a helper nobody asked for.
- **No silent decisions** — if you choose between alternatives, write a decision YAML.
- **Ask when stuck** — if the spec is ambiguous or the codebase contradicts the plan, ask the user rather than guessing.
- **Respect context boundaries** — when the spec touches one context (e.g. `applies_to: server`), don't drift into another (`client/`) "while you're there".
