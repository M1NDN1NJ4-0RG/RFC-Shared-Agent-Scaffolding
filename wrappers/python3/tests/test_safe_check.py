"""Unit tests for safe_check.py contract verification script.

This test module validates that safe_check.py correctly verifies the
Python3 implementations of safe-run and safe-archive conform to their
M0 specification contracts.

Purpose
-------
Meta-test that validates the safe_check.py contract verification script
works correctly in a clean, isolated environment.

Test Coverage
-------------
- End-to-end contract verification in a clean repository layout
- Verifies safe-run failure path creates artifacts
- Verifies safe-run success path doesn't create artifacts
- Verifies safe-archive moves files correctly
- Verifies safe-archive respects no-clobber semantics (M0-P1-I3)

Environment Variables
---------------------
SAFE_RUN_BIN : str, optional
    Path to Rust canonical binary (set by test setup).

Examples
--------
Run tests via pytest::

    pytest test_safe_check.py

Exit Codes
----------
0
    All tests passed
1
    One or more tests failed

Contract Validation
-------------------
The test validates that safe_check.py successfully verifies:
- safe-run exit code preservation (contract safe-run-001)
- safe-run failure artifact generation (contract safe-run-003)
- safe-archive move semantics with no-clobber (contract M0-P1-I3)

Test Dependencies
-----------------
Requires the following scripts in relative paths:
- scripts/python3/safe_run.py
- scripts/python3/safe_archive.py
- scripts/python3/safe_check.py
- scripts/python3/preflight_automerge_ruleset.py

The test creates a temporary directory and copies all scripts to the
expected relative paths before running safe_check.py.

Platform Notes
--------------
- Uses tempfile.TemporaryDirectory for isolated test execution
- All tests are platform-independent (Linux, macOS, Windows compatible)
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"
SAFE_CHECK = SCRIPTS / "safe_check.py"


def run_safe_check(workdir: Path, env=None, timeout=60):
    """Run safe_check.py as a subprocess in the specified directory.

    :param workdir: Working directory for subprocess execution
    :param env: Optional environment variable overrides (dict)
    :param timeout: Timeout in seconds (default: 60)
    :returns: subprocess.CompletedProcess instance with returncode, stdout, stderr

    Executes safe_check.py which runs contract verification tests for
    safe-run and safe-archive. The working directory must contain the
    scripts in the expected relative paths.
    """
    e = os.environ.copy()
    if env:
        e.update(env)
    proc = subprocess.run(
        [sys.executable, str(SAFE_CHECK)],
        cwd=str(workdir),
        env=e,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return proc


class TestSafeCheck(unittest.TestCase):
    """Test safe_check.py wrapper script functionality."""

    def test_safe_check_passes_in_clean_repo(self):
        """Test that safe-check passes in a clean repository."""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            # Provide the scripts in cwd, since safe_check expects relative paths.
            scripts_dir = wd / "scripts" / "python3"
            scripts_dir.mkdir(parents=True)
            for name in [
                "safe_run.py",
                "safe_archive.py",
                "safe_check.py",
                "preflight_automerge_ruleset.py",
            ]:
                (scripts_dir / name).write_bytes((SCRIPTS / name).read_bytes())

            proc = subprocess.run(
                [sys.executable, str(scripts_dir / "safe_check.py")],
                cwd=str(wd),
                env=os.environ.copy(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            self.assertEqual(
                proc.returncode,
                0,
                msg=f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
            )
            # sanity: should mention PASS somewhere
            self.assertRegex(proc.stdout + proc.stderr, r"PASS|OK")
