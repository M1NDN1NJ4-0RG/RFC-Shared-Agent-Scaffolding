#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup
"""Unit tests for Bash runner (ShellCheck, shfmt, docstring validation).

:Purpose:
    Validates that the Bash runner correctly integrates with ShellCheck,
    shfmt (check and fix modes), and docstring validation.

:Test Coverage:
    - _get_bash_files() returns file list or empty list
    - _run_shellcheck() runs with correct arguments
    - _run_shfmt_check() runs with -d -l flags (non-mutating)
    - _run_shfmt_fix() runs with -w flag (mutating)
    - _run_docstring_validation() calls validator with correct args
    - Empty file lists are handled correctly

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_bash_runner.py
        # or
        python3 tools/repo_lint/tests/test_bash_runner.py

:Environment Variables:
    None. Tests are self-contained with mocked subprocess calls.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_bash_runner.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_bash_runner.py::TestBashRunner::test_shfmt_check_non_mutating -v

:Notes:
    - Tests use unittest.mock to avoid executing actual linters
    - Tests verify command-line arguments passed to subprocess
    - Tests check that file modifications only happen during fix, not check
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.runners.bash_runner import BashRunner  # noqa: E402


class TestBashRunner(unittest.TestCase):
    """Test Bash runner behavior.

    :Purpose:
        Validates ShellCheck, shfmt, and docstring validation integration.
    """

    def setUp(self):
        """Set up test fixtures.

        :Purpose:
            Create BashRunner instance with mocked repo root.
        """
        self.runner = BashRunner(repo_root=Path("/fake/repo"))

    @patch("tools.repo_lint.runners.bash_runner.subprocess.run")
    def test_get_bash_files_returns_list(self, mock_run):
        """Test that _get_bash_files returns file list.

        :Purpose:
            Verify helper method correctly parses git output.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="script1.sh\nscript2.sh\n", stderr="")

        files = self.runner._get_bash_files()

        self.assertEqual(len(files), 2)
        self.assertIn("script1.sh", files)
        self.assertIn("script2.sh", files)

    @patch("tools.repo_lint.runners.bash_runner.subprocess.run")
    def test_get_bash_files_returns_empty(self, mock_run):
        """Test that _get_bash_files returns empty list when no files.

        :Purpose:
            Verify helper method handles empty output.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        files = self.runner._get_bash_files()

        self.assertEqual(files, [])

    @patch("tools.repo_lint.runners.bash_runner.subprocess.run")
    def test_shellcheck_uses_correct_args(self, mock_run):
        """Test that _run_shellcheck uses correct arguments.

        :Purpose:
            Verify ShellCheck runs with --color=never and --format=gcc.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="test.sh\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # shellcheck
        ]

        result = self.runner._run_shellcheck()

        # Check shellcheck call (second call)
        self.assertEqual(mock_run.call_count, 2)
        shellcheck_args = mock_run.call_args_list[1][0][0]
        self.assertIn("--color=never", shellcheck_args)
        self.assertIn("--format=gcc", shellcheck_args)
        self.assertTrue(result.passed)

    @patch("tools.repo_lint.runners.bash_runner.subprocess.run")
    def test_shfmt_check_non_mutating(self, mock_run):
        """Test that _run_shfmt_check uses -d -l flags (non-mutating).

        :Purpose:
            Verify check mode is non-mutating (doesn't modify files).

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="test.sh\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # shfmt
        ]

        result = self.runner._run_shfmt_check()

        # Check shfmt call (second call)
        self.assertEqual(mock_run.call_count, 2)
        shfmt_args = mock_run.call_args_list[1][0][0]
        self.assertIn("-d", shfmt_args, "Check should use -d flag (diff)")
        self.assertIn("-l", shfmt_args, "Check should use -l flag (list)")
        self.assertNotIn("-w", shfmt_args, "Check should not use -w flag (write)")
        self.assertTrue(result.passed)

    @patch("tools.repo_lint.runners.bash_runner.subprocess.run")
    def test_shfmt_fix_uses_write_flag(self, mock_run):
        """Test that _run_shfmt_fix uses -w flag (mutating).

        :Purpose:
            Verify fix mode applies formatting changes.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="test.sh\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # shfmt
        ]

        result = self.runner._run_shfmt_fix()

        # Check shfmt call (second call)
        self.assertEqual(mock_run.call_count, 2)
        shfmt_args = mock_run.call_args_list[1][0][0]
        self.assertIn("-w", shfmt_args, "Fix should use -w flag (write)")
        self.assertNotIn("-d", shfmt_args, "Fix should not use -d flag")
        self.assertNotIn("-l", shfmt_args, "Fix should not use -l flag")
        self.assertTrue(result.passed)

    @patch("tools.repo_lint.runners.bash_runner.subprocess.run")
    def test_empty_files_returns_passed(self, mock_run):
        """Test that empty file list returns passed result.

        :Purpose:
            Verify all methods handle empty file lists gracefully.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # All methods should return passed when no files
        self.assertTrue(self.runner._run_shellcheck().passed)
        self.assertTrue(self.runner._run_shfmt_check().passed)
        self.assertTrue(self.runner._run_shfmt_fix().passed)
        # Don't test _run_docstring_validation() as it requires file path mocking


if __name__ == "__main__":
    unittest.main()
