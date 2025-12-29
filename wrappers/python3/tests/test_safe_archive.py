"""Unit tests for safe_archive.py archival tool.

This test module validates the safe_archive.py implementation, focusing
on M0-P1-I3 no-clobber semantics (both strict and auto-suffix modes),
compression functionality, and move operations.

Purpose
-------
Validates that the Python safe-archive wrapper correctly implements the
M0-P1-I3 no-clobber contract and archival operations.

Test Coverage
-------------
- Strict no-clobber mode: Fails when destination exists (M0-P1-I3)
- Auto-suffix mode (default): Creates .2, .3, etc. when destination exists (M0-P1-I3)
- Multiple collision handling: Correctly increments suffix (.2, .3, .4, ...)
- Gzip compression: Archives with gzip compression (Python built-in)
- Specific file archival: Archives individual files by path
- Move semantics: Source file removed after archival (not copied)

Environment Variables
---------------------
SAFE_FAIL_DIR : str, optional
    Source directory for failure logs (tested by tests).

SAFE_ARCHIVE_DIR : str, optional
    Destination directory for archived logs (tested by tests).

SAFE_ARCHIVE_COMPRESS : str, optional
    Compression method: none, gzip, xz, zstd (tested by tests).

Examples
--------
Run tests via pytest::

    pytest test_safe_archive.py

Exit Codes
----------
0
    All tests passed
1
    One or more tests failed

Contract Validation (M0-P1-I3)
------------------------------
- **Strict no-clobber**: SAFE_ARCHIVE_NO_CLOBBER=1 or --no-clobber flag
  - If destination exists: RuntimeError, exit code 2
  - Source file unchanged
  - Destination file unchanged

- **Auto-suffix (default)**: No --no-clobber flag
  - If destination exists: Append .2, .3, etc. until unique
  - Source file moved to suffixed destination
  - Original destination unchanged
  - Warning printed to stderr

Test Dependencies
-----------------
Requires safe_archive.py in the expected relative path.
All tests use temporary directories for isolation.

Platform Notes
--------------
- Uses tempfile.TemporaryDirectory for isolated test execution
- gzip compression tested (Python built-in, always available)
- xz and zstd compression not tested (requires external tools)
- All tests are platform-independent (Linux, macOS, Windows compatible)
"""

import gzip
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"
SAFE_ARCHIVE = SCRIPTS / "safe_archive.py"


def _py():
    """Get path to current Python interpreter.

    :returns: sys.executable path

    Used to ensure safe_archive.py uses the same Python interpreter
    as the test runner, avoiding version mismatches.
    """
    return sys.executable


def run_archive(args, workdir: Path, env=None, timeout=25):
    """Run safe_archive.py as a subprocess with specified arguments.

    :param args: Arguments to pass to safe_archive.py (list[str])
    :param workdir: Working directory for subprocess execution
    :param env: Optional environment variable overrides (dict)
    :param timeout: Timeout in seconds (default: 25)
    :returns: subprocess.CompletedProcess instance with returncode, stdout, stderr

    This helper function invokes safe_archive.py with the specified arguments,
    capturing stdout and stderr for verification. The working directory is set
    to workdir to isolate test artifacts.
    """
    e = os.environ.copy()
    if env:
        e.update(env)
    e["PYTHONUTF8"] = "1"
    cmd = [_py(), str(SAFE_ARCHIVE)] + args
    return subprocess.run(cmd, cwd=str(workdir), env=e, text=True, capture_output=True, timeout=timeout)


class TestSafeArchive(unittest.TestCase):
    """Test safe_archive.py wrapper script functionality.
    
    Validates archival operations including file moving, compression,
    and no-clobber semantics.
    """
    
    def test_moves_all_no_clobber(self):
        """Test that --all moves all files with no-clobber behavior."""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            fail = wd / ".agent" / "FAIL-LOGS"
            arc = wd / ".agent" / "FAIL-ARCHIVE"
            fail.mkdir(parents=True)
            arc.mkdir(parents=True)

            (fail / "a fail.txt").write_text("A", encoding="utf-8")
            # Create a destination with same name -> should fail with strict no-clobber
            (arc / "a fail.txt").write_text("EXISTS", encoding="utf-8")

            # M0-P1-I3: Enable strict no-clobber mode via env var
            r = run_archive(["--all"], wd, env={"SAFE_ARCHIVE_NO_CLOBBER": "1"})
            self.assertEqual(r.returncode, 2)
            self.assertIn("Destination exists", r.stderr)
            self.assertTrue((fail / "a fail.txt").exists())

    def test_auto_suffix_default(self):
        """Test M0-P1-I3: Default auto-suffix behavior when destination exists"""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            fail = wd / ".agent" / "FAIL-LOGS"
            arc = wd / ".agent" / "FAIL-ARCHIVE"
            fail.mkdir(parents=True)
            arc.mkdir(parents=True)

            (fail / "test.log").write_text("NEW", encoding="utf-8")
            # Create a destination with same name
            (arc / "test.log").write_text("OLD", encoding="utf-8")

            # Default behavior: should auto-suffix
            r = run_archive(["--all"], wd)
            self.assertEqual(r.returncode, 0, msg=r.stderr)

            # Source should be moved
            self.assertFalse((fail / "test.log").exists())

            # Original destination should be unchanged
            self.assertEqual((arc / "test.log").read_text(encoding="utf-8"), "OLD")

            # New file should have .2 suffix
            self.assertTrue((arc / "test.log.2").exists())
            self.assertEqual((arc / "test.log.2").read_text(encoding="utf-8"), "NEW")

    def test_auto_suffix_multiple_collisions(self):
        """Test M0-P1-I3: Auto-suffix increments correctly when .2, .3 already exist"""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            fail = wd / ".agent" / "FAIL-LOGS"
            arc = wd / ".agent" / "FAIL-ARCHIVE"
            fail.mkdir(parents=True)
            arc.mkdir(parents=True)

            # Create multiple files in archive to test suffix iteration
            (arc / "test.log").write_text("FIRST", encoding="utf-8")
            (arc / "test.log.2").write_text("SECOND", encoding="utf-8")
            (arc / "test.log.3").write_text("THIRD", encoding="utf-8")

            # New file to archive
            (fail / "test.log").write_text("FOURTH", encoding="utf-8")

            # Should find .4 as the next available suffix
            r = run_archive(["--all"], wd)
            self.assertEqual(r.returncode, 0, msg=r.stderr)

            # Source should be moved
            self.assertFalse((fail / "test.log").exists())

            # All existing files should be unchanged
            self.assertEqual((arc / "test.log").read_text(encoding="utf-8"), "FIRST")
            self.assertEqual((arc / "test.log.2").read_text(encoding="utf-8"), "SECOND")
            self.assertEqual((arc / "test.log.3").read_text(encoding="utf-8"), "THIRD")

            # New file should have .4 suffix
            self.assertTrue((arc / "test.log.4").exists())
            self.assertEqual((arc / "test.log.4").read_text(encoding="utf-8"), "FOURTH")

    def test_moves_and_gzip(self):
        """Test archival with gzip compression enabled."""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            fail = wd / ".agent" / "FAIL-LOGS"
            arc = wd / ".agent" / "FAIL-ARCHIVE"
            fail.mkdir(parents=True)
            arc.mkdir(parents=True)

            src = fail / "x-fail.txt"
            src.write_text("hello\nworld\n", encoding="utf-8")

            r = run_archive(["--all"], wd, env={"SAFE_ARCHIVE_COMPRESS": "gzip"})
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            self.assertFalse(src.exists())

            gz = arc / "x-fail.txt.gz"
            self.assertTrue(gz.exists())
            with gzip.open(gz, "rt", encoding="utf-8") as f:
                data = f.read()
            self.assertIn("hello", data)

    def test_archive_specific_files(self):
        """Test archiving specific files instead of --all."""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            fail = wd / ".agent" / "FAIL-LOGS"
            arc = wd / ".agent" / "FAIL-ARCHIVE"
            fail.mkdir(parents=True)
            arc.mkdir(parents=True)

            f1 = fail / "one.txt"
            f2 = fail / "two.txt"
            f1.write_text("1", encoding="utf-8")
            f2.write_text("2", encoding="utf-8")

            r = run_archive([str(f1)], wd)
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            self.assertFalse(f1.exists())
            self.assertTrue((arc / "one.txt").exists())
            self.assertTrue(f2.exists())


if __name__ == "__main__":
    unittest.main()
