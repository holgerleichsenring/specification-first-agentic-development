---
name: deliver-spec
description: "Deliver a finished spec: commit as 'feat: … ({id})' through the gate, read its verdict, push, open the PR. Triggers after apply-spec, or on 'deliver the spec', 'ship it', 'open the PR'."
user-invocable: true
---

# Deliver Spec

The one owner of a spec's commit. Run it in the spec's worktree (branch `spec/{id}`) once apply-spec has verified the done criteria. Stop at the first failure and report it; never push past one.

## 1. Check the preconditions

```bash
git branch --show-current          # must be spec/{id}
gh auth status                     # must succeed
```

A `phase/{id}` branch cut under 2.4 is accepted: if it still carries `.{project}/phases/`, run update-project's `scripts/migrate-specs-layout.py` on it and commit first; push and open the PR on `phase/{id}` (until the script is removed).

If `gh auth status` fails, stop **before pushing** and tell the user: `gh` must be installed and authenticated to open the pull request.

## 2. Commit through the gate

Stage the spec's work: code, tests, the spec now in `specs/done/`, `decisions/{id}.yaml`, the `context.yaml` entry. Note HEAD, then commit once, with a literal `-m`:

```bash
git add -A
git status --short                 # nothing unrelated may ride along
head=$(git rev-parse --short HEAD)
git commit -m "feat: {short description} ({id})"
```

Keep `({id})` exactly: the id in parentheses is what the commit gate keys on. Never pipe the commit and never build the message with `$(…)` or `-F -`; the gate cannot read those and lets the commit through unchecked.

With `gate: git` the stages run inside this Bash call, in the commit-msg hook: give the call a timeout of 600000 ms. The hook's own deadline is 570 s, so a slow suite blocks with a ledger line instead of being cut off.

The plugin's gate runs every context's `verify:` stages at this commit, once. If it blocks, the commit did not happen: fix the cause and commit again. Never bypass it.

## 3. Read the verdict

The gate writes one line per spec commit to `spec-first-gate.log` in the git common directory, shared by all worktrees. Read the newest line for this spec, this tree and the HEAD you noted:

```bash
log="$(git rev-parse --path-format=absolute --git-common-dir)/spec-first-gate.log"
awk -F'\t' -v id="{id}" -v tree="$(git rev-parse --show-toplevel)" -v head="$head" \
  '$3 == id && $4 == tree && $5 == head' "$log" | tail -1
```

Fields: time, verdict, spec, tree, parent, detail.

- **passed**: the verify stages ran and were green. Go on. With `gate: git` the line comes from the commit-msg hook; it counts the same.
- **not-gated** with `gate: project`: the project's own gate checked the commit. The commit exists, so it passed there. Go on, and say in the PR body that the project's gate checked it.
- **not-gated** with any other detail, or **no line at all**: no gate checked this commit (hooks disabled, the hook timed out or could not start, PyYAML missing, no verify stages declared). Run the stages yourself now, as below. On a fix, `git commit --amend --no-edit`; the amend is gated again.
- **blocked**: the commit did not happen. Fix the cause and go back to step 2.

Running the stages by hand: read `verify:` from every `.{project}/contexts/*/context.yaml`, each `{label, command, when_present?}`, and run them in order from the **repository root**. `when_present` set and that path absent: skip the stage and say so, `skipped {label}: {when_present} not present`. A non-zero exit stops delivery: report the label, the command and the tail of its output. No stages anywhere: say **"no verify stages declared"** and go on.

## 4. Push and open the pull request

```bash
git push -u origin spec/{id}
gh pr create --base {default-branch} --head spec/{id} \
  --title "feat: {short description} ({id})" --body-file {body.md}
```

Write the body from the spec, in this order:

- **Goal**: the spec's `goal:`.
- **Done**: each `done:` criterion with how it was confirmed.
- **Tests**: each `tests:` entry, and who ran the verify stages: the plugin's gate (the ledger line), the project's gate, or this skill by hand (with any skipped stage and why).
- **Decisions**: one line per entry of `decisions/{id}.yaml` (chose / over).
- **Upgrade impact**: the spec's `upgrade_impact:`, or "nothing an operator must change".
- **Proven live**: the spec's `proven_live:`: what the tests prove, and what still needs a live check.

Report the PR URL to the user. Removing the worktree after merge is the user's call: `git worktree remove {path}`.
