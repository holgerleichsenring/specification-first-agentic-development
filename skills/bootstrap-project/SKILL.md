---
name: bootstrap-project
description: "Set up Specification-First Agentic Development in a new or existing project. Triggers when the user asks to 'set up spec-first', 'bootstrap the methodology', 'initialize project structure', or wants to add context.yaml and phase tracking to their project."
user-invocable: true
---

# Bootstrap Project

Set up the Specification-First Agentic Development methodology in a project.

## What You Create

```
.{project-name}/
  context.yaml              # central state tracker
  coding-principles.md      # code quality rules
  decisions.md              # decision log
  phases/
    planned/                # upcoming specs
    active/                 # current work (max 1)
    done/                   # completed phases
```

Plus a `CLAUDE.md` (or equivalent prompt file) at the project root.

## Steps

### 1. Choose the directory name

Ask the user what their project is called. The methodology directory is `.{project-name}/` (e.g., `.myapp/`, `.backend/`). If the project already has a name, use it.

### 2. Analyze the codebase

Before writing any files, analyze the existing codebase to extract:
- **Stack**: runtime, language, frameworks, testing tools, SDKs
- **Architecture**: patterns, layers, module structure
- **Naming conventions**: actual conventions used in existing code
- **Quality rules**: line limits, test patterns, principles already followed

Don't invent conventions — extract them from what's already there. For greenfield projects, ask the user about their preferences.

### 3. Create the directory structure

Create the `.{project-name}/` directory with subdirectories `phases/planned/`, `phases/active/`, `phases/done/`.

### 4. Write context.yaml

Use the template below as a starting point. Fill in everything you discovered in step 2.

The `methodology.version` field tracks which version of the Spec-First methodology was used to bootstrap. Set it to `1.0.0`.

```yaml
# yaml-language-server: $schema=context.schema.json
meta:
  project: {project-name}
  version: 0.1.0
  type: [{type}]
  purpose: "{one-line description}"

methodology:
  version: "1.0.0"

stack:
  runtime: {runtime}
  lang: {language}
  infra: [{infrastructure}]
  testing: [{test frameworks}]
  sdks: [{sdks}]

arch:
  style: [{architecture style}]
  patterns: [{patterns}]
  layers:
    - {Layer1}
    - {Layer2}

quality:
  lang: english-only
  limits:
    method-lines: 20
    class-lines: 120
    types-per-file: 1
  principles: [SOLID, DRY, GuardClauses, FailFast]
  naming:
    classes: PascalCase
    # ... adapt to what you found in the codebase
  testing:
    style: AAA
    naming: "{Method}_{Scenario}_{Expected}"

state:
  done: {}
  active: {}
  planned: {}
```

### 5. Write coding-principles.md

Extract the actual coding principles from the codebase. Use the template in this plugin's `templates/coding-principles.md` as a structural guide, but fill it with what you actually observe. Sections to include:

- Language policy
- Hard limits (method size, class size, types per file)
- Naming conventions
- Architecture principles
- Error handling approach
- Testing conventions
- What NOT to do

### 6. Write decisions.md

Create with the starter template — just the header and format example. Don't fill in fake decisions.

```markdown
# Decision Log

<!--
For every phase, log the decisions that shaped the implementation.
Format: [Category] Decision -- rationale

Categories: Architecture, Tooling, Implementation, TradeOff, Security
-->
```

### 7. Write CLAUDE.md

Create a `CLAUDE.md` at the project root with:
- Context file read order
- The 10-step implementation workflow
- Key rules from coding-principles.md
- Phase directory structure explanation

### 8. Confirm with the user

Show what you created and ask the user to review. The methodology is now ready — they can start writing their first phase spec.

## Templates

This skill references templates from the plugin's `templates/` directory. These are structural guides — always adapt content to the actual project.
