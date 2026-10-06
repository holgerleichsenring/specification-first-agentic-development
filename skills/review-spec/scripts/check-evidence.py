#!/usr/bin/env python3
"""Check that every fact of a spec cites evidence that resolves.

Each `facts[].evidence` is read with the evidence grammar (shared with agent-smith's
EvidenceReferences; the parse cases in ../evidence-cases.yaml are the contract) and resolved
against the repository: every cited path a file, every cited line inside it, every
`observed:` segment dated.

Usage:
  check-evidence.py [--repo-root DIR] [--evidence-root NAME=PATH ...] SPEC [SPEC ...]
  check-evidence.py --self-test [--cases FILE]

Exit codes: 0 clean, 1 problems found, 2 usage error, 3 the check did not run (no PyYAML),
4 the spec lies under a 2.4 phases directory (run update-project's migrate-specs-layout.py).
"""

import argparse
import datetime
import functools
import glob
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:  # stdlib has no YAML parser; never pass silently
    print("evidence check did not run: needs PyYAML (pip install pyyaml)", file=sys.stderr)
    sys.exit(3)

# --- the grammar -----------------------------------------------------------------------------

LINE_LIST = re.compile(r"^\d+(-\d+)?(,\d+(-\d+)?)*$")
QUALIFIED = re.compile(r"^(?P<qualifier>[a-z][a-z0-9-]*):(?P<rest>.*/.*)$")
ROOT_FILE_WITH_LINES = re.compile(
    r"^(?P<path>[A-Za-z0-9_.-]*[A-Za-z0-9_-]\.[A-Za-z0-9]+):(?P<lines>\d+(-\d+)?(,\d+(-\d+)?)*)$")
HOST_SEGMENT = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$")
MINTED = re.compile(r"^\[L\d+\]")
DATE_SHAPED = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
OBSERVED = "observed:"
INT_MAX = 2**31 - 1


class Reference:
    def __init__(self, qualifier, path, line_text):
        self.qualifier = qualifier
        self.path = path
        self.line_text = line_text
        self.lines = parse_lines(line_text) if line_text is not None else None

    @property
    def has_unparseable_lines(self):
        return self.line_text is not None and self.lines is None

    @property
    def is_host_shaped(self):
        return HOST_SEGMENT.match(self.path.split("/", 1)[0]) is not None


def parse_lines(text):
    """'12', '12-14', '3,7-9' as (from, to) ranges; None when not a line list."""
    if not LINE_LIST.match(text):
        return None
    ranges = []
    for part in text.split(","):
        bounds = [int(b) for b in part.split("-")]
        if any(b > INT_MAX for b in bounds):
            return None
        ranges.append((bounds[0], bounds[-1]))
    return ranges


def tokens(segment):
    for raw in re.split(r"[ \t\n\r]+", segment):
        token = raw.lstrip("(`\"").rstrip(",;.)`\"")
        if token:
            yield token


def reference_of(token, previous):
    if "://" in token:
        return None
    if token[0] == ":":
        return None if previous is None else Reference(previous.qualifier, previous.path, token[1:])
    qualified = QUALIFIED.match(token)
    qualifier = qualified.group("qualifier") if qualified else None
    rest = qualified.group("rest") if qualified else token
    if "/" in rest:
        colon = rest.find(":")
        return Reference(qualifier, rest, None) if colon < 0 else Reference(qualifier, rest[:colon], rest[colon + 1:])
    root = ROOT_FILE_WITH_LINES.match(token)
    return Reference(None, root.group("path"), root.group("lines")) if root else None


def read(evidence):
    """One evidence line -> (references, observations, minted)."""
    references, observations, minted = [], [], []
    previous = None
    for raw in (evidence or "").split(";"):
        segment = raw.strip()
        if segment.startswith(OBSERVED):
            observations.append(segment)
        elif MINTED.match(segment):
            minted.append(segment)
        else:
            for token in tokens(segment):
                reference = reference_of(token, previous)
                if reference is None:
                    continue
                references.append(reference)
                previous = reference
    return references, observations, minted


# --- resolution ------------------------------------------------------------------------------

def line_count(data):
    """Lines end at '\\n'; a trailing newline closes the last line; an empty file has none."""
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    if not data:
        return 0
    newlines = data.count(b"\n")
    return newlines if data.endswith(b"\n") else newlines + 1


def date_problem(observation):
    dates = DATE_SHAPED.findall(observation)
    if not dates:
        return ("an observation states no date (yyyy-MM-dd)", None)
    for text in dates:
        try:
            datetime.datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return ("'%s' is not a date" % text, None)
    return None


def bounds_problem(reference, count):
    for start, end in reference.lines or []:
        cited = "%s:%d" % (reference.path, start) + ("" if end == start else "-%d" % end)
        if start < 1:
            return ("lines count from 1", cited)
        if end < start:
            return ("the range runs backwards", cited)
        if end > count:
            return ("past the end of a %d-line file" % count, cited)
    return None


class Policy:
    """The plugin's policy: no minted lines, no reference is a problem, unknown qualifier is a
    problem, a plan is not evidence, an observation needs a date."""

    def __init__(self, repo_root, evidence_roots, refused_prefixes):
        self.repo_root = repo_root
        self.evidence_roots = evidence_roots
        self.refused_prefixes = refused_prefixes

    def base_for(self, qualifier):
        """Directory a reference resolves against; None = accepted unchecked; False = unknown."""
        if qualifier is None:
            return self.repo_root
        if qualifier not in self.evidence_roots:
            return False
        base = os.path.join(self.repo_root, self.evidence_roots[qualifier])
        return base if os.path.isdir(base) else None


def probe(base, path):
    full = os.path.join(base, path)
    if not os.path.isfile(full):
        return None
    with open(full, "rb") as handle:
        return line_count(handle.read())


def reference_problem(reference, policy):
    base = policy.base_for(reference.qualifier)
    if base is None:
        return None
    if base is False:
        return ("the qualifier '%s' names no repository this check knows (add it to evidence_roots:)"
                % reference.qualifier, reference.path)
    if reference.qualifier is None and any(reference.path.startswith(p) for p in policy.refused_prefixes):
        return ("a plan is not evidence — cite what it rests on, or a dated observation", reference.path)
    # A host-shaped path is probed first: 'mcr.microsoft.com/dotnet/sdk:10.0' is an image tag.
    if reference.has_unparseable_lines and not reference.is_host_shaped:
        return unparseable(reference)
    count = probe(base, reference.path)
    if count is None:
        return None if reference.is_host_shaped else ("not a file (missing, or a directory)", reference.path)
    if reference.has_unparseable_lines:
        return unparseable(reference)
    return bounds_problem(reference, count)


def unparseable(reference):
    return ("the lines '%s' do not parse" % reference.line_text, reference.path)


def check(evidence, policy):
    references, observations, minted = read(evidence)
    problems = []
    if not (references or observations or minted):
        problems.append(("cites no path or dated observation", None))
    problems.extend(("a minted look line is not evidence here", None) for _ in minted)
    problems.extend(p for p in map(date_problem, observations) if p)
    problems.extend(p for p in (reference_problem(r, policy) for r in references) if p)
    return problems


# --- the spec and its project ----------------------------------------------------------------

def meta_dir_of(spec):
    """The `.{project}` directory holding `specs/<state>/<spec>`, or None."""
    directory = os.path.dirname(os.path.abspath(spec))
    while True:
        parent = os.path.dirname(directory)
        if os.path.basename(directory) == "specs":
            return parent
        if os.path.basename(directory) == "phases":
            raise LegacyLayout("%s lies under a 2.4 phases directory: run update-project's "
                               "migrate-specs-layout.py" % spec)
        if parent == directory:
            return None
        directory = parent


def load_yaml(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as error:
        raise UsageError("cannot read %s: %s" % (path, error))


@functools.lru_cache(maxsize=None)
def context_roots(meta):
    roots = {}
    for context in sorted(glob.glob(os.path.join(meta, "contexts", "*", "context.yaml"))):
        declared = (load_yaml(context) or {}).get("evidence_roots") or {}
        if not isinstance(declared, dict):
            raise UsageError("%s: evidence_roots: must map a qualifier to a path" % context)
        for name, path in declared.items():
            if name in roots and roots[name] != str(path):
                raise UsageError("evidence_roots: '%s' maps to '%s' and '%s'" % (name, roots[name], path))
            roots[name] = str(path)
    return roots


def policy_for(spec, repo_root, overrides):
    meta = meta_dir_of(spec)
    roots = dict(context_roots(meta)) if meta else {}
    roots.update(overrides)
    refused = []
    if meta:
        relative = os.path.relpath(meta, repo_root).replace(os.sep, "/")
        refused = ["%s/specs/planned/" % relative, "%s/specs/active/" % relative]
    return Policy(repo_root, roots, refused)


def text(value):
    return "" if value is None else value if isinstance(value, str) else str(value)


def check_spec(spec, repo_root, overrides):
    policy = policy_for(spec, repo_root, overrides)
    document = load_yaml(spec) or {}
    facts = document.get("facts") if isinstance(document, dict) else None
    failures = []
    for fact in facts or []:
        if not isinstance(fact, dict):
            continue
        claim = text(fact.get("claim"))
        for reason, path in check(text(fact.get("evidence")), policy):
            failures.append('%s: "%s" — %s%s' % (spec, claim, reason, "" if path is None else ": " + path))
    return failures


class UsageError(Exception):
    pass


class LegacyLayout(Exception):
    pass


def git_toplevel(spec):
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=os.path.dirname(os.path.abspath(spec)),
                             capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        raise UsageError("not inside a git repository; pass --repo-root")
    return out.stdout.strip()


# --- self-test -------------------------------------------------------------------------------

def self_test(cases_path):
    cases = load_yaml(cases_path) or []
    failures = 0
    for index, case in enumerate(cases, 1):
        references, observations, minted = read(case["evidence"])
        actual = {
            "references": [{k: v for k, v in (("qualifier", r.qualifier), ("path", r.path), ("lines", r.line_text))
                            if v is not None} for r in references],
            "observations": len(observations),
            "minted": len(minted),
        }
        expected = {
            "references": [{k: str(v) for k, v in ref.items()} for ref in case.get("references") or []],
            "observations": case.get("observations", 0),
            "minted": case.get("minted", 0),
        }
        if actual != expected:
            failures += 1
            print("case %d FAILED: %r\n  expected %r\n  actual   %r" % (index, case["evidence"], expected, actual))
    print("%d of %d parse cases agree" % (len(cases) - failures, len(cases)))
    return 1 if failures else 0


def main(argv):
    parser = argparse.ArgumentParser(description="Check a spec's facts against the repository.")
    parser.add_argument("specs", nargs="*", metavar="SPEC")
    parser.add_argument("--repo-root", help="repository root paths resolve against (default: git toplevel)")
    parser.add_argument("--evidence-root", action="append", default=[], metavar="NAME=PATH",
                        help="map a qualifier to a path relative to the repository root, over evidence_roots:; "
                             "a path that does not exist accepts the qualifier unchecked")
    parser.add_argument("--self-test", action="store_true", help="run the parse cases")
    parser.add_argument("--cases", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                        os.pardir, "evidence-cases.yaml"))
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            return self_test(args.cases)
        if not args.specs:
            parser.print_usage(sys.stderr)
            return 2
        overrides = {}
        for item in args.evidence_root:
            name, sep, path = item.partition("=")
            if not sep or not name:
                raise UsageError("--evidence-root takes NAME=PATH, got '%s'" % item)
            overrides[name] = path
        failures = []
        for spec in args.specs:
            if not os.path.isfile(spec):
                raise UsageError("no such spec: %s" % spec)
            repo_root = os.path.abspath(args.repo_root or git_toplevel(spec))
            failures.extend(check_spec(spec, repo_root, overrides))
    except UsageError as error:
        print("check-evidence: %s" % error, file=sys.stderr)
        return 2
    except LegacyLayout as error:
        print("check-evidence: %s" % error, file=sys.stderr)
        return 4
    for failure in failures:
        print(failure)
    if failures:
        print("%d evidence problem(s) in %d spec(s)" % (len(failures), len(args.specs)), file=sys.stderr)
        return 1
    print("evidence resolves: %d spec(s)" % len(args.specs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
