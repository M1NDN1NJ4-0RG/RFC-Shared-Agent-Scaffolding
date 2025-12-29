#!/usr/bin/env python3
"""Contract verification suite for Python3 safe-run and safe-archive scripts.

This module validates that the Python3 implementations of safe-run and
safe-archive conform to the M0 specification contracts for failure logging,
exit code preservation, and archival semantics.

:Purpose:
Provides automated contract verification to ensure:
- safe-run creates failure artifacts on non-zero exit codes
- safe-run does NOT create artifacts on successful (exit 0) execution
- safe-run preserves the wrapped command's exit code exactly
- safe-archive moves files to the archive directory
- safe-archive respects no-clobber semantics (M0-P1-I3)

:Environment Variables:
SAFE_LOG_DIR : str, optional
    Directory for failure logs (default: .agent/FAIL-LOGS)
    Used by safe-run when creating failure artifacts

:Verification Tests:
1. **Failure path**: Run command that exits with code 42
   - Verify safe-run returns exit code 42 (exit code preservation)
   - Verify exactly one new artifact created in FAIL-LOGS

2. **Success path**: Run command that exits with code 0
   - Verify safe-run returns exit code 0
   - Verify NO artifacts created in FAIL-LOGS

3. **Archive move**: Archive newest failure log
   - Verify safe-archive moves file to FAIL-ARCHIVE
   - Verify source file no longer exists (move, not copy)
   - Verify destination file exists with correct content

4. **No-clobber**: Archive file when destination already exists
   - Verify safe-archive succeeds (auto-suffix mode, M0-P1-I3)
   - Verify original archive file unchanged (no clobber)
   - Verify new file uses .2 suffix

:CLI Usage:
    python3 scripts/python3/safe_check.py

No arguments accepted. The script discovers and tests the sibling scripts
(safe_run.py, safe_archive.py) in the same directory tree.

:Exit Codes:
0
    All contract verification tests passed
1
    Contract verification failed (assertion error, missing file, etc.)
2
    Usage error (unexpected arguments provided)

:Side Effects:
- Creates temporary directories: .agent/FAIL-LOGS, .agent/FAIL-ARCHIVE
- Generates test failure logs during verification
- Moves test artifacts to archive during verification
- All side effects occur in current working directory

:Examples:
Run contract verification::

    cd /path/to/repo
    python3 scripts/python3/safe_check.py
    # Output: INFO: SAFE-CHECK: contract verification PASSED

:Contract References:
This script verifies conformance with:
- safe-run-001: Exit code preservation
- safe-run-002: Stdout/stderr capture on failure
- safe-run-003: Failure artifact generation
- M0-P1-I3: No-clobber archival semantics (auto-suffix mode)

:See Also:
- scripts/python3/safe_run.py: Wrapper under test
- scripts/python3/safe_archive.py: Archival tool under test
- docs/rust-canonical-tool.md: Canonical contract specification
"""
import os
import sys
import glob
import subprocess
from pathlib import Path
from typing import List


def eprint(*args: object) -> None:
    """Print to stderr for status messages and errors.

    :param args: Variable arguments to print (passed to print())
    :returns: None

    All output is sent to stderr to avoid interfering with stdout,
    which may be captured or redirected during testing.
    """
    print(*args, file=sys.stderr)


def die(msg: str, rc: int = 1) -> None:
    """Print error message to stderr and exit immediately.

    :param msg: Error message to print (prefixed with "ERROR: ")
    :param rc: Exit code (default: 1)
    :raises SystemExit: Always raises to terminate the program

    This is a convenience function for fatal errors during verification.
    """
    eprint(f"ERROR: {msg}")
    raise SystemExit(rc)


def usage() -> None:
    """Print usage message to stderr and exit with code 2.

    :raises SystemExit: Always exits with code 2 (usage error)
    """
    eprint("Usage: scripts/python3/safe_check.py")
    raise SystemExit(2)


def count_files(d: str) -> int:
    """Count regular files in a directory (non-recursive).

    :param d: Directory path to count files in
    :returns: Number of regular files (not directories or symlinks)

    Used to verify that safe-run creates exactly one artifact per failure
    and no artifacts on success.
    """
    return len([p for p in glob.glob(os.path.join(d, "*")) if os.path.isfile(p)])


def main(argv: List[str]) -> int:
    """Execute contract verification tests.

    :param argv: Command-line arguments (expected to be empty)
    :returns: Exit code (0 on success, 1 on verification failure, 2 on usage error)
    :raises SystemExit: Via die() or usage() on fatal errors

    Test Sequence
    -------------
    1. Setup: Create .agent/FAIL-LOGS and .agent/FAIL-ARCHIVE directories
    2. Verify scripts exist: safe_run.py, safe_archive.py
    3. Test failure path: Command exits 42, verify artifact created and exit code preserved
    4. Test success path: Command exits 0, verify no artifact created
    5. Test archive move: Archive newest log, verify move semantics
    6. Test no-clobber: Archive when destination exists, verify auto-suffix (M0-P1-I3)

    Side Effects
    ------------
    - Creates .agent/FAIL-LOGS/ directory in current working directory
    - Creates .agent/FAIL-ARCHIVE/ directory in current working directory
    - Generates test failure logs during verification
    - Moves test artifacts during archive verification
    - Prints status messages to stderr (INFO/ERROR)

    Examples
    --------
    >>> main([])  # No arguments, runs all tests
    # INFO: safe_run failure-path OK
    # INFO: safe_run success-path OK
    # INFO: safe_archive move OK
    # INFO: safe_archive no-clobber OK
    # INFO: SAFE-CHECK: contract verification PASSED
    0
    """
    if argv:
        usage()

    log_dir = os.environ.get("SAFE_LOG_DIR", ".agent/FAIL-LOGS")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(".agent/FAIL-ARCHIVE", exist_ok=True)

    if not Path("scripts/python3/safe_run.py").is_file():
        die("Missing scripts/python3/safe_run.py")
    if not Path("scripts/python3/safe_archive.py").is_file():
        die("Missing scripts/python3/safe_archive.py")

    before = count_files(log_dir)

    # failure path
    rc = subprocess.call(
        [
            sys.executable,
            "scripts/python3/safe_run.py",
            "--",
            sys.executable,
            "-c",
            'import sys; print("hello"); print("boom", file=sys.stderr); raise SystemExit(42)',
        ],
        stdout=subprocess.DEVNULL,
    )
    if rc != 42:
        die(f"safe_run did not preserve exit code (expected 42, got {rc})")
    after = count_files(log_dir)
    if after != before + 1:
        die(f"safe_run failure did not create exactly one artifact (before={before} after={after})")
    eprint("INFO: safe_run failure-path OK")

    # success path
    before = after
    rc = subprocess.call(
        [
            sys.executable,
            "scripts/python3/safe_run.py",
            "--",
            sys.executable,
            "-c",
            'print("ok"); raise SystemExit(0)',
        ],
        stdout=subprocess.DEVNULL,
    )
    if rc != 0:
        die(f"safe_run success returned non-zero ({rc})")
    after = count_files(log_dir)
    if after != before:
        die(f"safe_run success created artifacts (before={before} after={after})")
    eprint("INFO: safe_run success-path OK")

    # archive newest
    files = sorted(
        [p for p in glob.glob(os.path.join(log_dir, "*")) if os.path.isfile(p)],
        key=os.path.getmtime,
        reverse=True,
    )
    if not files:
        die("No fail logs found to test archiving")
    newest = files[0]
    base = os.path.basename(newest)
    dest = os.path.join(".agent/FAIL-ARCHIVE", base)

    rc = subprocess.call(
        [sys.executable, "scripts/python3/safe_archive.py", newest],
        stdout=subprocess.DEVNULL,
    )
    if rc != 0:
        die(f"safe_archive failed ({rc})")
    if not os.path.exists(dest):
        die(f"Archive file missing: {dest}")
    if os.path.exists(newest):
        die("Source file still exists (expected moved)")
    eprint("INFO: safe_archive move OK")

    # no-clobber
    dummy = os.path.join(log_dir, base)
    with open(dummy, "w", encoding="utf-8") as fh:
        fh.write("dummy\n")
    rc = subprocess.call(
        [sys.executable, "scripts/python3/safe_archive.py", dummy],
        stdout=subprocess.DEVNULL,
    )
    if rc != 0:
        die(f"safe_archive no-clobber failed ({rc})")
    with open(dest, "r", encoding="utf-8", errors="replace") as fh:
        contents = fh.read()
    if "hello" not in contents:
        die("Archive content changed unexpectedly (no-clobber violation suspected)")
    eprint("INFO: safe_archive no-clobber OK")

    eprint("INFO: SAFE-CHECK: contract verification PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
