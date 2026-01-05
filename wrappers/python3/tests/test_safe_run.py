"""Unit tests for safe_run.py Python wrapper.

This test module validates the Python wrapper's behavior for the safe-run tool,
including success/failure paths, environment variable handling, signal handling,
and event ledger generation.

:Purpose:
Validates that the Python wrapper for safe-run correctly delegates to the Rust
canonical tool and satisfies contract requirements per M0-P1-I1 and M0-P1-I2.

:Test Coverage:
- Success path: Command exits 0, no artifacts created
- Failure path: Command exits non-zero, artifact created, exit code preserved
- Custom log directory via SAFE_LOG_DIR environment variable
- Tail snippet output via SAFE_SNIPPET_LINES environment variable
- SIGINT handling: Creates ABORTED log with exit code 130
- Event ledger: Sequence numbers and standardized META events
- Merged view: Optional SAFE_RUN_VIEW=merged format

:Contract Validation:
- safe-run-001: Exit code preservation (test_failure_creates_log_and_preserves_exit_code)
- safe-run-002: Stdout/stderr capture on failure (test_failure_creates_log_and_preserves_exit_code)
- safe-run-003: Failure artifact generation (test_failure_creates_log_and_preserves_exit_code)
- safe-run-004: Signal handling SIGINT -> exit 130 (test_sigint_creates_aborted_log)
- safe-run-005: Tail snippet output (test_snippet_lines_printed_to_stderr)

:Environment Variables:
SAFE_RUN_BIN : str, optional
    Path to Rust canonical binary. Required for tests unless binary is
    discoverable via standard search order.

SAFE_LOG_DIR : str, optional
    Directory for failure logs (tested by tests).

SAFE_SNIPPET_LINES : int, optional
    Number of tail lines for stderr snippet (tested by tests).

:Examples:
Run tests via pytest::

    pytest test_safe_run.py

Run tests via unittest::

    python3 test_safe_run.py

:Exit Codes:
0
    All tests passed
1
    One or more tests failed

:Notes:
- Tests invoke actual safe_run.py wrapper (not unit-tested in isolation)
- Requires Rust binary to be built and discoverable
- Uses tempfile.TemporaryDirectory for test isolation
- SIGINT test timing-dependent (may need retries on slow systems)

:Platform Notes:
- Uses tempfile.TemporaryDirectory for isolated test execution
- SIGINT test uses subprocess.Popen with signal.SIGINT
- All tests are platform-independent (Linux, macOS, Windows compatible)
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"
SAFE_RUN = SCRIPTS / "safe_run.py"


def run_safe_run(cmd_args, workdir: Path, env=None, timeout=25):
    """Run safe_run.py as a subprocess with specified command.

    :param cmd_args: Command to run through safe_run (list[str])
    :param workdir: Working directory for subprocess execution
    :param env: Optional environment variable overrides (dict)
    :param timeout: Timeout in seconds (default: 25)
    :returns: subprocess.CompletedProcess instance with returncode, stdout, stderr

    This helper function invokes safe_run.py with the specified command,
    capturing stdout and stderr for verification. The working directory
    is set to workdir to isolate test artifacts.

    Environment variables from os.environ are copied and merged with
    any overrides provided in the env parameter.
    """
    e = os.environ.copy()
    if env:
        e.update(env)
    # Ensure the wrapped command uses the same Python when we call python.
    e.setdefault("PYTHONUTF8", "1")

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
    """Get path to current Python interpreter.

    :returns: sys.executable path

    Used to ensure wrapped commands use the same Python interpreter
    as the test runner, avoiding version mismatches.
    """
    return sys.executable


def list_fail_logs(log_dir: Path):
    """List all regular files in the fail log directory.

    :param log_dir: Path to .agent/FAIL-LOGS directory
    :returns: Sorted list of Path objects for regular files

    Used to count failure artifacts and verify safe-run behavior.
    Returns empty list if directory doesn't exist.
    """
    if not log_dir.exists():
        return []
    return sorted(p for p in log_dir.iterdir() if p.is_file())


class TestSafeRun(unittest.TestCase):
    """Test safe_run.py wrapper script functionality."""

    def test_success_creates_no_artifacts(self):
        """Test that successful runs don't create FAIL-LOGS artifacts."""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            log_dir = wd / ".agent" / "FAIL-LOGS"
            proc = run_safe_run([_py(), "-c", 'print("ok")'], workdir=wd)

            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertIn("ok", proc.stdout)
            # On success, safe-run must create no artifacts.
            self.assertFalse(log_dir.exists(), "FAIL-LOGS directory should not be created on success")

    def test_failure_creates_log_and_preserves_exit_code(self):
        """Test that failures create FAIL-LOGS and preserve exit code."""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            log_dir = wd / ".agent" / "FAIL-LOGS"
            proc = run_safe_run(
                [
                    _py(),
                    "-c",
                    'import sys; print("OUT"); print("ERR", file=sys.stderr); raise SystemExit(7)',
                ],
                workdir=wd,
            )

            self.assertEqual(proc.returncode, 7)
            self.assertTrue(log_dir.exists())
            logs = list_fail_logs(log_dir)
            self.assertEqual(len(logs), 1)
            content = logs[0].read_text(encoding="utf-8", errors="replace")
            self.assertIn("=== STDOUT ===", content)
            self.assertIn("OUT", content)
            self.assertIn("=== STDERR ===", content)
            self.assertIn("ERR", content)

    def test_custom_log_dir_env(self):
        """Test that AGENT_FAIL_LOG_DIR environment variable works."""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            custom = wd / "custom_logs"
            proc = run_safe_run(
                [_py(), "-c", "raise SystemExit(3)"],
                workdir=wd,
                env={"SAFE_LOG_DIR": str(custom)},
            )
            self.assertEqual(proc.returncode, 3)
            self.assertTrue(custom.exists())
            self.assertEqual(len(list_fail_logs(custom)), 1)

    def test_snippet_lines_printed_to_stderr(self):
        """Test that snippet lines are printed to stderr."""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            proc = run_safe_run(
                [
                    _py(),
                    "-c",
                    "import sys;\n"
                    'print("line1");\n'
                    'print("line2");\n'
                    'print("line3", file=sys.stderr);\n'
                    'print("line4", file=sys.stderr);\n'
                    "raise SystemExit(9)",
                ],
                workdir=wd,
                env={"SAFE_SNIPPET_LINES": "1"},
            )

            self.assertEqual(proc.returncode, 9)
            # Should include the tail snippet with at least the last line of each stream.
            # Per conformance spec safe-run-005, we only require the actual lines,
            # not specific header text.
            self.assertIn("line2", proc.stderr)
            self.assertIn("line4", proc.stderr)

    def test_sigint_creates_aborted_log(self):
        """Test that SIGINT creates an aborted log file."""
        # Run a long-ish process via safe-run, then SIGINT safe-run itself.
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            log_dir = wd / ".agent" / "FAIL-LOGS"

            e = os.environ.copy()
            e["PYTHONUTF8"] = "1"

            # This child prints once immediately, then sleeps.
            cmd = [
                _py(),
                str(SAFE_RUN),
                _py(),
                "-c",
                'import time; print("START"); time.sleep(10)',
            ]
            p = subprocess.Popen(
                cmd,
                cwd=str(wd),
                env=e,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            try:
                # Wait until we see output so we know the pipeline is live.
                start = time.time()
                out = ""
                while time.time() - start < 5:
                    chunk = p.stdout.readline()
                    if chunk:
                        out += chunk
                        if "START" in out:
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
            self.assertRegex(logs[0].name, r"ABORTED")
            content = logs[0].read_text(encoding="utf-8", errors="replace")
            self.assertIn("START", content)

    def test_event_ledger(self):
        """Test that event ledger is generated with sequence numbers"""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            log_dir = wd / ".agent" / "FAIL-LOGS"
            proc = run_safe_run(
                [
                    _py(),
                    "-c",
                    'print("out1"); import sys; print("err1", file=sys.stderr); print("out2"); raise SystemExit(5)',
                ],
                workdir=wd,
            )

            self.assertEqual(proc.returncode, 5)
            self.assertTrue(log_dir.exists())
            logs = list_fail_logs(log_dir)
            self.assertEqual(len(logs), 1)
            content = logs[0].read_text(encoding="utf-8", errors="replace")

            # Check for event ledger markers
            self.assertIn("--- BEGIN EVENTS ---", content)
            self.assertIn("--- END EVENTS ---", content)

            # Check for standardized META events
            self.assertIn("[SEQ=1][META] safe-run start: cmd=", content)
            self.assertIn("[META] safe-run exit: code=5", content)

            # Check for stdout/stderr events
            self.assertIn("[STDOUT] out1", content)
            self.assertIn("[STDOUT] out2", content)
            self.assertIn("[STDERR] err1", content)

    def test_merged_view(self):
        """Test optional merged view output"""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            log_dir = wd / ".agent" / "FAIL-LOGS"
            proc = run_safe_run(
                [_py(), "-c", 'print("line1"); raise SystemExit(3)'],
                workdir=wd,
                env={"SAFE_RUN_VIEW": "merged"},
            )

            self.assertEqual(proc.returncode, 3)
            self.assertTrue(log_dir.exists())
            logs = list_fail_logs(log_dir)
            self.assertEqual(len(logs), 1)
            content = logs[0].read_text(encoding="utf-8", errors="replace")

            # Check for merged view markers
            self.assertIn("--- BEGIN MERGED (OBSERVED ORDER) ---", content)
            self.assertIn("--- END MERGED ---", content)

            # Check for merged view format with [#seq]
            self.assertIn("[#1][META]", content)
            self.assertIn("[#2][STDOUT] line1", content)


if __name__ == "__main__":
    unittest.main()
