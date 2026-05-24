---
name: log-decision
description: "Append an architectural or design decision to the active phase's YAML file under decisions/. Triggers when the user makes a choice between alternatives, says 'log this decision', 'record this choice', or when a non-obvious design decision is made during implementation."
user-invocable: true
---

# Log Decision

Append a decision entry to the phase's YAML file under `.{project}/decisions/`. Decisions capture the **why** behind choices — the code shows the what, but six months later nobody remembers the reasoning.

## When to Log

Log a decision when:
- Choosing between two or more viable approaches
- Rejecting a common or expected pattern for a specific reason
- Accepting a trade-off (performance vs. readability, simplicity vs. flexibility)
- Making a security-relevant choice
- Choosing a tool, library, or framework
- Narrowing a phase's scope (in/out trade-offs)

Don't log:
- Obvious choices (using the project's language, following established patterns)
- Temporary decisions ("I'll refactor this later")
- Style preferences already covered by `coding-principles.md`

## File Convention

**One YAML file per phase.** Filename = `<phase-or-run-id>.yaml`:

| Source                | Filename          |
|-----------------------|-------------------|
| Phase decisions       | `decisions/p0042.yaml` |
| Run-attached note     | `decisions/r07.yaml`   |

The file holds ALL decisions made within that phase or run. Multiple decisions for one phase = multiple entries in the same file's `decisions:` array. Glob `decisions/p0042.yaml` to see every decision for that phase; cat `decisions/*.yaml` to dump everything.

## YAML Shape

```yaml
# yaml-language-server: $schema=../decision.schema.json
phase: p0042                # OR: run: r07   (exactly one — must match filename)

decisions:
  - category: Architecture
    chose: "<one-line summary of what was picked>"
    over: "<one-line summary of the obvious rejected alternative>"   # optional
    reason: |
      Multi-line explanation. Cite constraints, prior incidents,
      related decisions via [[other-phase-id]].
    alternatives:           # optional
      - "<one-line — what else was considered, why rejected>"

  - category: TradeOff
    chose: "..."
    reason: |
      ...
```

| Category         | Use when                                                          |
|------------------|-------------------------------------------------------------------|
| `Architecture`   | Structural decisions: patterns, layers, module boundaries         |
| `Tooling`        | Library, framework, or tool choices                               |
| `Implementation` | How something is built (algorithm, data structure, approach)      |
| `TradeOff`       | Accepting a limitation for a specific benefit                     |
| `Security`       | Security-relevant choices                                         |
| `Scope`          | In/out trade-offs at phase boundaries                             |

Only `category` and `chose` are required. `over`, `reason`, `alternatives` are optional — but encouraged for non-trivial decisions.

## Steps

### 1. Identify the phase or run

Check which phase is currently active in `.{project}/contexts/<name>/context.yaml` (`state.active`). If multiple contexts have active phases, ask the user which one this decision belongs to. If no phase is active, ask whether the decision attaches to a phase ID (planned/done) or to a run ID.

### 2. Read or create the phase decision file

Target path: `.{project}/decisions/<phase-id>.yaml`.

- If it exists: read it, preserve its `phase:` (or `run:`) field and its existing `decisions:` entries.
- If it doesn't exist: create a fresh file with the schema header, the `phase:` (or `run:`) field, and an empty `decisions:` array ready to receive the new entry.

### 3. Compose the new entry

Author the entry following the shape above. Lead with `category` and `chose:`. Add `over:`, `reason:`, and `alternatives:` only when they apply.

### 4. Append to the file

Add the new entry to the END of the `decisions:` array (chronological order). Do not rewrite or reorder existing entries.

### 5. Confirm

Show the user the new entry and the file path. If they want to refine the wording, edit the file.

## Examples

`decisions/p0042.yaml` (after two decisions logged in phase p0042):

```yaml
# yaml-language-server: $schema=../decision.schema.json
phase: p0042

decisions:
  - category: Architecture
    chose: "Adapter pattern for ticket providers"
    over: "Direct SDK coupling per provider"
    reason: |
      Lets GitHub/Jira/AzureDevOps swap behind one ITicketProvider without
      touching application logic. Each SDK surface stays isolated in
      Infrastructure; the rest of the codebase sees only the contract.
    alternatives:
      - "Repository pattern — rejected, overkill for read-mostly ticket data"

  - category: TradeOff
    chose: "Raw HttpClient for GitHub API"
    over: "Octokit SDK"
    reason: |
      Octokit adds 3 MB of transitive deps for 4 API calls. Raw HttpClient
      with a small typed wrapper is leaner and the responses are stable JSON.
```

`decisions/r07.yaml` (a run-attached decision file):

```yaml
# yaml-language-server: $schema=../decision.schema.json
run: r07

decisions:
  - category: Implementation
    chose: "Rollback the last 3 commits via revert, not reset"
    over: "git reset --hard HEAD~3 + force push"
    reason: |
      The branch was already pushed and other operators had pulled it.
      Force-pushing would have orphaned their work. Three explicit revert
      commits preserve history and let downstream branches merge cleanly.
```
