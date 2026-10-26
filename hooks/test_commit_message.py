#!/usr/bin/env python3
"""Exercises the commit-message resolver and the gate over every invocation form.

Run it directly:  python3 hooks/test_commit_message.py
or with unittest: python3 -m unittest discover -s hooks -p 'test_*.py'

The Resolve_* cases call the resolver as a function. The Gate_* cases drive
spec-gate.py itself against throwaway repositories. A repository with no
.{project}/contexts makes the gate say "nothing to gate", which is the tell that it
recognised the commit as a spec commit at all. The verify cases give the repository a
context.yaml whose stages pass or fail as told, and read the ledger line left behind.
"""

import contextlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import traceback
import unittest

HOOKS_DIR = pathlib.Path(__file__).resolve().parent
RESOLVER_PATH = HOOKS_DIR / "commit-message.py"
GATE_PATH = HOOKS_DIR / "spec-gate.py"
_GATE_VARIABLES = [f"SPEC_GATE_{name}" for name in ("LOG", "DEADLINE")]
GATE_ENTERED = "nothing to gate"
MARKER_MESSAGE = "feat: something (p9999)"
MINTED_MARKER_MESSAGE = "feat: something (2026-08-24-8a3f)"

_GIT_IDENTITY = ["-c", "user.email=gate@example.invalid", "-c", "user.name=Spec Gate"]
_resolver_module = None


def _environment():
    """A git environment that ignores the operator's global and system config, and none of
    the gate's own variables, so a test sets exactly what it means to."""
    environment = dict(os.environ)
    environment.pop("CLAUDE_PROJECT_DIR", None)
    for variable in _GATE_VARIABLES:
        environment.pop(variable, None)
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    environment["GIT_CONFIG_SYSTEM"] = os.devnull
    return environment


def _resolve(command, cwd):
    global _resolver_module
    if _resolver_module is None:
        spec = importlib.util.spec_from_file_location("commit_message", RESOLVER_PATH)
        _resolver_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_resolver_module)
    return _resolver_module.resolve(command, cwd)


def _git(repo, *args):
    subprocess.run(["git", *_GIT_IDENTITY, *args], cwd=repo, env=_environment(),
                   check=True, capture_output=True, text=True)


@contextlib.contextmanager
def _repository(*messages):
    """A throwaway repository carrying one commit per given message."""
    with tempfile.TemporaryDirectory() as path:
        _git(path, "init", "-q")
        for message in messages:
            (pathlib.Path(path) / "tracked.txt").write_text(message)
            _git(path, "add", "-A")
            _git(path, "commit", "-q", "-m", message)
        yield path


def _run_gate(command, cwd, ledger=None, extra=None, interpreter=None):
    """Drive the gate; without a ledger path its record goes nowhere. `ledger="default"`
    leaves SPEC_GATE_LOG unset, so the gate writes where it would in a real session."""
    payload = json.dumps({"tool_input": {"command": command}, "cwd": cwd})
    environment = _environment()
    if ledger != "default":
        environment["SPEC_GATE_LOG"] = str(ledger) if ledger else os.devnull
    environment.update(extra or {})
    return subprocess.run(interpreter or [sys.executable, str(GATE_PATH)], input=payload,
                          cwd=cwd, env=environment, capture_output=True, text=True)


def _context_yaml(stages, gate=None):
    lines = ["meta:", "  workdir: \".\""] + ([f"gate: {gate}"] if gate is not None else [])
    lines += ["verify:"] if stages else []
    for stage in stages:
        lines.append(f"  - label: {stage['label']}")
        lines.append(f"    command: {json.dumps(stage['command'])}")
        if "when_present" in stage:
            lines.append(f"    when_present: {stage['when_present']}")
    return "\n".join(lines) + "\n"


@contextlib.contextmanager
def _project_repository(stages=({"label": "check", "command": "exit 0"},), context="default", gate=None):
    """A throwaway spec-first project whose one context declares the given verify stages."""
    with _repository("seed") as repo:
        directory = pathlib.Path(repo) / ".demo" / "contexts" / context
        directory.mkdir(parents=True)
        (directory / "context.yaml").write_text(_context_yaml(list(stages), gate))
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "chore: a project to gate")
        yield repo


def _ledger(path):
    """The ledger as a list of fields per line."""
    path = pathlib.Path(path)
    if not path.exists():
        return []
    return [line.split("\t") for line in path.read_text().splitlines() if line]


def _notice(completed):
    """The JSON notice the gate printed on stdout, or None."""
    return json.loads(completed.stdout) if completed.stdout.strip() else None


def Resolve_DashM_ReturnsTheMessage():
    result = _resolve('git commit -m "feat: the gate reads the message (p0508)"', ".")
    assert result.message == "feat: the gate reads the message (p0508)", result


def Resolve_RepeatedDashM_ReturnsAllParagraphs():
    result = _resolve('git commit -m "feat: subject (p0508)" -m "body paragraph"', ".")
    assert result.message == "feat: subject (p0508)\n\nbody paragraph", result


def Resolve_HeredocMessage_StillResolves():
    command = "git commit -m \"$(cat <<'EOF'\nfeat: heredoc subject (p0508)\n\nbody\nEOF\n)\""
    result = _resolve(command, ".")
    assert result.message is not None and "(p0508)" in result.message, result


def Resolve_DashFFile_ReadsIt():
    with tempfile.TemporaryDirectory() as path:
        message_file = pathlib.Path(path) / "message.txt"
        message_file.write_text("feat: from a file (p0508)\n")
        result = _resolve(f'git commit -F "{message_file}"', ".")
        assert result.message is not None and "(p0508)" in result.message, result


def Resolve_DashFFileRelativeToALeadingCd_ReadsIt():
    with tempfile.TemporaryDirectory() as path:
        (pathlib.Path(path) / "message.txt").write_text("feat: relative file (p0508)\n")
        with tempfile.TemporaryDirectory() as elsewhere:
            result = _resolve(f"cd {path} && git commit -F message.txt", elsewhere)
            assert result.message is not None and "(p0508)" in result.message, result


def Resolve_DashFFileAfterASemicolonCd_ReadsIt():
    # A `;` glued to the cd argument by shlex would hide the commit segment.
    with tempfile.TemporaryDirectory() as path:
        (pathlib.Path(path) / "message.txt").write_text("feat: after a semicolon (p0508)\n")
        with tempfile.TemporaryDirectory() as elsewhere:
            result = _resolve(f"cd {path}; git commit -F message.txt", elsewhere)
            assert result.message is not None and "(p0508)" in result.message, result


def Resolve_SemicolonInsideTheQuotedMessage_KeepsTheWholeMessage():
    # A `;` inside a quoted -m subject must not cut the message before the marker.
    with tempfile.TemporaryDirectory() as path:
        result = _resolve(f'cd {path} && git commit -q -m "feat: a; b (p0508)" 2>&1 | tail -1', path)
        assert result.message is not None and result.message.strip() == "feat: a; b (p0508)", result


def Resolve_SemicolonInsideASingleQuotedMessage_KeepsTheWholeMessage():
    with tempfile.TemporaryDirectory() as path:
        result = _resolve(f"cd {path}; git commit -m 'feat: a; b && c | d (p0508)'", path)
        assert result.message is not None and result.message.strip() == "feat: a; b && c | d (p0508)", result


def Resolve_WorkDirAfterASemicolonCd_IsTheCdTarget():
    _resolve("git commit -m x", ".")
    with tempfile.TemporaryDirectory() as path:
        with tempfile.TemporaryDirectory() as elsewhere:
            directory = _resolver_module.work_directory(f'cd {path};git commit -m "x; y (p0508)"', elsewhere)
            assert pathlib.Path(directory).resolve() == pathlib.Path(path).resolve(), directory


def Resolve_AmendNoEdit_ReturnsThePreviousMessage():
    with _repository("feat: the previous message (p0508)") as repo:
        result = _resolve("git commit --amend --no-edit", repo)
        assert result.message is not None, result
        assert result.message.strip() == "feat: the previous message (p0508)", result


def Resolve_DashCRev_ReturnsThatRevisionsMessage():
    with _repository("feat: older (p0507)", "feat: newer (p0508)") as repo:
        result = _resolve("git commit -C HEAD~1", repo)
        assert result.message is not None, result
        assert result.message.strip() == "feat: older (p0507)", result


def Resolve_BareCommit_ReportsUnresolvable():
    result = _resolve("git commit -a", ".")
    assert result.message is None, result
    assert result.reason, result


def Resolve_DashFStdin_ReportsUnresolvable():
    result = _resolve("git commit -F -", ".")
    assert result.message is None, result
    assert result.reason, result


def Gate_AmendNoEditCarryingASpecMarker_IsGated():
    with _repository(MARKER_MESSAGE) as repo:
        completed = _run_gate("git commit --amend --no-edit", repo)
        assert GATE_ENTERED in completed.stderr, completed.stderr


def Gate_DashFFileCarryingASpecMarker_IsGated():
    with _repository("seed") as repo:
        (pathlib.Path(repo) / "message.txt").write_text(MARKER_MESSAGE + "\n")
        completed = _run_gate("git commit -F message.txt", repo)
        assert GATE_ENTERED in completed.stderr, completed.stderr


def Gate_MessageWithoutAMarker_PassesThrough():
    with _repository("seed") as repo:
        completed = _run_gate('git commit -m "chore: no spec here"', repo)
        assert completed.returncode == 0, completed
        assert completed.stderr == "" and completed.stdout == "", completed


def Gate_UnresolvableMessage_PassesThroughAndSaysSo():
    with _repository("seed") as repo:
        completed = _run_gate("git commit -F -", repo)
        assert completed.returncode == 0, completed
        assert "could not read" in completed.stderr, completed.stderr
        assert GATE_ENTERED not in completed.stderr, completed.stderr


def Gate_UnresolvableMessage_IsRecordedAsNotGated():
    with _project_repository() as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        _run_gate("git commit -F -", repo, ledger)
        assert [line[1] for line in _ledger(ledger)] == ["not-gated"], _ledger(ledger)


def Gate_MessageBuiltByTheShell_PassesThroughAndSaysSo():
    with _project_repository() as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        completed = _run_gate('git commit -m "$(cat message.txt)"', repo, ledger)
        assert completed.returncode == 0, completed
        assert "built by the shell" in completed.stderr, completed.stderr
        assert [line[1] for line in _ledger(ledger)] == ["not-gated"], _ledger(ledger)


def Gate_InvocationFromThisSession_LeavesATrace():
    with _project_repository() as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger)
        assert completed.returncode == 0, completed
        lines = _ledger(ledger)
        assert len(lines) == 1, lines
        assert lines[0][1] == "passed" and lines[0][2] == "p9999", lines


def Gate_InvocationFromAWorktree_GatesTheWorktree():
    with _project_repository() as repo, tempfile.TemporaryDirectory() as elsewhere:
        worktree = pathlib.Path(elsewhere) / "worktree"
        _git(repo, "worktree", "add", "-q", "-b", "gate-probe", str(worktree))
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', str(worktree), ledger)
        assert completed.returncode == 0, completed
        lines = _ledger(ledger)
        assert len(lines) == 1 and lines[0][1] == "passed", lines
        assert os.path.realpath(lines[0][3]) == os.path.realpath(worktree), lines


def Gate_PassingRun_IsDistinguishableFromNoRun():
    with _project_repository() as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        _run_gate('git commit -m "chore: no spec here"', repo, ledger)
        assert _ledger(ledger) == [], _ledger(ledger)
        _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger)
        assert [line[1] for line in _ledger(ledger)] == ["passed"], _ledger(ledger)


def Gate_CommitCarryingADateMintedId_Gates():
    with _repository("seed") as repo:
        completed = _run_gate(f'git commit -m "{MINTED_MARKER_MESSAGE}"', repo)
        assert GATE_ENTERED in completed.stderr, completed.stderr


def Gate_DateMintedIdIsRecordedInTheLedger():
    with _project_repository() as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        _run_gate(f'git commit -m "{MINTED_MARKER_MESSAGE}"', repo, ledger)
        assert [line[2] for line in _ledger(ledger)] == ["2026-08-24-8a3f"], _ledger(ledger)


def Gate_MalformedDateMintedMarker_PassesThrough():
    with _repository("seed") as repo:
        completed = _run_gate('git commit -m "chore: nightly (2026-13-99-zzzz)"', repo)
        assert completed.returncode == 0, completed
        assert completed.stderr == "", completed.stderr


# --- the verify stages ---------------------------------------------------------------------

def Gate_PassingStages_RecordPassed():
    stages = [{"label": "build", "command": "exit 0"}, {"label": "test", "command": "true"}]
    with _project_repository(stages) as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger)
        assert completed.returncode == 0, completed
        assert [(line[1], line[5]) for line in _ledger(ledger)] == [("passed", "build,test")], _ledger(ledger)
        assert "passed build, test" in _notice(completed)["systemMessage"], completed.stdout


def Gate_FailingStage_BlocksWithExitTwoAndNamesIt():
    stages = [{"label": "build", "command": "exit 0"},
              {"label": "test", "command": "echo the suite is red; exit 1"},
              {"label": "lint", "command": "touch lint-ran"}]
    with _project_repository(stages) as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger)
        assert completed.returncode == 2, completed
        assert "the suite is red" in completed.stderr, completed.stderr
        assert "test failed" in completed.stderr, completed.stderr
        assert [(line[1], line[5]) for line in _ledger(ledger)] == [("blocked", "test")], _ledger(ledger)
        assert not (pathlib.Path(repo) / "lint-ran").exists(), "a stage after the red one ran"


def Gate_StagesRunFromTheTreesTopLevel():
    stages = [{"label": "where", "command": "test -d .demo"}]
    with _project_repository(stages) as repo:
        nested = pathlib.Path(repo) / "src" / "deep"
        nested.mkdir(parents=True)
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', str(nested))
        assert completed.returncode == 0, completed


def Gate_WhenPresentAbsent_SkipsAndNamesTheStage():
    stages = [{"label": "web", "command": "exit 1", "when_present": "web/package.json"},
              {"label": "build", "command": "exit 0"}]
    with _project_repository(stages) as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger)
        assert completed.returncode == 0, completed
        assert "skipped web: web/package.json not present" in _notice(completed)["systemMessage"], completed.stdout
        assert [line[5] for line in _ledger(ledger)] == ["build (skipped: web)"], _ledger(ledger)


def Gate_WhenPresentPresent_RunsTheStage():
    stages = [{"label": "web", "command": "exit 1", "when_present": "tracked.txt"}]
    with _project_repository(stages) as repo:
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo)
        assert completed.returncode == 2, completed


def Gate_StagesOfEveryContext_RunInContextOrder():
    with _project_repository([{"label": "second", "command": "test -f first-ran"}], context="b") as repo:
        directory = pathlib.Path(repo) / ".demo" / "contexts" / "a"
        directory.mkdir(parents=True)
        (directory / "context.yaml").write_text(_context_yaml([{"label": "first", "command": "touch first-ran"}]))
        with tempfile.TemporaryDirectory() as elsewhere:
            ledger = pathlib.Path(elsewhere) / "spec-gate.log"
            completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger)
            assert completed.returncode == 0, completed
            assert [line[5] for line in _ledger(ledger)] == ["first,second"], _ledger(ledger)


def Gate_AnUnknownStageKey_IsIgnoredAndTheStageRuns():
    with _project_repository([]) as repo:
        path = pathlib.Path(repo) / ".demo" / "contexts" / "default" / "context.yaml"
        path.write_text("verify:\n  - label: build\n    command: exit 1\n    when_changed: [\"src/**\"]\n")
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo)
        assert completed.returncode == 2, completed


def Gate_AStageWithoutACommand_Blocks():
    with _project_repository([]) as repo:
        path = pathlib.Path(repo) / ".demo" / "contexts" / "default" / "context.yaml"
        path.write_text("verify:\n  - label: build\n")
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo)
        assert completed.returncode == 2, completed
        assert "needs a label and a command" in completed.stderr, completed.stderr


def Gate_StageOverDeadline_Blocks():
    with _project_repository([{"label": "slow", "command": "sleep 30"}]) as repo, \
            tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        started = __import__("time").monotonic()
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger,
                              extra={"SPEC_GATE_DEADLINE": "1"})
        assert __import__("time").monotonic() - started < 20, "the stage was not stopped at the deadline"
        assert completed.returncode == 2, completed
        assert [line[5] for line in _ledger(ledger)] == ["slow (over the deadline)"], _ledger(ledger)


def Gate_NoVerifyStages_PassesLoudly():
    with _project_repository([]) as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger)
        assert completed.returncode == 0, completed
        notice = _notice(completed)
        assert "no verify stages declared" in notice["systemMessage"], completed.stdout
        assert "no verify stages declared" in notice["hookSpecificOutput"]["additionalContext"], completed.stdout
        assert [(line[1], line[5]) for line in _ledger(ledger)] == [
            ("not-gated", "no verify stages declared")], _ledger(ledger)


def Gate_WithoutPyYaml_IsNotGatedAndSaysSo():
    runner = ("import runpy, sys; sys.modules['yaml'] = None; "
              f"runpy.run_path({str(GATE_PATH)!r}, run_name='__main__')")
    with _project_repository() as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger,
                              interpreter=[sys.executable, "-c", runner])
        assert completed.returncode == 0, completed
        assert "PyYAML" in _notice(completed)["systemMessage"], completed.stdout
        assert [line[1] for line in _ledger(ledger)] == ["not-gated"], _ledger(ledger)


def Gate_DefaultLedger_IsSharedByEveryWorktree():
    with _project_repository() as repo, tempfile.TemporaryDirectory() as elsewhere:
        worktree = pathlib.Path(elsewhere) / "worktree"
        _git(repo, "worktree", "add", "-q", "-b", "gate-probe", str(worktree))
        _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, "default")
        _run_gate(f'git commit -m "{MINTED_MARKER_MESSAGE}"', str(worktree), "default")
        ledger = pathlib.Path(repo) / ".git" / "spec-first-gate.log"
        assert [line[2] for line in _ledger(ledger)] == ["p9999", "2026-08-24-8a3f"], _ledger(ledger)


def Gate_TheLedgerParent_IsTheTreesHead():
    with _project_repository() as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger)
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo,
                              capture_output=True, text=True).stdout.strip()
        assert [line[4] for line in _ledger(ledger)] == [head], _ledger(ledger)


# --- who owns the gate ----------------------------------------------------------------------

RED = ({"label": "test", "command": "exit 1"},)


def Gate_GateProject_StepsAsideWithOneLine():
    with _project_repository(RED, gate="project") as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger)
        assert completed.returncode == 0, completed
        notice = _notice(completed)["systemMessage"]
        assert "owns its commit gate" in notice and len(notice.splitlines()) == 1, notice
        assert [(line[1], line[5]) for line in _ledger(ledger)] == [("not-gated", "gate: project")], _ledger(ledger)


def Gate_GateProjectWithoutPyYaml_StillStepsAside():
    runner = ("import runpy, sys; sys.modules['yaml'] = None; "
              f"runpy.run_path({str(GATE_PATH)!r}, run_name='__main__')")
    with _project_repository(RED, gate="project") as repo, tempfile.TemporaryDirectory() as elsewhere:
        ledger = pathlib.Path(elsewhere) / "spec-gate.log"
        _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo, ledger, interpreter=[sys.executable, "-c", runner])
        assert [line[5] for line in _ledger(ledger)] == ["gate: project"], _ledger(ledger)


def Gate_GateProjectQuotedWithAComment_StepsAside():
    with _project_repository(RED, gate="\"project\"   # our own hook") as repo:
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo)
        assert completed.returncode == 0, completed


def Gate_GatePluginExplicit_RunsTheStages():
    with _project_repository(RED, gate="plugin") as repo:
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo)
        assert completed.returncode == 2, completed


def Gate_AContextWithoutADeclaration_DoesNotConflict():
    with _project_repository(RED, gate="project") as repo:
        directory = pathlib.Path(repo) / ".demo" / "contexts" / "web"
        directory.mkdir(parents=True)
        (directory / "context.yaml").write_text(_context_yaml(list(RED)))
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo)
        assert completed.returncode == 0, completed


def Gate_GateConflict_Blocks():
    with _project_repository(gate="project") as repo:
        directory = pathlib.Path(repo) / ".demo" / "contexts" / "web"
        directory.mkdir(parents=True)
        (directory / "context.yaml").write_text(_context_yaml([], gate="plugin"))
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo)
        assert completed.returncode == 2, completed
        assert "different gates" in completed.stderr, completed.stderr


def Gate_GateUnknownValue_Blocks():
    with _project_repository(gate="ours") as repo:
        completed = _run_gate(f'git commit -m "{MARKER_MESSAGE}"', repo)
        assert completed.returncode == 2, completed
        assert "must be plugin or project" in completed.stderr, completed.stderr


def _cases():
    return [(name, case) for name, case in list(globals().items())
            if callable(case) and (name.startswith("Resolve_") or name.startswith("Gate_"))]


def load_tests(loader, tests, pattern):
    """unittest discovery runs the same cases main() does."""
    suite = unittest.TestSuite()
    for name, case in _cases():
        suite.addTest(unittest.FunctionTestCase(case, description=name))
    return suite


def main():
    cases = _cases()
    failed = []
    for name, case in cases:
        try:
            case()
            print(f"PASS {name}")
        except Exception:
            failed.append(name)
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"\n{len(cases) - len(failed)}/{len(cases)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
