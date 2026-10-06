"""Cases for migrate-specs-layout.py: run with `python3 -m unittest` from this directory."""

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "migrate-specs-layout.py")
_spec = importlib.util.spec_from_file_location("migrate_specs_layout", SCRIPT)
migrate_specs_layout = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migrate_specs_layout)

SPEC = """# yaml-language-server: $schema=../../phase-spec.schema.json
phase: 2026-08-24-8a3f   # the id
goal: "move the phase"

decisions:
  - key: |
      text
phase: not-top-level-twice
"""

SCHEMA = """{
  "title": "Custom",
  "required": ["phase", "goal"],
  "properties": {
    "phase": { "type": "string", "pattern": "^custom$" },
    "goal": { "type": "string", "description": "the phase goal" },
    "owner": { "type": "string" }
  }
}
"""

DECISION_SCHEMA = """{
  "required": ["decisions"],
  "oneOf": [
    { "required": ["phase"] },
    { "required": ["run"] }
  ],
  "properties": {
    "phase": { "type": "string" },
    "run": { "type": "string" },
    "decisions": { "type": "array" }
  }
}
"""


class MigrateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self._tmp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "test")
        self.project = os.path.join(self.root, ".proj")

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True, text=True).stdout

    def write(self, relative, content):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)

    def read(self, relative):
        with open(os.path.join(self.root, relative), encoding="utf-8", newline="") as handle:
            return handle.read()

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "fixture")

    def run_script(self, *argv, cwd=None):
        out = io.StringIO()
        previous = os.getcwd()
        os.chdir(cwd or self.root)
        try:
            code = migrate_specs_layout.migrate(list(argv), out)
        finally:
            os.chdir(previous)
        return code, out.getvalue()

    def project_fixture(self):
        self.write(".proj/contexts/default/context.yaml",
                   'state:\n  done:\n    p1: "x -> .proj/phases/done/p1-x.yaml"\n')
        self.write(".proj/phases/planned/2026-08-24-8a3f-move.yaml", SPEC)
        self.write(".proj/phases/active/.gitkeep", "")
        self.write(".proj/phases/done/p1-x.yaml", "phase: p1\r\ngoal: \"crlf\"\r\n")
        self.write(".proj/phases/done/p1-x.notes.md", "phase: is prose here\n")

    def test_migrate_moves_states_and_edits_top_level_key_only(self):
        self.project_fixture()
        self.commit()
        code, _ = self.run_script(self.project)
        self.assertEqual(0, code)
        self.assertFalse(os.path.exists(os.path.join(self.project, "phases")))
        moved = self.read(".proj/specs/planned/2026-08-24-8a3f-move.yaml")
        self.assertEqual(SPEC.replace("phase: 2026", "spec: 2026").replace("../../phase-spec", "../../spec"), moved)
        self.assertEqual("spec: p1\r\ngoal: \"crlf\"\r\n", self.read(".proj/specs/done/p1-x.yaml"))
        self.assertEqual("phase: is prose here\n", self.read(".proj/specs/done/p1-x.notes.md"))
        self.assertTrue(os.path.isfile(os.path.join(self.project, "specs/active/.gitkeep")))
        self.assertIn("RM .proj/phases/planned/2026-08-24-8a3f-move.yaml -> .proj/specs/planned/",
                      self.git("status", "--porcelain"))

    def test_migrate_rewrites_decision_key(self):
        self.project_fixture()
        self.write(".proj/decisions/p1.yaml",
                   "# yaml-language-server: $schema=../decision.schema.json\n# phase: in a comment\nphase: p1\n"
                   "decisions:\n  - category: Scope\n    chose: \"phase: stays in a value\"\n")
        self.commit()
        self.run_script(self.project)
        self.assertEqual("# yaml-language-server: $schema=../decision.schema.json\n# phase: in a comment\nspec: p1\n"
                         "decisions:\n  - category: Scope\n    chose: \"phase: stays in a value\"\n",
                         self.read(".proj/decisions/p1.yaml"))

    def test_migrate_customised_schema_keeps_all_but_the_key(self):
        self.project_fixture()
        self.write(".proj/phase-spec.schema.json", SCHEMA)
        self.write(".proj/decision.schema.json", DECISION_SCHEMA)
        self.commit()
        self.run_script(self.project)
        self.assertFalse(os.path.exists(os.path.join(self.project, "phase-spec.schema.json")))
        self.assertEqual(SCHEMA.replace('"phase"', '"spec"'), self.read(".proj/spec.schema.json"))
        self.assertEqual(DECISION_SCHEMA.replace('"phase"', '"spec"'), self.read(".proj/decision.schema.json"))
        self.assertEqual({"type": "string", "pattern": "^custom$"},
                         json.loads(self.read(".proj/spec.schema.json"))["properties"]["spec"])

    def test_migrate_rewrites_pointers_and_headers(self):
        self.project_fixture()
        self.commit()
        self.run_script(self.project)
        self.assertEqual('state:\n  done:\n    p1: "x -> .proj/specs/done/p1-x.yaml"\n',
                         self.read(".proj/contexts/default/context.yaml"))
        self.assertTrue(self.read(".proj/specs/planned/2026-08-24-8a3f-move.yaml")
                        .startswith("# yaml-language-server: $schema=../../spec.schema.json\n"))

    def test_migrate_lists_files_naming_old_path(self):
        self.project_fixture()
        self.write("CLAUDE.md", "read\n.proj/phases/active/*.yaml\n")
        self.write("docs/notes.md", "nothing here\n")
        self.write(".proj/decisions/p1.yaml", "phase: p1\nreason: \"was in .proj/phases/done/\"\n")
        self.commit()
        code, report = self.run_script(self.project)
        self.assertEqual(0, code)
        listed = report.split("review by hand:\n")[1].split()
        self.assertEqual(["CLAUDE.md:2"], listed)

    def test_migrate_no_phases_dir_is_noop(self):
        self.write(".proj/contexts/default/context.yaml", "state: {}\n")
        self.write(".proj/stray.txt", "untracked\n")
        code, report = self.run_script(self.project)
        self.assertEqual(0, code)
        self.assertIn("nothing to move", report)

    def test_migrate_untracked_or_ambiguous_refuses(self):
        self.project_fixture()
        self.commit()
        self.write(".proj/phases/planned/new.yaml", "phase: new\n")
        with self.assertRaises(migrate_specs_layout.Refused):
            self.run_script(self.project)
        self.assertTrue(os.path.isdir(os.path.join(self.project, "phases/done")))
        os.remove(os.path.join(self.project, "phases/planned/new.yaml"))
        self.write(".other/contexts/default/context.yaml", "state: {}\n")
        self.write(".other/phases/planned/a.yaml", "phase: a\n")
        self.commit()
        with self.assertRaises(migrate_specs_layout.Refused):
            self.run_script()
        cli = subprocess.run([sys.executable, SCRIPT], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(1, cli.returncode)
        self.assertIn("more than one", cli.stderr)

    def test_migrate_without_argument_finds_the_one_project(self):
        self.project_fixture()
        self.commit()
        code, _ = self.run_script()
        self.assertEqual(0, code)
        self.assertTrue(os.path.isdir(os.path.join(self.project, "specs/planned")))


if __name__ == "__main__":
    unittest.main()
