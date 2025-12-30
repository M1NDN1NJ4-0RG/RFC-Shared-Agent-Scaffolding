#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup
"""Unit tests for CLI dispatch logic and runner selection.

:Purpose:
    Validates Phase 7 Item 7.1.1 - Test runner dispatch logic:
    - --only flag filters to correct runner
    - Runners skip when no files present
    - All runners execute when files present and no --only flag

:Test Coverage:
    - _run_all_runners() filters runners based on --only flag
    - _run_all_runners() skips runners when has_files() returns False
    - _run_all_runners() executes all runners when files present
    - Unknown language for --only flag returns INTERNAL_ERROR
    - No files for specified --only language returns INTERNAL_ERROR

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_cli_dispatch.py
        # or
        python3 tools/repo_lint/tests/test_cli_dispatch.py

:Environment Variables:
    None. Tests are self-contained with mocked runners.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_cli_dispatch.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_cli_dispatch.py::TestRunnerDispatch::test_only_flag_filters_runners -v

:Notes:
    - Tests use unittest.mock to avoid executing actual runners
    - Tests verify correct runners are invoked based on --only flag
    - Tests verify has_files() gating logic
"""

import argparse
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.cli import _run_all_runners  # noqa: E402
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

    @patch("tools.repo_lint.cli.PythonRunner")
    @patch("tools.repo_lint.cli.BashRunner")
    @patch("tools.repo_lint.cli.PowerShellRunner")
    @patch("tools.repo_lint.cli.PerlRunner")
    @patch("tools.repo_lint.cli.YAMLRunner")
    @patch("tools.repo_lint.cli.RustRunner")
    @patch("tools.repo_lint.cli.report_results")
    def test_only_flag_filters_runners(
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

    @patch("tools.repo_lint.cli.PythonRunner")
    @patch("tools.repo_lint.cli.BashRunner")
    @patch("tools.repo_lint.cli.PowerShellRunner")
    @patch("tools.repo_lint.cli.PerlRunner")
    @patch("tools.repo_lint.cli.YAMLRunner")
    @patch("tools.repo_lint.cli.RustRunner")
    @patch("tools.repo_lint.cli.report_results")
    def test_all_runners_execute_without_only(
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

    @patch("tools.repo_lint.cli.PythonRunner")
    @patch("tools.repo_lint.cli.BashRunner")
    @patch("tools.repo_lint.cli.PowerShellRunner")
    @patch("tools.repo_lint.cli.PerlRunner")
    @patch("tools.repo_lint.cli.YAMLRunner")
    @patch("tools.repo_lint.cli.RustRunner")
    def test_runners_skip_when_no_files(
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
        with patch("tools.repo_lint.cli.report_results", return_value=ExitCode.SUCCESS):
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

    @patch("tools.repo_lint.cli.PythonRunner")
    @patch("tools.repo_lint.cli.BashRunner")
    @patch("tools.repo_lint.cli.PowerShellRunner")
    @patch("tools.repo_lint.cli.PerlRunner")
    @patch("tools.repo_lint.cli.YAMLRunner")
    @patch("tools.repo_lint.cli.RustRunner")
    def test_no_files_for_only_language_returns_error(
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
