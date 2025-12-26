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
SAFE_ARCHIVE = SCRIPTS / 'safe-archive.py'


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
            # Create a destination with same name -> should fail with strict no-clobber
            (arc / 'a fail.txt').write_text('EXISTS', encoding='utf-8')

            # M0-P1-I3: Enable strict no-clobber mode via env var
            r = run_archive(['--all'], wd, env={'SAFE_ARCHIVE_NO_CLOBBER': '1'})
            self.assertEqual(r.returncode, 2)
            self.assertIn('Destination exists', r.stderr)
            self.assertTrue((fail / 'a fail.txt').exists())

    def test_auto_suffix_default(self):
        """Test M0-P1-I3: Default auto-suffix behavior when destination exists"""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            fail = wd / '.agent' / 'FAIL-LOGS'
            arc = wd / '.agent' / 'FAIL-ARCHIVE'
            fail.mkdir(parents=True)
            arc.mkdir(parents=True)

            (fail / 'test.log').write_text('NEW', encoding='utf-8')
            # Create a destination with same name
            (arc / 'test.log').write_text('OLD', encoding='utf-8')

            # Default behavior: should auto-suffix
            r = run_archive(['--all'], wd)
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            
            # Source should be moved
            self.assertFalse((fail / 'test.log').exists())
            
            # Original destination should be unchanged
            self.assertEqual((arc / 'test.log').read_text(encoding='utf-8'), 'OLD')
            
            # New file should have .2 suffix
            self.assertTrue((arc / 'test.log.2').exists())
            self.assertEqual((arc / 'test.log.2').read_text(encoding='utf-8'), 'NEW')

    def test_auto_suffix_multiple_collisions(self):
        """Test M0-P1-I3: Auto-suffix increments correctly when .2, .3 already exist"""
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            fail = wd / '.agent' / 'FAIL-LOGS'
            arc = wd / '.agent' / 'FAIL-ARCHIVE'
            fail.mkdir(parents=True)
            arc.mkdir(parents=True)

            # Create multiple files in archive to test suffix iteration
            (arc / 'test.log').write_text('FIRST', encoding='utf-8')
            (arc / 'test.log.2').write_text('SECOND', encoding='utf-8')
            (arc / 'test.log.3').write_text('THIRD', encoding='utf-8')
            
            # New file to archive
            (fail / 'test.log').write_text('FOURTH', encoding='utf-8')

            # Should find .4 as the next available suffix
            r = run_archive(['--all'], wd)
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            
            # Source should be moved
            self.assertFalse((fail / 'test.log').exists())
            
            # All existing files should be unchanged
            self.assertEqual((arc / 'test.log').read_text(encoding='utf-8'), 'FIRST')
            self.assertEqual((arc / 'test.log.2').read_text(encoding='utf-8'), 'SECOND')
            self.assertEqual((arc / 'test.log.3').read_text(encoding='utf-8'), 'THIRD')
            
            # New file should have .4 suffix
            self.assertTrue((arc / 'test.log.4').exists())
            self.assertEqual((arc / 'test.log.4').read_text(encoding='utf-8'), 'FOURTH')

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
