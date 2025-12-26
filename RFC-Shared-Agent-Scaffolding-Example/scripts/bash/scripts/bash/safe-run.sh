#!/usr/bin/env bash
# safe-run.sh
# Runs a command verbatim. If it fails, capture stdout+stderr with event ledger.
# If it succeeds, create no artifacts.
#
# Env:
#   SAFE_LOG_DIR       default: .agent/FAIL-LOGS
#   SAFE_SNIPPET_LINES default: 0  (if >0, prints tail snippet to stderr on failure)
#   SAFE_RUN_VIEW      if "merged", emit optional merged view

set -u

SAFE_LOG_DIR="${SAFE_LOG_DIR:-.agent/FAIL-LOGS}"
SAFE_SNIPPET_LINES="${SAFE_SNIPPET_LINES:-0}"
SAFE_RUN_VIEW="${SAFE_RUN_VIEW:-}"

if [ "$#" -lt 1 ]; then
  echo "usage: safe-run.sh <command> [args...]" >&2
  exit 2
fi

mkdir -p "$SAFE_LOG_DIR" 2>/dev/null || true

# Build command string for META event (properly escaped)
# Simple escaping: replace double quotes with escaped quotes
CMD_STR=$(printf '%s' "$*" | sed 's/"/\\"/g')

# Temp files for split streams and event ledger
TMP_STDOUT="$(mktemp -t safe-run-stdout.XXXXXX)" || exit 1
TMP_STDERR="$(mktemp -t safe-run-stderr.XXXXXX)" || exit 1
TMP_EVENTS="$(mktemp -t safe-run-events.XXXXXX)" || exit 1

# Build a stable-ish name (timestamp + pid).
TS="$(date -u +%Y%m%dT%H%M%SZ 2>/dev/null || date +%Y%m%dT%H%M%SZ)"
PID="$$"
BASE="$TS-pid$PID"

ABORTED="0"
SEQ=0

cleanup_tmp() {
  [ -f "$TMP_STDOUT" ] && rm -f "$TMP_STDOUT" 2>/dev/null || true
  [ -f "$TMP_STDERR" ] && rm -f "$TMP_STDERR" 2>/dev/null || true
  [ -f "$TMP_EVENTS" ] && rm -f "$TMP_EVENTS" 2>/dev/null || true
  [ -f "${TMP_EVENTS}.seq" ] && rm -f "${TMP_EVENTS}.seq" 2>/dev/null || true
  [ -f "${TMP_EVENTS}.lock" ] && rm -f "${TMP_EVENTS}.lock" 2>/dev/null || true
  [ -d "${TMP_EVENTS}.lock" ] && rmdir "${TMP_EVENTS}.lock" 2>/dev/null || true
  # Clean up FIFOs if they exist (or any file at those paths)
  [ -n "${FIFO_STDOUT:-}" ] && [ -e "$FIFO_STDOUT" ] && rm -f "$FIFO_STDOUT" 2>/dev/null || true
  [ -n "${FIFO_STDERR:-}" ] && [ -e "$FIFO_STDERR" ] && rm -f "$FIFO_STDERR" 2>/dev/null || true
}

# Emit event to ledger file (with locking for concurrent access)
emit_event() {
  local stream="$1"
  local text="$2"
  
  # Use flock for atomic sequence increment and write
  # flock is available on Linux; for macOS we use a simpler approach
  if command -v flock >/dev/null 2>&1; then
    (
      flock -x 200
      local seq
      if [ -f "${TMP_EVENTS}.seq" ]; then
        seq=$(cat "${TMP_EVENTS}.seq")
      else
        seq=0
      fi
      seq=$((seq + 1))
      printf '%d' "$seq" > "${TMP_EVENTS}.seq"
      printf '[SEQ=%d][%s] %s\n' "$seq" "$stream" "$text" >> "$TMP_EVENTS"
    ) 200>"${TMP_EVENTS}.lock"
  else
    # Fallback for systems without flock (macOS, etc.)
    # Use a simple lock file approach (less atomic but works)
    while ! mkdir "${TMP_EVENTS}.lock" 2>/dev/null; do
      sleep 0.01  # 10ms to reduce busy-waiting
    done
    local seq
    if [ -f "${TMP_EVENTS}.seq" ]; then
      seq=$(cat "${TMP_EVENTS}.seq")
    else
      seq=0
    fi
    seq=$((seq + 1))
    printf '%d' "$seq" > "${TMP_EVENTS}.seq"
    printf '[SEQ=%d][%s] %s\n' "$seq" "$stream" "$text" >> "$TMP_EVENTS"
    rmdir "${TMP_EVENTS}.lock" 2>/dev/null || true
  fi
}

save_log() {
  local status="$1"
  local out="$SAFE_LOG_DIR/${BASE}-${status}.log"
  local n=0
  local cand="$out"
  
  # no-clobber safety
  while [ -e "$cand" ]; do
    n=$((n+1))
    cand="$SAFE_LOG_DIR/${BASE}-${status}-$n.log"
  done
  
  # Write log with M0-P1-I1 split sections + new event ledger
  {
    # M0-P1-I1 markers (keep backward compatible)
    echo "=== STDOUT ==="
    [ -f "$TMP_STDOUT" ] && cat "$TMP_STDOUT"
    echo ""
    echo "=== STDERR ==="
    [ -f "$TMP_STDERR" ] && cat "$TMP_STDERR"
    echo ""
    # New event ledger section
    echo "--- BEGIN EVENTS ---"
    [ -f "$TMP_EVENTS" ] && cat "$TMP_EVENTS"
    echo "--- END EVENTS ---"
    
    # Optional merged view
    if [ "$SAFE_RUN_VIEW" = "merged" ]; then
      echo ""
      echo "--- BEGIN MERGED (OBSERVED ORDER) ---"
      if [ -f "$TMP_EVENTS" ]; then
        # Convert [SEQ=N][STREAM] text to [#N][STREAM] text
        sed 's/\[SEQ=\([0-9]*\)\]/[#\1]/g' "$TMP_EVENTS"
      fi
      echo "--- END MERGED ---"
    fi
  } > "$cand" 2>/dev/null || true
  
  echo "$cand"
}

on_int() {
  ABORTED="1"
  save_log "ABORTED" >/dev/null
  cleanup_tmp
  exit 130
}

on_term() {
  ABORTED="1"
  save_log "ABORTED" >/dev/null
  cleanup_tmp
  exit 143
}

trap on_int INT
trap on_term TERM

# Emit start event
emit_event "META" "safe-run start: cmd=\"$CMD_STR\""

# Run command capturing stdout/stderr separately while tracking events
# We use named pipes (FIFOs) to capture output in order
# Create FIFOs in a temp directory to reduce race conditions
FIFO_DIR="$(mktemp -d -t safe-run-fifos.XXXXXX)" || { cleanup_tmp; exit 1; }
FIFO_STDOUT="$FIFO_DIR/stdout"
FIFO_STDERR="$FIFO_DIR/stderr"
mkfifo "$FIFO_STDOUT" "$FIFO_STDERR" || { rm -rf "$FIFO_DIR"; cleanup_tmp; exit 1; }

# Background readers that capture to files, emit events, and stream to console
(
  while IFS= read -r line; do
    printf '%s\n' "$line" >> "$TMP_STDOUT"
    emit_event "STDOUT" "$line"
    printf '%s\n' "$line"
  done < "$FIFO_STDOUT"
) &
READER_OUT_PID=$!

(
  while IFS= read -r line; do
    printf '%s\n' "$line" >> "$TMP_STDERR"
    emit_event "STDERR" "$line"
    printf '%s\n' "$line" >&2
  done < "$FIFO_STDERR"
) &
READER_ERR_PID=$!

# Run the command
"$@" > "$FIFO_STDOUT" 2> "$FIFO_STDERR"
CMD_RC=$?

# Wait for readers to finish
wait "$READER_OUT_PID" 2>/dev/null || true
wait "$READER_ERR_PID" 2>/dev/null || true

# Clean up FIFOs only (not the event ledger files yet)
[ -n "${FIFO_STDOUT:-}" ] && [ -p "$FIFO_STDOUT" ] && rm -f "$FIFO_STDOUT" 2>/dev/null || true
[ -n "${FIFO_STDERR:-}" ] && [ -p "$FIFO_STDERR" ] && rm -f "$FIFO_STDERR" 2>/dev/null || true
[ -n "${FIFO_DIR:-}" ] && [ -d "$FIFO_DIR" ] && rmdir "$FIFO_DIR" 2>/dev/null || true

# Emit exit event
emit_event "META" "safe-run exit: code=$CMD_RC"

if [ "$CMD_RC" -eq 0 ]; then
  cleanup_tmp
  exit 0
fi

# Failure: create log
cand="$(save_log "FAIL")"

# Optional tail snippet to stderr
if [ "$SAFE_SNIPPET_LINES" -gt 0 ] 2>/dev/null; then
  echo "--- safe-run failure tail ($SAFE_SNIPPET_LINES lines) ---" >&2
  tail -n "$SAFE_SNIPPET_LINES" "$cand" >&2 || true
  echo "--- end tail ---" >&2
fi

echo "safe-run: command failed (rc=$CMD_RC). log: $cand" >&2
cleanup_tmp
exit "$CMD_RC"
