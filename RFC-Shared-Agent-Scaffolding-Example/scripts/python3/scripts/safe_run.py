#!/usr/bin/env python3
# safe_run.py (Python 3)
#
# Safe Execution Contract (M0-P1-I1, M0-P1-I2 + Event Ledger):
# - Executes the command verbatim.
# - On success: creates NO artifacts.
# - On failure: writes split stdout/stderr with section markers + event ledger to SAFE_LOG_DIR
# - Log format: {ISO8601_TIMESTAMP}-pid{PID}-{STATUS}.log
# - On abort (SIGINT/SIGTERM): still writes partial output with "ABORTED" status

import os
import re
import sys
import time
import shlex
import signal
import tempfile
import subprocess
import threading
from collections import deque
from typing import Deque, List, Optional, Tuple, BinaryIO


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def usage() -> int:
    eprint("Usage: scripts/python3/safe_run.py [--] <command> [args...]")
    eprint("")
    eprint("Environment:")
    eprint("  SAFE_LOG_DIR        Failure log directory (default: .agent/FAIL-LOGS)")
    eprint("  SAFE_SNIPPET_LINES  On failure/abort, print last N lines of output to stderr (default: 0)")
    eprint("  SAFE_RUN_VIEW       If 'merged', emit optional merged view")
    return 2


def iso8601_timestamp() -> str:
    """Return current time in ISO8601 format (UTC): YYYYMMDDTHHMMSSZ"""
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


class _AbortState:
    """Small shared state mutated by signal handlers."""

    def __init__(self) -> None:
        self.aborted: bool = False
        self.signal_name: Optional[str] = None
        self.exit_code: Optional[int] = None


class EventLedger:
    """Thread-safe event ledger for tracking observed-order events."""
    
    def __init__(self) -> None:
        self.events: List[Tuple[int, str, str]] = []  # (seq, stream, text)
        self.seq: int = 0
        self.lock = threading.Lock()
    
    def emit(self, stream: str, text: str) -> None:
        """Emit an event with the next sequence number."""
        with self.lock:
            self.seq += 1
            self.events.append((self.seq, stream, text))
    
    def write_to_file(self, f: BinaryIO) -> None:
        """Write all events to a file object."""
        with self.lock:
            for seq, stream, text in self.events:
                f.write(f"[SEQ={seq}][{stream}] {text}\n".encode())


def _install_signal_handlers(state: _AbortState) -> Tuple[object, object]:
    """Install SIGINT/SIGTERM handlers."""
    old_int = signal.getsignal(signal.SIGINT)
    old_term = signal.getsignal(signal.SIGTERM)

    def on_sigint(signum: int, frame: object) -> None:  # noqa: ARG001
        state.aborted = True
        state.signal_name = "SIGINT"
        state.exit_code = 130
        raise KeyboardInterrupt

    def on_sigterm(signum: int, frame: object) -> None:  # noqa: ARG001
        state.aborted = True
        state.signal_name = "SIGTERM"
        state.exit_code = 143
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, on_sigint)
    signal.signal(signal.SIGTERM, on_sigterm)
    return old_int, old_term


def _restore_signal_handlers(old_int: object, old_term: object) -> None:
    signal.signal(signal.SIGINT, old_int)   # type: ignore[arg-type]
    signal.signal(signal.SIGTERM, old_term) # type: ignore[arg-type]


def main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        return usage()
    if argv[0] == "--":
        argv = argv[1:]
    if not argv:
        return usage()

    log_dir = os.environ.get("SAFE_LOG_DIR", ".agent/FAIL-LOGS")
    snippet_lines_raw = os.environ.get("SAFE_SNIPPET_LINES", "0")
    view_mode = os.environ.get("SAFE_RUN_VIEW", "")
    
    if not re.fullmatch(r"\d+", snippet_lines_raw):
        eprint("ERROR: SAFE_SNIPPET_LINES must be a non-negative integer")
        return 1
    snippet_lines = int(snippet_lines_raw)

    ts = iso8601_timestamp()
    pid = os.getpid()
    # Properly escape command for META event (use shell quoting)
    cmd_str = " ".join(shlex.quote(arg) for arg in argv)

    # Temporary files for stdout, stderr, and event ledger
    tmp_stdout_path: Optional[str] = None
    tmp_stderr_path: Optional[str] = None
    tmp_stdout_fh: Optional[object] = None
    tmp_stderr_fh: Optional[object] = None

    # Event ledger
    ledger = EventLedger()
    
    # Tail snippets
    tail_stdout: Deque[bytes] = deque(maxlen=snippet_lines if snippet_lines > 0 else 1)
    tail_stderr: Deque[bytes] = deque(maxlen=snippet_lines if snippet_lines > 0 else 1)

    state = _AbortState()
    old_int, old_term = _install_signal_handlers(state)

    proc: Optional[subprocess.Popen] = None
    rc: int = 1

    try:
        tmp_stdout_fh_obj = tempfile.NamedTemporaryFile(prefix="safe-run-stdout-", suffix=".tmp", delete=False)
        tmp_stdout_fh = tmp_stdout_fh_obj
        tmp_stdout_path = tmp_stdout_fh_obj.name

        tmp_stderr_fh_obj = tempfile.NamedTemporaryFile(prefix="safe-run-stderr-", suffix=".tmp", delete=False)
        tmp_stderr_fh = tmp_stderr_fh_obj
        tmp_stderr_path = tmp_stderr_fh_obj.name

        # Emit start event
        ledger.emit("META", f'safe-run start: cmd="{cmd_str}"')

        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert proc.stdout is not None
        assert proc.stderr is not None

        stdout_done = threading.Event()
        stderr_done = threading.Event()
        
        def _read_stdout() -> None:
            try:
                for raw in iter(proc.stdout.readline, b""):
                    if raw == b"":
                        break
                    # Remove trailing newline for ledger (add back for file/console)
                    line_text = raw.decode("utf-8", "replace").rstrip("\n\r")
                    
                    sys.stdout.buffer.write(raw)
                    sys.stdout.flush()
                    tmp_stdout_fh_obj.write(raw)
                    tmp_stdout_fh_obj.flush()
                    ledger.emit("STDOUT", line_text)
                    
                    if snippet_lines > 0:
                        tail_stdout.append(raw)
            except Exception:
                pass
            finally:
                stdout_done.set()
        
        def _read_stderr() -> None:
            try:
                for raw in iter(proc.stderr.readline, b""):
                    if raw == b"":
                        break
                    # Remove trailing newline for ledger (add back for file/console)
                    line_text = raw.decode("utf-8", "replace").rstrip("\n\r")
                    
                    sys.stderr.buffer.write(raw)
                    sys.stderr.flush()
                    tmp_stderr_fh_obj.write(raw)
                    tmp_stderr_fh_obj.flush()
                    ledger.emit("STDERR", line_text)
                    
                    if snippet_lines > 0:
                        tail_stderr.append(raw)
            except Exception:
                pass
            finally:
                stderr_done.set()
        
        stdout_thread = threading.Thread(target=_read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
        
        stdout_thread.start()
        stderr_thread.start()

        try:
            rc = proc.wait()
            stdout_done.wait(timeout=5)
            stderr_done.wait(timeout=5)
        except KeyboardInterrupt:
            state.aborted = True
            if state.signal_name is None:
                state.signal_name = "SIGINT"
            if state.exit_code is None:
                state.exit_code = 130

            try:
                proc.terminate()
            except Exception:
                pass

            try:
                rc = proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
                rc = state.exit_code or 130
        finally:
            try:
                proc.stdout.close()
            except Exception:
                pass
            try:
                proc.stderr.close()
            except Exception:
                pass

        # Emit exit event
        ledger.emit("META", f"safe-run exit: code={rc}")

    finally:
        _restore_signal_handlers(old_int, old_term)

    # Success path: remove temp files and return 0
    if not state.aborted and rc == 0:
        try:
            if tmp_stdout_fh is not None:
                tmp_stdout_fh.close()
            if tmp_stderr_fh is not None:
                tmp_stderr_fh.close()
            if tmp_stdout_path and os.path.exists(tmp_stdout_path):
                os.remove(tmp_stdout_path)
            if tmp_stderr_path and os.path.exists(tmp_stderr_path):
                os.remove(tmp_stderr_path)
        except Exception:
            pass
        return 0

    # Failure/abort: create log artifact
    os.makedirs(log_dir, exist_ok=True)

    status = "ABORTED" if state.aborted else "FAIL"
    out_path = os.path.join(log_dir, f"{ts}-pid{pid}-{status}.log")

    try:
        if tmp_stdout_fh is not None:
            tmp_stdout_fh.close()
        if tmp_stderr_fh is not None:
            tmp_stderr_fh.close()
    except Exception:
        pass

    # Write log with M0 split sections + event ledger
    try:
        with open(out_path, "wb") as dst:
            # M0-P1-I1: Split stdout/stderr
            dst.write(b"=== STDOUT ===\n")
            if tmp_stdout_path and os.path.exists(tmp_stdout_path):
                with open(tmp_stdout_path, "rb") as src:
                    while True:
                        chunk = src.read(1024 * 1024)
                        if not chunk:
                            break
                        dst.write(chunk)
            
            dst.write(b"\n=== STDERR ===\n")
            if tmp_stderr_path and os.path.exists(tmp_stderr_path):
                with open(tmp_stderr_path, "rb") as src:
                    while True:
                        chunk = src.read(1024 * 1024)
                        if not chunk:
                            break
                        dst.write(chunk)
            
            # Event ledger
            dst.write(b"\n--- BEGIN EVENTS ---\n")
            ledger.write_to_file(dst)
            dst.write(b"--- END EVENTS ---\n")
            
            # Optional merged view
            if view_mode == "merged":
                dst.write(b"\n--- BEGIN MERGED (OBSERVED ORDER) ---\n")
                with ledger.lock:
                    for seq, stream, text in ledger.events:
                        dst.write(f"[#{seq}][{stream}] {text}\n".encode())
                dst.write(b"--- END MERGED ---\n")
        
        # Clean up temp files
        if tmp_stdout_path and os.path.exists(tmp_stdout_path):
            try:
                os.remove(tmp_stdout_path)
            except Exception:
                pass
        if tmp_stderr_path and os.path.exists(tmp_stderr_path):
            try:
                os.remove(tmp_stderr_path)
            except Exception:
                pass
    except Exception as e:
        eprint(f"ERROR: Failed to write log file: {e}")
        return 1

    final_rc = state.exit_code if state.aborted and state.exit_code is not None else rc

    eprint("")
    if state.aborted:
        eprint(f"SAFE-RUN: aborted ({state.signal_name or 'signal'})")
    else:
        eprint(f"SAFE-RUN: command failed (exit={rc})")
    eprint(f"SAFE-RUN: log saved to: {out_path}")

    if snippet_lines > 0:
        eprint("")
        eprint(f"SAFE-RUN: STDOUT tail (last {snippet_lines} lines):")
        for b in list(tail_stdout)[-snippet_lines:]:
            eprint(b.decode("utf-8", "replace").rstrip("\n"))
        eprint("")
        eprint(f"SAFE-RUN: STDERR tail (last {snippet_lines} lines):")
        for b in list(tail_stderr)[-snippet_lines:]:
            eprint(b.decode("utf-8", "replace").rstrip("\n"))

    return int(final_rc)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
