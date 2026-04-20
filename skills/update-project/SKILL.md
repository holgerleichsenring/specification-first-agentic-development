---
name: update-project
description: "Sync an existing project's methodology files with a newer plugin version. Triggers when the user says 'update methodology', 'sync templates', 'update spec-first', or when methodology.version in context.yaml is older than the plugin version."
user-invocable: true
---

# Update Project

Sync an existing project's Specification-First methodology files with the latest plugin version. Preserves user customizations while bringing in methodology improvements.

## When to Use

- The plugin was updated and the project's `methodology.version` in `context.yaml` is older
- The user explicitly asks to sync or update the methodology
- New templates or structural changes were introduced in a newer plugin version

## How It Works

The plugin's templates carry an inline methodology version (currently `1.0.0`). The user's `context.yaml` has a `methodology.version` field set during bootstrap. When these differ, this skill helps merge the changes.

## Steps

### 1. Check versions

Read the user's `context.yaml` and find the `methodology.version` field.

Compare with the plugin's current version from `.claude-plugin/plugin.json` (`version` field).

If they match, tell the user they're up to date. Done.

If `methodology.version` is missing, it means the project was set up before versioning existed. Treat it as `0.0.0`.

### 2. Show what changed

For each methodology file, compare the user's version with the plugin's template:

| File | What to compare |
|------|-----------------|
| `context.yaml` | Structure and field names (not user content) |
| `coding-principles.md` | Sections and rules (not project-specific values) |
| `decisions.md` | Header format and category list |
| `CLAUDE.md` / `prompt.md` | Workflow steps, read order, rules |
| `phase-spec.schema.json` | Schema fields and validation rules |

Present a summary of what's new or changed per file. Be specific: "New field `methodology.version` added to context.yaml", not "context.yaml was updated".

### 3. Propose merge

For each file with changes:

- **Additive changes** (new fields, new sections): propose adding them while keeping all existing user content intact.
- **Modified sections** (updated wording, reordered steps): show the diff and let the user choose between old and new.
- **Removed sections**: flag them but don't auto-delete. The user decides.

Never overwrite user customizations silently. The user's `context.yaml` stack, arch, quality, and state sections are theirs — only touch the methodology-related structure.

### 4. Ask approval

Show the complete list of proposed changes and ask the user to approve before writing anything.

### 5. Apply changes

Write the approved changes to each file. Update `methodology.version` in `context.yaml` to match the plugin version.

### 6. Log the update

Add an entry to `decisions.md`:

```markdown
## Methodology Update (v{old} → v{new})

- [Tooling] Updated Spec-First methodology from v{old} to v{new} -- {summary of key changes}
```

## Safety

- Git is your safety net. If something goes wrong, the user can `git diff` and revert.
- Never modify files outside the project's methodology directory unless explicitly told to (e.g., updating `CLAUDE.md` at root).
- Always show diffs before writing.
- Preserve every line of user-written content in `context.yaml` (stack, arch, quality, state sections).
