---
name: deliver-series
description: "Deliver a series of specs as one PR: review each, build groups in parallel worktrees, merge, verify the merged tree, push, watch CI. Triggers on 'deliver the series', 'build all of {base}'."
user-invocable: true
---

# Deliver Series

Takes a series (`{base}a`, `{base}b`, ...) or a list of spec ids from planned specs to one pull request. Run it in the main thread: it spawns a reviewer and builders, and only the main thread holds the Agent tool. Stop and report at the first step you cannot finish; never push past a red check.

Before you start, ask the user one question if they have not answered it: **may this skill merge the pull request when CI is green?** Without a yes, it stops at a green PR.

## 1. Collect the specs

```bash
git fetch origin
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)
ls .{project}/specs/planned/{base}*-*.yaml        # or the ids the user named
```

Read every spec in full. Order them by `requires:`, then by letter. A spec that requires one outside the list must find it in `specs/done/` on the default branch; otherwise stop and say which.

## 2. Review every spec before any code

For each spec run `/spec-first:review-spec`: the evidence script, then one fresh reviewer with the brief from that skill. Give the reviewer the whole series, not one spec, so it can see where two specs contradict each other. Apply every cut, re-run the evidence script, and commit the result once:

```bash
git commit -m "docs: apply the review to the {base} series"
```

A REFUSE sends that spec back to the user. Build the rest only if nothing left depends on it.

## 3. Group the specs

List the files each spec's `steps` create, modify or delete, and the files its facts say will change. Specs that share a file go in one group and are built one after another, in `requires` order. Specs that share no file go in separate groups and are built at the same time.

Lines that every spec adds to the same index file (the `state:` entries in `context.yaml`, a changelog) do not make two specs share a file: those conflicts are resolved at the merge in step 6.

Tell the user the groups and why, then go on.

## 4. One worktree and one builder per group

For each group, cut a branch and a worktree from the default branch, named after the group's first spec:

```bash
git worktree add -b spec/{first-id} ../{repo}-{first-id} "$base"
git -C ../{repo}-{first-id} log -1 --format=%h        # check it is the sha you expect
```

Spawn one background subagent per group. It has no conversation history, so put everything in its prompt:

- the worktree path and branch, and that it works only there (absolute paths, no `cd` into other checkouts);
- the specs in build order, with their paths;
- the project's rules: the root `AGENTS.md` (or `CLAUDE.md` in a project without one), each context's coding principles, and the decisions files its specs require;
- the instruction to run `/spec-first:apply-spec` for each spec, then commit it exactly as deliver-spec step 2 says: one commit per spec, `feat: {short description} ({id})`, a literal `-m`, never piped, never built with `$(...)`, and the commit command on its own (no heredoc in the same command line);
- after each commit, read the gate's ledger line for that spec (deliver-spec step 3). No line means the gate never ran on that commit: run the verify stages by hand and say so;
- the gates of all builders share one machine. A timing-bound test that fails under that load and passes alone is re-run once and named in the report, not hidden;
- no push, no pull request, no merge;
- report: each spec's commit sha, its ledger line, what is proven only by tests, and anything left open.

Wait for every builder's notification. Do not predict a result that has not arrived.

## 5. Check what the builders report

For every spec: a commit exists with `({id})` in its subject, and a `passed` ledger line, from the plugin's hook or with `gate: git` from the commit-msg hook (or `gate: project`), names that spec, that tree and that commit's parent. A spec without one never met a gate; run its stages by hand on its branch before merging it.

## 6. Merge into one integration branch

```bash
git worktree add -b spec/{base} ../{repo}-{base} "$base"
git -C ../{repo}-{base} merge --no-ff spec/{first-id}       # once per group branch
```

A merge commit carries no spec id in its subject, so the gate does not run on it. That is why step 7 exists.

On a conflict:

- **Index and state lines** (`context.yaml` `state:` entries, changelogs, lists): keep both sides' lines.
- **Anything else**: read both commits first (`git show {sha} -- {file}` for each side), then write the version that does what both specs intended. Record it as a decision in the affected spec's `decisions/{id}.yaml`, starting `Merge note {date} ({branch} into spec/{base}):`, with what each side wanted and how the result serves both.

After all merges, look for the same helper or type added by two branches and keep one copy, in a separate `chore:` commit without a spec id.

## 7. Verify the merged tree

Build and run every context's `verify:` stages by hand on the integration branch, from the repository root. Every spec passed alone; this proves they pass together. Fix what breaks in a commit of its own (a fix to one spec's behaviour carries that spec's id and goes through the gate).

## 8. Look for files only a builder had

```bash
git -C ../{repo}-{base} status --ignored --short
```

Also run it in each builder's worktree. A file a test, manifest or script needs that is ignored (`!!`) or untracked (`??`) exists only on that machine: its test passed there and will fail everywhere else. Commit it, with an ignore exception if a broad rule swallowed it.

## 9. Check what an update costs an operator

```bash
git diff "$base"...spec/{base} --stat -- deploy/ infra/ k8s/ helm/ charts/ terraform/ '*.tf' 'docker-compose*' .env.example
```

The rule: **an update must not force an infrastructure change.** For every change found, the default must stay what it was, and the new behaviour is opt-in, unless a spec's `upgrade_impact` says otherwise and explains why. A schema change that old instances cannot run beside (a dropped column during a rolling deploy) goes out in two releases: stop using it first, remove it in the next. List each opt-in for the PR body.

## 10. Push and open one pull request

```bash
git -C ../{repo}-{base} push -u origin spec/{base}
gh pr create --base {default-branch} --head spec/{base} --title "{type}: {what the series does}" --body-file {body.md}
```

Write the body in plain language for the person who deploys it:

- one line saying which series and specs it contains;
- **Upgrade impact**: what an operator must change, or "Deploying this needs no infrastructure change", followed by each opt-in;
- **What changed**: per spec or group, what is different for a user and why, in a sentence or two each;
- **Verification**: that every spec commit passed the gate, and the results on the merged tree (test counts per suite, build);
- **Not proven live**: each `proven_live` item, everything only tests prove;
- **Open**: anything found and not fixed, with the spec that will fix it.

## 11. Wait for CI and fix what is red

```bash
gh pr checks {number} --watch
gh run view {run-id} --log-failed        # when a check is red
```

Read the failing log, find the cause, fix it on the integration branch, run the affected tests, commit, push, and wait again. A check that is red on the default branch too is not this PR's; say so instead of fixing around it.

## 12. Merge, only if the user said so

With the user's yes from the start and every check green:

```bash
gh pr merge {number} --merge
```

Use the merge method the repository allows. Without a yes, report the PR URL and stop. Removing the worktrees is the user's call: `git worktree remove {path}`.
