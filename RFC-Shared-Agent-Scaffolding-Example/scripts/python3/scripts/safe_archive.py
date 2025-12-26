#!/usr/bin/env python3
# safe_archive.py (Python 3)
# Non-destructively archive failure logs from .agent/FAIL-LOGS to .agent/FAIL-ARCHIVE using no-clobber semantics.
import os
import sys
import shutil
import subprocess
import gzip
from typing import List

def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)

def usage() -> int:
    eprint("Usage: scripts/python3/safe_archive.py [--all | <file> ...]")
    eprint("")
    eprint("Environment:")
    eprint("  SAFE_FAIL_DIR           Source directory (default: .agent/FAIL-LOGS)")
    eprint("  SAFE_ARCHIVE_DIR        Destination directory (default: .agent/FAIL-ARCHIVE)")
    eprint("  SAFE_ARCHIVE_COMPRESS   Compression: none|gzip|xz|zstd (default: none)")
    return 2

def have_cmd(cmd: str) -> bool:
    for p in os.environ.get("PATH", "").split(os.pathsep):
        exe = os.path.join(p, cmd)
        if os.path.isfile(exe) and os.access(exe, os.X_OK):
            return True
    return False

def compress_file(method: str, path: str) -> None:
    method = method or "none"
    if method == "none":
        return
    if method == "gzip":
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

def archive_one(src: str, archive_dir: str, compress: str) -> None:
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

def main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        return usage() if not argv else usage()

    fail_dir = os.environ.get("SAFE_FAIL_DIR", ".agent/FAIL-LOGS")
    archive_dir = os.environ.get("SAFE_ARCHIVE_DIR", ".agent/FAIL-ARCHIVE")
    compress = os.environ.get("SAFE_ARCHIVE_COMPRESS", "none")

    os.makedirs(fail_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)

    if argv and argv[0] == "--all":
        files = [os.path.join(fail_dir, n) for n in sorted(os.listdir(fail_dir))
                 if os.path.isfile(os.path.join(fail_dir, n))]
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
    raise SystemExit(main(sys.argv[1:]))
