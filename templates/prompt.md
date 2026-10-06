# Project Name -- AI Agent Instructions

## Context Files (read in this order)

1. **Every** `.yourproject/contexts/<name>/context.yaml` (glob `contexts/*/context.yaml`) -- architecture, stack, integrations, spec status PER stack
2. **Every** `.yourproject/contexts/<name>/coding-principles.md` -- code quality rules per stack (ALWAYS follow)
3. `.yourproject/specs/active/*.yaml` -- the spec being implemented (its `applies_to:` names the dominant context)
4. `.yourproject/decisions/*.yaml` -- past decisions, one YAML per spec or run (read the active spec's file and its `requires:` chain)
5. `.yourproject/memory/MEMORY.md` -- the experiential-memory index, one line per recorded fact; recall detail from `.yourproject/memory/<name>.md` on demand when a line touches your task

## Spec Directory Structure

```
.yourproject/specs/
  done/       # completed specs (historical reference)
  active/     # spec currently being worked on (max 1)
  planned/    # upcoming specs with requirements
```

## Experiential Memory (remember / recall)

`.yourproject/memory/` holds typed Markdown facts: one file per memory with
frontmatter `name` (kebab-slug = filename), `description` (one line), and
`metadata.type` (`feedback` = how the operator wants the agent to work,
ratification required; `project` = goals/constraints/state not derivable from
code or git; `reference` = external pointers). `MEMORY.md` is the index --
one line per memory, content never in the index.

- **Recall before re-deriving**: when the index hints at a fact you are about
  to work out from scratch, read the entry file instead.
- **Remember sparingly**: store what code and git cannot already tell the
  next agent -- one fact per file; check the index for an existing entry and
  update rather than duplicate; delete a memory that turns out wrong; link
  related memories as `[[slug]]` (a cited slug requires its committed
  definition). A new or changed `feedback` entry is a PROPOSAL until the
  operator ratifies it.
- **Memory vs decision**: a decision records a CHOICE (`decisions/`); a
  memory records a transferable FACT or RULE. Never duplicate one into the
  other.

## Implementation Workflow (follow this order for every spec)

1. **Write spec first** -- create `.yourproject/specs/planned/{id}-slug.yaml` with goal, `applies_to:`, steps, and definition of done BEFORE writing any code. No exceptions.
2. **A worktree per spec** -- commit the spec and its planned entry on branch `spec/{id}` in a new worktree cut from the default branch; all work on the spec happens there.
3. **Review the spec** -- run review-spec: the evidence script must pass and a fresh reviewer must answer BUILD (or BUILD WITH CUTS, cuts applied) before any code.
4. **Move to active** -- move the spec file from `planned/` to `active/` when starting work.
5. **Plan first** -- explore codebase, design approach, get user approval before coding.
6. **Implement step by step** -- contracts/models first, then implementation, then wiring, then tests.
7. **Build after each step** -- fix errors immediately, don't accumulate them.
8. **Run ALL tests** -- the contexts' `verify:` stages and every other check; zero failures before moving on.
9. **Log decisions** -- one YAML per spec at `.yourproject/decisions/{id}.yaml`; each entry: what was chosen, what alternatives existed, and why.
10. **Update state** -- move spec from `planned`/`active` to `done` in the relevant context's `context.yaml`.
11. **Move to done** -- move the spec file from `active/` to `done/`.
12. **Deliver** -- run deliver-spec: verify stages, one commit `feat: {short description} ({id})`, push, pull request.

## Key Rules

- **English only** -- all code, comments, docs, exceptions, logs, commit messages.
- **No over-engineering** -- only build what the spec requires, nothing more.
- **Tests** -- every new public method gets at least one test.
- **Follow each context's coding-principles.md** -- these are constraints, not suggestions.
