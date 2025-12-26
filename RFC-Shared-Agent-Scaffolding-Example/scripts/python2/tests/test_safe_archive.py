# -*- coding: utf-8 -*-
from __future__ import print_function
import os, tempfile, shutil, unittest, glob
from ._helpers import run_py, read_text, list_files

class SafeArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.mkdtemp(prefix="safe-archive-test-")
        self.scripts=os.path.join(self.tmp, "scripts")
        os.makedirs(self.scripts)
        shutil.copy2(os.path.join(os.path.dirname(__file__), "..", "safe_archive.py"), os.path.join(self.scripts, "safe_archive.py"))
        self.safe_archive=os.path.join(self.scripts, "safe_archive.py")
        self.fail_dir=os.path.join(self.tmp, ".agent", "FAIL-LOGS")
        self.arc_dir=os.path.join(self.tmp, ".agent", "FAIL-ARCHIVE")
        os.makedirs(self.fail_dir)
        os.makedirs(self.arc_dir)
        # sample logs with spaces in name to test path handling
        with open(os.path.join(self.fail_dir, "a fail.txt"), "w", encoding="utf-8") as f:
            f.write("AAA\n")
        with open(os.path.join(self.fail_dir, "b.txt"), "w", encoding="utf-8") as f:
            f.write("BBB\n")

        self.env=os.environ.copy()
        self.env["SAFE_FAIL_DIR"]=self.fail_dir
        self.env["SAFE_ARCHIVE_DIR"]=self.arc_dir

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_moves_all_no_clobber(self):
        rc, out, err, cmd = run_py(self.safe_archive, ["--all"], cwd=self.tmp, env=self.env)
        self.assertEqual(rc, 0, "stderr=%s" % err)
        self.assertEqual(list_files(self.fail_dir), [], "fail dir should be empty after move")
        archived=list_files(self.arc_dir)
        self.assertEqual(len(archived), 2)
        # Running again should be no-op (still rc 0) due to no-clobber
        # Put a new file and also a conflicting file name in fail_dir
        with open(os.path.join(self.fail_dir, "b.txt"), "w", encoding="utf-8") as f:
            f.write("NEW\n")
        rc2, out2, err2, cmd2 = run_py(self.safe_archive, ["--all"], cwd=self.tmp, env=self.env)
        self.assertEqual(rc2, 0, "stderr=%s" % err2)
        # b.txt should still exist in fail_dir because archive already has it
        self.assertTrue(os.path.exists(os.path.join(self.fail_dir, "b.txt")))

    def test_gzip_compress(self):
        # repopulate
        shutil.rmtree(self.fail_dir)
        os.makedirs(self.fail_dir)
        with open(os.path.join(self.fail_dir, "x.txt"), "w", encoding="utf-8") as f:
            f.write("HELLO\n")
        env=self.env.copy()
        env["SAFE_ARCHIVE_COMPRESS"]="gzip"
        rc, out, err, cmd = run_py(self.safe_archive, ["--all"], cwd=self.tmp, env=env)
        self.assertEqual(rc, 0, "stderr=%s" % err)
        gz=glob.glob(os.path.join(self.arc_dir, "x.txt.gz"))
        self.assertEqual(len(gz), 1, "expected gzip file, got %r" % gz)
        self.assertFalse(os.path.exists(os.path.join(self.arc_dir, "x.txt")), "uncompressed should not remain when gzip")
        self.assertEqual(list_files(self.fail_dir), [])

if __name__ == "__main__":
    unittest.main()
