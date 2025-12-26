#!/usr/bin/env python2
# -*- coding: utf-8 -*-
\
# safe_run.py (Python 2)
# Run a command verbatim. On failure, capture combined stdout/stderr to .agent/FAIL-LOGS and preserve exit code.
from __future__ import print_function
import os
import re
import sys
import time
import signal
import tempfile
try:
    from collections import deque
except Exception:
    deque = None
import subprocess

# Global-ish state so our signal handlers can stop the child process and still
# ensure partial output is written to FAIL-LOGS.
_STATE = {
    "proc": None,
    "aborted": False,
}


def _handle_signal(signum, frame):
    """Mark the run as aborted and attempt to stop the child process."""
    _STATE["aborted"] = True
    p = _STATE.get("proc")
    if p is None:
        return
    try:
        # Politely ask first; fall back to a hard kill if needed.
        p.send_signal(signum)
    except Exception:
        try:
            p.terminate()
        except Exception:
            pass

def eprint(*args):
    print(*args, file=sys.stderr)

def usage():
    eprint("Usage: scripts/python2/safe_run.py [--] <command> [args...]")
    eprint("")
    eprint("Environment:")
    eprint("  SAFE_LOG_DIR        Failure log directory (default: .agent/FAIL-LOGS)")
    eprint("  SAFE_SNIPPET_LINES  On failure, print last N lines of output to stderr (default: 0)")
    return 2

def slugify(s):
    s = (s or "").lower()
    s = re.sub(r'[^a-z0-9._-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    s = re.sub(r'-{2,}', '-', s)
    return s or "command"

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        return usage()
    if argv[0] == "--":
        argv = argv[1:]
    if not argv:
        return usage()

    log_dir = os.environ.get("SAFE_LOG_DIR", ".agent/FAIL-LOGS")
    snippet_lines = os.environ.get("SAFE_SNIPPET_LINES", "0")
    if not re.match(r'^\d+$', snippet_lines):
        eprint("ERROR: SAFE_SNIPPET_LINES must be a non-negative integer")
        return 1
    snippet_lines = int(snippet_lines)

    # Install signal handlers so Ctrl+C (SIGINT) and SIGTERM still preserve
    # partial output in FAIL-LOGS with an ABORTED suffix.
    signal.signal(signal.SIGINT, _handle_signal)
    try:
        signal.signal(signal.SIGTERM, _handle_signal)
    except Exception:
        # Some platforms may not support SIGTERM the same way.
        pass

    # Run command, stream output, and buffer to a temp file (not RAM).
    cmd_str = " ".join(argv)
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    _STATE["proc"] = proc

    # Keep only a small rolling tail for optional snippet printing.
    tail_buf = None
    if snippet_lines > 0 and deque is not None:
        tail_buf = deque(maxlen=snippet_lines)

    tmp_fh = tempfile.NamedTemporaryFile(prefix="safe-run-", suffix=".tmp", delete=False)
    tmp_path = tmp_fh.name
    try:
        for raw in iter(proc.stdout.readline, b''):
            if raw == b'':
                break

            # Mirror to stdout.
            try:
                sys.stdout.write(raw)
            except Exception:
                # Last-ditch: decode then re-encode using stdout encoding.
                enc = getattr(sys.stdout, "encoding", None) or "utf-8"
                sys.stdout.write(raw.decode("utf-8", "replace").encode(enc, "replace"))
            try:
                sys.stdout.flush()
            except Exception:
                pass

            # Persist to disk buffer.
            try:
                tmp_fh.write(raw)
                tmp_fh.flush()
            except Exception:
                pass

            if tail_buf is not None:
                tail_buf.append(raw)
    except KeyboardInterrupt:
        _STATE["aborted"] = True
        # Try to stop child cleanly; then wait.
        try:
            proc.send_signal(signal.SIGINT)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass
        try:
            tmp_fh.close()
        except Exception:
            pass

    rc = None
    try:
        rc = proc.wait()
    except Exception:
        rc = 1

    aborted = bool(_STATE.get("aborted"))
    if aborted:
        # Conventional shell-ish code for SIGINT is 130.
        rc = 130

    if rc == 0:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        return 0

    if not os.path.isdir(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError:
            pass

    ts = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    slug = slugify(cmd_str)
    suffix = "-aborted" if aborted else "-fail"
    out_path = os.path.join(log_dir, "%s-%s%s.txt" % (ts, slug, suffix))
    if os.path.exists(out_path):
        out_path = os.path.join(log_dir, "%s-%s%s-%d.txt" % (ts, slug, suffix, os.getpid()))

    # Move buffered output into final artifact.
    try:
        with open(tmp_path, "rb") as src:
            with open(out_path, "wb") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    eprint("")
    if aborted:
        eprint("SAFE-RUN: command aborted (exit=%d)" % rc)
    else:
        eprint("SAFE-RUN: command failed (exit=%d)" % rc)
    eprint("SAFE-RUN: log saved to: %s" % out_path)

    if snippet_lines > 0:
        eprint("")
        eprint("SAFE-RUN: last %d lines of output:" % snippet_lines)
        if tail_buf is not None:
            for b in list(tail_buf):
                eprint(b.decode('utf-8', 'replace').rstrip("\n"))
        else:
            # Fallback if deque is unavailable: read from the saved file.
            try:
                with open(out_path, "rb") as fh:
                    data = fh.read()
                # Best-effort tail.
                text = data.decode("utf-8", "replace")
                lines = text.splitlines()[-snippet_lines:]
                for line in lines:
                    eprint(line)
            except Exception:
                pass

    return rc

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
