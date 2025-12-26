# -*- coding: utf-8 -*-
from __future__ import print_function
import os, sys, subprocess, tempfile, shutil, stat, signal, time

def which(cmd):
    for p in os.environ.get("PATH","").split(os.pathsep):
        c=os.path.join(p, cmd)
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None

def pick_python():
    # Prefer python3, but fall back to python if needed. Tests can override with TEST_PY env var.
    forced=os.environ.get("TEST_PY")
    if forced:
        return forced
    for cand in ("python3","python","python2"):
        p=which(cand)
        if p:
            return p
    return sys.executable

def run_py(script_path, args, cwd, env=None, input_bytes=None, timeout=30):
    py=pick_python()
    cmd=[py, script_path] + list(args)
    p=subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate(input=input_bytes, timeout=timeout)
    return p.returncode, out, err, cmd

def make_exe(path, content):
    d=os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    st=os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def list_files(root):
    out=[]
    for dp, dn, fn in os.walk(root):
        for f in fn:
            out.append(os.path.join(dp, f))
    return sorted(out)

def read_text(path):
    with open(path, "rb") as f:
        data=f.read()
    try:
        return data.decode("utf-8")
    except Exception:
        return data.decode("utf-8", "replace")

def find_one(glob_pat):
    import glob
    hits=glob.glob(glob_pat)
    hits.sort()
    return hits[0] if hits else None
