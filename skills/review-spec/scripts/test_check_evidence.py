"""Resolution cases for check-evidence.py: run with `python3 -m unittest` from this directory."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "check-evidence.py")
_spec = importlib.util.spec_from_file_location("check_evidence", SCRIPT)
check_evidence = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_evidence)


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.write("src/a.cs", "".join("line %d\n" % n for n in range(1, 11)))  # 10 lines
        self.write("src/empty.txt", "")
        os.makedirs(os.path.join(self.root, "src/dir"))
        os.makedirs(os.path.join(self.root, "vendor/other/docs"))
        self.write("vendor/other/docs/x.md", "one\ntwo")
        self.write(".proj/contexts/default/context.yaml",
                   "evidence_roots:\n  other: vendor/other\n  absent: not/here\n")
        self.policy = check_evidence.policy_for(
            os.path.join(self.root, ".proj/phases/planned/x.yaml"), self.root, {})

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, relative, content):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def problems(self, evidence):
        return check_evidence.check(evidence, self.policy)

    def test_existing_lines_resolve(self):
        self.assertEqual([], self.problems("src/a.cs:1-10, :3; observed: a scan, 2026-10-02"))

    def test_missing_file_is_a_problem(self):
        self.assertEqual([("not a file (missing, or a directory)", "src/nope.cs")], self.problems("src/nope.cs:1"))

    def test_directory_is_a_problem(self):
        self.assertEqual([("not a file (missing, or a directory)", "src/dir")], self.problems("src/dir"))

    def test_past_the_end_line_zero_descending_are_problems(self):
        paths = [p for _, p in self.problems("src/a.cs:11; src/a.cs:0; src/a.cs:7-3; src/a.cs:10")]
        self.assertEqual(["src/a.cs:11", "src/a.cs:0", "src/a.cs:7-3"], paths)

    def test_trailing_newline_is_not_a_line_and_empty_file_has_none(self):
        self.assertEqual(10, check_evidence.line_count(b"".join(b"x\n" for _ in range(10))))
        self.assertEqual(0, check_evidence.line_count(b""))
        self.assertEqual(1, len(self.problems("src/empty.txt:1")))

    def test_overflow_number_does_not_parse(self):
        [(reason, path)] = self.problems("src/a.cs:99999999999")
        self.assertIn("do not parse", reason)

    def test_host_shaped_missing_path_is_not_a_problem(self):
        self.assertEqual([], self.problems("mcr.microsoft.com/dotnet/sdk:10.0; ghcr.io/owner/image"))

    def test_observed_without_or_with_invalid_date_is_a_problem(self):
        self.assertEqual(1, len(self.problems("observed: a scan of the tree")))
        self.assertEqual([("'2026-02-30' is not a date", None)], self.problems("observed: a scan, 2026-02-30"))

    def test_planned_and_active_paths_are_refused(self):
        for state in ("planned", "active"):
            self.write(".proj/phases/%s/y.yaml" % state, "phase: y\n")
            [(reason, _)] = self.problems(".proj/phases/%s/y.yaml" % state)
            self.assertIn("a plan is not evidence", reason)

    def test_unknown_qualifier_is_a_problem(self):
        [(reason, _)] = self.problems("elsewhere:docs/x.md:1")
        self.assertIn("'elsewhere'", reason)

    def test_declared_qualifier_resolves_against_its_root(self):
        self.assertEqual([], self.problems("other:docs/x.md:2"))
        self.assertEqual([("past the end of a 2-line file", "docs/x.md:3")], self.problems("other:docs/x.md:3"))

    def test_declared_qualifier_without_a_tree_is_accepted_unchecked(self):
        self.assertEqual([], self.problems("absent:docs/x.md:900"))

    def test_minted_line_and_no_reference_are_problems(self):
        self.assertEqual(1, len(self.problems("[L3] api: ran 'ls' exited 0")))
        self.assertEqual(1, len(self.problems("the code says so")))

    def test_cli_exit_codes(self):
        spec = self.write(".proj/phases/planned/z.yaml", textwrap.dedent("""\
            phase: z
            facts:
              - claim: "a fine fact"
                evidence: "src/a.cs:2"
              - claim: "a broken fact"
                evidence: "src/a.cs:20"
            """))
        run = subprocess.run([sys.executable, SCRIPT, "--repo-root", self.root, spec], capture_output=True, text=True)
        self.assertEqual(1, run.returncode)
        self.assertIn('"a broken fact"', run.stdout)
        self.assertNotIn('"a fine fact"', run.stdout)
        usage = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
        self.assertEqual(2, usage.returncode)


if __name__ == "__main__":
    unittest.main()
