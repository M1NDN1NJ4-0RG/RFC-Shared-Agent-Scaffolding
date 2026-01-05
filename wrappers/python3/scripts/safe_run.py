#!/usr/bin/env python3
"""Python wrapper for the Rust canonical safe-run tool.

This module provides a thin invoker that discovers and executes the Rust
canonical implementation of safe-run. It does NOT reimplement any contract
logic or business rules - all functionality is delegated to the Rust binary.

:Purpose:
Acts as a language-specific entry point for Python users while maintaining
contract conformance through the canonical Rust implementation. The wrapper
handles binary discovery, platform detection, and transparent argument forwarding.

:Binary Discovery Order:
Per docs/wrapper-discovery.md, the wrapper searches for the Rust binary in
this deterministic order:

1. **SAFE_RUN_BIN** environment variable (if set, used without validation)
2. **./rust/target/release/safe-run** (dev mode, relative to repo root)
3. **./dist/<os>/<arch>/safe-run** (CI artifacts, platform-specific)
4. **PATH lookup** (system-wide installation via which/shutil.which)
5. **Error with instructions** (exit 127 if not found)

:Environment Variables:
SAFE_RUN_BIN : str, optional
    Override binary path. If set, this path is used without validation.
    The wrapper will attempt to execute it and report errors if it fails.

All other environment variables are passed through to the Rust canonical tool:

SAFE_LOG_DIR : str, optional
    Directory for failure logs (default: .agent/FAIL-LOGS)
SAFE_SNIPPET_LINES : int, optional
    Number of tail lines to print on failure (default: 0)
    The snippet is printed after "command failed ... log:" line for quick
    diagnosis. Full output is always in the log file. Set to 0 to disable.
    Note: Extremely large values may produce noisy stderr.
SAFE_RUN_VIEW : str, optional
    Output view format: 'split' (default) or 'merged'

:CLI Interface:
The wrapper accepts the same arguments as the Rust canonical tool:

    python3 safe_run.py [--] <command> [args...]

The optional "--" separator is stripped before forwarding to Rust, which
expects the structure: safe-run run <command> [args...]

:Examples:
Basic usage with argument forwarding::

    python3 safe_run.py python3 -c "print('hello')"
    python3 safe_run.py -- bash -c "exit 42"

Using environment override::

    export SAFE_RUN_BIN=/custom/path/to/safe-run
    python3 safe_run.py echo "uses custom binary"

:Exit Codes:
0
    Command succeeded (proxied from Rust tool)
1-125
    Command failed with specific exit code (proxied from Rust tool)
126
    Permission denied executing the binary
127
    Binary not found (exhausted all discovery locations)
130
    SIGINT/Ctrl+C (proxied from Rust tool)

:Platform Notes:
- **Linux**: Expects x86_64 or aarch64 architecture
- **macOS**: Supports both Intel (x86_64) and Apple Silicon (aarch64/arm64)
- **Windows**: Expects x86_64 (future support, requires .exe extension)
- **Other**: Falls back to PATH lookup only

:Contract References:
This wrapper implements the discovery contract defined in:
- docs/wrapper-discovery.md: Binary discovery cascade
- docs/rust-canonical-tool.md: Canonical tool architecture

The Rust binary implements the conformance contracts:
- safe-run-001: Exit code preservation
- safe-run-002: Stdout/stderr capture and logging
- safe-run-003: Failure artifact generation
- safe-run-004: Signal handling (SIGINT -> exit 130)
- safe-run-005: Tail snippet output

:See Also:
- Repository: https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding
- Releases: https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Optional


def find_repo_root() -> Optional[Path]:
    """Walk up from script location to find repository root.

    Searches for repository markers (RFC specification file or .git directory)
    by traversing parent directories from the script's location.

    :returns: Path to repository root if found, None otherwise
    :raises: None - returns None on failure instead of raising

    Detection Logic
    ---------------
    Searches for either:
    - RFC-Shared-Agent-Scaffolding-v0.1.0.md (repository specification file)
    - .git/ directory (Git repository marker)

    The search starts at the script's parent directory and walks upward
    until a marker is found or the filesystem root is reached.

    Examples
    --------
    >>> root = find_repo_root()
    >>> if root:
    ...     print(f"Repository root: {root}")
    ... else:
    ...     print("Not in a repository")
    """
    script_path = Path(__file__).resolve()
    current = script_path.parent

    while current != current.parent:
        if (current / "RFC-Shared-Agent-Scaffolding-v0.1.0.md").exists() or (current / ".git").is_dir():
            return current
        current = current.parent

    return None


def detect_platform() -> str:
    """Detect OS and architecture for CI artifact path resolution.

    :returns: Platform string in format "<os>/<arch>" for dist/ path construction

    Supported Platforms
    -------------------
    Operating Systems:
    - Linux -> "linux"
    - macOS (Darwin) -> "macos"
    - Windows -> "windows"
    - Other -> "unknown"

    Architectures:
    - x86_64, AMD64 -> "x86_64"
    - aarch64, arm64 -> "aarch64"
    - Other -> "unknown"

    Examples
    --------
    >>> detect_platform()
    'linux/x86_64'  # On Linux x86_64
    >>> detect_platform()
    'macos/aarch64'  # On Apple Silicon Mac

    Notes
    -----
    - Uses platform.system() for OS detection
    - Uses platform.machine() for architecture detection
    - Returns "unknown/unknown" for unsupported platforms (caller handles gracefully)
    """
    # Detect OS
    system = platform.system()
    if system == "Linux":
        os_name = "linux"
    elif system == "Darwin":
        os_name = "macos"
    elif system == "Windows":
        os_name = "windows"
    else:
        os_name = "unknown"

    # Detect architecture
    machine = platform.machine()
    if machine in ("x86_64", "AMD64"):
        arch = "x86_64"
    elif machine in ("aarch64", "arm64"):
        arch = "aarch64"
    else:
        arch = "unknown"

    return f"{os_name}/{arch}"


def find_safe_run_binary() -> Optional[str]:
    """Binary discovery cascade per docs/wrapper-discovery.md.

    Implements the deterministic binary discovery rules that all language
    wrappers must follow to locate the Rust canonical tool.

    :returns: Absolute path to safe-run binary if found, None otherwise

    Discovery Order
    ---------------
    1. **SAFE_RUN_BIN environment variable**
       - If set, return the path immediately without validation
       - Let exec fail with a clear error if the path is invalid
       - Use case: Testing, CI overrides, custom installations

    2. **Dev mode: ./rust/target/release/safe-run[.exe]**
       - Relative to repository root
       - Must be executable
       - On Windows, checks for .exe extension
       - Use case: Local development, testing Rust changes

    3. **CI artifact: ./dist/<os>/<arch>/safe-run[.exe]**
       - Platform-specific path based on detect_platform()
       - Must be executable
       - On Windows, checks for .exe extension
       - Use case: CI workflows with pre-built binaries

    4. **PATH lookup via shutil.which**
       - Search system PATH for 'safe-run'
       - Use case: System-wide installation, published releases

    5. **Not found**
       - Return None (caller handles error message and exit 127)

    Side Effects
    ------------
    - Calls find_repo_root() to determine repository location
    - Calls detect_platform() for CI artifact path construction

    Examples
    --------
    >>> binary = find_safe_run_binary()
    >>> if binary:
    ...     print(f"Found: {binary}")
    ... else:
    ...     print("Not found - will exit with error")

    Notes
    -----
    - Per spec, SAFE_RUN_BIN is returned without validation
    - File existence and execute permissions are checked for dev/CI paths
    - The function does not raise exceptions; returns None on failure
    """
    # 1. Environment override (use without validation per spec)
    safe_run_bin = os.environ.get("SAFE_RUN_BIN")
    if safe_run_bin:
        # Return the path even if it doesn't exist - let exec fail with clear error
        return safe_run_bin

    repo_root = find_repo_root()
    is_windows = platform.system() == "Windows"

    # 2. Dev mode: ./rust/target/release/safe-run (or .exe on Windows)
    if repo_root:
        dev_bin = repo_root / "rust" / "target" / "release" / "safe-run"
        if dev_bin.is_file() and os.access(dev_bin, os.X_OK):
            return str(dev_bin)
        # On Windows, also try .exe extension
        if is_windows:
            dev_bin_exe = repo_root / "rust" / "target" / "release" / "safe-run.exe"
            if dev_bin_exe.is_file() and os.access(dev_bin_exe, os.X_OK):
                return str(dev_bin_exe)

    # 3. CI artifact: ./dist/<os>/<arch>/safe-run (or .exe on Windows)
    if repo_root:
        platform_str = detect_platform()
        if platform_str != "unknown/unknown":
            parts = platform_str.split("/")
            ci_bin = repo_root / "dist" / parts[0] / parts[1] / "safe-run"
            if ci_bin.is_file() and os.access(ci_bin, os.X_OK):
                return str(ci_bin)
            # On Windows, also try .exe extension
            if is_windows:
                ci_bin_exe = repo_root / "dist" / parts[0] / parts[1] / "safe-run.exe"
                if ci_bin_exe.is_file() and os.access(ci_bin_exe, os.X_OK):
                    return str(ci_bin_exe)

    # 4. PATH lookup
    which_result = shutil.which("safe-run")
    if which_result:
        return which_result

    # 5. Not found
    return None


def main() -> int:
    """Main execution: discover binary and exec with argument forwarding.

    :returns: Exit code (127 if binary not found, otherwise does not return)
    :raises SystemExit: Via os.execvp() on successful binary execution

    Behavior
    --------
    1. Discover binary using find_safe_run_binary()
    2. If not found: print actionable error to stderr, return 127
    3. If found: parse arguments and exec the Rust binary

    Argument Handling
    -----------------
    - Accepts optional "--" separator as first argument (stripped before forwarding)
    - All arguments after "--" (or all if no "--") are passed to Rust binary
    - The wrapper prepends "run" subcommand required by Rust CLI structure
    - Final command structure: <binary> run <user_args...>

    Error Handling
    --------------
    - Binary not found: Prints detailed error with installation instructions, exit 127
    - FileNotFoundError: Binary path exists but file is missing/not executable, exit 127
    - PermissionError: Binary exists but lacks execute permission, exit 126
    - OSError: Other execution failures, exit 127

    Exit Codes
    ----------
    126
        Permission denied (binary not executable)
    127
        Command not found (binary discovery failed or exec failed)
    Does not return
        On successful exec, the Rust binary replaces this process

    Side Effects
    ------------
    - Prints error messages to stderr on failure
    - Calls os.execvp() which replaces the current process on success
    - Does not return if binary execution succeeds

    Examples
    --------
    Typical usage (does not return)::

        sys.exit(main())  # Discovers and execs Rust binary

    Error case (returns 127)::

        # If binary not found, prints error and returns 127
        code = main()  # Returns instead of exec'ing
    """
    binary = find_safe_run_binary()

    if not binary:
        print(
            """\
ERROR: Rust canonical tool not found.

Searched locations:
  1. SAFE_RUN_BIN env var (not set or invalid)
  2. ./rust/target/release/safe-run (not found)
  3. ./dist/<os>/<arch>/safe-run (not found)
  4. PATH lookup (not found)

To install:
  1. Clone the repository
  2. cd rust/
  3. cargo build --release

Or download a pre-built binary from:
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases

For more information, see:
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/docs/rust-canonical-tool.md
""",
            file=sys.stderr,
        )
        return 127

    # Parse arguments: handle optional "--" separator
    args = sys.argv[1:]
    if args and args[0] == "--":
        args = args[1:]

    # Invoke the Rust canonical tool with all arguments passed through
    # The 'run' subcommand is required by the Rust CLI structure
    try:
        os.execvp(binary, [binary, "run"] + args)
    except FileNotFoundError:
        # Binary path was found during discovery but doesn't exist or isn't executable
        print(f"ERROR: Binary not found or not executable: {binary}", file=sys.stderr)
        print("\nTo install the Rust canonical tool:", file=sys.stderr)
        print("  1. Clone the repository", file=sys.stderr)
        print("  2. cd rust/", file=sys.stderr)
        print("  3. cargo build --release", file=sys.stderr)
        print("\nOr download a pre-built binary from:", file=sys.stderr)
        print(
            "  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases",
            file=sys.stderr,
        )
        return 127
    except PermissionError:
        print(f"ERROR: Permission denied executing: {binary}", file=sys.stderr)
        print(f"Try: chmod +x {binary}", file=sys.stderr)
        return 126
    except OSError as e:
        print(f"ERROR: Failed to execute {binary}: {e}", file=sys.stderr)
        return 127


if __name__ == "__main__":
    sys.exit(main())
