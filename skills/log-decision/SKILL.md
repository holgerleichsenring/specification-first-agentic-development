---
name: log-decision
description: "Log an architectural or design decision as a YAML file under decisions/. Triggers when the user makes a choice between alternatives, says 'log this decision', 'record this choice', or when a non-obvious design decision is made during implementation."
user-invocable: true
---

# Log Decision

Write a decision as a structured YAML file under `.{project}/decisions/`. Decisions capture the **why** behind choices — the code shows the what, but six months later nobody remembers the reasoning.

## When to Log

Log a decision when:
- Choosing between two or more viable approaches
- Rejecting a common or expected pattern for a specific reason
- Accepting a trade-off (performance vs. readability, simplicity vs. flexibility)
- Making a security-relevant choice
- Choosing a tool, library, or framework

Don't log:
- Obvious choices (using the project's language, following established patterns)
- Temporary decisions ("I'll refactor this later")
- Style preferences already covered by `coding-principles.md`

## File Naming Convention

One decision per file. Filename = `<phase-or-run-id>-<slug>.yaml`:

| Source              | Filename example                                  |
|---------------------|---------------------------------------------------|
| Phase decision      | `decisions/p0042-adapter-pattern-for-providers.yaml` |
| Run-attached note   | `decisions/r07-emergency-rollback-rationale.yaml` |

Multiple decisions per phase → multiple files sharing the prefix:
- `decisions/p0042-adapter-pattern.yaml`
- `decisions/p0042-no-sdk-for-github.yaml`
- `decisions/p0042-rejected-repository-pattern.yaml`

Glob `p0042-*.yaml` to see every decision for that phase.

## YAML Shape

```yaml
# yaml-language-server: $schema=../decision.schema.json
phase: p0042                  # OR: run: r07   (exactly one)
category: Architecture        # Architecture | Tooling | Implementation | TradeOff | Security
chose: "<one-line summary of what was picked>"
over: "<one-line summary of the obvious rejected alternative>"
reason: |
  Multi-line explanation. Cite constraints, prior incidents,
  related decisions via [[other-decision-slug]].
alternatives:                 # optional
  - "<one-line — what else was considered, why rejected>"
```

| Category         | Use when                                                          |
|------------------|-------------------------------------------------------------------|
| `Architecture`   | Structural decisions: patterns, layers, module boundaries         |
| `Tooling`        | Library, framework, or tool choices                               |
| `Implementation` | How something is built (algorithm, data structure, approach)      |
| `TradeOff`       | Accepting a limitation for a specific benefit                     |
| `Security`       | Security-relevant choices                                         |

Use `Architecture` for major structural choices. If the natural fit is "explicitly NOT this", capture it as `chose` describing the chosen-by-omission and put the rejected option in `over` and `alternatives`.

## Steps

### 1. Identify the phase or run

Check which phase is currently active in `.{project}/contexts/<name>/context.yaml` (`state.active`). If multiple contexts have active phases, ask the user which one this decision belongs to. If no phase is active, ask whether the decision attaches to a phase ID (planned/done) or to a run ID.

### 2. Compose the YAML

Author a slug (lower-kebab-case, ~3–6 words capturing the decision). Build the filename `<id>-<slug>.yaml`.

Draft the YAML body:
- `chose:` and `over:` each ONE LINE.
- `reason:` multi-line; lead with the load-bearing constraint, not the conclusion.
- `alternatives:` optional; only when there were other named candidates worth recording.

### 3. Write the file

Write to `.{project}/decisions/<id>-<slug>.yaml`. Do NOT append to a flat log file — v2.0 has no `decisions.md`.

### 4. Confirm

Show the user the YAML and the file path. If they want to refine the wording, edit the file.

## Examples

`decisions/p0042-adapter-pattern-for-providers.yaml`:

```yaml
phase: p0042
category: Architecture
chose: "Adapter pattern for ticket providers"
over: "Direct SDK coupling per provider"
reason: |
  Lets GitHub/Jira/AzureDevOps swap behind one ITicketProvider without
  touching application logic. Each SDK surface stays isolated in
  Infrastructure; the rest of the codebase sees only the contract.
alternatives:
  - "Repository pattern — rejected, overkill for read-mostly ticket data"
  - "One handler per provider — rejected, duplicates the orchestration loop"
```

`decisions/p0042-no-sdk-for-github.yaml`:

```yaml
phase: p0042
category: TradeOff
chose: "Raw HttpClient for GitHub API"
over: "Octokit SDK"
reason: |
  Octokit adds 3 MB of transitive deps for 4 API calls we actually
  need. Raw HttpClient with a small typed wrapper is leaner and the
  responses are stable JSON.
```

`decisions/r07-emergency-rollback-rationale.yaml`:

```yaml
run: r07
category: Implementation
chose: "Rollback the last 3 commits via revert, not reset"
over: "git reset --hard HEAD~3 + force push"
reason: |
  The branch was already pushed and other operators had pulled it.
  Force-pushing would have orphaned their work. Three explicit revert
  commits preserve history and let downstream branches merge cleanly.
```
