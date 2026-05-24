---
name: create-phase
description: "Create a new phase specification for upcoming work. Triggers when the user wants to 'plan a new feature', 'write a phase spec', 'create a phase', or discusses upcoming work that should be captured as a spec."
user-invocable: true
---

# Create Phase

Write a phase specification for an upcoming unit of work. Every feature, refactor, or task starts as a spec before any code is written.

## Steps

### 1. Determine the phase number

Glob `.{project}/contexts/*/context.yaml` and find the highest phase number across all contexts' `state.{done,active,planned}` sections (phase IDs are project-wide, not per-context). The new phase is the next number (e.g., if the last is p42, the new one is p43). Use letter suffixes (p43a, p43b) for sub-phases of related work.

### 2. Discuss scope with the user

Before writing the spec, understand:
- **What** is being built or changed?
- **Why** — what problem does this solve?
- **What's in scope** and what's explicitly out?
- **Which stack(s)** does it touch? Use the free-text `applies_to:` field — e.g., "server", "client + docs", "all stacks". Pick wording that matches the project's actual context names.
- **Dependencies** — does this require other phases to be done first?

### 3. Write the spec

Create the file at `.{project}/phases/planned/p{NN}-{slug}.yaml` using this format:

```yaml
# yaml-language-server: $schema=../../phase-spec.schema.json
phase: p{NN}
goal: "One line — what we're building and why"

applies_to: "server"   # optional free-text scope hint — match the project's contexts/<name> vocabulary

requires: []  # phase IDs or preconditions

decisions:
  - key: "non-obvious choice — why"

steps:
  - id: step-name
    action: "imperative, single line"
    new:
      - "TypeName: description"
    modify:
      - "TypeName: what changes"

tests:
  - "Method_Scenario_Expected"

done:
  - "verifiable completion criterion"
```

### 4. Key principles for good specs

- **Goal fits in one line** — if it doesn't, the phase is too big. Split it.
- **Steps are imperative** — "Create X", "Add Y", "Modify Z". Not "we should consider".
- **Done criteria are verifiable** — someone can check each item as true/false.
- **Decisions capture the non-obvious** — don't log that you used the project's language. Log why you chose pattern A over pattern B. Decisions are written as separate YAML files under `decisions/<phase-id>-<slug>.yaml` during execution; the `decisions:` array in the spec captures decisions that were already made WHEN WRITING THE SPEC.
- **`applies_to:` is free text** — no enum, no validation. Match the project's existing context names so readers can grep `contexts/<name>/` and find the relevant stack.
- **Tests use AAA naming** — `Method_Scenario_Expected`.

### 5. Update context.yaml

Add the new phase to the `planned` section of the relevant context's `context.yaml`. If `applies_to:` names a single context, update only that one. If it spans multiple, pick the one with primary ownership (or all of them if the work genuinely splits):

```yaml
planned:
  p{NN}: "Short description -> .yourproject/phases/planned/p{NN}-slug.yaml"
```

### 6. Confirm with the user

Show the spec and ask for approval before considering it done.

## Examples

See the `examples/` directory in this skill for reference specs:

- `simple-phase.yaml` — a straightforward feature addition
- `refactor-phase.yaml` — a refactoring phase with rename/delete operations
