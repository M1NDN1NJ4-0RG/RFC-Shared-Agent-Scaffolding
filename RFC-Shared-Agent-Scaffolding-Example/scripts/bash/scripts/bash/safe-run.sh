#!/usr/bin/env bash
# safe-run.sh
# Runs a command verbatim. If it fails, capture combined stdout+stderr to a FAIL-LOG file.
# If it succeeds, create no artifacts.
#
# Env:
#   SAFE_LOG_DIR       default: .agent/FAIL-LOGS
#   SAFE_SNIPPET_LINES default: 0  (if >0, prints tail snippet to stderr on failure)

set -u

SAFE_LOG_DIR="${SAFE_LOG_DIR:-.agent/FAIL-LOGS}"
SAFE_SNIPPET_LINES="${SAFE_SNIPPET_LINES:-0}"

if [ "$#" -lt 1 ]; then
  echo "usage: safe-run.sh <command> [args...]" >&2
  exit 2
fi

mkdir -p "$SAFE_LOG_DIR" 2>/dev/null || true

# M0-P1-I1: Capture stdout and stderr separately
# mktemp exists on macOS + Linux.
TMP_STDOUT="$(mktemp -t safe-run-stdout.XXXXXX)" || exit 1
TMP_STDERR="$(mktemp -t safe-run-stderr.XXXXXX)" || exit 1

# Build a stable-ish name (timestamp + pid).
TS="$(date -u +%Y%m%dT%H%M%SZ 2>/dev/null || date +%Y%m%dT%H%M%SZ)"
PID="$$"
BASE="$TS-pid$PID"

ABORTED="0"

cleanup_tmp() {
  [ -f "$TMP_STDOUT" ] && rm -f "$TMP_STDOUT" 2>/dev/null || true
  [ -f "$TMP_STDERR" ] && rm -f "$TMP_STDERR" 2>/dev/null || true
}

save_abort_log() {
  # If we have any buffered output, preserve it with M0-P1-I1 markers.
  local out="$SAFE_LOG_DIR/${BASE}-ABORTED.log"
  if [ -f "$TMP_STDOUT" ] || [ -f "$TMP_STDERR" ]; then
    # no-clobber safety: if name exists, append counter.
    local n=0
    local cand="$out"
    while [ -e "$cand" ]; do
      n=$((n+1))
      cand="$SAFE_LOG_DIR/${BASE}-ABORTED-$n.log"
    done
    # M0-P1-I1: Section markers
    {
      echo "=== STDOUT ==="
      [ -f "$TMP_STDOUT" ] && cat "$TMP_STDOUT"
      echo ""
      echo "=== STDERR ==="
      [ -f "$TMP_STDERR" ] && cat "$TMP_STDERR"
    } > "$cand" 2>/dev/null || true
  fi
}

on_int() {
  ABORTED="1"
  # Don't echo extra junk unless we must.
  save_abort_log
  cleanup_tmp
  exit 130
}

on_term() {
  ABORTED="1"
  save_abort_log
  cleanup_tmp
  exit 143
}

trap on_int INT
trap on_term TERM

# M0-P1-I1: Capture stdout and stderr separately, while still streaming to console
# Using process substitution and tee to split streams
"$@" > >(tee "$TMP_STDOUT") 2> >(tee "$TMP_STDERR" >&2)
CMD_RC=$?

if [ "$CMD_RC" -eq 0 ]; then
  cleanup_tmp
  exit 0
fi

# Failure: create log with M0-P1-I1 section markers
OUT="$SAFE_LOG_DIR/${BASE}-FAIL.log"
# no-clobber
n=0
cand="$OUT"
while [ -e "$cand" ]; do
  n=$((n+1))
  cand="$SAFE_LOG_DIR/${BASE}-FAIL-$n.log"
done

# M0-P1-I1: Write log with section markers
{
  echo "=== STDOUT ==="
  [ -f "$TMP_STDOUT" ] && cat "$TMP_STDOUT"
  echo ""
  echo "=== STDERR ==="
  [ -f "$TMP_STDERR" ] && cat "$TMP_STDERR"
} > "$cand" 2>/dev/null || true

cleanup_tmp

# Optional tail snippet to stderr (useful for CI without opening the file).
if [ "$SAFE_SNIPPET_LINES" -gt 0 ] 2>/dev/null; then
  echo "--- safe-run failure tail ($SAFE_SNIPPET_LINES lines) ---" >&2
  tail -n "$SAFE_SNIPPET_LINES" "$cand" >&2 || true
  echo "--- end tail ---" >&2
fi

echo "safe-run: command failed (rc=$CMD_RC). log: $cand" >&2
exit "$CMD_RC"
