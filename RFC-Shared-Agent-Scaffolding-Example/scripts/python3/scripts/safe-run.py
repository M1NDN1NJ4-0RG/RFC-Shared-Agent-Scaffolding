#!/usr/bin/env python3
# safe-run.py - Thin invoker for Rust canonical safe-run tool
#
# This wrapper discovers and invokes the Rust canonical implementation.
# It does NOT reimplement any contract logic.
#
# Binary Discovery Order (per docs/wrapper-discovery.md):
#   1. SAFE_RUN_BIN env var (if set)
#   2. ./rust/target/release/safe-run (dev mode, relative to repo root)
#   3. ./dist/<os>/<arch>/safe-run (CI artifacts)
#   4. PATH lookup (system installation)
#   5. Error with actionable instructions (exit 127)

import os
import sys
import platform
import shutil
from pathlib import Path
from typing import Optional

def find_repo_root() -> Optional[Path]:
    """Walk up from script location to find repository root."""
    script_path = Path(__file__).resolve()
    current = script_path.parent
    
    while current != current.parent:
        if (current / "RFC-Shared-Agent-Scaffolding-v0.1.0.md").exists() or \
           (current / ".git").is_dir():
            return current
        current = current.parent
    
    return None

def detect_platform() -> str:
    """Detect OS and architecture for CI artifact path."""
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
    """Binary discovery cascade per docs/wrapper-discovery.md."""
    # 1. Environment override (use without validation per spec)
    safe_run_bin = os.environ.get("SAFE_RUN_BIN")
    if safe_run_bin:
        # Return the path even if it doesn't exist - let exec fail with clear error
        return safe_run_bin
    
    repo_root = find_repo_root()
    
    # 2. Dev mode: ./rust/target/release/safe-run
    if repo_root:
        dev_bin = repo_root / "rust" / "target" / "release" / "safe-run"
        if dev_bin.is_file() and os.access(dev_bin, os.X_OK):
            return str(dev_bin)
    
    # 3. CI artifact: ./dist/<os>/<arch>/safe-run
    if repo_root:
        platform_str = detect_platform()
        if platform_str != "unknown/unknown":
            parts = platform_str.split("/")
            ci_bin = repo_root / "dist" / parts[0] / parts[1] / "safe-run"
            if ci_bin.is_file() and os.access(ci_bin, os.X_OK):
                return str(ci_bin)
    
    # 4. PATH lookup
    which_result = shutil.which("safe-run")
    if which_result:
        return which_result
    
    # 5. Not found
    return None

def main() -> int:
    """Main execution."""
    binary = find_safe_run_binary()
    
    if not binary:
        print("""\
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
""", file=sys.stderr)
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
        print("  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases", file=sys.stderr)
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
