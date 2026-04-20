---
name: log-decision
description: "Log an architectural or design decision to decisions.md. Triggers when the user makes a choice between alternatives, says 'log this decision', 'record this choice', or when a non-obvious design decision is made during implementation."
user-invocable: true
---

# Log Decision

Append a decision entry to the project's `decisions.md` file. Decisions capture the **why** behind choices — the code shows the what, but six months later nobody remembers the reasoning.

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
- Style preferences already covered by coding-principles.md

## Format

Each entry goes under the current phase heading in `decisions.md`:

```markdown
## p{NN}: Phase Title

- [Category] What was chosen -- why, and what alternatives were rejected
```

### Categories

| Category | Use when |
|----------|----------|
| `Architecture` | Structural decisions: patterns, layers, module boundaries |
| `Tooling` | Library, framework, or tool choices |
| `Implementation` | How something is built (algorithm, data structure, approach) |
| `TradeOff` | Accepting a limitation for a specific benefit |
| `Security` | Security-relevant choices |
| `Rejected` | Documenting what was considered but not chosen (and why) |

## Steps

### 1. Identify the phase

Check which phase is currently active in `context.yaml`. If no phase is active, ask the user which phase this decision belongs to.

### 2. Read existing decisions

Read `decisions.md` to check if a heading for this phase already exists. If it does, append under it. If not, create the heading.

### 3. Write the entry

Format: `- [Category] Decision -- rationale`

The rationale should answer:
- What alternatives existed?
- Why was this one chosen?
- What trade-off was accepted?

### 4. Confirm

Show the user what was logged. If they want to refine the wording, update it.

## Examples

```markdown
- [Architecture] Adapter pattern for ticket providers -- allows GitHub/Jira/AzureDevOps
  to swap without touching application logic
- [TradeOff] No SDK for GitHub, raw HttpClient -- SDK added 3MB of transitive deps
  for 4 API calls we actually need
- [Rejected] Repository pattern considered -- overkill for read-mostly ticket data
- [Security] JWT validation against JWKS endpoint, not shared secret -- zero-trust
  boundary between services
```
