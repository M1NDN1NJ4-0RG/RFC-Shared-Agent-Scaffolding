import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / 'scripts'
SAFE_RUN = SCRIPTS / 'safe_run.py'


def run_safe_run(cmd_args, workdir: Path, env=None, timeout=25):
    """Run safe_run.py as a subprocess.

    cmd_args is the command to run *through* safe_run (list[str]).
    Returns subprocess.CompletedProcess.
    """
    e = os.environ.copy()
    if env:
        e.update(env)
    # Ensure the wrapped command uses the same Python when we call python.
    e.setdefault('PYTHONUTF8', '1')

    proc = subprocess.run(
        [_py(), str(SAFE_RUN), *cmd_args],
        cwd=str(workdir),
        env=e,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return proc


def _py():
    return sys.executable


def list_fail_logs(log_dir: Path):
    if not log_dir.exists():
        return []
    return sorted(p for p in log_dir.iterdir() if p.is_file())


class TestSafeRun(unittest.TestCase):
    def test_success_creates_no_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            log_dir = wd / '.agent' / 'FAIL-LOGS'
            proc = run_safe_run([
                _py(),
                '-c',
                'print("ok")'
            ], workdir=wd)

            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertIn('ok', proc.stdout)
            # On success, safe-run must create no artifacts.
            self.assertFalse(log_dir.exists(), 'FAIL-LOGS directory should not be created on success')

    def test_failure_creates_log_and_preserves_exit_code(self):
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            log_dir = wd / '.agent' / 'FAIL-LOGS'
            proc = run_safe_run([
                _py(),
                '-c',
                'import sys; print("OUT"); print("ERR", file=sys.stderr); raise SystemExit(7)'
            ], workdir=wd)

            self.assertEqual(proc.returncode, 7)
            self.assertTrue(log_dir.exists())
            logs = list_fail_logs(log_dir)
            self.assertEqual(len(logs), 1)
            content = logs[0].read_text(encoding='utf-8', errors='replace')
            self.assertIn('=== STDOUT ===', content)
            self.assertIn('OUT', content)
            self.assertIn('=== STDERR ===', content)
            self.assertIn('ERR', content)

    def test_custom_log_dir_env(self):
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            custom = wd / 'custom_logs'
            proc = run_safe_run([
                _py(),
                '-c',
                'raise SystemExit(3)'
            ], workdir=wd, env={'SAFE_LOG_DIR': str(custom)})
            self.assertEqual(proc.returncode, 3)
            self.assertTrue(custom.exists())
            self.assertEqual(len(list_fail_logs(custom)), 1)

    def test_snippet_lines_printed_to_stderr(self):
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            proc = run_safe_run([
                _py(),
                '-c',
                'import sys;\n'
                'print("line1");\n'
                'print("line2");\n'
                'print("line3", file=sys.stderr);\n'
                'print("line4", file=sys.stderr);\n'
                'raise SystemExit(9)'
            ], workdir=wd, env={'SAFE_SNIPPET_LINES': '1'})

            self.assertEqual(proc.returncode, 9)
            # Should include the tail snippet indicator and at least the last line of each stream.
            self.assertIn('STDOUT tail', proc.stderr)
            self.assertIn('line2', proc.stderr)
            self.assertIn('STDERR tail', proc.stderr)
            self.assertIn('line4', proc.stderr)

    def test_sigint_creates_aborted_log(self):
        # Run a long-ish process via safe-run, then SIGINT safe-run itself.
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            log_dir = wd / '.agent' / 'FAIL-LOGS'

            e = os.environ.copy()
            e['PYTHONUTF8'] = '1'

            # This child prints once immediately, then sleeps.
            cmd = [_py(), str(SAFE_RUN), _py(), '-c', 'import time; print("START"); time.sleep(10)']
            p = subprocess.Popen(cmd, cwd=str(wd), env=e, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            try:
                # Wait until we see output so we know the pipeline is live.
                start = time.time()
                out = ''
                while time.time() - start < 5:
                    chunk = p.stdout.readline()
                    if chunk:
                        out += chunk
                        if 'START' in out:
                            break
                # Now interrupt safe-run.
                p.send_signal(signal.SIGINT)
                rc = p.wait(timeout=15)
            finally:
                try:
                    p.kill()
                except Exception:
                    pass

            # Typical Ctrl+C is 130.
            self.assertEqual(rc, 130)
            self.assertTrue(log_dir.exists())
            logs = list_fail_logs(log_dir)
            self.assertEqual(len(logs), 1)
            self.assertRegex(logs[0].name, r'ABORTED')
            content = logs[0].read_text(encoding='utf-8', errors='replace')
            self.assertIn('START', content)

    def test_event_ledger(self):
        """Test that event ledger is generated with sequence numbers"""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            log_dir = wd / '.agent' / 'FAIL-LOGS'
            proc = run_safe_run([
                _py(),
                '-c',
                'print("out1"); import sys; print("err1", file=sys.stderr); print("out2"); raise SystemExit(5)'
            ], workdir=wd)

            self.assertEqual(proc.returncode, 5)
            self.assertTrue(log_dir.exists())
            logs = list_fail_logs(log_dir)
            self.assertEqual(len(logs), 1)
            content = logs[0].read_text(encoding='utf-8', errors='replace')
            
            # Check for event ledger markers
            self.assertIn('--- BEGIN EVENTS ---', content)
            self.assertIn('--- END EVENTS ---', content)
            
            # Check for standardized META events
            self.assertIn('[SEQ=1][META] safe-run start: cmd=', content)
            self.assertIn('[META] safe-run exit: code=5', content)
            
            # Check for stdout/stderr events
            self.assertIn('[STDOUT] out1', content)
            self.assertIn('[STDOUT] out2', content)
            self.assertIn('[STDERR] err1', content)

    def test_merged_view(self):
        """Test optional merged view output"""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            log_dir = wd / '.agent' / 'FAIL-LOGS'
            proc = run_safe_run([
                _py(),
                '-c',
                'print("line1"); raise SystemExit(3)'
            ], workdir=wd, env={'SAFE_RUN_VIEW': 'merged'})

            self.assertEqual(proc.returncode, 3)
            self.assertTrue(log_dir.exists())
            logs = list_fail_logs(log_dir)
            self.assertEqual(len(logs), 1)
            content = logs[0].read_text(encoding='utf-8', errors='replace')
            
            # Check for merged view markers
            self.assertIn('--- BEGIN MERGED (OBSERVED ORDER) ---', content)
            self.assertIn('--- END MERGED ---', content)
            
            # Check for merged view format with [#seq]
            self.assertIn('[#1][META]', content)
            self.assertIn('[#2][STDOUT] line1', content)


if __name__ == '__main__':
    unittest.main()
