#!/usr/bin/env python3
"""Exercises the gate as a git commit-msg hook (gate: git) and its installer.

Run it directly:  python3 hooks/test_git_hook.py
or with unittest: python3 -m unittest discover -s hooks -p 'test_*.py'

The GitHook_* cases install the hook into a throwaway project and make real commits, so
git itself runs the hook. The PreToolUse_* cases drive the Claude Code hook against the
same projects to prove that exactly one gate checks a commit. The Installer_* cases cover
what the installer refuses and what it replaces. The throwaway-repository and ledger
fixtures come from test_commit_message.py.
"""

import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import traceback
import unittest

HOOKS_DIR = pathlib.Path(__file__).resolve().parent
INSTALLER = HOOKS_DIR / "install-git-hook.py"
_spec = importlib.util.spec_from_file_location("gate_fixtures", HOOKS_DIR / "test_commit_message.py")
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)

_environment = _fixtures._environment
_project_repository = _fixtures._project_repository
_run_gate = _fixtures._run_gate
_ledger = _fixtures._ledger
_GIT_IDENTITY = _fixtures._GIT_IDENTITY

SPEC_MESSAGE = "feat: something (2026-10-27-84f4)"
GREEN = ({"label": "check", "command": "exit 0"},)
RED = ({"label": "check", "command": "echo the check failed; exit 1"},)


def _install(repo):
    return subprocess.run([sys.executable, str(INSTALLER), "--repo", repo],
                          env=_environment(), capture_output=True, text=True)


def _commit(repo, message, ledger, *flags):
    """A real commit, so git runs the installed hook. The change differs every time."""
    path = pathlib.Path(repo) / "change.txt"
    path.write_text(path.read_text() + "x" if path.exists() else "x")
    environment = _environment()
    environment["SPEC_GATE_LOG"] = str(ledger)
    subprocess.run(["git", "add", "-A"], cwd=repo, env=environment, check=True)
    return subprocess.run(["git", *_GIT_IDENTITY, "commit", *flags, "-m", message],
                          cwd=repo, env=environment, capture_output=True, text=True)


def _head_subject(repo):
    return subprocess.run(["git", "log", "-1", "--format=%s"], cwd=repo, env=_environment(),
                          capture_output=True, text=True).stdout.strip()


def GitHook_GreenStages_CommitLandsAndLedgerSaysPassed():
    with _project_repository(GREEN, gate="git") as repo, tempfile.TemporaryDirectory() as tmp:
        assert _install(repo).returncode == 0
        ledger = pathlib.Path(tmp) / "gate.log"
        completed = _commit(repo, SPEC_MESSAGE, ledger)
        assert completed.returncode == 0, completed
        assert _head_subject(repo) == SPEC_MESSAGE
        assert [line[1] for line in _ledger(ledger)] == ["passed"], _ledger(ledger)


def GitHook_RedStage_CommitIsBlocked():
    with _project_repository(RED, gate="git") as repo, tempfile.TemporaryDirectory() as tmp:
        assert _install(repo).returncode == 0
        ledger = pathlib.Path(tmp) / "gate.log"
        completed = _commit(repo, SPEC_MESSAGE, ledger)
        assert completed.returncode != 0, completed
        assert "the check failed" in completed.stderr, completed.stderr
        assert _head_subject(repo) != SPEC_MESSAGE
        assert [line[1] for line in _ledger(ledger)] == ["blocked"], _ledger(ledger)


def GitHook_StageRunningGit_DoesNotTouchTheCommittedRepo():
    # Inherited GIT_DIR would make this inner init and commit act on the outer repository.
    inner = ('d=$(mktemp -d) && cd "$d" && git init -q && '
             'git -c user.email=a@b.invalid -c user.name=n commit --allow-empty -qm inner && '
             'test "$(git rev-parse --show-toplevel)" = "$(pwd -P)"')
    with _project_repository(({"label": "inner", "command": inner},), gate="git") as repo, \
            tempfile.TemporaryDirectory() as tmp:
        assert _install(repo).returncode == 0
        completed = _commit(repo, SPEC_MESSAGE, pathlib.Path(tmp) / "gate.log")
        assert completed.returncode == 0, completed.stderr
        assert _head_subject(repo) == SPEC_MESSAGE


def GitHook_GateNotDeclaredGit_StepsAsideWithANotice():
    with _project_repository(RED) as repo, tempfile.TemporaryDirectory() as tmp:
        assert _install(repo).returncode == 0
        ledger = pathlib.Path(tmp) / "gate.log"
        completed = _commit(repo, SPEC_MESSAGE, ledger)
        assert completed.returncode == 0, completed
        assert "does not declare gate: git" in completed.stderr, completed.stderr
        assert _ledger(ledger) == [], _ledger(ledger)


def GitHook_BacktickInBody_IsNotFlagged():
    with _project_repository(GREEN, gate="git") as repo, tempfile.TemporaryDirectory() as tmp:
        assert _install(repo).returncode == 0
        ledger = pathlib.Path(tmp) / "gate.log"
        completed = _commit(repo, "docs: explain `verify:`\n\nThe stages run from `the top`.", ledger)
        assert completed.returncode == 0, completed
        assert "built by the shell" not in completed.stderr, completed.stderr
        assert _ledger(ledger) == [], _ledger(ledger)


def GitHook_CopyAloneWithoutResolver_Runs():
    with _project_repository(GREEN, gate="git") as repo, tempfile.TemporaryDirectory() as tmp:
        copy = pathlib.Path(tmp) / "spec-first-gate.py"
        shutil.copyfile(HOOKS_DIR / "spec-gate.py", copy)
        message = pathlib.Path(tmp) / "COMMIT_EDITMSG"
        message.write_text(SPEC_MESSAGE + "\n# a comment git strips\n")
        environment = _environment()
        environment["SPEC_GATE_LOG"] = str(pathlib.Path(tmp) / "gate.log")
        completed = subprocess.run([sys.executable, str(copy), "--commit-msg", str(message)],
                                   cwd=repo, env=environment, capture_output=True, text=True)
        assert completed.returncode == 0, completed
        assert [line[1] for line in _ledger(pathlib.Path(tmp) / "gate.log")] == ["passed"]


def PreToolUse_GateGitWithHookInstalled_StepsAside():
    with _project_repository(RED, gate="git") as repo, tempfile.TemporaryDirectory() as tmp:
        assert _install(repo).returncode == 0
        ledger = pathlib.Path(tmp) / "gate.log"
        completed = _run_gate(f'git commit -m "{SPEC_MESSAGE}"', repo, ledger)
        assert completed.returncode == 0, completed
        assert "the commit-msg hook gates this commit" in completed.stdout, completed.stdout
        assert _ledger(ledger) == [], _ledger(ledger)


def PreToolUse_GateGitWithoutHook_StillGates():
    with _project_repository(GREEN, gate="git") as repo, tempfile.TemporaryDirectory() as tmp:
        ledger = pathlib.Path(tmp) / "gate.log"
        completed = _run_gate(f'git commit -m "{SPEC_MESSAGE}"', repo, ledger)
        assert completed.returncode == 0, completed
        assert [line[1] for line in _ledger(ledger)] == ["passed"], _ledger(ledger)


def PreToolUse_GateGitNoVerify_StillGates():
    with _project_repository(RED, gate="git") as repo, tempfile.TemporaryDirectory() as tmp:
        assert _install(repo).returncode == 0
        ledger = pathlib.Path(tmp) / "gate.log"
        completed = _run_gate(f'git commit --no-verify -m "{SPEC_MESSAGE}"', repo, ledger)
        assert completed.returncode == 2, completed
        assert [line[1] for line in _ledger(ledger)] == ["blocked"], _ledger(ledger)


def Installer_ForeignCommitMsgHook_Refuses():
    with _project_repository(GREEN) as repo:
        hook = pathlib.Path(repo) / ".git" / "hooks" / "commit-msg"
        hook.write_text("#!/bin/sh\necho someone else's hook\n")
        completed = _install(repo)
        assert completed.returncode == 5, completed
        assert hook.read_text() == "#!/bin/sh\necho someone else's hook\n"


def Installer_OwnHook_IsReplaced():
    with _project_repository(GREEN) as repo:
        assert _install(repo).returncode == 0
        copy = pathlib.Path(repo) / ".git" / "hooks" / "spec-first-gate.py"
        copy.write_text("stale")
        assert _install(repo).returncode == 0
        assert copy.read_text() == (HOOKS_DIR / "spec-gate.py").read_text()
        assert "# spec-first commit gate" in (copy.parent / "commit-msg").read_text()


def _cases():
    return [(name, case) for name, case in list(globals().items())
            if callable(case) and name.split("_")[0] in ("GitHook", "PreToolUse", "Installer")]


def load_tests(loader, tests, pattern):
    """unittest discovery runs the same cases main() does."""
    suite = unittest.TestSuite()
    for name, case in _cases():
        suite.addTest(unittest.FunctionTestCase(case, description=name))
    return suite


def main():
    failures = 0
    for name, case in _cases():
        try:
            case()
            print(f"ok    {name}")
        except Exception:
            failures += 1
            print(f"FAIL  {name}")
            traceback.print_exc()
    print(f"{len(_cases()) - failures} passed, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
