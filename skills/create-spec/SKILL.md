---
name: create-spec
description: "Create a new spec for upcoming work. Triggers when the user wants to 'plan a new feature', 'write a spec', 'create a spec' (or a phase), or discusses upcoming work that should be captured as a spec."
user-invocable: true
---

# Create Spec

Write a specification for an upcoming unit of work. Every feature, refactor, or task starts as a spec before any code is written.

## Steps

### 1. Mint the spec id

A spec id is minted from the clock, never from a count: today's UTC date plus four random hex digits — `{yyyy-MM-dd}-{xxxx}`, e.g. `2026-08-24-8a3f`. Read the date off the machine you are on and take the four digits at random. Nothing else is consulted.

Minting therefore needs no knowledge of what anyone else has taken: a worktree cut this morning, a sandboxed agent with no network, and two agents working in parallel all mint safely, and the four hex digits give a 16-bit keyspace against a same-day collision. "What is the highest number so far?" is a question none of them can answer, and answering it wrongly is how two specs end up sharing one id.

The suffix's **fixed width** is what marks where the id ends and the label begins. Counter ids a project already carries (`p42`, `p0042`, `p0057a`) stay valid forever and are never renamed — that namespace is closed to NEW ids only.

**Specs cut from one piece of work form a series**: they share one minted number and differ by an appended lowercase letter — `2026-08-24-8a3fa`, `2026-08-24-8a3fb`. The letter is appended, never dashed; the bare number names no spec; a series is minted in one go, and a spec that turns up later mints its own number and says in prose what it follows.

### 2. Discuss scope with the user

Before writing the spec, understand:
- **What** is being built or changed?
- **Why** — what problem does this solve?
- **What's in scope** and what's explicitly out?
- **Which stack(s)** does it touch? Use the free-text `applies_to:` field — e.g., "server", "client + docs", "all stacks". Pick wording that matches the project's actual context names.
- **Dependencies** — does this require other specs to be done first?

### 3. Write the spec

Create the file at `.{project}/specs/planned/{id}-{label}.yaml` using this format.
**Keep it short**: `{label}` 2 to 5 words and at most 50 characters, `goal:` one sentence of at most 200, and the whole spec under **4,800 characters** — about 700 words of prose. The `facts:` register, where each claim carries the `file:line` that proves it, does not count toward that: a citation cannot be shortened without ceasing to be one. Limit your wording to what it takes to express the matter. The budget is one number for the whole file rather than a cap per field, so a spec spends it where it needs it.

The label is a **topic, area first** (`checkpoint-partial-restore`, `account-base-ref-search`): the leading word names the subject area, so kin group in a directory listing. The claim belongs in `goal:`, which has room and grammar a file name has not. Labels may repeat; the id is the identity.

```yaml
# yaml-language-server: $schema=../../spec.schema.json
spec: {id}
goal: "One sentence — what we build and why (<= 200 chars)"

applies_to: "server"   # optional free-text scope hint — match the project's contexts/<name> vocabulary

requires: []  # spec IDs or preconditions

facts:        # what you READ in the code — open the file before citing it
  - claim: "what is true of the code today"
    evidence: "src/Api/OrderHandler.cs:34-41"
assumptions:  # what the spec rests on that you did NOT open a file to confirm
  - claim: "what you expect"
    check: "how to confirm it before building"

scope:
  in: "what this spec changes"
  out: "what it deliberately leaves, and where that goes"

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

- **Goal fits in one line** — 200 characters. If it doesn't fit, the spec is too big. Split it.
- **A revision does not add** — a spec that comes back from review is rewritten within the same budget, not extended past it. What a round of review adds, it also displaces; a spec that grows with every round is how a one-page spec becomes ten.
- **Say it once** — do not restate the goal inside `scope:`, do not tell a future reader what not to conclude, and do not note that an existing rule still stands. What is out of scope is named, not argued.
- **Facts come from the code** — every fact cites a file (and lines) you opened; what you did not open is an assumption. Evidence that is not a file — a log, a scan, a conversation — starts with `observed:` and carries its date. In a project with no code yet, `facts: []` is the honest statement.
- **Steps are imperative** — "Create X", "Add Y", "Modify Z". Not "we should consider".
- **Done criteria are verifiable** — someone can check each item as true/false.
- **Decisions capture the non-obvious** — don't log that you used the project's language. Log why you chose pattern A over pattern B. Decisions are written as separate YAML files under `decisions/<spec-id>.yaml` during execution; the `decisions:` array in the spec captures decisions that were already made WHEN WRITING THE SPEC.
- **`applies_to:` is free text** — no enum, no validation. Match the project's existing context names so readers can grep `contexts/<name>/` and find the relevant stack.
- **Tests use AAA naming** — `Method_Scenario_Expected`.

### 5. Update context.yaml

Add the new spec to the `planned` section of the relevant context's `context.yaml`. If `applies_to:` names a single context, update only that one. If it spans multiple, pick the one with primary ownership (or all of them if the work genuinely splits):

```yaml
planned:
  {id}: "Short description -> .yourproject/specs/planned/{id}-label.yaml"
```

### 6. Confirm with the user

Show the spec and ask for approval. Do not go on until the user approves.

### 7. Commit the spec on a spec branch, in its own worktree

A worktree cut from the default branch does not contain an uncommitted spec, so the spec and its planned entry are committed there first. From the repository root:

```bash
git fetch origin 2>/dev/null || true
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo main)   # e.g. origin/main
wt="../$(basename "$PWD")-{id}"                                                       # outside the repo
git worktree add -b "spec/{id}" "$wt" "$base"
mkdir -p "$wt/.{project}/specs/planned"
mv .{project}/specs/planned/{id}-{label}.yaml "$wt/.{project}/specs/planned/"
git diff -- .{project}/contexts | git -C "$wt" apply                                  # the planned entry
git checkout -- .{project}/contexts
git -C "$wt" add .{project}
git -C "$wt" commit -m "spec: {id} {short description}"
```

The id is not in parentheses: that form marks the spec's one delivering commit (deliver-spec), which a project's commit gate may key on. If `git apply` fails because the default branch moved, add the planned entry to the worktree's `context.yaml` by hand. All further work on this spec happens in `$wt`; tell the user its path.

### 8. Review the spec

Run `/spec-first:review-spec` on the committed spec. No code before its verdict is BUILD, or BUILD WITH CUTS with the cuts applied.

## Examples

See the `examples/` directory in this skill for reference specs:

- `simple-spec.yaml` — a straightforward feature addition
- `refactor-spec.yaml` — a refactoring spec with rename/delete operations
