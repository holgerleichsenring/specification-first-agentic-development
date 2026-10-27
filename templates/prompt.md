# Project Name -- AI Agent Instructions

This file is the project's AGENTS.md: Codex, Cursor, Copilot and other coding agents read it at the
start of a session. Claude Code reads it through CLAUDE.md, which imports it with `@AGENTS.md`. Where a
step names a spec-first plugin command (Claude Code only), the same step says how to do it by hand.

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

1. **Write spec first** -- create `.yourproject/specs/planned/{id}-slug.yaml` with goal, `applies_to:`, steps, and definition of done BEFORE writing any code. No exceptions. The id is today's UTC date plus four random hex digits, e.g. `2026-08-24-8a3f`. (Plugin: `/spec-first:create-spec`.)
2. **A worktree per spec** -- commit the spec and its planned entry on branch `spec/{id}` in a new worktree cut from the default branch (`git worktree add -b spec/{id} ../<repo>-{id} origin/main`); all work on the spec happens there.
3. **Review the spec** -- before any code. (Plugin: `/spec-first:review-spec`.) By hand: run the evidence check, `python3 <spec-first clone>/skills/review-spec/scripts/check-evidence.py <spec>` (needs python3 and PyYAML), until it is clean; then open a fresh session with no history of this conversation, give it the spec, the goal in two or three sentences and the brief below, and apply its cuts. Build only on BUILD, or BUILD WITH CUTS with every cut applied.
4. **Move to active** -- move the spec file from `planned/` to `active/` when starting work.
5. **Plan first** -- explore codebase, design approach, get user approval before coding. (Plugin: `/spec-first:apply-spec` runs steps 4 to 11.)
6. **Implement step by step** -- contracts/models first, then implementation, then wiring, then tests.
7. **Build after each step** -- fix errors immediately, don't accumulate them.
8. **Test what you changed** -- the build and the affected tests while iterating; zero failures before moving on. The full `verify:` stages run once, at the spec commit, by the commit gate: the plugin's hook (`gate: plugin`, the default), the git commit-msg hook in this clone (`gate: git`, for every agent; install it with `python3 <spec-first clone>/hooks/install-git-hook.py`), or the project's own (`gate: project`). Without any of them, run the `verify:` commands by hand before the spec commit.
9. **Log decisions** -- one YAML per spec at `.yourproject/decisions/{id}.yaml`; each entry: what was chosen, what alternatives existed, and why. (Plugin: `/spec-first:log-decision`.)
10. **Update state** -- move spec from `planned`/`active` to `done` in the relevant context's `context.yaml`.
11. **Move to done** -- move the spec file from `active/` to `done/`.
12. **Deliver** -- one commit `feat: {short description} ({id})` through the gate, its verdict read in `spec-first-gate.log` in the git common directory, then push and open the pull request. (Plugin: `/spec-first:deliver-spec`.) `git commit --no-verify` skips the git hook: don't use it on a spec commit.

### The review brief

Give the fresh reviewer this text verbatim:

> Attack this spec before anyone builds it. Open every cited file around the cited lines — a valid citation is not a true claim. Follow every field, setting and value the spec touches to its sinks: who reads it, who writes it, what else breaks. Extract archives and generated files before reasoning about them. Check every step against the code as it is, not as the spec says it is. Answer with exactly one verdict — BUILD, BUILD WITH CUTS, or REFUSE — and back each finding with file:line evidence. For BUILD WITH CUTS name each cut precisely. REFUSE is a successful result when the spec is wrong. Check `upgrade_impact:` against what the steps will change: a new required setting, a changed default, a migration old instances cannot run beside, or a deploy file an operator must edit is an upgrade impact, and it is either opt-in or argued in the spec. A spec that consolidates or changes existing behaviour without a characterisation step is a finding.

## Key Rules

- **English only** -- all code, comments, docs, exceptions, logs, commit messages.
- **No over-engineering** -- only build what the spec requires, nothing more.
- **Tests** -- every new public method gets at least one test.
- **Follow each context's coding-principles.md** -- these are constraints, not suggestions.
