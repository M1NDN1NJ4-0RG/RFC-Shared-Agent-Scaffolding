#!/usr/bin/env python3
# safe-archive.py (Python 3)
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
    eprint("Usage: scripts/python3/safe-archive.py [--no-clobber] [--all | <file> ...]")
    eprint("")
    eprint("Options:")
    eprint("  --no-clobber            Fail if destination exists (default: auto-suffix)")
    eprint("")
    eprint("Environment:")
    eprint("  SAFE_FAIL_DIR           Source directory (default: .agent/FAIL-LOGS)")
    eprint("  SAFE_ARCHIVE_DIR        Destination directory (default: .agent/FAIL-ARCHIVE)")
    eprint("  SAFE_ARCHIVE_COMPRESS   Compression: none|gzip|xz|zstd (default: none)")
    eprint("  SAFE_ARCHIVE_NO_CLOBBER Set to 1 to enable strict no-clobber mode")
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

def archive_one(src: str, archive_dir: str, compress: str, strict_no_clobber: bool = False) -> None:
    """Archive a single file with M0-P1-I3 no-clobber semantics.
    
    Args:
        src: Source file path
        archive_dir: Destination directory
        compress: Compression method
        strict_no_clobber: If True, fail if destination exists. If False (default), auto-suffix.
    """
    if not os.path.exists(src):
        raise RuntimeError("File not found: %s" % src)
    
    base = os.path.basename(src)
    dest = os.path.join(archive_dir, base)
    
    if os.path.exists(dest):
        if strict_no_clobber:
            # M0-P1-I3: Strict no-clobber mode - fail with error
            raise RuntimeError("Destination exists: %s" % dest)
        else:
            # M0-P1-I3: Default auto-suffix mode - append .2, .3, etc.
            n = 2
            while os.path.exists(dest + "." + str(n)):
                n += 1
            dest = dest + "." + str(n)
            eprint("WARNING: destination exists, using auto-suffix: %s" % dest)
    
    shutil.move(src, dest)
    eprint("ARCHIVED: %s -> %s" % (src, dest))
    compress_file(compress, dest)

def main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        return usage() if not argv else usage()

    # M0-P1-I3: Check for strict no-clobber mode
    strict_no_clobber = False
    args = list(argv)
    
    # Check for --no-clobber flag
    if "--no-clobber" in args:
        strict_no_clobber = True
        args.remove("--no-clobber")
    
    # Check for SAFE_ARCHIVE_NO_CLOBBER env var
    if os.environ.get("SAFE_ARCHIVE_NO_CLOBBER") == "1":
        strict_no_clobber = True

    fail_dir = os.environ.get("SAFE_FAIL_DIR", ".agent/FAIL-LOGS")
    archive_dir = os.environ.get("SAFE_ARCHIVE_DIR", ".agent/FAIL-ARCHIVE")
    compress = os.environ.get("SAFE_ARCHIVE_COMPRESS", "none")

    os.makedirs(fail_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)

    try:
        if args and args[0] == "--all":
            files = [os.path.join(fail_dir, n) for n in sorted(os.listdir(fail_dir))
                     if os.path.isfile(os.path.join(fail_dir, n))]
            if not files:
                eprint("No files to archive in %s" % fail_dir)
                return 0
            for f in files:
                archive_one(f, archive_dir, compress, strict_no_clobber)
            return 0

        if not args:
            return usage()

        for f in args:
            archive_one(f, archive_dir, compress, strict_no_clobber)
        return 0
    except RuntimeError as e:
        eprint("ERROR: %s" % e)
        return 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
