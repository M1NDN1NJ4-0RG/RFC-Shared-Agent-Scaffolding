#!/usr/bin/env python3
# safe-check.py (Python 3)
# Contract verification for Python3 scripts.
import os
import sys
import glob
import subprocess
from pathlib import Path
from typing import List

def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)

def die(msg: str, rc: int = 1) -> None:
    eprint(f"ERROR: {msg}")
    raise SystemExit(rc)

def usage() -> None:
    eprint("Usage: scripts/python3/safe-check.py")
    raise SystemExit(2)

def count_files(d: str) -> int:
    return len([p for p in glob.glob(os.path.join(d, "*")) if os.path.isfile(p)])

def main(argv: List[str]) -> int:
    if argv:
        usage()

    log_dir = os.environ.get("SAFE_LOG_DIR", ".agent/FAIL-LOGS")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(".agent/FAIL-ARCHIVE", exist_ok=True)

    if not Path("scripts/python3/safe-run.py").is_file():
        die("Missing scripts/python3/safe-run.py")
    if not Path("scripts/python3/safe-archive.py").is_file():
        die("Missing scripts/python3/safe-archive.py")

    before = count_files(log_dir)

    # failure path
    rc = subprocess.call([sys.executable, "scripts/python3/safe-run.py", "--",
                          sys.executable, "-c", 'import sys; print("hello"); print("boom", file=sys.stderr); raise SystemExit(42)'],
                         stdout=subprocess.DEVNULL)
    if rc != 42:
        die(f"safe_run did not preserve exit code (expected 42, got {rc})")
    after = count_files(log_dir)
    if after != before + 1:
        die(f"safe_run failure did not create exactly one artifact (before={before} after={after})")
    eprint("INFO: safe_run failure-path OK")

    # success path
    before = after
    rc = subprocess.call([sys.executable, "scripts/python3/safe-run.py", "--",
                          sys.executable, "-c", 'print("ok"); raise SystemExit(0)'],
                         stdout=subprocess.DEVNULL)
    if rc != 0:
        die(f"safe_run success returned non-zero ({rc})")
    after = count_files(log_dir)
    if after != before:
        die(f"safe_run success created artifacts (before={before} after={after})")
    eprint("INFO: safe_run success-path OK")

    # archive newest
    files = sorted([p for p in glob.glob(os.path.join(log_dir, "*")) if os.path.isfile(p)],
                   key=lambda p: os.path.getmtime(p), reverse=True)
    if not files:
        die("No fail logs found to test archiving")
    newest = files[0]
    base = os.path.basename(newest)
    dest = os.path.join(".agent/FAIL-ARCHIVE", base)

    rc = subprocess.call([sys.executable, "scripts/python3/safe-archive.py", newest],
                         stdout=subprocess.DEVNULL)
    if rc != 0:
        die(f"safe_archive failed ({rc})")
    if not os.path.exists(dest):
        die(f"Archive file missing: {dest}")
    if os.path.exists(newest):
        die("Source file still exists (expected moved)")
    eprint("INFO: safe_archive move OK")

    # no-clobber
    dummy = os.path.join(log_dir, base)
    with open(dummy, "w", encoding="utf-8") as fh:
        fh.write("dummy\n")
    rc = subprocess.call([sys.executable, "scripts/python3/safe-archive.py", dummy],
                         stdout=subprocess.DEVNULL)
    if rc != 0:
        die(f"safe_archive no-clobber failed ({rc})")
    with open(dest, "r", encoding="utf-8", errors="replace") as fh:
        contents = fh.read()
    if "hello" not in contents:
        die("Archive content changed unexpectedly (no-clobber violation suspected)")
    eprint("INFO: safe_archive no-clobber OK")

    eprint("INFO: SAFE-CHECK: contract verification PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
