#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup

"""Tests for CLI Dispatch.

:Purpose:
    Unit tests for CLI Dispatch functionality.

:Environment Variables:
    None directly used. Tests may set environment variables temporarily via patching.

:Examples:
    Run all tests::

        python3 -m pytest test_cli_dispatch.py -v

:Exit Codes:
    Uses pytest exit codes:
    - 0: All tests passed
    - 1: Tests failed
    - 2: Test execution error
"""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.cli_argparse import _run_all_runners  # noqa: E402
from tools.repo_lint.common import ExitCode  # noqa: E402


class TestRunnerDispatch(unittest.TestCase):
    """Test runner dispatch logic per Phase 7 Item 7.1.1.

    :Purpose:
        Validates --only flag filtering and has_files() gating.
    """

    def setUp(self):
        """Set up test fixtures.

        :Purpose:
            Create mock runners and args for dispatch testing.
        """
        # Create mock args
        self.args_no_only = argparse.Namespace(ci=False, verbose=False, only=None)
        self.args_only_python = argparse.Namespace(ci=False, verbose=False, only="python")
        self.args_only_unknown = argparse.Namespace(ci=False, verbose=False, only="unknown")

    @patch("tools.repo_lint.cli_argparse.PythonRunner")
    @patch("tools.repo_lint.cli_argparse.BashRunner")
    @patch("tools.repo_lint.cli_argparse.PowerShellRunner")
    @patch("tools.repo_lint.cli_argparse.PerlRunner")
    @patch("tools.repo_lint.cli_argparse.YAMLRunner")
    @patch("tools.repo_lint.cli_argparse.RustRunner")
    @patch("tools.repo_lint.cli_argparse.report_results")
    def test_only_flag_filters_runners(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        mock_report,
        mock_rust,
        mock_yaml,
        mock_perl,
        mock_powershell,
        mock_bash,
        mock_python,
    ):
        """Test that --only flag filters to correct runner.

        :Purpose:
            Verify only the specified runner executes when --only is used.

        :param mock_report: Mocked report_results
        :param mock_rust: Mocked RustRunner class
        :param mock_yaml: Mocked YAMLRunner class
        :param mock_perl: Mocked PerlRunner class
        :param mock_powershell: Mocked PowerShellRunner class
        :param mock_bash: Mocked BashRunner class
        :param mock_python: Mocked PythonRunner class
        """
        # Set up mock instances
        for mock_cls in [mock_python, mock_bash, mock_powershell, mock_perl, mock_yaml, mock_rust]:
            mock_instance = MagicMock()
            mock_instance.has_files.return_value = True
            mock_instance.check_tools.return_value = []
            mock_instance.check.return_value = []
            mock_cls.return_value = mock_instance

        # Mock report to return success
        mock_report.return_value = ExitCode.SUCCESS

        # Run with --only python
        result = _run_all_runners(self.args_only_python, "Linting", lambda runner: runner.check())

        # Verify only Python runner was invoked
        mock_python.return_value.check.assert_called_once()
        mock_bash.return_value.check.assert_not_called()
        mock_powershell.return_value.check.assert_not_called()
        mock_perl.return_value.check.assert_not_called()
        mock_yaml.return_value.check.assert_not_called()
        mock_rust.return_value.check.assert_not_called()

        # Verify success exit code
        self.assertEqual(result, ExitCode.SUCCESS)

    @patch("tools.repo_lint.cli_argparse.PythonRunner")
    @patch("tools.repo_lint.cli_argparse.BashRunner")
    @patch("tools.repo_lint.cli_argparse.PowerShellRunner")
    @patch("tools.repo_lint.cli_argparse.PerlRunner")
    @patch("tools.repo_lint.cli_argparse.YAMLRunner")
    @patch("tools.repo_lint.cli_argparse.RustRunner")
    @patch("tools.repo_lint.cli_argparse.report_results")
    def test_all_runners_execute_without_only(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        mock_report,
        mock_rust,
        mock_yaml,
        mock_perl,
        mock_powershell,
        mock_bash,
        mock_python,
    ):
        """Test that all runners execute when no --only flag.

        :Purpose:
            Verify all runners with files execute when --only is not used.

        :param mock_report: Mocked report_results
        :param mock_rust: Mocked RustRunner class
        :param mock_yaml: Mocked YAMLRunner class
        :param mock_perl: Mocked PerlRunner class
        :param mock_powershell: Mocked PowerShellRunner class
        :param mock_bash: Mocked BashRunner class
        :param mock_python: Mocked PythonRunner class
        """
        # Set up mock instances
        for mock_cls in [mock_python, mock_bash, mock_powershell, mock_perl, mock_yaml, mock_rust]:
            mock_instance = MagicMock()
            mock_instance.has_files.return_value = True
            mock_instance.check_tools.return_value = []
            mock_instance.check.return_value = []
            mock_cls.return_value = mock_instance

        # Mock report to return success
        mock_report.return_value = ExitCode.SUCCESS

        # Run without --only
        result = _run_all_runners(self.args_no_only, "Linting", lambda runner: runner.check())

        # Verify all runners were invoked
        mock_python.return_value.check.assert_called_once()
        mock_bash.return_value.check.assert_called_once()
        mock_powershell.return_value.check.assert_called_once()
        mock_perl.return_value.check.assert_called_once()
        mock_yaml.return_value.check.assert_called_once()
        mock_rust.return_value.check.assert_called_once()

        # Verify success exit code
        self.assertEqual(result, ExitCode.SUCCESS)

    @patch("tools.repo_lint.cli_argparse.PythonRunner")
    @patch("tools.repo_lint.cli_argparse.BashRunner")
    @patch("tools.repo_lint.cli_argparse.PowerShellRunner")
    @patch("tools.repo_lint.cli_argparse.PerlRunner")
    @patch("tools.repo_lint.cli_argparse.YAMLRunner")
    @patch("tools.repo_lint.cli_argparse.RustRunner")
    def test_runners_skip_when_no_files(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        mock_rust,
        mock_yaml,
        mock_perl,
        mock_powershell,
        mock_bash,
        mock_python,
    ):
        """Test that runners skip when has_files() returns False.

        :Purpose:
            Verify runners are not invoked when they have no files to check.

        :param mock_rust: Mocked RustRunner class
        :param mock_yaml: Mocked YAMLRunner class
        :param mock_perl: Mocked PerlRunner class
        :param mock_powershell: Mocked PowerShellRunner class
        :param mock_bash: Mocked BashRunner class
        :param mock_python: Mocked PythonRunner class
        """
        # Set up mock instances - only Python has files
        for mock_cls in [mock_bash, mock_powershell, mock_perl, mock_yaml, mock_rust]:
            mock_instance = MagicMock()
            mock_instance.has_files.return_value = False
            mock_cls.return_value = mock_instance

        # Python has files
        mock_python_instance = MagicMock()
        mock_python_instance.has_files.return_value = True
        mock_python_instance.check_tools.return_value = []
        mock_python_instance.check.return_value = []
        mock_python.return_value = mock_python_instance

        # Run without --only
        with patch("tools.repo_lint.cli_argparse.report_results", return_value=ExitCode.SUCCESS):
            result = _run_all_runners(self.args_no_only, "Linting", lambda runner: runner.check())

        # Verify only Python runner was invoked
        mock_python.return_value.check.assert_called_once()
        mock_bash.return_value.check.assert_not_called()
        mock_powershell.return_value.check.assert_not_called()
        mock_perl.return_value.check.assert_not_called()
        mock_yaml.return_value.check.assert_not_called()
        mock_rust.return_value.check.assert_not_called()

        # Verify success exit code
        self.assertEqual(result, ExitCode.SUCCESS)

    def test_unknown_language_returns_error(self):
        """Test that unknown language for --only returns INTERNAL_ERROR.

        :Purpose:
            Verify appropriate error when --only specifies unknown language.
        """
        # Run with unknown language
        result = _run_all_runners(self.args_only_unknown, "Linting", lambda runner: runner.check())

        # Verify error exit code
        self.assertEqual(result, ExitCode.INTERNAL_ERROR)

    @patch("tools.repo_lint.cli_argparse.PythonRunner")
    @patch("tools.repo_lint.cli_argparse.BashRunner")
    @patch("tools.repo_lint.cli_argparse.PowerShellRunner")
    @patch("tools.repo_lint.cli_argparse.PerlRunner")
    @patch("tools.repo_lint.cli_argparse.YAMLRunner")
    @patch("tools.repo_lint.cli_argparse.RustRunner")
    def test_no_files_for_only_language_returns_error(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        mock_rust,
        mock_yaml,
        mock_perl,
        mock_powershell,
        mock_bash,
        mock_python,
    ):
        """Test that --only with no files for language returns INTERNAL_ERROR.

        :Purpose:
            Verify appropriate error when --only language has no files.

        :param mock_rust: Mocked RustRunner class
        :param mock_yaml: Mocked YAMLRunner class
        :param mock_perl: Mocked PerlRunner class
        :param mock_powershell: Mocked PowerShellRunner class
        :param mock_bash: Mocked BashRunner class
        :param mock_python: Mocked PythonRunner class
        """
        # Set up mock Python instance with no files
        mock_python_instance = MagicMock()
        mock_python_instance.has_files.return_value = False
        mock_python.return_value = mock_python_instance

        # Run with --only python but no Python files
        result = _run_all_runners(self.args_only_python, "Linting", lambda runner: runner.check())

        # Verify error exit code
        self.assertEqual(result, ExitCode.INTERNAL_ERROR)


if __name__ == "__main__":
    unittest.main()
