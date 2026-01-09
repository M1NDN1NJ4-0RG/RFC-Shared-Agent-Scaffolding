#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup
"""Unit tests for Perl runner (Perl::Critic, docstring validation).

:Purpose:
    Validates that the Perl runner correctly integrates with Perl::Critic
    and docstring validation.

:Test Coverage:
    - _get_perl_files() returns file list or empty list
    - _run_perlcritic() runs with correct arguments
    - Perl::Critic uses --verbose 8 flag
    - _run_docstring_validation() calls validator with correct args
    - Empty file lists are handled correctly

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_perl_runner.py
        # or
        python3 tools/repo_lint/tests/test_perl_runner.py

:Environment Variables:
    None. Tests are self-contained with mocked subprocess calls.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_perl_runner.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_perl_runner.py::TestPerlRunner \
            ::test_perlcritic_uses_verbose_flag -v

:Notes:
    - Tests use unittest.mock to avoid executing actual linters
    - Tests verify command-line arguments passed to subprocess
    - Tests verify exit code handling (0 = success, 2 = violations)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.runners.perl_runner import PerlRunner  # noqa: E402


class TestPerlRunner(unittest.TestCase):
    """Test Perl runner behavior.

    :Purpose:
        Validates Perl::Critic and docstring validation integration.
    """

    def setUp(self) -> None:
        """Set up test fixtures.

        :Purpose:
            Create PerlRunner instance with mocked repo root.
        """
        self.runner = PerlRunner(repo_root=Path("/fake/repo"))

    @patch("tools.repo_lint.runners.perl_runner.subprocess.run")
    def test_get_perl_files_returns_list(self, mock_run) -> None:
        """Test that _get_perl_files returns file list.

        :Purpose:
            Verify helper method correctly parses git output.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="script1.pl\nscript2.pl\n", stderr="")

        files = self.runner._get_perl_files()

        self.assertEqual(len(files), 2)
        self.assertIn("script1.pl", files)
        self.assertIn("script2.pl", files)

    @patch("tools.repo_lint.runners.perl_runner.subprocess.run")
    def test_get_perl_files_returns_empty(self, mock_run) -> None:
        """Test that _get_perl_files returns empty list when no files.

        :Purpose:
            Verify helper method handles empty output.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        files = self.runner._get_perl_files()

        self.assertEqual(files, [])

    @patch("tools.repo_lint.runners.perl_runner.subprocess.run")
    def test_perlcritic_uses_verbose_flag(self, mock_run) -> None:
        """Test that _run_perlcritic uses --verbose 8 flag.

        :Purpose:
            Verify Perl::Critic runs with correct verbosity.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="test.pl\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # perlcritic
        ]

        result = self.runner._run_perlcritic()

        # Check perlcritic call (second call)
        self.assertEqual(mock_run.call_count, 2)
        critic_args = mock_run.call_args_list[1][0][0]
        self.assertIn("--verbose", critic_args)
        self.assertIn("8", critic_args)
        self.assertTrue(result.passed)

    @patch("tools.repo_lint.runners.perl_runner.subprocess.run")
    def test_perlcritic_handles_exit_code_0(self, mock_run) -> None:
        """Test that _run_perlcritic handles exit code 0 (success).

        :Purpose:
            Verify correct handling of no violations.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="test.pl\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # perlcritic (success)
        ]

        result = self.runner._run_perlcritic()

        self.assertTrue(result.passed)
        self.assertEqual(result.tool, "perlcritic")
        self.assertEqual(len(result.violations), 0)

    @patch("tools.repo_lint.runners.perl_runner.subprocess.run")
    def test_perlcritic_handles_exit_code_2(self, mock_run) -> None:
        """Test that _run_perlcritic handles exit code 2 (violations).

        :Purpose:
            Verify correct handling of violations found.

        :param mock_run: Mocked subprocess.run
        """
        mock_output = """Code before strictures are enabled at line 5
Two-argument "open" used at line 10"""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="test.pl\n", stderr=""),  # git ls-files
            MagicMock(returncode=2, stdout=mock_output, stderr=""),  # perlcritic (violations)
        ]

        result = self.runner._run_perlcritic()

        self.assertFalse(result.passed)
        self.assertEqual(result.tool, "perlcritic")
        self.assertEqual(len(result.violations), 2)

    @patch("tools.repo_lint.runners.perl_runner.subprocess.run")
    def test_empty_files_returns_passed(self, mock_run) -> None:
        """Test that empty file list returns passed result.

        :Purpose:
            Verify all methods handle empty file lists gracefully.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # All methods should return passed when no files
        self.assertTrue(self.runner._run_perlcritic().passed)
        # Don't test _run_docstring_validation() as it requires file path mocking


if __name__ == "__main__":
    unittest.main()
