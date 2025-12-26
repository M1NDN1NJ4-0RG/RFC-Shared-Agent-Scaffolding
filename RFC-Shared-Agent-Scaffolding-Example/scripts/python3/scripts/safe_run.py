#!/usr/bin/env python3
# safe_run.py (Python 3)
#
# Safe Execution Contract:
# - Executes the command verbatim.
# - On success: creates NO artifacts.
# - On failure: writes combined stdout/stderr to SAFE_LOG_DIR (default: .agent/FAIL-LOGS)
#   and preserves the original exit code.
# - On abort (SIGINT Ctrl+C, SIGTERM): still writes partial output to SAFE_LOG_DIR
#   using an "ABORTED" suffix for forensics.

import os
import re
import sys
import time
import signal
import tempfile
import subprocess
from collections import deque
from typing import Deque, List, Optional, Tuple


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def usage() -> int:
    eprint("Usage: scripts/python3/safe_run.py [--] <command> [args...]")
    eprint("")
    eprint("Environment:")
    eprint("  SAFE_LOG_DIR        Failure log directory (default: .agent/FAIL-LOGS)")
    eprint("  SAFE_SNIPPET_LINES  On failure/abort, print last N lines of output to stderr (default: 0)")
    return 2


def slugify(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9._-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    s = re.sub(r"-{2,}", "-", s)
    return s or "command"


class _AbortState:
    """Small shared state mutated by signal handlers."""

    def __init__(self) -> None:
        self.aborted: bool = False
        self.signal_name: Optional[str] = None
        self.exit_code: Optional[int] = None


def _install_signal_handlers(state: _AbortState) -> Tuple[object, object]:
    """
    Install SIGINT/SIGTERM handlers that:
      - mark the run as aborted (so we can persist partial logs)
      - unwind any blocking reads via KeyboardInterrupt
    """
    old_int = signal.getsignal(signal.SIGINT)
    old_term = signal.getsignal(signal.SIGTERM)

    def on_sigint(signum: int, frame: object) -> None:  # noqa: ARG001
        state.aborted = True
        state.signal_name = "SIGINT"
        # 128 + SIGINT(2) = 130 (common shell convention)
        state.exit_code = 130
        raise KeyboardInterrupt

    def on_sigterm(signum: int, frame: object) -> None:  # noqa: ARG001
        state.aborted = True
        state.signal_name = "SIGTERM"
        # 128 + SIGTERM(15) = 143
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
    if not re.fullmatch(r"\d+", snippet_lines_raw):
        eprint("ERROR: SAFE_SNIPPET_LINES must be a non-negative integer")
        return 1
    snippet_lines = int(snippet_lines_raw)

    cmd_str = " ".join(argv)
    slug = slugify(cmd_str)
    ts = time.strftime("%Y%m%d-%H%M%S", time.localtime())

    # Spool output to a temp file to avoid unbounded in-memory growth.
    # This is NOT a contract artifact because it is deleted on success.
    tmp_path: Optional[str] = None
    tmp_fh: Optional[object] = None

    # Tail snippet (bytes) for printing on failure/abort
    tail: Deque[bytes] = deque(maxlen=snippet_lines if snippet_lines > 0 else 1)

    state = _AbortState()
    old_int, old_term = _install_signal_handlers(state)

    proc: Optional[subprocess.Popen] = None
    rc: int = 1

    try:
        tmp_fh_obj = tempfile.NamedTemporaryFile(prefix="safe-run-", suffix=".tmp", delete=False)
        tmp_fh = tmp_fh_obj
        tmp_path = tmp_fh_obj.name

        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert proc.stdout is not None

        def _write_chunk(b: bytes) -> None:
            sys.stdout.buffer.write(b)
            sys.stdout.flush()
            tmp_fh_obj.write(b)
            tmp_fh_obj.flush()
            if snippet_lines > 0:
                tail.append(b)

        try:
            for raw in iter(proc.stdout.readline, b""):
                if raw == b"":
                    break
                _write_chunk(raw)
        except KeyboardInterrupt:
            # Marked aborted by signal handlers above.
            state.aborted = True
            if state.signal_name is None:
                state.signal_name = "SIGINT"
            if state.exit_code is None:
                state.exit_code = 130

            # Try graceful termination of the child, then hard kill.
            try:
                proc.terminate()
            except Exception:
                pass

            try:
                # Drain any remaining output quickly for forensics.
                remaining = proc.communicate(timeout=2)[0] or b""
                if remaining:
                    _write_chunk(remaining)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        finally:
            try:
                proc.stdout.close()
            except Exception:
                pass

        rc = proc.wait()

    finally:
        _restore_signal_handlers(old_int, old_term)

    # Success path: remove temp file and return 0 (no artifacts).
    if not state.aborted and rc == 0:
        try:
            if tmp_fh is not None:
                tmp_fh.close()
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return 0

    # Failure/abort: promote temp file to final log artifact in SAFE_LOG_DIR.
    os.makedirs(log_dir, exist_ok=True)

    suffix = "ABORTED" if state.aborted else "fail"
    out_path = os.path.join(log_dir, f"{ts}-{slug}-{suffix}.txt")
    if os.path.exists(out_path):
        out_path = os.path.join(log_dir, f"{ts}-{slug}-{suffix}-{os.getpid()}.txt")

    try:
        if tmp_fh is not None:
            tmp_fh.close()
    except Exception:
        pass

    if tmp_path and os.path.exists(tmp_path):
        try:
            os.replace(tmp_path, out_path)
        except OSError:
            with open(tmp_path, "rb") as src, open(out_path, "wb") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    else:
        with open(out_path, "wb") as fh:
            fh.write(b"")

    final_rc = state.exit_code if state.aborted and state.exit_code is not None else rc

    eprint("")
    if state.aborted:
        eprint(f"SAFE-RUN: aborted ({state.signal_name or 'signal'})")
    else:
        eprint(f"SAFE-RUN: command failed (exit={rc})")
    eprint(f"SAFE-RUN: log saved to: {out_path}")

    if snippet_lines > 0:
        eprint("")
        eprint(f"SAFE-RUN: last {snippet_lines} lines of output:")
        for b in list(tail)[-snippet_lines:]:
            eprint(b.decode("utf-8", "replace").rstrip("\n"))

    return int(final_rc)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
