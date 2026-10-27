#!/usr/bin/env python3
"""The spec-first commit gate: a PreToolUse hook on Bash, and a git commit-msg hook.

It fires on every Bash call and gates only a `git commit` whose message carries a
spec id in parentheses, e.g. `feat: ... (2026-08-24-8a3f)`: the form deliver-spec
writes. Every other command passes at once.

When it gates, it runs the `verify:` stages of every `.{project}/contexts/*/context.yaml`
in the tree the commit runs in, from that tree's top level, in context order and then in
declaration order. The first red stage blocks the commit: exit 2, with the stage's output
on stderr, which Claude Code hands back to Claude.

A project that runs its own commit gate says so with `gate: project` at the top level of
one of its context.yaml files; the gate then steps aside in one line, so exactly one gate
checks the commit. Absent, or `gate: plugin`, this gate runs. Two different values, or any
other value, block until the declaration is fixed.

`gate: git` hands the gate to a git commit-msg hook, which install-git-hook.py writes into
a clone together with a copy of this script. Started as `spec-gate.py --commit-msg <file>`,
the copy reads the final message from the file git hands it, so every agent and every
commit typed by hand meets the same stages. It runs only where `gate: git` is declared.
The PreToolUse hook steps aside for `gate: git` only when this clone has the hook and its
copy installed and the command does not skip hooks (-n, --no-verify, core.hooksPath);
otherwise it gates the commit itself, so a fresh clone is never left ungated.

Every spec commit it recognises leaves one line in the ledger, whether it passed, was
blocked or was let through unchecked: time, verdict, spec id, tree, the tree's HEAD (the
new commit's parent) and a detail. A spec commit with no line never met the gate. The
ledger is `spec-first-gate.log` in the repository's git common directory, so every
worktree of one repository writes to one file and nothing is ever committed.

A notice on a commit that is not blocked goes out as JSON on stdout (systemMessage for
the user, additionalContext for Claude): Claude Code shows nobody stderr of a hook that
exits 0.

Environment: SPEC_GATE_LOG names another ledger file, SPEC_GATE_DEADLINE the seconds all
stages may take together (default 1700, below the hook's timeout of 1800, so a slow
suite blocks instead of being cancelled, which would let the commit through unchecked).
A commit-msg run under Claude Code (CLAUDECODE=1) sits inside one Bash call, capped at
600 s, so its default is 570.

POSIX only: the stages run in their own process group, killed at the deadline.
"""

import glob
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
EXIT_BLOCK = 2
LEDGER_NAME = "spec-first-gate.log"
DEFAULT_DEADLINE = 1700
BASH_CALL_DEADLINE = 570
HOOK_MARKER = "# spec-first commit gate"
HOOK_COPY = "spec-first-gate.py"
# What a commit-msg hook inherits from git and must not hand to a stage: a stage that runs
# git elsewhere (a test fixture's temp repository) would otherwise act on this repository.
GIT_HOOK_VARIABLES = ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_PREFIX")
# A command that keeps git from running its hooks: the commit-msg hook would never see it.
SKIPS_HOOKS = re.compile(r"(?:^|\s)(?:--no-verify|-[A-Za-z]*n[A-Za-z]*)(?=\s|$)|core\.hooksPath")
TAIL_LINES = 40
PREFIX = "[spec-first gate]"

# The marker a commit message carries, in either id namespace: a counter id, e.g. (p0272)
# or (p73a), or a date-minted id, e.g. (2026-08-24-8a3f) and series member
# (2026-08-24-8a3fa). A commit spanning several specs names them all: (id, id).
SPEC_ID = r"(?:p[0-9]+[a-z]?|[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9a-f]{4}[a-z]?)"
SPEC_MARKER = re.compile(rf"\(({SPEC_ID})(?:[, \t\r\f\v]+{SPEC_ID})*\)")
# A stricter shape for the no-marker warning, so "p12" in prose does not trigger it.
STRICT_SPEC_ID = re.compile(
    r"(?:^|[^0-9A-Za-z-])(p[0-9]{4,6}[a-z]?|[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9a-f]{4}[a-z]?)(?:[^0-9A-Za-z-]|$)")

# A real `git commit`: the command word at the start of a line or after a separator, git's
# global options in between (a flag, and for the flags that take one, its value), and the
# subcommand ending at whitespace, a separator or the line, because `commit-graph` is not
# `commit`. A command that only mentions the shape (echo, grep) does not match.
_SPACE = r"[ \t\r\f\v]"
_VALUE = r"(?:\"[^\"\n]*\"|'[^'\n]*'|[^\s]+)"
_VALUE_FLAG = r"(?:-[Cc]|--(?:git-dir|work-tree|namespace|exec-path|super-prefix|config-env))"
_OPTION = rf"(?:{_VALUE_FLAG}{_SPACE}*{_VALUE}|--[A-Za-z][A-Za-z0-9-]*(?:=[^\s]*)?|-[A-Za-z]+)"
COMMIT_SHAPE = re.compile(
    rf"(?:^|[;&|]|&&){_SPACE}*git(?:{_SPACE}+{_OPTION})*{_SPACE}+commit(?:{_SPACE}|[;&|]|$)",
    re.MULTILINE)
SHELL_SUBSTITUTION = re.compile(r"\$\(|`")
# Read by a line scan, not by YAML, so the declaration holds where PyYAML is missing.
GATE_DECLARATION = re.compile(r"^gate:[ \t]*(['\"]?)([^'\"#\s]*)\1[ \t]*(?:#.*)?$", re.MULTILINE)
GATE_OWNERS = ("plugin", "project", "git")


def _load_resolver():
    spec = importlib.util.spec_from_file_location(
        "commit_message", os.path.join(HOOKS_DIR, "commit-message.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(tree, *args):
    try:
        completed = subprocess.run(["git", "-C", tree, *args], capture_output=True, text=True)
    except OSError:
        return None
    return completed.stdout.strip() if completed.returncode == 0 else None


class Gate:
    def __init__(self, command, cwd, mode="tool"):
        self.command = command
        self.cwd = cwd
        self.mode = mode  # "tool": the PreToolUse hook; "git": the commit-msg hook
        self.message = ""
        self.tree = None
        self.notices = []

    # --- reporting -------------------------------------------------------------------------

    def spec_id(self):
        marker = SPEC_MARKER.search(self.message)
        if marker:
            return marker.group(1)
        subject = self.message.splitlines()[0] if self.message else ""
        strict = STRICT_SPEC_ID.search(subject)
        return strict.group(1) if strict else "unknown"

    def ledger_path(self, tree):
        override = os.environ.get("SPEC_GATE_LOG")
        if override:
            return override
        common = _git(tree, "rev-parse", "--path-format=absolute", "--git-common-dir")
        return os.path.join(common, LEDGER_NAME) if common else None

    def record(self, verdict, tree, detail):
        """One ledger line, written in one O_APPEND write so parallel worktrees never
        interleave their lines."""
        path = self.ledger_path(tree)
        if not path:
            return
        parent = _git(tree, "rev-parse", "--short", "HEAD") or "none"
        fields = [time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), verdict, self.spec_id(),
                  tree, parent, detail]
        line = "\t".join(re.sub(r"[\t\r\n]+", " ", field) for field in fields) + "\n"
        try:
            handle = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
            try:
                os.write(handle, line.encode("utf-8"))
            finally:
                os.close(handle)
        except OSError:
            pass

    def log(self, text):
        print(f"{PREFIX} {text}", file=sys.stderr)

    def notify(self, text):
        """A line the user and Claude both see on a commit that goes ahead."""
        self.log(text)
        self.notices.append(f"{PREFIX} {text}")

    def flush_notices(self):
        if not self.notices:
            return
        text = "\n".join(self.notices)
        print(json.dumps({"systemMessage": text,
                          "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "additionalContext": text}}))

    def not_gated(self, tree, detail, text):
        self.record("not-gated", tree, detail)
        self.notify(text)
        return 0

    def block(self, detail, text):
        self.record("blocked", self.tree, detail)
        print(f"\nSPEC GATE BLOCKED COMMIT: {text}", file=sys.stderr)
        return EXIT_BLOCK

    # --- the decision ----------------------------------------------------------------------

    def run(self):
        if not COMMIT_SHAPE.search(self.command):
            return 0
        resolver = _load_resolver()
        resolution = resolver.resolve(self.command, self.cwd)
        if resolution.message is None:
            return self.not_gated(
                self.cwd, f"unreadable message: {resolution.reason}",
                f"could not read the commit message ({resolution.reason}); not gated. "
                "Run the verify stages by hand if this is a spec commit.")
        self.message = resolution.message
        if not SPEC_MARKER.search(self.message):
            return self.unmarked()
        self.tree = self.resolve_tree(resolver)
        if self.tree is None:
            print(f"{PREFIX} cannot resolve the git tree to gate", file=sys.stderr)
            return EXIT_BLOCK
        return self.gate()

    def unmarked(self):
        # A message git hands the hook in a file never went through a shell.
        if self.mode == "tool" and SHELL_SUBSTITUTION.search(self.message):
            return self.not_gated(
                self.cwd, "message built by a shell substitution",
                f"the commit message is built by the shell ({self.message[:60]}); its text never "
                "reached the gate, so it was not gated. Run the verify stages by hand if this is "
                "a spec commit.")
        subject = self.message.splitlines()[0] if self.message else ""
        # create-spec and review-spec commit as `spec: {id} ...` on purpose, without the
        # marker: that is the planning commit, not the delivering one.
        if not subject.startswith("spec:") and STRICT_SPEC_ID.search(subject):
            return self.not_gated(
                self.cwd, "spec named in the subject without a marker",
                "the subject names a spec but carries no marker the gate reads. Write it as "
                "'(<id>)' or '(<id>, <id>)'. Not gated; run the verify stages by hand.")
        return 0

    def resolve_tree(self, resolver):
        """The tree the commit runs in: the cwd moved by a leading cd and git's -C, then the
        cwd, then the session's project directory, each resolved to its git top level."""
        for candidate in (resolver.work_directory(self.command, self.cwd or "."), self.cwd,
                          os.environ.get("CLAUDE_PROJECT_DIR", ".")):
            if candidate and os.path.isdir(candidate):
                top = _git(candidate, "rev-parse", "--show-toplevel")
                if top:
                    return top
        return None

    def gate(self):
        contexts = sorted(path for path in glob.glob(os.path.join(self.tree, ".*", "contexts", "*", "context.yaml"))
                          if os.sep + ".git" + os.sep not in path)
        if not contexts:
            return self.not_gated(
                self.tree, "no contexts",
                f"no .{{project}}/contexts/*/context.yaml in {self.tree}; nothing to gate.")
        owner = self.owner(contexts)
        if owner is not None:
            return owner
        try:
            import yaml
        except ImportError:
            return self.not_gated(
                self.tree, "PyYAML missing",
                "the verify stages could not be read: the gate needs PyYAML (pip install pyyaml). "
                "Not gated; run the verify stages by hand.")
        stages = []
        for context in contexts:
            try:
                with open(context, encoding="utf-8") as handle:
                    document = yaml.safe_load(handle) or {}
            except (OSError, yaml.YAMLError) as error:
                return self.block(f"unreadable {os.path.relpath(context, self.tree)}",
                                  f"cannot read {context}: {error}")
            problem, found = self.stages_of(document, context)
            if problem:
                return self.block(f"malformed verify in {os.path.relpath(context, self.tree)}", problem)
            stages.extend(found)
        if not stages:
            return self.not_gated(
                self.tree, "no verify stages declared",
                "no verify stages declared in any context.yaml; the commit is not gated.")
        return self.run_stages(stages)

    def owner(self, contexts):
        """None when this gate runs; otherwise the exit code of stepping aside or blocking."""
        declared = {}
        for context in contexts:
            try:
                with open(context, encoding="utf-8") as handle:
                    found = GATE_DECLARATION.search(handle.read())
            except OSError:
                continue
            if found:
                declared[os.path.relpath(context, self.tree)] = found.group(2)
        unknown = {path: value for path, value in declared.items() if value not in GATE_OWNERS}
        if unknown:
            named = ", ".join(f"{path}: {value or '(empty)'}" for path, value in unknown.items())
            return self.block("unknown gate value", f"gate: must be plugin, project or git ({named}).")
        if len(set(declared.values())) > 1:
            named = ", ".join(f"{path}: {value}" for path, value in declared.items())
            return self.block("conflicting gate declarations",
                              f"the contexts declare different gates ({named}); one repository has one gate.")
        if "project" in declared.values():
            where = ", ".join(declared)
            return self.not_gated(
                self.tree, "gate: project",
                f"this project owns its commit gate (gate: project in {where}); the spec-first gate steps aside.")
        if self.mode == "git":
            if "git" in declared.values():
                return None
            self.log("this repository does not declare gate: git, so the commit-msg hook steps aside; "
                     "the Claude Code plugin's gate, if installed, checks spec commits.")
            return 0
        if "git" in declared.values():
            if git_hook_installed(self.tree) and not SKIPS_HOOKS.search(self.command):
                # No ledger line here: the commit-msg hook writes the one line this commit gets.
                self.notify("gate: git; the commit-msg hook gates this commit.")
                return 0
            self.notify("gate: git is declared, but this clone has no spec-first commit-msg hook "
                        "or the command skips hooks; the plugin gates this commit itself.")
        return None

    def stages_of(self, document, context):
        verify = document.get("verify") if isinstance(document, dict) else None
        if verify is None:
            return None, []
        if not isinstance(verify, list):
            return f"{context}: verify: must be a list of stages", []
        found = []
        for index, stage in enumerate(verify):
            if not isinstance(stage, dict) or not isinstance(stage.get("label"), str) \
                    or not isinstance(stage.get("command"), str):
                return f"{context}: verify stage {index + 1} needs a label and a command", []
            found.append(stage)
        return None, found

    def run_stages(self, stages):
        deadline = time.monotonic() + deadline_seconds(self.mode)
        ran, skipped = [], []
        self.log(f"spec commit detected; gating {self.tree}: {', '.join(s['label'] for s in stages)}")
        for stage in stages:
            label = stage["label"]
            when_present = stage.get("when_present")
            if isinstance(when_present, str) and not os.path.exists(os.path.join(self.tree, when_present)):
                skipped.append(label)
                self.notify(f"skipped {label}: {when_present} not present")
                continue
            self.log(f"{label}: {stage['command']}")
            outcome, output = run_stage(stage["command"], self.tree, deadline - time.monotonic())
            if outcome != "ok":
                print(tail(output), file=sys.stderr)
                reason = f"{label} (over the deadline)" if outcome == "timeout" else label
                return self.block(reason, f"{reason} failed. Fix it before committing the spec.")
            ran.append(label)
            self.log(f"{label} ok")
        detail = ",".join(ran) + (f" (skipped: {','.join(skipped)})" if skipped else "")
        self.record("passed", self.tree, detail)
        self.notify(f"passed {', '.join(ran) or 'no stage'} for {self.spec_id()}")
        return 0


def deadline_seconds(mode):
    if os.environ.get("SPEC_GATE_DEADLINE"):
        return float(os.environ["SPEC_GATE_DEADLINE"])
    if mode == "git" and os.environ.get("CLAUDECODE") == "1":
        return float(BASH_CALL_DEADLINE)
    return float(DEFAULT_DEADLINE)


def git_hook_installed(tree):
    """True when this clone's hooks directory holds our commit-msg hook and the gate copy
    it runs: only then does the commit-msg hook really gate the commit."""
    hooks = _git(tree, "rev-parse", "--git-path", "hooks")
    if not hooks:
        return False
    hooks = hooks if os.path.isabs(hooks) else os.path.join(tree, hooks)
    try:
        with open(os.path.join(hooks, "commit-msg"), encoding="utf-8") as handle:
            marked = HOOK_MARKER in handle.read(2048)
    except OSError:
        return False
    return marked and os.path.isfile(os.path.join(hooks, HOOK_COPY))


def final_message(text, tree):
    """The message git will record: comment lines and everything below the scissors line of
    `git commit -v` removed, with the comment character the repository configured."""
    char = _git(tree, "config", "core.commentChar") or "#"
    if char == "auto" or len(char) != 1:
        char = "#"
    scissors = f"{char} ------------------------ >8 ------------------------"
    lines = []
    for line in text.splitlines():
        if line == scissors:
            break
        if not line.startswith(char):
            lines.append(line)
    return "\n".join(lines).strip("\n")


def run_commit_msg(path):
    """The commit-msg hook: git runs it from the work tree's top level with the message file."""
    tree = _git(".", "rev-parse", "--show-toplevel")
    if tree is None:
        print(f"{PREFIX} cannot resolve the git tree to gate", file=sys.stderr)
        return EXIT_BLOCK
    for variable in GIT_HOOK_VARIABLES:
        os.environ.pop(variable, None)
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as error:
        print(f"{PREFIX} cannot read the commit message ({error}); not gated.", file=sys.stderr)
        return 0
    gate = Gate("", tree, mode="git")
    gate.message = final_message(text, tree)
    if not SPEC_MARKER.search(gate.message):
        return gate.unmarked()
    gate.tree = tree
    return gate.gate()


def run_stage(command, tree, budget):
    """Run one stage through the shell from the tree's top level. Its whole process group
    is killed at the deadline, so a stuck child cannot outlive the gate."""
    if budget <= 0:
        return "timeout", ""
    with tempfile.TemporaryFile(mode="w+") as output:
        process = subprocess.Popen(command, shell=True, cwd=tree, stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=budget)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError:
                pass
            process.wait()
            code = None
        output.seek(0)
        text = output.read()
    if code is None:
        return "timeout", text
    return ("ok" if code == 0 else "failed"), text


def tail(text):
    return "\n".join(text.splitlines()[-TAIL_LINES:])


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--commit-msg":
        return run_commit_msg(sys.argv[2])
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    cwd = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or "."
    gate = Gate(command, cwd)
    code = gate.run()
    if code == 0:
        gate.flush_notices()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
