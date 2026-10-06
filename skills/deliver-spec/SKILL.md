---
name: deliver-spec
description: "Deliver a finished spec: run the verify stages, commit as 'feat: … ({id})', push the spec branch, open the PR. Triggers after apply-spec, or on 'deliver the spec', 'ship it', 'open the PR'."
user-invocable: true
---

# Deliver Spec

The one owner of a spec's commit. Run it in the spec's worktree (branch `spec/{id}`) once apply-spec has verified the done criteria. Stop at the first failure and report it; never push past one.

## 1. Check the preconditions

```bash
git branch --show-current          # must be spec/{id}
gh auth status                     # must succeed
```

A `phase/{id}` branch cut under 2.4 is accepted in 2.5: if it still carries `.{project}/phases/`, run update-project's `scripts/migrate-specs-layout.py` on it and commit first; push and open the PR on `phase/{id}` (until the script is removed).

If `gh auth status` fails, stop **before pushing** and tell the user: `gh` must be installed and authenticated to open the pull request.

## 2. Run the verify stages

Read `verify:` from every `.{project}/contexts/*/context.yaml`. Each stage is `{label, command, when_present?}`. For each stage, in order, from the **repository root**:

- `when_present` set and that path (relative to the repository root) absent: skip the stage and say so — `skipped {label}: {when_present} not present`.
- Otherwise run `command` through the shell. A non-zero exit stops delivery: report the label, the command and the tail of its output, then fix and re-run from the first stage.

No `verify:` stages anywhere: say **"no verify stages declared — relying on the project's own gate"** and go on. A project's commit hook, if any, runs at step 3.

## 3. Commit

Stage the spec's work — code, tests, the spec now in `specs/done/`, `decisions/{id}.yaml`, the `context.yaml` entry — and commit once:

```bash
git add -A
git status --short                 # nothing unrelated may ride along
git commit -m "feat: {short description} ({id})"
```

Keep `({id})` exactly — the id in parentheses is what a project's commit gate keys on. If the gate blocks, fix the cause and commit again; never bypass it.

## 4. Push and open the pull request

```bash
git push -u origin spec/{id}
gh pr create --base {default-branch} --head spec/{id} \
  --title "feat: {short description} ({id})" --body-file {body.md}
```

Write the body from the spec, in this order:

- **Goal** — the spec's `goal:`.
- **Done** — each `done:` criterion with how it was confirmed.
- **Tests** — each `tests:` entry and the verify stages run (or skipped, with why).
- **Decisions** — one line per entry of `decisions/{id}.yaml` (chose / over).

Report the PR URL to the user. Removing the worktree after merge is the user's call: `git worktree remove {path}`.
