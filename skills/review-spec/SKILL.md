---
name: review-spec
description: "Review a phase spec before any code: a script resolves every cited file and line, then a fresh-context reviewer answers BUILD, BUILD WITH CUTS or REFUSE. Triggers after create-phase, or when the user says 'review the spec'."
user-invocable: true
allowed-tools: Bash(python3 *)
---

# Review Spec

Run this in the main thread: the reviewer must be a fresh subagent, and only the main thread holds the Agent tool. The spec under review is the planned file create-phase just committed in the phase worktree.

## 1. Run the evidence check

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check-evidence.py" .{project}/phases/planned/{id}-{label}.yaml
```

It reads every `facts[].evidence` and checks: each cited path is a file, each cited line lies inside it, each `observed:` segment carries a real date (`yyyy-MM-dd`). Refused: a fact citing nothing, a minted `[Ln]` line, a path under `.{project}/phases/planned/` or `active/` (a plan is not evidence), a qualifier (`name:path/…`) not declared in a context's `evidence_roots:`. A declared qualifier resolves against its path when that path exists in this checkout; otherwise it is accepted unchecked.

- Exit 0: clean. Exit 1: fix every printed line — re-open the file, re-cite, or turn the fact into an assumption. Re-run until 0.
- Exit 2: usage error — fix the call. Exit 3, or `python3` missing: tell the user **"evidence check did not run"** and why. Never treat a check that did not run as a pass.

## 2. Spawn one reviewer

Spawn ONE subagent. It has no conversation history, so give it everything:

- the spec path and full text;
- the wider goal — what the user asked for and why, in two or three sentences;
- this brief, verbatim:

> Attack this spec before anyone builds it. Open every cited file around the cited lines — a valid citation is not a true claim. Follow every field, setting and value the spec touches to its sinks: who reads it, who writes it, what else breaks. Extract archives and generated files before reasoning about them. Check every step against the code as it is, not as the spec says it is. Answer with exactly one verdict — BUILD, BUILD WITH CUTS, or REFUSE — and back each finding with file:line evidence. For BUILD WITH CUTS name each cut precisely. REFUSE is a successful result when the spec is wrong.

## 3. Apply and repeat

- **BUILD**: done. Report the verdict to the user.
- **BUILD WITH CUTS**: apply every cut. After each cut, grep the old wording across `goal`, `scope`, `decisions`, `steps`, `tests`, `done` and `facts` — a cut left standing in another register is not applied. Stay inside the spec budget.
- **REFUSE**: rewrite or split the spec per the findings, or take it back to the user.

After any change re-run step 1, then spawn a fresh reviewer (step 2). Stop when the verdict is BUILD, or BUILD WITH CUTS with every cut applied and the script clean. Commit the reviewed spec in the phase worktree:

```bash
git add .{project} && git commit -m "spec: review {id}"
```
