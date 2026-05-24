---
name: bootstrap-project
description: "Set up Specification-First Agentic Development in a new or existing project. Triggers when the user asks to 'set up spec-first', 'bootstrap the methodology', 'initialize project structure', or wants to add contexts/ and phase tracking to their project."
user-invocable: true
---

# Bootstrap Project

Set up the Specification-First Agentic Development methodology in a project.

## What You Create (v2.0 layout)

```
.{project-name}/
  contexts/
    default/                  # single-stack default. Monorepos add more:
      context.yaml            #   contexts/server/, contexts/client/, ...
      coding-principles.md
  decisions/                  # one YAML file per decision; filename = phase-or-run id + slug
  phases/
    planned/                  # upcoming specs
    active/                   # current work (max 1)
    done/                     # completed phases
```

Plus a `CLAUDE.md` (or equivalent prompt file) at the project root.

**Why this layout:**
- `contexts/<name>/` per stack. Single-stack projects use `contexts/default/`. Monorepos add siblings (`contexts/server/`, `contexts/client/`, `contexts/docs/`) — each with its own `context.yaml` (with `workdir:` pointing at the sub-tree) and its own `coding-principles.md`.
- `decisions/` only. One YAML file per decision; filename `<phase-id>-<slug>.yaml` or `<run-id>-<slug>.yaml`. No flat `decisions.md` append-log.

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
  version: "2.0.0"
stack: {...}
arch: {...}
quality: {...}
state:
  done: {}
  active: {}
  planned: {}
```

### 6. Write each context's `coding-principles.md`

Extract the actual coding principles from the codebase of that stack. Use `templates/contexts/default/coding-principles.md` as the structural guide. Sections:
- Language policy
- Hard limits (method size, class size, types per file)
- Naming conventions
- Architecture principles
- Error handling approach
- Testing conventions
- What NOT to do

Different stacks have different conventions — C# `PascalCase`, TypeScript `camelCase`, Python `snake_case`. Each `contexts/<name>/coding-principles.md` is self-contained for its stack.

### 7. Decisions directory

Create `.{project-name}/decisions/` empty. The `/spec-first:log-decision` skill writes one YAML file per decision at `decisions/<phase-id>-<slug>.yaml`. Do not seed it with placeholder content.

### 8. Write CLAUDE.md

Create a `CLAUDE.md` at the project root with:
- Context-file read order pointing at the new layout (glob `contexts/*/context.yaml`, glob `decisions/*.yaml`)
- The 10-step implementation workflow
- Key rules from the contexts' coding-principles
- Phase directory structure explanation

### 9. Confirm with the user

Show what you created and ask the user to review. The methodology is now ready — they can start writing their first phase spec.

## Templates

This skill references templates from the plugin's `templates/` directory:
- `templates/contexts/default/context.yaml`
- `templates/contexts/default/coding-principles.md`
- `templates/decisions/p0001-example-decision.yaml` (shape reference, not copied as-is)
- `templates/decision.schema.json` and `templates/phase-spec.schema.json` (copy to `.{project}/` so editors validate)

These are structural guides — always adapt content to the actual project.
