---
name: deliver-spec
description: "Deliver a finished phase: run the context's verify stages, commit as 'feat: … ({id})', push the phase branch and open the pull request. Triggers after apply-spec, or when the user says 'deliver the phase', 'ship it' or 'open the PR'."
user-invocable: true
---

# Deliver Spec

The one owner of a phase's commit. Run it in the phase's worktree (branch `phase/{id}`) once apply-spec has verified the done criteria. Stop at the first failure and report it; never push past one.

## 1. Check the preconditions

```bash
git branch --show-current          # must be phase/{id}
gh auth status                     # must succeed
```

If `gh auth status` fails, stop **before pushing** and tell the user: `gh` must be installed and authenticated to open the pull request.

## 2. Run the verify stages

Read `verify:` from every `.{project}/contexts/*/context.yaml`. Each stage is `{label, command, when_present?}`. For each stage, in order, from the **repository root**:

- `when_present` set and that path (relative to the repository root) absent: skip the stage and say so — `skipped {label}: {when_present} not present`.
- Otherwise run `command` through the shell. A non-zero exit stops delivery: report the label, the command and the tail of its output, then fix and re-run from the first stage.

No `verify:` stages anywhere: say **"no verify stages declared — relying on the project's own gate"** and go on. A project's commit hook, if any, runs at step 3.

## 3. Commit

Stage the phase's work — code, tests, the spec now in `phases/done/`, `decisions/{id}.yaml`, the `context.yaml` entry — and commit once:

```bash
git add -A
git status --short                 # nothing unrelated may ride along
git commit -m "feat: {short description} ({id})"
```

Keep `({id})` exactly — the id in parentheses is what a project's commit gate keys on. If the gate blocks, fix the cause and commit again; never bypass it.

## 4. Push and open the pull request

```bash
git push -u origin phase/{id}
gh pr create --base {default-branch} --head phase/{id} \
  --title "feat: {short description} ({id})" --body-file {body.md}
```

Write the body from the spec, in this order:

- **Goal** — the spec's `goal:`.
- **Done** — each `done:` criterion with how it was confirmed.
- **Tests** — each `tests:` entry and the verify stages run (or skipped, with why).
- **Decisions** — one line per entry of `decisions/{id}.yaml` (chose / over).

Report the PR URL to the user. Removing the worktree after merge is the user's call: `git worktree remove {path}`.
