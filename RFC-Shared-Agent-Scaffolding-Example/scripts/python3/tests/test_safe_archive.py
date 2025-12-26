import gzip
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / 'scripts'
SAFE_ARCHIVE = SCRIPTS / 'safe_archive.py'


def _py():
    return sys.executable


def run_archive(args, workdir: Path, env=None, timeout=25):
    e = os.environ.copy()
    if env:
        e.update(env)
    e['PYTHONUTF8'] = '1'
    cmd = [_py(), str(SAFE_ARCHIVE)] + args
    return subprocess.run(cmd, cwd=str(workdir), env=e, text=True, capture_output=True, timeout=timeout)


class TestSafeArchive(unittest.TestCase):
    def test_moves_all_no_clobber(self):
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            fail = wd / '.agent' / 'FAIL-LOGS'
            arc = wd / '.agent' / 'FAIL-ARCHIVE'
            fail.mkdir(parents=True)
            arc.mkdir(parents=True)

            (fail / 'a fail.txt').write_text('A', encoding='utf-8')
            # Create a destination with same name -> should fail no-clobber
            (arc / 'a fail.txt').write_text('EXISTS', encoding='utf-8')

            r = run_archive(['--all'], wd)
            self.assertEqual(r.returncode, 2)
            self.assertIn('Destination exists', r.stderr)
            self.assertTrue((fail / 'a fail.txt').exists())

    def test_moves_and_gzip(self):
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            fail = wd / '.agent' / 'FAIL-LOGS'
            arc = wd / '.agent' / 'FAIL-ARCHIVE'
            fail.mkdir(parents=True)
            arc.mkdir(parents=True)

            src = fail / 'x-fail.txt'
            src.write_text('hello\nworld\n', encoding='utf-8')

            r = run_archive(['--all'], wd, env={'SAFE_ARCHIVE_COMPRESS': 'gzip'})
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            self.assertFalse(src.exists())

            gz = arc / 'x-fail.txt.gz'
            self.assertTrue(gz.exists())
            with gzip.open(gz, 'rt', encoding='utf-8') as f:
                data = f.read()
            self.assertIn('hello', data)

    def test_archive_specific_files(self):
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            fail = wd / '.agent' / 'FAIL-LOGS'
            arc = wd / '.agent' / 'FAIL-ARCHIVE'
            fail.mkdir(parents=True)
            arc.mkdir(parents=True)

            f1 = fail / 'one.txt'
            f2 = fail / 'two.txt'
            f1.write_text('1', encoding='utf-8')
            f2.write_text('2', encoding='utf-8')

            r = run_archive([str(f1)], wd)
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            self.assertFalse(f1.exists())
            self.assertTrue((arc / 'one.txt').exists())
            self.assertTrue(f2.exists())


if __name__ == '__main__':
    unittest.main()
