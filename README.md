# Specification-First Agentic Development

A methodology for AI-assisted software development where **specifications drive implementation**.

It creates a straight forward, stable and traceable pattern for implementations with every available coding agent. 

## The Problem

When working with AI coding agents, three things go wrong repeatedly:

1. **Context amnesia**: the AI loses track of what was built and why between sessions
2. **Architectural drift**: without constraints, the AI makes inconsistent decisions
3. **Decision rationale vanishes**: six months later, nobody knows *why* a particular approach was chosen

## The Solution

Treat documentation as a **first-class development artifact**. Every feature starts as a specification. Every decision gets logged. The AI agent reads context files in a defined order before writing a single line of code.

## Core Principles

### 1. Specification Before Code

Every unit of work (called a **phase**) starts as a markdown file that defines:
- **Goal**: what we're building and why
- **Scope**: exactly what's in and out
- **Prerequisites**: what must exist before starting
- **Definition of Done**: checkboxes that must all pass

No code is written until the spec exists. The spec is the contract between human and AI.

### 2. Central State Tracking

A single `context.yaml` file serves as the source of truth:
- Project metadata (stack, architecture, integrations)
- Quality constraints (coding conventions, naming rules, limits)
- Phase status (done / active / planned) as compressed information

The AI reads this first, every time. It knows what exists, what's being built, and what's coming.

### 3. Decision Capture

Every phase produces entries in a `decisions.md` log:
- What was chosen
- What alternatives existed
- Why this approach won

This transforms implicit tribal knowledge into explicit, searchable history.

### 4. Phase Workflow

Phases flow through three states:

```
planned/  -->  active/  -->  done/
```

- **Planned**: spec written, waiting for implementation
- **Active**: currently being implemented (max one at a time)
- **Done**: completed, archived with updated checklists

### 5. Quality as Contract

Coding principles aren't suggestions -- they're load-bearing constraints:
- Hard limits (method length, class size, types per file)
- Naming conventions (enforced, not aspirational)
- Architecture patterns (defined, not discovered)

The AI reads these before every session and operates within them.

## Directory Structure

```
.yourproject/
  context.yaml                        # central state tracker
  coding-principles.md                # code quality rules
  decisions.md                        # decision log (why, not what)
  phases/
    planned/                          # upcoming specs
      p{NN}-feature-slug.md
    active/                           # current work (max 1)
      p{NN}-feature-slug.md
    done/                             # completed phases
      p{NN}-feature-slug.md
  runs/                               # execution logs (optional)
```

## AI Agent Instructions

The AI agent receives a `prompt.md` (or `CLAUDE.md`) that defines:

1. **Read order**: which files to read and in what sequence
2. **Workflow**: the step-by-step process for every phase
3. **Rules**: non-negotiable conventions and constraints

See [templates/prompt.md](templates/prompt.md) for a complete example.

## Implementation Workflow

For every phase, the AI follows this order:

1. **Read context**: context.yaml, coding principles, active phase spec
2. **Plan**: explore codebase, design approach, get human approval
3. **Implement**: contracts first, then implementation, then wiring, then tests
4. **Verify**: build after each step, run all tests
5. **Log decisions**: append to decisions.md
6. **Update state**: move phase to done in context.yaml
7. **Commit**: one commit per phase

## Getting Started

### Option A: Bootstrap Prompt (recommended)

Paste this prompt into your AI agent (Claude Code, ChatGPT, etc.) to set up the structure automatically:

```
I want to set up specification-first agentic development for this project.

1. Create a `.yourproject/` directory (replace "yourproject" with my project name) with:
   - context.yaml: fill in the stack, architecture, layers, quality rules,
     and naming conventions based on what you see in the codebase.
   - coding-principles.md: extract the actual conventions from the existing code
     (language, limits, naming, patterns, testing style).
   - decisions.md: empty starter with the template header.
   - phases/planned/: empty directory
   - phases/active/: empty directory
   - phases/done/: empty directory

2. Create a .claude/prompt.md (or CLAUDE.md) with:
   - Read order: context.yaml -> coding-principles.md -> active phase -> decisions.md
   - The 10-step implementation workflow (spec first, plan, implement, test, log decisions, update state)
   - Key rules from the coding principles

3. Analyze the codebase and populate context.yaml with:
   - Actual stack (runtime, language, frameworks, test tools)
   - Architecture style and patterns you observe
   - Layer structure as it exists
   - Quality conventions you can extract from existing code

Don't invent conventions -- extract them from what's already here.
```

### Option B: Manual Setup

1. Copy the [templates/](templates/) directory into your project
2. Rename the directory to match your project (e.g., `.myproject/`)
3. Fill in `context.yaml` with your stack, architecture, and conventions
4. Write your first phase spec in `phases/planned/`
5. Point your AI agent at `prompt.md`

## Templates

| File | Purpose |
|------|---------|
| [context.yaml](templates/context.yaml) | Project metadata, architecture, phase tracking |
| [prompt.md](templates/prompt.md) | AI agent instructions and workflow |
| [coding-principles.md](templates/coding-principles.md) | Code quality rules and conventions |
| [phase-spec.md](templates/phase-spec.md) | Template for a new phase specification |
| [decisions.md](templates/decisions.md) | Decision log starter |

## Real-World Example

The [examples/agent-smith/](examples/agent-smith/) directory contains extracted artifacts from a real .NET 8 project that used this methodology across 70+ phases:

```
examples/agent-smith/
  context.yaml                              # full project state with 60+ completed phases
  prompt.md                                 # the actual AI agent instructions used
  decisions.md                              # architectural decisions (extract)
  phases/
    planned/
      p25-pr-review.md                      # example: spec before implementation
    active/                                 # (empty -- nothing in progress)
    done/
      p59-pr-comment-webhook.md             # example: completed phase with checked-off DoD
  runs/                                     # execution logs from agent runs
```

## Background

This methodology emerged from building [Agent Smith](https://github.com/holgerleichsenring/agent-smith), an AI orchestration framework, entirely with AI-assisted development across 70+ phases over several months.

Read the full rationale: [The Why Never Gets Written Down](https://codingsoul.org/2026/04/11/the-why-never-gets-written-down/)

## License

MIT
