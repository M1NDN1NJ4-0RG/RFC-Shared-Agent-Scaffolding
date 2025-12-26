#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# safe_check.py (Python 2)
# Contract verification for Python2 scripts.
from __future__ import print_function
import os
import sys
import glob
import subprocess
import time

def eprint(*args):
    print(*args, file=sys.stderr)

def die(msg, rc=1):
    eprint("ERROR: %s" % msg)
    sys.exit(rc)

def usage():
    eprint("Usage: scripts/python2/safe_check.py")
    sys.exit(2)

def count_files(d):
    return len([p for p in glob.glob(os.path.join(d, "*")) if os.path.isfile(p)])

def main(argv):
    if argv:
        usage()

    log_dir = os.environ.get("SAFE_LOG_DIR", ".agent/FAIL-LOGS")
    for d in (log_dir, ".agent/FAIL-ARCHIVE"):
        if not os.path.isdir(d):
            try:
                os.makedirs(d)
            except OSError:
                pass

    if not os.path.isfile("scripts/python2/safe_run.py"):
        die("Missing scripts/python2/safe_run.py")
    if not os.path.isfile("scripts/python2/safe_archive.py"):
        die("Missing scripts/python2/safe_archive.py")

    before = count_files(log_dir)

    # failure path
    rc = subprocess.call([sys.executable, "scripts/python2/safe_run.py", "--",
                          sys.executable, "-c", 'import sys; sys.stdout.write("hello\\n"); sys.stderr.write("boom\\n"); sys.exit(42)'],
                         stdout=open(os.devnull, "wb"))
    if rc != 42:
        die("safe_run did not preserve exit code (expected 42, got %d)" % rc)

    after = count_files(log_dir)
    if after != before + 1:
        die("safe_run failure did not create exactly one artifact (before=%d after=%d)" % (before, after))
    eprint("INFO: safe_run failure-path OK")

    # success path
    before = after
    rc = subprocess.call([sys.executable, "scripts/python2/safe_run.py", "--",
                          sys.executable, "-c", 'import sys; sys.stdout.write("ok\\n"); sys.exit(0)'],
                         stdout=open(os.devnull, "wb"))
    if rc != 0:
        die("safe_run success returned non-zero (%d)" % rc)
    after = count_files(log_dir)
    if after != before:
        die("safe_run success created artifacts (before=%d after=%d)" % (before, after))
    eprint("INFO: safe_run success-path OK")

    # archive newest
    files = sorted([p for p in glob.glob(os.path.join(log_dir, "*")) if os.path.isfile(p)],
                   key=lambda p: os.path.getmtime(p), reverse=True)
    if not files:
        die("No fail logs found to test archiving")
    newest = files[0]
    base = os.path.basename(newest)
    dest = os.path.join(".agent/FAIL-ARCHIVE", base)

    rc = subprocess.call([sys.executable, "scripts/python2/safe_archive.py", newest],
                         stdout=open(os.devnull, "wb"))
    if rc != 0:
        die("safe_archive failed (%d)" % rc)
    if not os.path.exists(dest):
        die("Archive file missing: %s" % dest)
    if os.path.exists(newest):
        die("Source file still exists (expected moved)")
    eprint("INFO: safe_archive move OK")

    # no-clobber
    dummy = os.path.join(log_dir, base)
    with open(dummy, "wb") as fh:
        fh.write(b"dummy\n")

    rc = subprocess.call([sys.executable, "scripts/python2/safe_archive.py", dummy],
                         stdout=open(os.devnull, "wb"))
    if rc != 0:
        die("safe_archive no-clobber failed (%d)" % rc)

    with open(dest, "rb") as fh:
        contents = fh.read().decode("utf-8", "replace")
    if "hello" not in contents:
        die("Archive content changed unexpectedly (no-clobber violation suspected)")
    eprint("INFO: safe_archive no-clobber OK")

    eprint("INFO: SAFE-CHECK: contract verification PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
