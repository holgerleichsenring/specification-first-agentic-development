---
name: example-memory
description: One-line description shown in the index — what this fact tells the next agent.
metadata:
  type: project    # feedback | project | reference
---

The fact itself — a few lines of Markdown, one fact per file. Link related
memories as [[other-slug]]; a cited slug must have its committed definition
in this directory.

<!--
Entry convention (shared across agent-smith runs and IDE sessions):

- Filename = `<name>.md`; `name` is a kebab-case slug and matches the
  filename. `description` is exactly one line — it becomes this memory's
  line in MEMORY.md.
- `metadata.type`:
    feedback  — how the operator wants the agent to work (corrections,
                confirmed approaches, with the why). Policy only after the
                operator RATIFIES it; until then it is a pending proposal.
    project   — ongoing goals, constraints, and state that code and git
                cannot tell the next agent.
    reference — pointers to external resources.
- The index MEMORY.md holds one line per memory and no content.

Curation discipline:
- Store what code and git cannot already tell the next agent.
- One fact per file — a description needing "and" is two memories.
- Check the index for an existing entry first; update, don't duplicate.
- Delete or rewrite a memory the moment it turns out wrong.
- A decision records a CHOICE (decisions/); a memory records a
  transferable FACT or RULE. Never copy decisions into memory.

This file is a shape reference — do not copy it into a project as-is.
-->
