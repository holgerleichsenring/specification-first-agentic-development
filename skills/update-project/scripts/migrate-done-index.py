#!/usr/bin/env python3
"""Move every context's state.done out of context.yaml into contexts/<name>/done.md (spec-first 2.9.0).

What it does, inside the project directory (the `.{project}` directory):
  - for each contexts/*/context.yaml with a `done:` key under `state:`, reads its entries in file order
    (a YAML parser, so quoting and escapes are decoded) and writes them to contexts/<name>/done.md, one
    line each: `- {id}: {entry}`. An existing done.md keeps its lines first; ids it already has are not
    written twice;
  - splices the `done:` block out of context.yaml as a text edit: every other line, comment and flow
    style survives byte for byte. A `state:` left with nothing under it goes too. The result must parse
    to the same document minus state.done, or nothing is written;
  - adds `<project>/contexts/*/done.md merge=union` and `<project>/memory/MEMORY.md merge=union` to the
    repository root's .gitattributes, keeping whatever it already holds.

Comment lines inside the done block are not carried over. Nothing is committed.

Usage:
  migrate-done-index.py [PROJECT_DIR]

Without PROJECT_DIR it takes the one directory, the current one or a direct child of it, that holds
contexts/*/context.yaml. None or several: refused.

Exit codes: 0 migrated or nothing to move, 1 refused (nothing changed), 2 usage error. Needs PyYAML.
"""

import glob
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - reported at run time
    yaml = None

HEADER = (
    "# Done\n"
    "\n"
    "One line per finished spec, newest first: `- {id}: {what shipped, in what area} -> {pointer to the spec}`.\n"
    "Search it for the area you touch; never read it front to back. Merged with merge=union (.gitattributes):\n"
    "add or replace your own line, never reorder the others.\n"
)
ENTRY = re.compile(r"^- (?P<id>[^\s:]+): (?P<entry>.*)$")


class Refused(Exception):
    pass


class Usage(Exception):
    pass


def git(cwd, *args):
    run = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if run.returncode != 0:
        raise Refused("git %s failed: %s" % (" ".join(args), run.stderr.strip()))
    return run.stdout


def read(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def find_project(start):
    candidates = [start] + [os.path.join(start, name) for name in sorted(os.listdir(start))]
    found = [path for path in candidates
             if os.path.isdir(path) and glob.glob(os.path.join(path, "contexts", "*", "context.yaml"))]
    if len(found) != 1:
        raise Refused("%s directory holds contexts/*/context.yaml here (%s); pass the project directory"
                      % ("no" if not found else "more than one", ", ".join(found) or start))
    return found[0]


def indent(line):
    return len(line) - len(line.lstrip(" "))


def blank(line):
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def key(line):
    stripped = line.strip()
    colon = stripped.find(":")
    return stripped[:colon].strip().strip("'\"") if colon >= 0 else ""


def end_of_block(lines, head):
    """The line after the block opened at `head`; trailing comments at or above its indent belong to the next key."""
    own = indent(lines[head])
    end = len(lines)
    for i in range(head + 1, len(lines)):
        if not blank(lines[i]) and indent(lines[i]) <= own:
            end = i
            break
    while end > head + 1 and blank(lines[end - 1]) and (not lines[end - 1].strip() or indent(lines[end - 1]) <= own):
        end -= 1
    return end


def find_key(lines, name, at, start, stop):
    for i in range(start, stop):
        if not blank(lines[i]) and indent(lines[i]) == at and key(lines[i]) == name:
            return i
    return -1


def splice(text):
    """The text with state.done removed (and an emptied state), or None when there is no done key."""
    lines = text.split("\n")
    state = find_key(lines, "state", 0, 0, len(lines))
    if state < 0:
        return None
    state_end = end_of_block(lines, state)
    child = next((indent(l) for l in lines[state + 1:state_end] if not blank(l)), None)
    if child is None:
        return None
    done = find_key(lines, "done", child, state + 1, state_end)
    if done < 0:
        return None
    lines[done:end_of_block(lines, done)] = []
    state_end = end_of_block(lines, state)
    if all(blank(l) for l in lines[state + 1:state_end]):
        lines[state:state_end] = []
        while state > 0 and state < len(lines) and not lines[state].strip() and not lines[state - 1].strip():
            del lines[state]
    return "\n".join(lines)


def one_line(value):
    return ("" if value is None else str(value)).replace("\r\n", " ").replace("\n", " ").replace("\r", " ")


def entries_of(done_md):
    return [(m.group("id"), m.group("entry")) for m in map(ENTRY.match, done_md.split("\n")) if m]


def compose(existing, migrated):
    """done.md text: the existing file (or the header) with the migrated entries it lacks appended."""
    text = existing if existing is not None else HEADER
    have = {spec_id for spec_id, _ in entries_of(text)}
    added = ["- %s: %s" % (spec_id, entry) for spec_id, entry in migrated if spec_id not in have]
    if not added:
        return text
    body = text.rstrip("\n")
    separator = "\n" if entries_of(text) else "\n\n"
    return body + separator + "\n".join(added) + "\n"


def attributes(top, project):
    relative = os.path.relpath(project, top).replace(os.sep, "/")
    prefix = "" if relative == "." else relative + "/"
    return [prefix + "contexts/*/done.md merge=union", prefix + "memory/MEMORY.md merge=union"]


def ensure_attributes(path, lines):
    existing = read(path) if os.path.isfile(path) else ""
    have = set(existing.split("\n"))
    missing = [line for line in lines if line not in have]
    if not missing:
        return False
    head = existing if not existing or existing.endswith("\n") else existing + "\n"
    write(path, head + "\n".join(missing) + "\n")
    return True


def plan_context(path):
    text = read(path)
    document = yaml.safe_load(text) or {}
    state = document.get("state") if isinstance(document, dict) else None
    if not isinstance(state, dict) or "done" not in state:
        return None
    done = state.get("done") or {}
    if not isinstance(done, dict):
        raise Refused("%s: state.done is not a mapping" % path)
    spliced = splice(text)
    if spliced is None:
        raise Refused("%s: state.done is there but its block cannot be located as text" % path)
    expected = dict(document)
    expected["state"] = {k: v for k, v in state.items() if k != "done"}
    if not expected["state"]:
        del expected["state"]
    if (yaml.safe_load(spliced) or {}) != expected:
        raise Refused("%s: removing the done block would change more than state.done" % path)
    return spliced, [(str(spec_id), one_line(entry)) for spec_id, entry in done.items()]


def migrate(argv, out=sys.stdout):
    if yaml is None:
        raise Refused("PyYAML is required: pip install pyyaml")
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        raise Usage("usage: migrate-done-index.py [PROJECT_DIR]")
    project = os.path.abspath(argv[0]) if argv else find_project(os.getcwd())
    if not os.path.isdir(os.path.join(project, "contexts")):
        raise Usage("no contexts/ under %s" % project)
    top = git(project, "rev-parse", "--show-toplevel").strip()
    work = []
    for context in sorted(glob.glob(os.path.join(project, "contexts", "*", "context.yaml"))):
        planned = plan_context(context)
        if planned is not None:
            work.append((context, planned))
    for context, (spliced, migrated) in work:
        done_md = os.path.join(os.path.dirname(context), "done.md")
        write(done_md, compose(read(done_md) if os.path.isfile(done_md) else None, migrated))
        write(context, spliced)
        print("%s: %d entr%s -> %s" % (os.path.relpath(context, top), len(migrated),
                                       "y" if len(migrated) == 1 else "ies", os.path.relpath(done_md, top)), file=out)
    if not work:
        print("nothing to move: no context.yaml under %s carries state.done" % project, file=out)
    if ensure_attributes(os.path.join(top, ".gitattributes"), attributes(top, project)):
        print(".gitattributes: done.md and MEMORY.md merge with merge=union", file=out)
    return 0


def main():
    try:
        return migrate(sys.argv[1:])
    except Usage as error:
        print(error, file=sys.stderr)
        return 2
    except Refused as error:
        print("refused: %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
