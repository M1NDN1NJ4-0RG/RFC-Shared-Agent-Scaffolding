#!/usr/bin/env bash
#
# safe-archive.sh - Archive safe-run failure logs with optional compression
#
# DESCRIPTION:
#   Moves failure logs from FAIL-LOGS to FAIL-ARCHIVE with no-clobber safety.
#   Supports optional compression via gzip, xz, or zstd. By default archives
#   one log per invocation; use --all to archive all logs at once.
#
#   Part of the safe-run toolchain contract (M0-P1-I2): Handles log lifecycle
#   after safe-run creates forensic artifacts.
#
# USAGE:
#   safe-archive.sh           # Archive one log (default)
#   safe-archive.sh --all     # Archive all logs
#
# INPUTS:
#   Arguments:
#     --all    Archive all logs instead of just one (optional)
#     (no args defaults to archiving one log)
#
#   Environment Variables:
#     SAFE_FAIL_DIR          Source directory (default: .agent/FAIL-LOGS)
#     SAFE_ARCHIVE_DIR       Destination directory (default: .agent/FAIL-ARCHIVE)
#     SAFE_ARCHIVE_COMPRESS  Compression: none|gzip|xz|zstd (default: none)
#
# OUTPUTS:
#   Exit Codes:
#     0  Success (logs archived, or no logs to archive)
#     1  Compression tool not found (when SAFE_ARCHIVE_COMPRESS set)
#     2  Invalid usage (unknown arguments)
#
#   Stdout:
#     (silent on success)
#
#   Stderr:
#     "skip (exists): <filename>" - file already in archive (no-clobber)
#     "gzip not found" - compression tool missing
#
#   Side Effects:
#     - Moves log files from FAIL-LOGS to FAIL-ARCHIVE
#     - Creates FAIL-ARCHIVE directory if it doesn't exist
#     - Compresses archived logs in-place (if SAFE_ARCHIVE_COMPRESS set)
#     - Never overwrites existing archive files (no-clobber guarantee)
#
# LOG FILE PATTERNS:
#   Matches logs created by safe-run (M0-P1-I2 naming):
#     *-FAIL.log     Normal failure (non-zero exit)
#     *-ABORTED.log  Signal termination (SIGTERM, SIGINT)
#     *-ERROR.log    Internal safe-run error
#
# COMPRESSION FORMATS:
#   none  No compression (default)
#   gzip  Creates .log.gz files (requires gzip command)
#   xz    Creates .log.xz files (requires xz command)
#   zstd  Creates .log.zst files (requires zstd command)
#
# NO-CLOBBER BEHAVIOR:
#   If destination file exists (with or without compression extension),
#   skips that file and prints warning to stderr. Original remains in FAIL-LOGS.
#
# PLATFORM COMPATIBILITY:
#   - Linux: Fully tested on Ubuntu 20.04+
#   - macOS: Compatible with Bash 3.2+ (default macOS shell)
#   - Windows: Works via Git Bash, WSL, MSYS2
#   - Uses find -print0 + read -d '' for macOS Bash 3.2 compatibility
#
# CONTRACT REFERENCES:
#   - M0-P1-I2: Log lifecycle and naming format
#   - Test vector: conformance/vectors.json (safe-archive behavior)
#   - Related: safe-run.sh creates logs, safe-check.sh verifies archiving
#
# EXAMPLES:
#   # Archive one log with default settings
#   safe-archive.sh
#
#   # Archive all logs at once
#   safe-archive.sh --all
#
#   # Archive with gzip compression
#   SAFE_ARCHIVE_COMPRESS=gzip safe-archive.sh --all
#
#   # Custom directories
#   SAFE_FAIL_DIR=/tmp/failures SAFE_ARCHIVE_DIR=/backups safe-archive.sh --all
#
#   # Use xz compression for better compression ratio
#   SAFE_ARCHIVE_COMPRESS=xz safe-archive.sh --all
#
# SEE ALSO:
#   - safe-run.sh: Creates failure logs
#   - safe-check.sh: Verifies archive behavior
# safe-archive.sh
# Moves failure logs from FAIL-LOGS -> FAIL-ARCHIVE with no-clobber safety.
# Optional compression via external tools.
#
# Env:
#   SAFE_FAIL_DIR          default: .agent/FAIL-LOGS
#   SAFE_ARCHIVE_DIR       default: .agent/FAIL-ARCHIVE
#   SAFE_ARCHIVE_COMPRESS  none|gzip|xz|zstd (default: none)
#
# IMPLEMENTATION NOTES:
# - Uses 'set -eu' for error handling (no pipefail needed - no pipes in main logic)
# - macOS Bash 3.2 compatible: no mapfile/readarray
# - Uses find -print0 + read -d '' for safe handling of filenames with spaces
# - Compression happens in-place in archive dir (move first, compress second)
#

set -eu

# Environment variable defaults
SAFE_FAIL_DIR="${SAFE_FAIL_DIR:-.agent/FAIL-LOGS}"
SAFE_ARCHIVE_DIR="${SAFE_ARCHIVE_DIR:-.agent/FAIL-ARCHIVE}"
SAFE_ARCHIVE_COMPRESS="${SAFE_ARCHIVE_COMPRESS:-none}"

# usage - Display usage message and exit
# Called on invalid arguments
usage() {
  echo "usage: safe-archive.sh [--all]" >&2
  exit 2
}

# Parse command-line arguments
# ALL=0: Archive one file (default)
# ALL=1: Archive all files (--all flag)
ALL="0"
case "${1-}" in
  "" ) ;; 
  --all) ALL="1" ;;
  *) usage ;;
esac

# Create archive directory if it doesn't exist (mkdir -p is idempotent)
mkdir -p "$SAFE_ARCHIVE_DIR" 2>/dev/null || true

# If source directory doesn't exist, nothing to do (not an error)

# If source directory doesn't exist, nothing to do (not an error)
if [ ! -d "$SAFE_FAIL_DIR" ]; then
  # Nothing to do.
  exit 0
fi

# compress_one - Compress a single file in-place using configured tool
# Args:
#   $1 = path to file in archive dir
# Returns: 0 on success, 1 on error (tool not found or compression failed)
# Side effect: Replaces file with compressed version (.gz, .xz, or .zst)
compress_one() {
  # $1 = path to file in archive dir
  local f="$1"
  case "$SAFE_ARCHIVE_COMPRESS" in
    none) return 0 ;;  # No compression
    gzip)
      # gzip: -n (no timestamp), -f (force overwrite .gz if exists)
      command -v gzip >/dev/null 2>&1 || { echo "gzip not found" >&2; return 1; }
      gzip -n -f "$f"
      ;;
    xz)
      # xz: -T0 (use all CPU cores), -f (force overwrite)
      command -v xz >/dev/null 2>&1 || { echo "xz not found" >&2; return 1; }
      xz -T0 -f "$f"
      ;;
    zstd)
      # zstd: -q (quiet), -T0 (multithreaded), -f (force overwrite)
      command -v zstd >/dev/null 2>&1 || { echo "zstd not found" >&2; return 1; }
      zstd -q -T0 -f "$f"
      ;;
    *)
      echo "Unknown SAFE_ARCHIVE_COMPRESS=$SAFE_ARCHIVE_COMPRESS" >&2
      return 1
      ;;
  esac
}

#
# MAIN ARCHIVAL LOOP
# Uses find + read for macOS Bash 3.2 compatibility (no mapfile/readarray)
# Processes logs matching M0-P1-I2 naming pattern: *-{FAIL|ABORTED|ERROR}.log
#

# macOS Bash 3.2 compatible: no mapfile/readarray.
# Use find -print0 + read -d '' to safely handle spaces.
# M0-P1-I2: Match new log naming format *-{STATUS}.log
find "$SAFE_FAIL_DIR" -type f \( -name '*-FAIL.log' -o -name '*-ABORTED.log' -o -name '*-ERROR.log' \) -print0 2>/dev/null | \
while IFS= read -r -d '' SRC; do
  BN="$(basename "$SRC")"
  DST="$SAFE_ARCHIVE_DIR/$BN"

  # no-clobber: check for existing file with any compression extension
  if [ -e "$DST" ] || [ -e "$DST.gz" ] || [ -e "$DST.xz" ] || [ -e "$DST.zst" ]; then
    echo "skip (exists): $BN" >&2
    continue
  fi

  # Move first (atomic operation), then compress in-place in archive
  # This ensures log is safely moved before compression (no data loss on compress failure)
  mv "$SRC" "$DST"
  compress_one "$DST"

  if [ "$ALL" = "0" ]; then
    # archive just one by default (performance optimization for large log dirs)
    exit 0
  fi
done

exit 0
