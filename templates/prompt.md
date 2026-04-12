# Project Name -- AI Agent Instructions

## Context Files (read in this order)

1. `.yourproject/context.yaml` -- architecture, stack, integrations, phase status
2. `.yourproject/coding-principles.md` -- code quality rules (ALWAYS follow)
3. `.yourproject/phases/active/p{NN}-*.md` -- spec for the phase being implemented
4. `.yourproject/decisions.md` -- past architectural decisions (for consistency)

## Phase Directory Structure

```
.yourproject/phases/
  done/       # completed phases (historical reference)
  active/     # phase currently being worked on (max 1)
  planned/    # upcoming phases with requirements
```

## Implementation Workflow (follow this order for every phase)

1. **Write phase spec first** -- create `.yourproject/phases/planned/p{NN}-slug.md` with goal, scope, and definition of done BEFORE writing any code. No exceptions.
2. **Move to active** -- move the phase file from `planned/` to `active/` when starting work.
3. **Plan first** -- explore codebase, design approach, get user approval before coding.
4. **Implement step by step** -- contracts/models first, then implementation, then wiring, then tests.
5. **Build after each step** -- fix errors immediately, don't accumulate them.
6. **Run ALL tests** -- ensure zero failures before moving on.
7. **Log decisions** -- append to `.yourproject/decisions.md` under `## p{NN}: Phase Title`. Each entry: what was chosen, what alternatives existed, and why.
8. **Update state** -- move phase from `planned`/`active` to `done` in `context.yaml`.
9. **Move to done** -- move the phase file from `active/` to `done/`.
10. **Commit** -- one commit per phase, descriptive message.

## Key Rules

- **English only** -- all code, comments, docs, exceptions, logs, commit messages.
- **No over-engineering** -- only build what the phase requires, nothing more.
- **Tests** -- every new public method gets at least one test.
- **Follow coding-principles.md** -- these are constraints, not suggestions.
