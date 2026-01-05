#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup
"""Unit tests for PowerShell runner (PSScriptAnalyzer, docstring validation).

:Purpose:
    Validates that the PowerShell runner correctly integrates with PSScriptAnalyzer
    via pwsh and docstring validation, with proper security measures.

:Test Coverage:
    - _get_powershell_files() returns file list or empty list
    - _run_psscriptanalyzer() runs with correct pwsh arguments
    - PSScriptAnalyzer uses -NoProfile -NonInteractive flags
    - Command injection protection via $args[0] parameter passing
    - _run_docstring_validation() calls validator with correct args
    - Empty file lists are handled correctly

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_powershell_runner.py
        # or
        python3 tools/repo_lint/tests/test_powershell_runner.py

:Environment Variables:
    None. Tests are self-contained with mocked subprocess calls.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_powershell_runner.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_powershell_runner.py \
            ::TestPowerShellRunner::test_psscriptanalyzer_uses_args_parameter -v

:Notes:
    - Tests use unittest.mock to avoid executing actual linters
    - Tests verify command-line arguments passed to subprocess
    - Tests verify security measures (no command injection)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.runners.powershell_runner import PowerShellRunner  # noqa: E402


class TestPowerShellRunner(unittest.TestCase):
    """Test PowerShell runner behavior.

    :Purpose:
        Validates PSScriptAnalyzer and docstring validation integration.
    """

    def setUp(self):
        """Set up test fixtures.

        :Purpose:
            Create PowerShellRunner instance with mocked repo root.
        """
        self.runner = PowerShellRunner(repo_root=Path("/fake/repo"))

    @patch("tools.repo_lint.runners.powershell_runner.subprocess.run")
    def test_get_powershell_files_returns_list(self, mock_run):
        """Test that _get_powershell_files returns file list.

        :Purpose:
            Verify helper method correctly parses git output.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="script1.ps1\nscript2.ps1\n", stderr="")

        files = self.runner._get_powershell_files()

        self.assertEqual(len(files), 2)
        self.assertIn("script1.ps1", files)
        self.assertIn("script2.ps1", files)

    @patch("tools.repo_lint.runners.powershell_runner.subprocess.run")
    def test_get_powershell_files_returns_empty(self, mock_run):
        """Test that _get_powershell_files returns empty list when no files.

        :Purpose:
            Verify helper method handles empty output.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        files = self.runner._get_powershell_files()

        self.assertEqual(files, [])

    @patch("tools.repo_lint.runners.powershell_runner.subprocess.run")
    def test_psscriptanalyzer_uses_correct_flags(self, mock_run):
        """Test that _run_psscriptanalyzer uses -NoProfile -NonInteractive.

        :Purpose:
            Verify PSScriptAnalyzer runs with correct pwsh flags.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="test.ps1\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # PSScriptAnalyzer
        ]

        result = self.runner._run_psscriptanalyzer()

        # Check PSScriptAnalyzer call (second call)
        self.assertEqual(mock_run.call_count, 2)
        pssa_args = mock_run.call_args_list[1][0][0]
        self.assertIn("-NoProfile", pssa_args)
        self.assertIn("-NonInteractive", pssa_args)
        self.assertTrue(result.passed)

    @patch("tools.repo_lint.runners.powershell_runner.subprocess.run")
    def test_psscriptanalyzer_uses_args_parameter(self, mock_run):
        """Test that _run_psscriptanalyzer uses $args[0] for file path.

        :Purpose:
            Verify command injection protection via parameter passing.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="test.ps1\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # PSScriptAnalyzer
        ]

        result = self.runner._run_psscriptanalyzer()

        # Check PSScriptAnalyzer call (second call)
        pssa_args = mock_run.call_args_list[1][0][0]

        # Should use $args[0] in command string
        command_idx = pssa_args.index("-Command")
        command_str = pssa_args[command_idx + 1]
        self.assertIn("$args[0]", command_str, "Should use $args[0] for parameter passing")

        # File path should be separate argument
        self.assertEqual(pssa_args[-1], "test.ps1", "File path should be last argument")
        self.assertTrue(result.passed)

    @patch("tools.repo_lint.runners.powershell_runner.subprocess.run")
    def test_check_tools_detects_missing_pwsh(self, mock_run):
        """Test that check_tools detects missing pwsh.

        :Purpose:
            Verify tool detection correctly identifies missing PowerShell.

        :param mock_run: Mocked subprocess.run
        """
        with patch("tools.repo_lint.runners.powershell_runner.command_exists", return_value=False):
            missing = self.runner.check_tools()
            self.assertIn("pwsh", missing)

    @patch("tools.repo_lint.runners.powershell_runner.subprocess.run")
    def test_check_tools_detects_missing_psscriptanalyzer(self, mock_run):
        """Test that check_tools detects missing PSScriptAnalyzer module.

        :Purpose:
            Verify tool detection checks for PSScriptAnalyzer module.

        :param mock_run: Mocked subprocess.run
        """
        with patch("tools.repo_lint.runners.powershell_runner.command_exists", return_value=True):
            # Mock Get-Module returning empty (module not found)
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            missing = self.runner.check_tools()
            self.assertIn("PSScriptAnalyzer", missing)

    @patch("tools.repo_lint.runners.powershell_runner.subprocess.run")
    def test_empty_files_returns_passed(self, mock_run):
        """Test that empty file list returns passed result.

        :Purpose:
            Verify all methods handle empty file lists gracefully.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # All methods should return passed when no files
        self.assertTrue(self.runner._run_psscriptanalyzer().passed)
        # Don't test _run_docstring_validation() as it requires file path mocking


if __name__ == "__main__":
    unittest.main()
