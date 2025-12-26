# -*- coding: utf-8 -*-
from __future__ import print_function
import os, tempfile, shutil, unittest
from ._helpers import run_py

class SafeCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.mkdtemp(prefix="safe-check-test-")
        self.scripts=os.path.join(self.tmp, "scripts")
        os.makedirs(self.scripts)
        # safe_check expects sibling scripts in same directory
        for name in ("safe_check.py","safe_run.py","safe_archive.py","preflight_automerge_ruleset.py"):
            shutil.copy2(os.path.join(os.path.dirname(__file__), "..", name), os.path.join(self.scripts, name))
        self.safe_check=os.path.join(self.scripts, "safe_check.py")
        self.env=os.environ.copy()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_self_check_passes(self):
        rc, out, err, cmd = run_py(self.safe_check, [], cwd=self.tmp, env=self.env, timeout=60)
        self.assertEqual(rc, 0, "stderr=%s\nstdout=%s" % (err, out))
        self.assertIn(b"PASS", out)

if __name__ == "__main__":
    unittest.main()
