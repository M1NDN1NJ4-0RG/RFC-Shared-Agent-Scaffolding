#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# safe_archive.py (Python 2)
# Non-destructively archive failure logs from .agent/FAIL-LOGS to .agent/FAIL-ARCHIVE using no-clobber semantics.
from __future__ import print_function
import os
import sys
import shutil
import re
import subprocess

def eprint(*args):
    print(*args, file=sys.stderr)

def usage():
    eprint("Usage: scripts/python2/safe_archive.py [--all | <file> ...]")
    eprint("")
    eprint("Environment:")
    eprint("  SAFE_FAIL_DIR           Source directory (default: .agent/FAIL-LOGS)")
    eprint("  SAFE_ARCHIVE_DIR        Destination directory (default: .agent/FAIL-ARCHIVE)")
    eprint("  SAFE_ARCHIVE_COMPRESS   Compression: none|gzip|xz|zstd (default: none)")
    return 2

def have_cmd(cmd):
    for p in os.environ.get("PATH", "").split(os.pathsep):
        exe = os.path.join(p, cmd)
        if os.path.isfile(exe) and os.access(exe, os.X_OK):
            return True
    return False

def compress_file(method, path):
    method = method or "none"
    if method == "none":
        return
    if method == "gzip":
        import gzip
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
    raise RuntimeError("Invalid SAFE_ARCHIVE_COMPRESS value: %s" % method)

def archive_one(src, archive_dir, compress):
    if not os.path.exists(src):
        raise RuntimeError("File not found: %s" % src)
    base = os.path.basename(src)
    dest = os.path.join(archive_dir, base)
    if os.path.exists(dest):
        eprint("SKIP: destination exists (no-clobber): %s" % dest)
        return
    shutil.move(src, dest)
    eprint("ARCHIVED: %s -> %s" % (src, dest))
    compress_file(compress, dest)

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        return usage() if not argv else (usage() or 0)

    fail_dir = os.environ.get("SAFE_FAIL_DIR", ".agent/FAIL-LOGS")
    archive_dir = os.environ.get("SAFE_ARCHIVE_DIR", ".agent/FAIL-ARCHIVE")
    compress = os.environ.get("SAFE_ARCHIVE_COMPRESS", "none")

    if not os.path.isdir(fail_dir):
        try:
            os.makedirs(fail_dir)
        except OSError:
            pass
    if not os.path.isdir(archive_dir):
        try:
            os.makedirs(archive_dir)
        except OSError:
            pass

    if argv and argv[0] == "--all":
        files = []
        for name in sorted(os.listdir(fail_dir)):
            p = os.path.join(fail_dir, name)
            if os.path.isfile(p):
                files.append(p)
        if not files:
            eprint("No files to archive in %s" % fail_dir)
            return 0
        for f in files:
            archive_one(f, archive_dir, compress)
        return 0

    if not argv:
        return usage()

    for f in argv:
        archive_one(f, archive_dir, compress)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
