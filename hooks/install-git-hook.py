#!/usr/bin/env python3
"""Installs the spec-first commit gate as a git commit-msg hook in one clone.

Run it from inside the repository (or pass --repo <path>). It finds the clone's hooks
directory with `git rev-parse --git-path hooks`, so core.hooksPath and worktrees are
honoured, copies spec-gate.py there as spec-first-gate.py and writes a commit-msg hook
that runs the copy. The copy keeps working when the plugin is upgraded or removed;
re-run this script after an upgrade to bring the copy up to date.

The hook gates only where a context declares `gate: git`. When the copy or a python3 is
missing it says so and lets the commit through, so a broken install never blocks commits
that name no spec. `git commit --no-verify` skips every commit-msg hook, this one too.

Hooks live per clone: every teammate runs this once in each clone.

Exit codes:
  0  installed, or an earlier install of this hook replaced
  2  usage error, or not inside a git repository
  3  Windows: the gate runs stages in POSIX process groups
  4  the hooks directory is tracked by the repository (core.hooksPath into the work tree)
  5  a commit-msg hook that is not ours is already there; nothing was changed
"""

import json
import os
import shutil
import stat
import subprocess
import sys

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_SOURCE = os.path.join(HOOKS_DIR, "spec-gate.py")
HOOK_MARKER = "# spec-first commit gate"
HOOK_COPY = "spec-first-gate.py"

HOOK_SCRIPT = """#!/bin/sh
{marker} {version}
# Written by install-git-hook.py from the spec-first plugin; re-run it to update.
# Gates commits whose message names a spec, where a context declares gate: git.
gate="$(dirname "$0")/{copy}"
if [ ! -f "$gate" ]; then
  echo "[spec-first gate] $gate is missing, so this commit is not gated. Re-run install-git-hook.py." >&2
  exit 0
fi
for python in python3 python; do
  if command -v "$python" >/dev/null 2>&1 && "$python" -c 'import sys; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; then
    exec "$python" "$gate" --commit-msg "$1"
  fi
done
echo "[spec-first gate] no python3 found, so this commit is not gated." >&2
exit 0
"""


def git(repo, *args):
    completed = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return completed.stdout.strip() if completed.returncode == 0 else None


def plugin_version():
    try:
        with open(os.path.join(HOOKS_DIR, "..", ".claude-plugin", "plugin.json"), encoding="utf-8") as handle:
            return json.load(handle).get("version", "unknown")
    except (OSError, ValueError):
        return "unknown"


def hooks_directory(top):
    hooks = git(top, "rev-parse", "--git-path", "hooks")
    if hooks is None:
        return None
    return os.path.normpath(hooks if os.path.isabs(hooks) else os.path.join(top, hooks))


def tracked(top, hooks):
    """True when the hooks directory sits in the work tree and the repository tracks files
    in it (.husky, .githooks): writing there would change the project, not this clone."""
    relative = os.path.relpath(hooks, top)
    if relative.startswith(".."):
        return False
    return bool(git(top, "ls-files", "--", relative))


def install(repo):
    if os.name == "nt":
        print("install-git-hook: the gate needs a POSIX system; Windows is not supported.", file=sys.stderr)
        return 3
    top = git(repo, "rev-parse", "--show-toplevel")
    hooks = hooks_directory(top) if top else None
    if not top or not hooks:
        print(f"install-git-hook: {repo} is not inside a git repository.", file=sys.stderr)
        return 2
    if tracked(top, hooks):
        print(f"install-git-hook: {hooks} is tracked by the repository (core.hooksPath). Add the "
              "spec-first gate to that hook setup by hand; nothing was changed.", file=sys.stderr)
        return 4
    hook = os.path.join(hooks, "commit-msg")
    if os.path.exists(hook):
        with open(hook, encoding="utf-8", errors="replace") as handle:
            if HOOK_MARKER not in handle.read(2048):
                print(f"install-git-hook: {hook} already exists and is not the spec-first hook; "
                      "nothing was changed. Merge the two by hand.", file=sys.stderr)
                return 5
    os.makedirs(hooks, exist_ok=True)
    shutil.copyfile(GATE_SOURCE, os.path.join(hooks, HOOK_COPY))
    with open(hook, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(HOOK_SCRIPT.format(marker=HOOK_MARKER, version=plugin_version(), copy=HOOK_COPY))
    os.chmod(hook, os.stat(hook).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"install-git-hook: commit-msg hook and {HOOK_COPY} written to {hooks}. It gates spec "
          "commits where a context declares gate: git.")
    return 0


def main(argv):
    if len(argv) == 1:
        return install(".")
    if len(argv) == 3 and argv[1] == "--repo":
        return install(argv[2])
    print("usage: install-git-hook.py [--repo <path>]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
