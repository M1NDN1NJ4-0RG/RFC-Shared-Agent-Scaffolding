#!/usr/bin/env bash
# safe-archive.sh
# Moves failure logs from FAIL-LOGS -> FAIL-ARCHIVE with no-clobber safety.
# Optional compression via external tools.
#
# Env:
#   SAFE_FAIL_DIR          default: .agent/FAIL-LOGS
#   SAFE_ARCHIVE_DIR       default: .agent/FAIL-ARCHIVE
#   SAFE_ARCHIVE_COMPRESS  none|gzip|xz|zstd (default: none)

set -eu

SAFE_FAIL_DIR="${SAFE_FAIL_DIR:-.agent/FAIL-LOGS}"
SAFE_ARCHIVE_DIR="${SAFE_ARCHIVE_DIR:-.agent/FAIL-ARCHIVE}"
SAFE_ARCHIVE_COMPRESS="${SAFE_ARCHIVE_COMPRESS:-none}"

usage() {
  echo "usage: safe-archive.sh [--all]" >&2
  exit 2
}

ALL="0"
case "${1-}" in
  "" ) ;; 
  --all) ALL="1" ;;
  *) usage ;;
esac

mkdir -p "$SAFE_ARCHIVE_DIR" 2>/dev/null || true

if [ ! -d "$SAFE_FAIL_DIR" ]; then
  # Nothing to do.
  exit 0
fi

compress_one() {
  # $1 = path to file in archive dir
  local f="$1"
  case "$SAFE_ARCHIVE_COMPRESS" in
    none) return 0 ;;
    gzip)
      command -v gzip >/dev/null 2>&1 || { echo "gzip not found" >&2; return 1; }
      gzip -n -f "$f"
      ;;
    xz)
      command -v xz >/dev/null 2>&1 || { echo "xz not found" >&2; return 1; }
      xz -T0 -f "$f"
      ;;
    zstd)
      command -v zstd >/dev/null 2>&1 || { echo "zstd not found" >&2; return 1; }
      zstd -q -T0 -f "$f"
      ;;
    *)
      echo "Unknown SAFE_ARCHIVE_COMPRESS=$SAFE_ARCHIVE_COMPRESS" >&2
      return 1
      ;;
  esac
}

# macOS Bash 3.2 compatible: no mapfile/readarray.
# Use find -print0 + read -d '' to safely handle spaces.
# M0-P1-I2: Match new log naming format *-{STATUS}.log
find "$SAFE_FAIL_DIR" -type f \( -name '*-FAIL.log' -o -name '*-ABORTED.log' -o -name '*-ERROR.log' \) -print0 2>/dev/null | \
while IFS= read -r -d '' SRC; do
  BN="$(basename "$SRC")"
  DST="$SAFE_ARCHIVE_DIR/$BN"

  # no-clobber
  if [ -e "$DST" ] || [ -e "$DST.gz" ] || [ -e "$DST.xz" ] || [ -e "$DST.zst" ]; then
    echo "skip (exists): $BN" >&2
    continue
  fi

  # Move first, then compress in-place in archive.
  mv "$SRC" "$DST"
  compress_one "$DST"

  if [ "$ALL" = "0" ]; then
    # archive just one by default
    exit 0
  fi
done

exit 0
