---
name: bootstrap-project
description: "Set up Specification-First Agentic Development in a new or existing project. Triggers when the user asks to 'set up spec-first', 'bootstrap the methodology', 'initialize project structure', or wants to add contexts/ and phase tracking to their project."
user-invocable: true
---

# Bootstrap Project

Set up the Specification-First Agentic Development methodology in a project.

## What You Create (v2.1 layout)

```
.{project-name}/
  contexts/
    default/                  # single-stack default. Monorepos add more:
      context.yaml            #   contexts/server/, contexts/client/, ...
      coding-principles.md
  decisions/                  # one YAML file per decision; filename = phase-or-run id + slug
  memory/
    MEMORY.md                 # experiential-memory index; one entry file per memory beside it
  phases/
    planned/                  # upcoming specs
    active/                   # current work (max 1)
    done/                     # completed phases
```

Plus a `CLAUDE.md` (or equivalent prompt file) at the project root.

**Why this layout:**
- `contexts/<name>/` per stack. Single-stack projects use `contexts/default/`. Monorepos add siblings (`contexts/server/`, `contexts/client/`, `contexts/docs/`) — each with its own `context.yaml` (with `workdir:` pointing at the sub-tree) and its own `coding-principles.md`.
- `decisions/` only. One YAML file per decision; filename `<phase-id>-<slug>.yaml` or `<run-id>-<slug>.yaml`. No flat `decisions.md` append-log.
- `memory/` holds typed Markdown facts (one file per memory, `MEMORY.md` as index) — the experiential-memory store agent-smith runs and IDE sessions share.

## Steps

### 1. Choose the directory name

Ask the user what their project is called. The methodology directory is `.{project-name}/` (e.g., `.myapp/`, `.backend/`). If the project already has a name, use it.

### 2. Detect single-stack vs. monorepo

Inspect the project root. If it clearly contains multiple stacks (separate package roots — e.g., `server/` + `client/`, or `apps/api/` + `apps/web/`), ask the user whether to bootstrap them as separate contexts now or start with `contexts/default/` and split later. Default: start with `default/`, split later — the rest of the methodology supports growth.

### 3. Analyze the codebase

Before writing any files, analyze each target stack to extract:
- **Stack**: runtime, language, frameworks, testing tools, SDKs
- **Architecture**: patterns, layers, module structure
- **Naming conventions**: actual conventions used in existing code
- **Quality rules**: line limits, test patterns, principles already followed
- **Workdir**: the relative path from the repo root where this stack lives (`.` for single-stack at root, `src/Server` for a sub-tree)

Don't invent conventions — extract them from what's already there. For greenfield projects, ask the user about their preferences.

### 4. Create the directory structure

Create:
- `.{project-name}/contexts/<name>/` for each target stack (`default/` for single-stack)
- `.{project-name}/decisions/`
- `.{project-name}/memory/`
- `.{project-name}/phases/planned/`, `phases/active/`, `phases/done/`

### 5. Write each context's `context.yaml`

Use the template at `templates/contexts/default/context.yaml` as a starting point. Per stack:
- Set `meta.workdir` to that stack's sub-tree path (`.` for single-stack default at the repo root).
- Set `methodology.version` to the plugin's current version (read from `.claude-plugin/plugin.json`).
- Fill `stack`, `arch`, `quality` from what step 3 found.
- Leave `state.{done,active,planned}` empty for greenfield, or seed with what already exists.

```yaml
# yaml-language-server: $schema=../../context.schema.json
meta:
  project: {project-name}
  version: 0.1.0
  type: [{type}]
  purpose: "{one-line description}"
  workdir: "."                        # relative path; "." = repo root, "src/Server" = monorepo sub
methodology:
  version: "2.1.0"
stack: {...}
arch: {...}
quality: {...}
state:
  done: {}
  active: {}
  planned: {}
```

### 6. Write each context's `coding-principles.md`

This file is **prescriptive**: it tells an agent *how new code must be written* in
this stack, in the imperative ("Controllers are thin — inject `IMediator` and only
`Send`"). It is **not** a description of the project. Use the codebase as *evidence
for which rules apply* — not as content to transcribe.

**The failure mode to avoid:** a file that inventories the target framework, package
versions, and middleware order and calls that "principles". Those are observations,
not principles — no one can write new code from them. If a section states a fact
without a rule, it belongs at the **end** under a "Build facts to preserve" heading,
never at the top. A `coding-principles.md` whose first sections are csproj/build
archaeology has failed, even if every fact in it is correct.

Required sections, each written as rules:
- **Language policy** — the non-negotiable language rule.
- **Architecture / the "red thread"** — the single path every feature follows
  (request → handler → persistence → response), the layers, and where each type
  lives, named for *this* stack. This is the most important section and the one a
  facts-dump omits entirely. Include a small flow diagram and a "where things live" table.
- **Hard limits** — method size, class size, types per file, constructor params.
- **Naming conventions** — the actual casing/suffix rules of this stack.
- **Design principles** — SOLID, composition over inheritance, one-responsibility, DI.
- **Error handling** — how errors are thrown, caught, logged.
- **Testing** — framework, naming, AAA.
- **What NOT to do** — the concrete anti-patterns for this stack.
- **(last) Build facts to preserve** — framework version, build flags, middleware
  order: only what a change must not break, kept at the bottom.

See `example-coding-principles.md` in this skill for a filled-in reference (a layered
.NET / MediatR API) — an *example of the shape*, not a template to copy. Different
stacks have different conventions (C# `PascalCase`, TypeScript `camelCase`, Python
`snake_case`) and a different red thread; each `contexts/<name>/coding-principles.md`
is self-contained for its stack. `templates/contexts/default/coding-principles.md` is
the minimal skeleton for a greenfield project with no code to derive rules from.

### 7. Decisions directory

Create `.{project-name}/decisions/` empty. The `/spec-first:log-decision` skill writes one YAML file per decision at `decisions/<phase-id>-<slug>.yaml`. Do not seed it with placeholder content.

### 8. Memory store

Create `.{project-name}/memory/` with a `MEMORY.md` index copied from
`templates/memory/MEMORY.md`. The store opens EMPTY of entries — one Markdown
file per memory lands beside the index later (frontmatter `name` kebab-slug,
`description` one line, `metadata.type` in `feedback` | `project` |
`reference`; see `templates/memory/example-memory.md` for the entry
convention). Do not distil "memories" from the codebase at bootstrap:
memories arrive from future sessions and runs, and a `feedback` entry becomes
policy only after the operator ratifies it.

### 9. Write CLAUDE.md

Create a `CLAUDE.md` at the project root, based on `templates/prompt.md`, with:
- Context-file read order pointing at the new layout: 1. glob `contexts/*/context.yaml`, 2. each context's `coding-principles.md`, 3. `phases/active/*.yaml`, 4. `decisions/*.yaml`, 5. `memory/MEMORY.md` (recall entry detail on demand)
- The remember/recall discipline section (memory vs decision boundary, curation rules)
- The 10-step implementation workflow
- Key rules from the contexts' coding-principles
- Phase directory structure explanation

### 10. Confirm with the user

Show what you created and ask the user to review. The methodology is now ready — they can start writing their first phase spec.

## Reference example

`example-coding-principles.md` (in this skill directory) is a filled-in, fully
prescriptive `coding-principles.md` for one stack. Read it before writing step 6 —
it is the target shape (red thread first, build facts last).

## Templates

This skill references templates from the plugin's `templates/` directory:
- `templates/contexts/default/context.yaml`
- `templates/contexts/default/coding-principles.md`
- `templates/decisions/p0001-example-decision.yaml` (shape reference, not copied as-is)
- `templates/memory/MEMORY.md` (copied as the empty index) and `templates/memory/example-memory.md` (entry-shape reference, not copied)
- `templates/prompt.md` (basis for the root CLAUDE.md)
- `templates/decision.schema.json` and `templates/phase-spec.schema.json` (copy to `.{project}/` so editors validate)

These are structural guides — always adapt content to the actual project.
