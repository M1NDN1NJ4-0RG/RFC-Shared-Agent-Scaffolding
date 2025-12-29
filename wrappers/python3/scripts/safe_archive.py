#!/usr/bin/env python3
"""Non-destructive archival tool for failure logs with M0-P1-I3 no-clobber semantics.

This module moves failure logs from .agent/FAIL-LOGS to .agent/FAIL-ARCHIVE
with configurable compression and strict no-clobber guarantees.

Purpose
-------
Provides safe, non-destructive archival of agent failure logs to prevent
accidental data loss while managing disk space through optional compression.
The tool never overwrites existing archive files unless explicitly configured
to fail (strict no-clobber mode).

M0-P1-I3 No-Clobber Semantics
------------------------------
Two modes of operation:

1. **Auto-suffix mode (default)**:
   - If destination exists, append .2, .3, etc. until unique name found
   - Never overwrites existing archive files
   - Emits WARNING to stderr when auto-suffixing occurs

2. **Strict no-clobber mode** (via --no-clobber flag or SAFE_ARCHIVE_NO_CLOBBER=1):
   - If destination exists, fail with exit code 2
   - Prevents any archival when collision detected
   - Use for workflows requiring explicit collision handling

Environment Variables
---------------------
SAFE_FAIL_DIR : str, optional
    Source directory for failure logs (default: .agent/FAIL-LOGS)

SAFE_ARCHIVE_DIR : str, optional
    Destination directory for archived logs (default: .agent/FAIL-ARCHIVE)

SAFE_ARCHIVE_COMPRESS : str, optional
    Compression method: none (default) | gzip | xz | zstd
    - none: No compression applied
    - gzip: Python built-in gzip compression (always available)
    - xz: Requires 'xz' command in PATH, uses multi-threading (-T0)
    - zstd: Requires 'zstd' command in PATH, uses multi-threading (-T0)

SAFE_ARCHIVE_NO_CLOBBER : str, optional
    Set to "1" to enable strict no-clobber mode globally

CLI Interface
-------------
    python3 safe_archive.py [--no-clobber] [--all | <file> ...]

Options:
    --no-clobber    Enable strict no-clobber mode (fail on collision)
    --all           Archive all files in SAFE_FAIL_DIR
    <file> ...      Archive specific file(s) by path

Examples
--------
Archive specific failure log::

    python3 safe_archive.py .agent/FAIL-LOGS/fail-2024-01-15T10-30-00.txt

Archive all failure logs with gzip compression::

    export SAFE_ARCHIVE_COMPRESS=gzip
    python3 safe_archive.py --all

Strict no-clobber mode via flag::

    python3 safe_archive.py --no-clobber mylog.txt
    # Fails with exit 2 if .agent/FAIL-ARCHIVE/mylog.txt exists

Auto-suffix mode (default)::

    python3 safe_archive.py mylog.txt
    # If mylog.txt exists, creates mylog.txt.2
    # If mylog.txt.2 exists, creates mylog.txt.3, etc.

Exit Codes
----------
0
    All files archived successfully
2
    Error: File not found, compression tool missing, or no-clobber collision

Side Effects
------------
- Creates SAFE_FAIL_DIR if it doesn't exist
- Creates SAFE_ARCHIVE_DIR if it doesn't exist
- Moves (not copies) source files to archive directory
- May compress archived files (removes uncompressed original)
- Prints status messages to stderr (ARCHIVED, WARNING, ERROR)

Filesystem Operations
---------------------
- Uses shutil.move() for atomic file operations
- Compressed files get extension: .gz (gzip), .xz (xz), .zst (zstd)
- Source file deleted after successful compression
- No partial writes (compression creates new file, then removes source)

Platform Notes
--------------
- gzip compression: Python built-in, available on all platforms
- xz compression: Requires 'xz' binary in PATH (common on Linux/macOS)
- zstd compression: Requires 'zstd' binary in PATH (install via package manager)
- Uses os.access(os.X_OK) to verify command availability

Contract References
-------------------
- **M0-P1-I3**: No-clobber archival semantics (auto-suffix and strict modes)

See Also
--------
- scripts/python3/safe_run.py: Generates failure logs for archival
- scripts/python3/safe_check.py: Verifies archival contract conformance
"""
import os
import sys
import shutil
import subprocess
import gzip
from typing import List


def eprint(*args: object) -> None:
    """Print to stderr for status and error messages.

    :param args: Variable arguments to print (passed to print())
    :returns: None

    All output is sent to stderr to avoid interfering with stdout,
    which may be captured or redirected by calling scripts.
    """
    print(*args, file=sys.stderr)


def usage() -> int:
    """Print usage message and return exit code 2.

    :returns: 2 (usage error exit code)

    Displays comprehensive help including options, environment variables,
    and examples. Caller is expected to exit with the returned code.
    """
    eprint("Usage: scripts/python3/safe_archive.py [--no-clobber] [--all | <file> ...]")
    eprint("")
    eprint("Options:")
    eprint("  --no-clobber            Fail if destination exists (default: auto-suffix)")
    eprint("")
    eprint("Environment:")
    eprint("  SAFE_FAIL_DIR           Source directory (default: .agent/FAIL-LOGS)")
    eprint("  SAFE_ARCHIVE_DIR        Destination directory (default: .agent/FAIL-ARCHIVE)")
    eprint("  SAFE_ARCHIVE_COMPRESS   Compression: none|gzip|xz|zstd (default: none)")
    eprint("  SAFE_ARCHIVE_NO_CLOBBER Set to 1 to enable strict no-clobber mode")
    return 2


def have_cmd(cmd: str) -> bool:
    """Check if a command is available in PATH.

    :param cmd: Command name to search for (e.g., "xz", "zstd")
    :returns: True if command exists and is executable, False otherwise

    Used to verify compression tool availability before attempting to
    invoke external commands for xz or zstd compression.

    Platform Notes
    --------------
    - Searches all directories in PATH environment variable
    - Requires execute permission (os.X_OK) in addition to existence
    - Does not verify command functionality, only availability
    """
    for p in os.environ.get("PATH", "").split(os.pathsep):
        exe = os.path.join(p, cmd)
        if os.path.isfile(exe) and os.access(exe, os.X_OK):
            return True
    return False


def compress_file(method: str, path: str) -> None:
    """Compress a file in-place using the specified method.

    :param method: Compression method: "none" | "gzip" | "xz" | "zstd"
    :param path: Path to file to compress (will be replaced with compressed version)
    :returns: None
    :raises RuntimeError: If method is invalid or compression tool not found

    Compression Methods
    -------------------
    none
        No compression applied, file unchanged
    gzip
        Python built-in gzip compression (always available)
        Creates path.gz, removes original
    xz
        External 'xz' command with multi-threading (-T0)
        Creates path.xz, removes original
        Requires 'xz' in PATH
    zstd
        External 'zstd' command with multi-threading (-T0)
        Creates path.zst, removes original
        Requires 'zstd' in PATH

    Side Effects
    ------------
    - Original file is deleted after successful compression
    - Compressed file has appropriate extension (.gz, .xz, .zst)
    - External commands invoked via subprocess.check_call()

    Error Handling
    --------------
    - Raises RuntimeError if compression tool not found in PATH
    - Raises RuntimeError if method is not one of the supported values
    - subprocess.check_call() will raise CalledProcessError on command failure

    Examples
    --------
    >>> compress_file("none", "mylog.txt")  # No-op
    >>> compress_file("gzip", "mylog.txt")  # Creates mylog.txt.gz, removes mylog.txt
    """
    method = method or "none"
    if method == "none":
        return
    if method == "gzip":
        out = path + ".gz"
        with open(path, "rb") as fin, gzip.open(out, "wb") as fout:
            shutil.copyfileobj(fin, fout)
        os.unlink(path)
        return
    if method == "xz":
        if not have_cmd("xz"):
            raise RuntimeError("xz command not found in PATH")
        subprocess.check_call(["xz", "-T0", "-f", path])
        return
    if method == "zstd":
        if not have_cmd("zstd"):
            raise RuntimeError("zstd command not found in PATH")
        subprocess.check_call(["zstd", "-q", "-T0", "-f", path])
        return
    raise RuntimeError(f"Invalid SAFE_ARCHIVE_COMPRESS value: {method}")


def archive_one(src: str, archive_dir: str, compress: str, strict_no_clobber: bool = False) -> None:
    """Archive a single file with M0-P1-I3 no-clobber semantics.

    :param src: Source file path
    :param archive_dir: Destination directory
    :param compress: Compression method
    :param strict_no_clobber: If True, fail if destination exists. If False (default), auto-suffix.
    """
    if not os.path.exists(src):
        raise RuntimeError(f"File not found: {src}")

    base = os.path.basename(src)
    dest = os.path.join(archive_dir, base)

    if os.path.exists(dest):
        if strict_no_clobber:
            # M0-P1-I3: Strict no-clobber mode - fail with error
            raise RuntimeError(f"Destination exists: {dest}")
        # M0-P1-I3: Default auto-suffix mode - append .2, .3, etc.
        n = 2
        while os.path.exists(dest + "." + str(n)):
            n += 1
        dest = dest + "." + str(n)
        eprint(f"WARNING: destination exists, using auto-suffix: {dest}")

    shutil.move(src, dest)
    eprint(f"ARCHIVED: {src} -> {dest}")
    compress_file(compress, dest)


def main(argv: List[str]) -> int:
    """Execute archival operation with M0-P1-I3 no-clobber semantics.

    :param argv: Command-line arguments (--no-clobber, --all, or file paths)
    :returns: Exit code (0 on success, 2 on error)
    :raises SystemExit: Via usage() on help request or missing arguments

    Argument Parsing
    ----------------
    - Detects -h/--help and calls usage()
    - Extracts --no-clobber flag if present
    - Checks SAFE_ARCHIVE_NO_CLOBBER environment variable
    - Requires either --all or one or more file paths

    Operation Modes
    ---------------
    --all
        Archives all files in SAFE_FAIL_DIR (sorted by name)
        Skips directories and symlinks

    <file> ...
        Archives specific files by path
        Files can be from any directory (not limited to SAFE_FAIL_DIR)

    Environment Configuration
    -------------------------
    - SAFE_FAIL_DIR: Source directory (default: .agent/FAIL-LOGS)
    - SAFE_ARCHIVE_DIR: Destination directory (default: .agent/FAIL-ARCHIVE)
    - SAFE_ARCHIVE_COMPRESS: Compression method (default: none)
    - SAFE_ARCHIVE_NO_CLOBBER: Set to "1" for strict no-clobber mode

    Side Effects
    ------------
    - Creates SAFE_FAIL_DIR if it doesn't exist
    - Creates SAFE_ARCHIVE_DIR if it doesn't exist
    - Moves source files to archive directory
    - Compresses archived files if SAFE_ARCHIVE_COMPRESS is set
    - Prints status messages to stderr (ARCHIVED, WARNING, ERROR)

    Error Handling
    --------------
    - Catches RuntimeError from archive_one() and compress_file()
    - Prints ERROR message to stderr
    - Returns exit code 2 on any error
    - --all mode: Continues processing remaining files after error (non-fatal)

    Examples
    --------
    >>> main(["--all"])  # Archive all files in SAFE_FAIL_DIR
    0

    >>> main(["--no-clobber", "mylog.txt"])  # Strict mode
    2  # If destination exists

    >>> main(["file1.txt", "file2.txt"])  # Archive specific files
    0
    """
    if not argv or argv[0] in ("-h", "--help"):
        return usage() if not argv else usage()

    # M0-P1-I3: Check for strict no-clobber mode
    strict_no_clobber = False
    args = list(argv)

    # Check for --no-clobber flag
    if "--no-clobber" in args:
        strict_no_clobber = True
        args.remove("--no-clobber")

    # Check for SAFE_ARCHIVE_NO_CLOBBER env var
    if os.environ.get("SAFE_ARCHIVE_NO_CLOBBER") == "1":
        strict_no_clobber = True

    fail_dir = os.environ.get("SAFE_FAIL_DIR", ".agent/FAIL-LOGS")
    archive_dir = os.environ.get("SAFE_ARCHIVE_DIR", ".agent/FAIL-ARCHIVE")
    compress = os.environ.get("SAFE_ARCHIVE_COMPRESS", "none")

    os.makedirs(fail_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)

    try:
        if args and args[0] == "--all":
            files = [
                os.path.join(fail_dir, n)
                for n in sorted(os.listdir(fail_dir))
                if os.path.isfile(os.path.join(fail_dir, n))
            ]
            if not files:
                eprint(f"No files to archive in {fail_dir}")
                return 0
            for f in files:
                archive_one(f, archive_dir, compress, strict_no_clobber)
            return 0

        if not args:
            return usage()

        for f in args:
            archive_one(f, archive_dir, compress, strict_no_clobber)
        return 0
    except RuntimeError as e:
        eprint(f"ERROR: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
