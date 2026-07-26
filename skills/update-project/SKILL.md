---
name: update-project
description: "Sync an existing project's methodology files with a newer plugin version. Triggers when the user says 'update methodology', 'sync templates', 'update spec-first', or when methodology.version in context.yaml is older than the plugin version. Handles the big-bang v1.x → v2.0 layout migration."
user-invocable: true
---

# Update Project

Sync an existing project's Specification-First methodology files with the latest plugin version. Preserves user customizations while bringing in methodology improvements.

For v1.x → v2.0 this performs a one-shot structural migration: the flat `context.yaml` + `coding-principles.md` move into `contexts/default/`, and the append-only `decisions.md` Markdown log splits into per-decision YAML files under `decisions/`.

## When to Use

- The plugin was updated and the project's `methodology.version` in `context.yaml` is older
- The user explicitly asks to sync or update the methodology
- New templates or structural changes were introduced in a newer plugin version

## How It Works

The plugin's templates carry an inline methodology version (currently `2.1.0`). The user's `context.yaml` has a `methodology.version` field set during bootstrap. When these differ, this skill helps merge the changes.

## Steps

### 1. Check versions

Read the user's methodology version:
- v2.x project: read `.{project}/contexts/<default-or-only>/context.yaml` → `methodology.version`.
- v1.x project: read `.{project}/context.yaml` (flat) → `methodology.version`. Missing field = treat as `0.0.0`.

Compare with the plugin's current version from `.claude-plugin/plugin.json` (`version` field).

If they match, tell the user they're up to date. Done.

### 2. Pick the migration path

| From    | To     | Path                                                  |
|---------|--------|-------------------------------------------------------|
| 0.0.0   | 2.1.0  | v1-to-v2 (treat as v1.0.0), then the 2.1.0 additions  |
| 1.x.x   | 2.1.0  | v1-to-v2, then the 2.1.0 additions                    |
| 2.0.x   | 2.1.0  | 2.1.0 additions (step 3c) + additive merge (step 3b)  |
| 2.1.x   | 2.y.y  | additive/diff merge (no migration)                    |

For v1 → v2 run step 3a (the structural migration) and then step 3c (the 2.1.0 additions). For 2.0.x → 2.1.0 run step 3c plus the step 3b additive merge. For later 2.x → 2.y skip to step 3b (additive merge).

### 3a. v1 → v2 big-bang migration

The migration is mechanical and structural-only. No content is rewritten — files are MOVED, formats are CONVERTED. Show the operator the full plan before touching anything; require explicit approval.

**Confirm with the operator before starting** that:
- The repo is committed clean (so `git diff` shows exactly the migration changes).
- Any in-flight work in `phases/active/` is at a safe checkpoint (the migration does not touch phase YAMLs but the operator should know what state they're starting from).

#### 3a.1. Move root context + principles into `contexts/default/`

```
.{project}/context.yaml          → .{project}/contexts/default/context.yaml
.{project}/coding-principles.md  → .{project}/contexts/default/coding-principles.md
```

Use `git mv` so history is preserved.

Inside the moved `context.yaml`:
- Update the schema reference: `# yaml-language-server: $schema=context.schema.json` → `# yaml-language-server: $schema=../../context.schema.json`.
- Add `meta.workdir: "."` (single-stack default — the existing project's code lives at the repo root from this context's perspective).
- Bump `methodology.version` to the plugin's current version (from `.claude-plugin/plugin.json`).

If a `.{project}/context.schema.json` exists alongside, leave it at the project root. The relative path adjustment above handles the new depth.

#### 3a.2. Split the `decisions.md` log into per-phase YAMLs

Read `.{project}/decisions.md`. The v1 format groups decisions under `## p{NN}: Title` headings with `- [Category] Decision -- rationale` bullets.

**One YAML file per phase**, all bullets under the heading become entries in that file's `decisions:` array. NOT one file per bullet.

For each `## p{NN}: Title` heading:
- Collect all `- [Category] body` bullets underneath (until the next heading).
- For each bullet:
  - `category` = `{Category}`. Normalise off-canonical labels (Scope already canonical; map Fix/Decision/Note/Quality/Cleanup/Reuse/Safety → Implementation; Flow → Architecture; Configuration → Tooling). Warn on anything else and default to Implementation.
  - Split `body` at the first ` — ` (em-dash) or ` -- ` (double-dash with spaces) — left side becomes `chose:`, right side becomes `reason:`. If there's no separator, the entire body becomes `chose:` and `reason:` is omitted.
  - `over:` is OMITTED unless the body text clearly names a rejected alternative. No `<TBD>` placeholders — the schema makes `over:` optional.
- Emit one file:

  ```yaml
  # yaml-language-server: $schema=../decision.schema.json
  phase: p{NN}
  decisions:
    - category: {Category}
      chose: "{...}"
      reason: |
        {...}
    - category: {Category}
      chose: "{...}"
      ...
  ```

- File path: `.{project}/decisions/p{NN}.yaml`. The filename IS the phase ID — no slug, no per-bullet suffix.

Convert any pre-existing `.{project}/decisions/*.md` files in the same shape: read each, derive the phase ID from its heading (or from the filename prefix as fallback, e.g. `p0146d-observation-fields.md` → `p0146d.yaml`), MERGE its bullets into the same phase's YAML if `decisions.md` also had entries for that phase, otherwise emit a fresh phase YAML. `git rm` each `.md` after.

After the split:
- `git rm .{project}/decisions.md`.
- The big-bang means the Markdown log is gone — every entry now lives in its phase's YAML file.

For a 1000-bullet `decisions.md` spanning 200 phases, expect ~200 YAML files — one per phase.

#### 3a.3. Add the schemas

Copy `templates/decision.schema.json` and `templates/phase-spec.schema.json` from the plugin into `.{project}/` if they're missing. Editors pick them up from there.

#### 3a.4. Emit warnings for notes/ and concepts/ directories

If `.{project}/notes/` or `.{project}/concepts/` exist:
- Do NOT automatically move them. Per operator instruction: "für mich sind das keine decisions. das sind die konzepte die zu phasen führen und dann hinterher decisions ableiten."
- Emit a warning listing every file under those directories and recommend the operator choose, per file:
  - (a) Copy the file out of `.{project}/` (e.g. into a `docs/notes/` or a separate branch) before continuing — they're conceptual exploration, not part of the spec-first artifact set.
  - (b) Rename to `phases/done/p{NN}-base-concept-{topic}.yaml` with a reserved ID range the operator picks. The file becomes a "base-concept phase" — documented foundation that was never executed as work but shaped subsequent phases.

The migration does NOT pick one — operator decides per file.

#### 3a.5. Update `state.{done,active,planned}` entries (optional housekeeping)

The `state.{done,active,planned}` sections in the moved `context.yaml` still reference phase YAMLs by path. v1 paths like `.{project}/phases/...` are unchanged in v2 — no rewrite needed. If the operator wants to add new `applies_to:` annotations to existing phase YAMLs, that's done lazily as each phase comes back into focus, not as part of this migration.

### 3b. 2.x → 2.y additive merge

For each methodology file, compare the user's version with the plugin's template:

| File | What to compare |
|------|-----------------|
| `contexts/<name>/context.yaml` | Structure and field names (not user content) |
| `contexts/<name>/coding-principles.md` | Sections and rules (not project-specific values) |
| `decision.schema.json` | Schema fields and validation rules |
| `phase-spec.schema.json` | Schema fields and validation rules |
| `CLAUDE.md` / `prompt.md` | Workflow steps, read order, rules |

Present a summary of what's new or changed per file. Be specific: "New field `meta.workdir` added to context.yaml", not "context.yaml was updated".

#### 3b.1. Propose merge

For each file with changes:

- **Additive changes** (new fields, new sections): propose adding them while keeping all existing user content intact.
- **Modified sections** (updated wording, reordered steps): show the diff and let the user choose between old and new.
- **Removed sections**: flag them but don't auto-delete. The user decides.

Never overwrite user customizations silently. The user's `contexts/<name>/context.yaml` stack, arch, quality, and state sections are theirs — only touch the methodology-related structure.

### 3c. 2.1.0 additions: memory store + root CLAUDE.md read order

Two retroactive changes bring pre-2.1.0 projects to parity with fresh bootstraps.

#### 3c.1. Create the memory store (structural-only)

If `.{project}/memory/` is missing:

- Create `.{project}/memory/` and copy `templates/memory/MEMORY.md` into it as the empty index.
- **Structural-only — no auto-distillation of history.** Do NOT convert the project's decisions, git log, or phase records into memory entries as part of this migration. The store opens empty; memories accumulate from future sessions and runs (entry convention: one Markdown file per memory beside the index, frontmatter `name` kebab-slug / `description` one line / `metadata.type` in `feedback` | `project` | `reference` — see `templates/memory/example-memory.md`), and a `feedback` entry becomes policy only after operator ratification.

#### 3c.2. Patch the root CLAUDE.md read-order block

A project bootstrapped before 2.1.0 typically still carries the v1 read order in its root `CLAUDE.md` (flat `context.yaml`, the retired `decisions.md` append log, `phases/active/*.md`). Sessions obey `CLAUDE.md` first, so they look in the wrong place before recovering — fix it here:

- Locate the context-file read-order block in the project's root `CLAUDE.md`.
- Replace ONLY that block with the v2 order (as in `templates/prompt.md`):
  1. glob `contexts/*/context.yaml`
  2. each context's `coding-principles.md`
  3. `phases/active/*.yaml`
  4. `decisions/*.yaml`
  5. `memory/MEMORY.md` (recall entry detail from `memory/<name>.md` on demand)
- If `CLAUDE.md` has no memory/recall discipline section yet, offer to add the one from `templates/prompt.md` alongside.

Because the root `CLAUDE.md` lives OUTSIDE the methodology directory, this edit ALWAYS requires explicit operator approval: show the exact before/after diff of the block and apply only after the operator approves. Leave every other section of `CLAUDE.md` untouched.

### 4. Ask approval

Show the complete list of proposed changes and ask the user to approve before writing anything.

### 5. Apply changes

Write the approved changes. Update `methodology.version` in every `contexts/<name>/context.yaml` to match the plugin version.

### 6. Log the update

Append a decision entry to the phase YAML the project uses for meta updates (or create a fresh `decisions/p-meta-update.yaml` if none exists):

```yaml
# yaml-language-server: $schema=../decision.schema.json
phase: p-meta-update            # or pick an existing meta-phase ID convention the project uses

decisions:
  - category: Tooling
    chose: "Updated Spec-First methodology from v{old} to v{new}"
    over: "Staying on v{old}"
    reason: |
      {Summary of key changes: contexts/ layout, YAML decisions, ...}
      Migration mode: {v1-to-v2 big-bang | 2.x additive merge}.
```

## Safety

- Git is your safety net. If something goes wrong, the user can `git diff` and revert.
- Before the v1 → v2 migration, require the working tree to be clean (or explicitly confirmed otherwise) so the migration's effects are isolated in `git diff`.
- Use `git mv` for file moves so history is preserved.
- Never modify files outside the project's methodology directory unless explicitly told to (e.g., updating `CLAUDE.md` at root).
- Always show diffs before writing.
- Preserve every line of user-written content in `contexts/<name>/context.yaml` (stack, arch, quality, state sections).
- For the v1 → v2 decisions-log split: when a bullet's body has no obvious `over:` (rejected alternative), OMIT the `over:` field. The schema makes it optional — never invent placeholder text.
