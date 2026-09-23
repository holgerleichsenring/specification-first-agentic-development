---
name: create-phase
description: "Create a new phase specification for upcoming work. Triggers when the user wants to 'plan a new feature', 'write a phase spec', 'create a phase', or discusses upcoming work that should be captured as a spec."
user-invocable: true
---

# Create Phase

Write a phase specification for an upcoming unit of work. Every feature, refactor, or task starts as a spec before any code is written.

## Steps

### 1. Mint the phase id

A phase id is minted from the clock, never from a count: today's UTC date plus four random hex digits — `{yyyy-MM-dd}-{xxxx}`, e.g. `2026-08-24-8a3f`. Read the date off the machine you are on and take the four digits at random. Nothing else is consulted.

Minting therefore needs no knowledge of what anyone else has taken: a worktree cut this morning, a sandboxed agent with no network, and two agents working in parallel all mint safely, and the four hex digits give a 16-bit keyspace against a same-day collision. "What is the highest number so far?" is a question none of them can answer, and answering it wrongly is how two phases end up sharing one id.

The suffix's **fixed width** is what marks where the id ends and the slug begins. Counter ids a project already carries (`p0042`, `p0057a`) stay valid forever and are never renamed — that namespace is closed to NEW ids only.

### 2. Discuss scope with the user

Before writing the spec, understand:
- **What** is being built or changed?
- **Why** — what problem does this solve?
- **What's in scope** and what's explicitly out?
- **Which stack(s)** does it touch? Use the free-text `applies_to:` field — e.g., "server", "client + docs", "all stacks". Pick wording that matches the project's actual context names.
- **Dependencies** — does this require other phases to be done first?

### 3. Write the spec

Create the file at `.{project}/phases/planned/{id}-{slug}.yaml` using this format.
**Keep it short**: `{slug}` at most 50 characters and at least 4 words, `goal:` one sentence of at most 200, and the whole spec under **4,800 characters** — about 700 words of prose. An evidence register, where each claim carries the `file:line` that proves it, does not count toward that: a citation cannot be shortened without ceasing to be one. Limit your wording to what it takes to express the matter. The budget is one number for the whole file rather than a cap per field, so a phase spends it where it needs it.

The slug states what CHANGES (`a-phase-id-can-be-minted-offline`), not the area it changes (`mcp-tools-call`) — length alone does not tell a claim from a label, which is what the word floor is for.

```yaml
# yaml-language-server: $schema=../../phase-spec.schema.json
phase: {id}
goal: "One sentence — what we build and why (<= 200 chars)"

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

- **Goal fits in one line** — 200 characters. If it doesn't fit, the phase is too big. Split it.
- **A revision does not add** — a spec that comes back from review is rewritten within the same budget, not extended past it. What a round of review adds, it also displaces; a spec that grows with every round is how a one-page phase becomes ten.
- **Say it once** — do not restate the goal inside `scope:`, do not tell a future reader what not to conclude, and do not note that an existing rule still stands. What is out of scope is named, not argued.
- **Steps are imperative** — "Create X", "Add Y", "Modify Z". Not "we should consider".
- **Done criteria are verifiable** — someone can check each item as true/false.
- **Decisions capture the non-obvious** — don't log that you used the project's language. Log why you chose pattern A over pattern B. Decisions are written as separate YAML files under `decisions/<phase-id>-<slug>.yaml` during execution; the `decisions:` array in the spec captures decisions that were already made WHEN WRITING THE SPEC.
- **`applies_to:` is free text** — no enum, no validation. Match the project's existing context names so readers can grep `contexts/<name>/` and find the relevant stack.
- **Tests use AAA naming** — `Method_Scenario_Expected`.

### 5. Update context.yaml

Add the new phase to the `planned` section of the relevant context's `context.yaml`. If `applies_to:` names a single context, update only that one. If it spans multiple, pick the one with primary ownership (or all of them if the work genuinely splits):

```yaml
planned:
  {id}: "Short description -> .yourproject/phases/planned/{id}-slug.yaml"
```

### 6. Confirm with the user

Show the spec and ask for approval before considering it done.

## Examples

See the `examples/` directory in this skill for reference specs:

- `simple-phase.yaml` — a straightforward feature addition
- `refactor-phase.yaml` — a refactoring phase with rename/delete operations
