# -*- coding: utf-8 -*-
from __future__ import print_function
import os, sys, tempfile, shutil, time, signal, subprocess, unittest, glob
from ._helpers import run_py, make_exe, read_text, list_files, pick_python

HERE=os.path.abspath(os.path.dirname(__file__))
SCRIPT_SRC=os.environ.get("SAFE_RUN_SRC")  # optional override

class SafeRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.mkdtemp(prefix="safe-run-test-")
        self.scripts=os.path.join(self.tmp, "scripts")
        os.makedirs(self.scripts)
        # Copy the script under test
        src = SCRIPT_SRC or os.path.join(os.path.dirname(HERE), "..", "safe_run.py")
        shutil.copy2(src, os.path.join(self.scripts, "safe_run.py"))
        self.safe_run=os.path.join(self.scripts, "safe_run.py")
        self.log_dir=os.path.join(self.tmp, ".agent", "FAIL-LOGS")
        self.env=os.environ.copy()
        self.env["SAFE_LOG_DIR"]=self.log_dir
        self.env["SAFE_SNIPPET_LINES"]="3"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_success_no_artifacts_and_exit0(self):
        rc, out, err, cmd = run_py(self.safe_run, ["--", pick_python(), "-c", "print('hello')"], cwd=self.tmp, env=self.env)
        self.assertEqual(rc, 0, "expected rc=0, got %s. stderr=%s" % (rc, err))
        self.assertIn(b"hello", out)
        # On success, should not create FAIL-LOGS, or leave it empty
        if os.path.isdir(self.log_dir):
            self.assertEqual(list_files(self.log_dir), [], "expected no artifacts on success")

    def test_failure_creates_fail_log_and_preserves_exit(self):
        rc, out, err, cmd = run_py(self.safe_run, ["--", pick_python(), "-c", "import sys; print('OUT'); sys.stderr.write('ERR\\n'); sys.exit(7)"], cwd=self.tmp, env=self.env)
        self.assertEqual(rc, 7, "exit code should be preserved")
        self.assertIn(b"OUT", out)
        self.assertIn(b"ERR", err)
        self.assertTrue(os.path.isdir(self.log_dir), "FAIL-LOGS dir should be created on failure")
        hits=glob.glob(os.path.join(self.log_dir, "*-fail.txt"))
        self.assertEqual(len(hits), 1, "expected one fail log, got %r" % hits)
        txt=read_text(hits[0])
        self.assertIn("OUT", txt)
        self.assertIn("ERR", txt)

    def test_snippet_lines_printed_to_stderr_on_failure(self):
        # Create a long output so snippet tail is meaningful
        prog="import sys\nfor i in range(10):\n print('LINE%d'%i)\n sys.stderr.write('E%d\\n'%i)\nsys.exit(2)\n"
        rc, out, err, cmd = run_py(self.safe_run, ["--", pick_python(), "-c", prog], cwd=self.tmp, env=self.env)
        self.assertEqual(rc, 2)
        # stderr should include "Tail" snippet markers and last lines
        self.assertIn(b"Tail", err)
        self.assertIn(b"LINE9", err)
        self.assertIn(b"E9", err)

    def test_sigint_creates_aborted_log(self):
        py=pick_python()
        cmd=[py, self.safe_run, "--", py, "-c", "import time,sys; print('START'); sys.stdout.flush(); time.sleep(10)"]
        p=subprocess.Popen(cmd, cwd=self.tmp, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # wait for START line
        time.sleep(0.5)
        p.send_signal(signal.SIGINT)
        out, err = p.communicate(timeout=15)
        self.assertIn(b"START", out)
        # wrapper should exit 130 on SIGINT
        self.assertEqual(p.returncode, 130, "expected 130 on Ctrl+C, got %s" % p.returncode)
        hits=glob.glob(os.path.join(self.log_dir, "*-aborted.txt"))
        self.assertEqual(len(hits), 1, "expected aborted log, got %r" % hits)
        txt=read_text(hits[0])
        self.assertIn("START", txt)

    def test_log_dir_override(self):
        alt=os.path.join(self.tmp, "custom_logs")
        env=self.env.copy()
        env["SAFE_LOG_DIR"]=alt
        rc, out, err, cmd = run_py(self.safe_run, ["--", pick_python(), "-c", "import sys; sys.exit(3)"], cwd=self.tmp, env=env)
        self.assertEqual(rc, 3)
        self.assertTrue(os.path.isdir(alt))
        self.assertEqual(len(glob.glob(os.path.join(alt, "*-fail.txt"))), 1)

if __name__ == "__main__":
    unittest.main()
