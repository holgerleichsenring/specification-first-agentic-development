"""Cases for migrate-done-index.py: run with `python3 -m unittest` from this directory."""

import importlib.util
import io
import os
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "migrate-done-index.py")
_spec = importlib.util.spec_from_file_location("migrate_done_index", SCRIPT)
migrate_done_index = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migrate_done_index)

CONTEXT = """# yaml-language-server: $schema=../../context.schema.json
meta:
  workdir: "."          # the repo root
state:
  done:
    p0002: "shipped the \\"second\\" thing -> .demo/specs/done/p0002.yaml"
    # a comment inside the block
    p0001: "shipped the first thing -> .demo/specs/done/p0001.yaml"
  active: {}

# the next section's comment
verify:
  - label: test
    command: make test
"""

MIGRATED = """# yaml-language-server: $schema=../../context.schema.json
meta:
  workdir: "."          # the repo root
state:
  active: {}

# the next section's comment
verify:
  - label: test
    command: make test
"""

ATTRIBUTES = [".demo/contexts/*/done.md merge=union", ".demo/memory/MEMORY.md merge=union"]


@unittest.skipIf(migrate_done_index.yaml is None, "PyYAML is not installed")
class MigrateDoneIndexTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self._tmp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "test")
        self.project = os.path.join(self.root, ".demo")

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=check)

    def path(self, *parts):
        return os.path.join(self.project, *parts)

    def put(self, relative, text):
        full = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)

    def read(self, relative):
        with open(os.path.join(self.root, relative), encoding="utf-8", newline="") as handle:
            return handle.read()

    def run_script(self):
        return migrate_done_index.migrate([self.project], out=io.StringIO())

    def test_state_done_moves_to_done_md_in_order_and_the_rest_stays_byte_identical(self):
        self.put(".demo/contexts/default/context.yaml", CONTEXT)

        self.assertEqual(self.run_script(), 0)

        self.assertEqual(self.read(".demo/contexts/default/context.yaml"), MIGRATED)
        done = self.read(".demo/contexts/default/done.md")
        self.assertTrue(done.startswith(migrate_done_index.HEADER))
        self.assertEqual(migrate_done_index.entries_of(done), [
            ("p0002", 'shipped the "second" thing -> .demo/specs/done/p0002.yaml'),
            ("p0001", "shipped the first thing -> .demo/specs/done/p0001.yaml"),
        ])

    def test_a_state_with_only_done_disappears(self):
        self.put(".demo/contexts/default/context.yaml",
                 'meta:\n  workdir: "."\nstate:\n  done:\n    p0001: "x"\n\n# verify next\nverify: []\n')

        self.run_script()

        self.assertEqual(self.read(".demo/contexts/default/context.yaml"),
                         'meta:\n  workdir: "."\n\n# verify next\nverify: []\n')

    def test_an_existing_done_md_keeps_its_lines_first_and_no_id_twice(self):
        self.put(".demo/contexts/default/context.yaml", CONTEXT)
        self.put(".demo/contexts/default/done.md", migrate_done_index.HEADER + "\n- s9: newest\n- p0002: kept\n")

        self.run_script()

        ids = [spec_id for spec_id, _ in migrate_done_index.entries_of(self.read(".demo/contexts/default/done.md"))]
        self.assertEqual(ids, ["s9", "p0002", "p0001"])

    def test_gitattributes_gain_the_two_lines_once_and_keep_their_own(self):
        self.put(".demo/contexts/default/context.yaml", CONTEXT)
        self.put(".gitattributes", "*.png binary")

        self.run_script()
        self.run_script()

        self.assertEqual(self.read(".gitattributes"), "*.png binary\n" + "\n".join(ATTRIBUTES) + "\n")

    def test_a_context_without_state_done_is_untouched(self):
        text = 'meta:\n  workdir: "."\nstate:\n  active: {}\n'
        self.put(".demo/contexts/default/context.yaml", text)

        self.run_script()

        self.assertEqual(self.read(".demo/contexts/default/context.yaml"), text)
        self.assertFalse(os.path.exists(self.path("contexts", "default", "done.md")))

    def test_a_project_reached_through_a_symlink_gets_attributes_relative_to_the_repository(self):
        self.put(".demo/contexts/default/context.yaml", CONTEXT)
        link = os.path.join(tempfile.mkdtemp(), "linked")
        os.symlink(self.root, link)

        migrate_done_index.migrate([os.path.join(link, ".demo")], out=io.StringIO())

        self.assertEqual(self.read(".gitattributes"), "\n".join(ATTRIBUTES) + "\n")

    def test_a_project_outside_the_repository_is_refused(self):
        self.assertRaises(migrate_done_index.Refused, migrate_done_index.attributes, self.project, self.root)

    def test_an_id_already_in_done_md_is_reported_as_skipped(self):
        self.put(".demo/contexts/default/context.yaml", CONTEXT)
        self.put(".demo/contexts/default/done.md", migrate_done_index.HEADER + "\n- p0002: kept\n")
        out = io.StringIO()

        migrate_done_index.migrate([self.project], out=out)

        self.assertIn("1 entry added", out.getvalue())
        self.assertIn("1 skipped (already in done.md)", out.getvalue())

    def test_a_list_form_state_done_is_migrated(self):
        self.put(".demo/contexts/default/context.yaml",
                 'meta:\n  workdir: "."\nstate:\n  done:\n    - "p01: first: with a colon"\n    - "p02: second"\n  active: {}\n')

        self.assertEqual(self.run_script(), 0)

        self.assertEqual(migrate_done_index.entries_of(self.read(".demo/contexts/default/done.md")),
                         [("p01", "first: with a colon"), ("p02", "second")])
        self.assertEqual(self.read(".demo/contexts/default/context.yaml"), 'meta:\n  workdir: "."\nstate:\n  active: {}\n')

    def test_two_branches_adding_different_done_lines_merge_with_both(self):
        self.put(".demo/contexts/default/context.yaml", CONTEXT)
        self.run_script()
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "migrated")
        done = ".demo/contexts/default/done.md"
        base = self.read(done)
        head, entries = base.split("- p0002:", 1)

        self.git("checkout", "-q", "-b", "branch")
        self.put(done, head + "- s-branch: the branch's spec\n- p0002:" + entries)
        self.git("commit", "-q", "-am", "branch line")
        self.git("checkout", "-q", "main")
        self.put(done, head + "- s-main: the main spec\n- p0002:" + entries)
        self.git("commit", "-q", "-am", "main line")

        merge = self.git("merge", "--no-edit", "branch", check=False)

        self.assertEqual(merge.returncode, 0, merge.stdout + merge.stderr)
        ids = [spec_id for spec_id, _ in migrate_done_index.entries_of(self.read(done))]
        self.assertEqual(sorted(ids[:2]), ["s-branch", "s-main"])
        self.assertEqual(ids[2:], ["p0002", "p0001"])
        self.assertNotIn("<<<<<<<", self.read(done))


if __name__ == "__main__":
    unittest.main()
