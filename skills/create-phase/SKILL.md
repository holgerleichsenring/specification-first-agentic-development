---
name: create-phase
description: "Create a new phase specification for upcoming work. Triggers when the user wants to 'plan a new feature', 'write a phase spec', 'create a phase', or discusses upcoming work that should be captured as a spec."
user-invocable: true
---

# Create Phase

Write a phase specification for an upcoming unit of work. Every feature, refactor, or task starts as a spec before any code is written.

## Steps

### 1. Determine the phase number

Read `context.yaml` and find the highest phase number in `done`, `active`, and `planned`. The new phase is the next number (e.g., if the last is p42, the new one is p43). Use letter suffixes (p43a, p43b) for sub-phases of related work.

### 2. Discuss scope with the user

Before writing the spec, understand:
- **What** is being built or changed?
- **Why** — what problem does this solve?
- **What's in scope** and what's explicitly out?
- **Dependencies** — does this require other phases to be done first?

### 3. Write the spec

Create the file at `.{project}/phases/planned/p{NN}-{slug}.yaml` using this format:

```yaml
# yaml-language-server: $schema=../../phase-spec.schema.json
phase: p{NN}
goal: "One line — what we're building and why"

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
- **Decisions capture the non-obvious** — don't log that you used the project's language. Log why you chose pattern A over pattern B.
- **Tests use AAA naming** — `Method_Scenario_Expected`.

### 5. Update context.yaml

Add the new phase to the `planned` section:

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
