---
name: create-phase
description: "Create a new phase specification for upcoming work. Triggers when the user wants to 'plan a new feature', 'write a phase spec', 'create a phase', or discusses upcoming work that should be captured as a spec."
user-invocable: true
---

# Create Phase

Write a phase specification for an upcoming unit of work. Every feature, refactor, or task starts as a spec before any code is written.

## Steps

### 1. Mint the phase id

Mint the id from the clock, not from a count: today's UTC date plus four random hex
digits, `{yyyy-MM-dd}-{xxxx}` — for example `2026-08-24-8a3f`. Take the date and the
random digits from the machine you are on; nothing else is consulted.

Minting needs no knowledge of what anyone else has taken, which is the point: a
worktree cut this morning, a sandboxed agent with no network and two people working in
parallel all mint safely, because the four hex digits carry a 16-bit keyspace against
same-day collision. Asking "what is the highest number so far" cannot be answered
offline, and answering it wrongly is how two phases end up sharing one id.

The suffix's FIXED WIDTH is what marks where the id ends and the descriptive slug
begins: `2026-08-24-8a3f-a-phase-id-can-be-minted-offline.yaml`.

Older projects carry counter ids (`p0042`, `p0057a`, `p0131c-pre`). That namespace stays
permanently valid and nothing minted from it is ever renamed — every existing id, every
`requires:` naming one and every commit message citing one keeps working. It is simply
closed to new ids.

### 2. Discuss scope with the user

Before writing the spec, understand:
- **What** is being built or changed?
- **Why** — what problem does this solve?
- **What's in scope** and what's explicitly out?
- **Which stack(s)** does it touch? Use the free-text `applies_to:` field — e.g., "server", "client + docs", "all stacks". Pick wording that matches the project's actual context names.
- **Dependencies** — does this require other phases to be done first?

### 3. Write the spec

Create the file at `.{project}/phases/planned/{id}-{slug}.yaml` using this format:

```yaml
# yaml-language-server: $schema=../../phase-spec.schema.json
phase: 2026-08-24-8a3f   # the id you minted in step 1
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
  2026-08-24-8a3f: "Short description -> .yourproject/phases/planned/2026-08-24-8a3f-slug.yaml"
```

### 6. Confirm with the user

Show the spec and ask for approval before considering it done.

## Examples

See the `examples/` directory in this skill for reference specs:

- `simple-phase.yaml` — a straightforward feature addition
- `refactor-phase.yaml` — a refactoring phase with rename/delete operations
