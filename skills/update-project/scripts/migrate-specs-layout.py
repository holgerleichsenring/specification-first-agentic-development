#!/usr/bin/env python3
"""Move a spec-first 2.4 project onto the 2.5 layout: phases/ becomes specs/, phase: becomes spec:.

What it does, inside the project directory (the `.{project}` directory):
  - git mv every tracked file under phases/ to the same path under specs/;
  - turns the top-level `phase:` key into `spec:` in every moved spec and in decisions/*.yaml,
    as a line-anchored text edit: comments, headers and layout survive byte for byte;
  - points `# yaml-language-server: $schema=` headers of moved specs at spec.schema.json;
  - rewrites `.{project}/phases/` pointers in contexts/*/context.yaml;
  - git mv phase-spec.schema.json to spec.schema.json and, in it and decision.schema.json, renames
    only the `phase` property and its `required` entries — every other customisation is kept;
  - LISTS every other tracked file of the repository that still names the old path (CLAUDE.md
    included); specs/, series/ and decisions/ are not listed. Nothing outside the directory changes.

Usage:
  migrate-specs-layout.py [PROJECT_DIR]

Without PROJECT_DIR it takes the one directory, the current one or a direct child of it, that
holds contexts/*/context.yaml beside phases/. None or several: refused.

Exit codes: 0 migrated or nothing to move, 1 refused (nothing changed), 2 usage error.
"""

import glob
import json
import os
import re
import subprocess
import sys

STATE_KEY = re.compile(r"^phase:", re.MULTILINE)
SCHEMA_HEADER = re.compile(r"^(# yaml-language-server: \$schema=\S*?)phase-spec\.schema\.json", re.MULTILINE)
PROPERTY_KEY = re.compile(r'"phase"(\s*:)')
REQUIRED_ARRAY = re.compile(r'("required"\s*:\s*\[)([^\]]*)(\])')


class Refused(Exception):
    pass


class Usage(Exception):
    pass


def git(cwd, *args):
    run = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if run.returncode != 0:
        raise Refused("git %s failed: %s" % (" ".join(args), run.stderr.strip()))
    return run.stdout


def find_project(start):
    candidates = [start] + [os.path.join(start, name) for name in sorted(os.listdir(start))]
    found = [path for path in candidates
             if os.path.isdir(os.path.join(path, "phases"))
             and glob.glob(os.path.join(path, "contexts", "*", "context.yaml"))]
    if len(found) != 1:
        raise Refused("%s directory holds contexts/*/context.yaml beside phases/ here (%s); pass the project directory"
                      % ("no" if not found else "more than one", ", ".join(found) or start))
    return found[0]


def read(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def spec_text(text):
    text = STATE_KEY.sub("spec:", text, count=1)
    return SCHEMA_HEADER.sub(r"\1spec.schema.json", text, count=1)


def schema_text(text, path):
    def required(match):
        return match.group(1) + match.group(2).replace('"phase"', '"spec"') + match.group(3)

    edited = REQUIRED_ARRAY.sub(required, PROPERTY_KEY.sub(r'"spec"\1', text))
    try:
        properties = json.loads(edited).get("properties") or {}
    except (ValueError, AttributeError) as error:
        raise Refused("%s does not read as a JSON schema after the edit: %s" % (path, error))
    if "phase" in properties:
        raise Refused("%s still declares phase after the edit" % path)
    return edited


def old_path_pattern(relative):
    prefix = "" if relative == "." else re.escape(relative + "/")
    return re.compile(r"(?<![\w./-])" + prefix + r"phases/")


class Plan:
    def __init__(self, project):
        self.project = project
        self.moves = []      # (source, target), relative to the project
        self.edits = {}      # target path relative to the project -> new text
        self.notes = []

    def edit(self, relative, before, after, note):
        if after != before:
            self.edits[relative] = after
            self.notes.append("%s: %s" % (relative, note))


def plan(project, top):
    result = Plan(project)
    relative_project = os.path.relpath(project, top).replace(os.sep, "/")
    pattern = old_path_pattern(relative_project)
    for source in git(project, "ls-files", "--", "phases").splitlines():
        target = "specs/" + source[len("phases/"):]
        if os.path.exists(os.path.join(project, target)):
            raise Refused("%s already exists" % target)
        result.moves.append((source, target))
        if target.endswith((".yaml", ".yml")):
            text = read(os.path.join(project, source))
            result.edit(target, text, spec_text(text), "phase: -> spec:")
    for decision in sorted(glob.glob(os.path.join(project, "decisions", "*.y*ml"))):
        relative = os.path.relpath(decision, project).replace(os.sep, "/")
        text = read(decision)
        result.edit(relative, text, STATE_KEY.sub("spec:", text, count=1), "phase: -> spec:")
    replacement = ("" if relative_project == "." else relative_project + "/") + "specs/"
    for context in sorted(glob.glob(os.path.join(project, "contexts", "*", "context.yaml"))):
        relative = os.path.relpath(context, project).replace(os.sep, "/")
        text = read(context)
        result.edit(relative, text, pattern.sub(replacement, text), "pointers -> specs/")
    old_schema = os.path.join(project, "phase-spec.schema.json")
    if os.path.isfile(old_schema):
        if os.path.exists(os.path.join(project, "spec.schema.json")):
            raise Refused("spec.schema.json already exists beside phase-spec.schema.json")
        result.moves.append(("phase-spec.schema.json", "spec.schema.json"))
        text = read(old_schema)
        result.edit("spec.schema.json", text, schema_text(text, old_schema), "phase property -> spec")
    decision_schema = os.path.join(project, "decision.schema.json")
    if os.path.isfile(decision_schema):
        text = read(decision_schema)
        result.edit("decision.schema.json", text, schema_text(text, decision_schema), "phase property -> spec")
    return result


def leftovers(project, top):
    """Tracked files of the repository, outside specs/, series/ and decisions/, naming the old path."""
    relative_project = os.path.relpath(project, top).replace(os.sep, "/")
    pattern = old_path_pattern(relative_project)
    skipped = tuple(("" if relative_project == "." else relative_project + "/") + d + "/"
                    for d in ("specs", "series", "decisions"))
    hits = []
    for path in git(top, "ls-files").splitlines():
        if path.startswith(skipped):
            continue
        try:
            text = read(os.path.join(top, path))
        except (OSError, UnicodeDecodeError):
            continue
        lines = [n for n, line in enumerate(text.splitlines(), 1)
                 if pattern.search(line) or "phase-spec.schema.json" in line]
        if lines:
            hits.append("%s:%s" % (path, ",".join(map(str, lines))))
    return hits


def migrate(argv, out=sys.stdout):
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        raise Usage("usage: migrate-specs-layout.py [PROJECT_DIR]")
    project = os.path.abspath(argv[0]) if argv else find_project(os.getcwd())
    if not os.path.isdir(project):
        raise Usage("no such directory: %s" % project)
    if not os.path.isdir(os.path.join(project, "phases")):
        print("nothing to move: %s has no phases/" % project, file=out)
        return 0
    top = git(project, "rev-parse", "--show-toplevel").strip()
    dirty = git(project, "status", "--porcelain", "--untracked-files=all", "--", ".")
    if dirty:
        raise Refused("uncommitted or untracked files under %s — commit first:\n%s" % (project, dirty.rstrip()))
    work = plan(project, top)
    for source, target in work.moves:
        os.makedirs(os.path.dirname(os.path.join(project, target)) or project, exist_ok=True)
        git(project, "mv", source, target)
    for relative, text in work.edits.items():
        write(os.path.join(project, relative), text)
    for directory, _, _ in sorted(os.walk(os.path.join(project, "phases")), reverse=True):
        if not os.listdir(directory):
            os.rmdir(directory)
    print("migrated %s" % project, file=out)
    print("moved %d file(s) under phases/ to specs/" % sum(1 for s, _ in work.moves if s.startswith("phases/")),
          file=out)
    for note in work.notes:
        print("  edited %s" % note, file=out)
    hits = leftovers(project, top)
    if hits:
        print("still naming the old path — review by hand:", file=out)
        for hit in hits:
            print("  %s" % hit, file=out)
    return 0


def main(argv):
    try:
        return migrate(argv)
    except Usage as error:
        print(error, file=sys.stderr)
        return 2
    except Refused as error:
        print("refused: %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
