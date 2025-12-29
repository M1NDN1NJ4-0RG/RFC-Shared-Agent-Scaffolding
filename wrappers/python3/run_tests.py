#!/usr/bin/env python3
"""Language-native test runner for Python3 wrappers.

Executes all Python3 unit tests for the safe-run/safe-check/safe-archive
wrapper implementations. This runner provides a native Python interface
that is functionally equivalent to run-tests.sh.

:Purpose:
Thin wrapper around existing run-tests.sh (Phase 5 decision).
Sets up environment (SAFE_RUN_BIN, working directory) and delegates
to the proven Bash runner. Future enhancement: migrate to fully
native implementation (see docs/future-work.md FW-011).

:Environment Variables:
SAFE_RUN_BIN : str, optional
    Path to Rust canonical binary.
    Default: {repo_root}/rust/target/release/safe-run
    Auto-detected from repository structure.

:Usage:
Run from wrapper directory::

    ./run_tests.py
    python3 run_tests.py

Run from repository root::

    python3 wrappers/python3/run_tests.py

:Examples:
Run all Python3 tests::

    ./run_tests.py

Run with custom binary path::

    SAFE_RUN_BIN=/path/to/safe-run ./run_tests.py

:Exit Codes:
0
    All tests passed
1
    One or more tests failed
2
    Prerequisites not met (bash not found)

:Notes:
- Requires Python 3.8+
- Requires bash to be available (thin wrapper implementation)
- Requires Rust canonical binary to be built
- Sets SAFE_RUN_BIN environment variable for tests
- Functionally equivalent to run-tests.sh (strict parity)

:See Also:
- run-tests.sh: Bash test runner (delegated to by this script)
- docs/testing/test-runner-contract.md: Parity contract specification
- docs/future-work.md: FW-011 (future native implementation)
"""

import os
import subprocess
import sys
from pathlib import Path


def find_repo_root(start_path: Path) -> Path:
    """Find repository root (2 levels up from wrapper directory).

    :param start_path: Starting directory (wrapper directory)
    :returns: Path to repository root
    """
    # Wrapper directory structure: repo_root/wrappers/python3/
    # So repo root is 2 levels up
    return start_path.parent.parent


def setup_environment() -> dict:
    """Set up test environment variables.

    :returns: Environment dictionary with SAFE_RUN_BIN set
    """
    # Get wrapper directory (where this script lives)
    wrapper_dir = Path(__file__).resolve().parent

    # Find repository root
    repo_root = find_repo_root(wrapper_dir)

    # Prepare environment
    env = os.environ.copy()

    # Set SAFE_RUN_BIN if not already set
    if "SAFE_RUN_BIN" not in env:
        rust_binary = repo_root / "rust" / "target" / "release" / "safe-run"
        env["SAFE_RUN_BIN"] = str(rust_binary)

    return env


def check_prerequisites() -> bool:
    """Check if bash is available.

    :returns: True if bash is found, False otherwise
    """
    try:
        subprocess.run(
            ["bash", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_tests() -> int:
    """Execute the test suite via run-tests.sh.

    :returns: Exit code (0=pass, 1=fail, 2=error)
    """
    # Get wrapper directory
    wrapper_dir = Path(__file__).resolve().parent

    # Check prerequisites
    if not check_prerequisites():
        print("ERROR: bash not found", file=sys.stderr)
        print("", file=sys.stderr)
        print("This test runner requires bash to be available.", file=sys.stderr)
        print("Install bash, then re-run this script.", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "Note: Future enhancement will remove bash dependency.",
            file=sys.stderr,
        )
        print("See docs/future-work.md FW-011 for details.", file=sys.stderr)
        return 2

    # Set up environment
    env = setup_environment()

    # Path to run-tests.sh
    bash_runner = wrapper_dir / "run-tests.sh"

    if not bash_runner.exists():
        print(
            f"ERROR: {bash_runner} not found",
            file=sys.stderr,
        )
        return 2

    # Run the Bash test runner
    try:
        result = subprocess.run(
            ["bash", str(bash_runner)],
            cwd=wrapper_dir,
            env=env,
            check=False,  # Don't raise on non-zero exit
        )
        return result.returncode
    except Exception as e:
        print(f"ERROR: Failed to run tests: {e}", file=sys.stderr)
        return 2


def main() -> int:
    """Main entry point.

    :returns: Exit code
    """
    return run_tests()


if __name__ == "__main__":
    sys.exit(main())
