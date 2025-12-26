import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / 'scripts'
SAFE_CHECK = SCRIPTS / 'safe-check.py'


def run_safe_check(workdir: Path, env=None, timeout=60):
    e = os.environ.copy()
    if env:
        e.update(env)
    proc = subprocess.run(
        [sys.executable, str(SAFE_CHECK)],
        cwd=str(workdir),
        env=e,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return proc


class TestSafeCheck(unittest.TestCase):
    def test_safe_check_passes_in_clean_repo(self):
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            # Provide the scripts in cwd, since safe_check expects relative paths.
            scripts_dir = wd / 'scripts' / 'python3'
            scripts_dir.mkdir(parents=True)
            for name in ['safe-run.py', 'safe-archive.py', 'safe-check.py', 'preflight-automerge-ruleset.py']:
                (SCRIPTS / name).replace(scripts_dir / name) if False else (scripts_dir / name).write_bytes((SCRIPTS / name).read_bytes())

            proc = subprocess.run(
                [sys.executable, str(scripts_dir / 'safe-check.py')],
                cwd=str(wd),
                env=os.environ.copy(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            self.assertEqual(proc.returncode, 0, msg=f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
            # sanity: should mention PASS somewhere
            self.assertRegex(proc.stdout + proc.stderr, r"PASS|OK")

