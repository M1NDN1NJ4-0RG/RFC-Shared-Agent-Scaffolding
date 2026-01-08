#!/usr/bin/env python3
# pylint: disable=wrong-import-position  # Test file needs special setup
"""Unit tests for TOML runner (Taplo).

:Purpose:
    Validates that the TOML runner correctly integrates with Taplo.

:Test Coverage:
    - has_files() detects TOML files (.toml extension)
    - check_tools() detects missing Taplo
    - _run_taplo() runs with correct arguments
    - _run_taplo() uses `taplo fmt` in fix mode (not --check)
    - _run_taplo() uses `taplo fmt --check` in check mode
    - _parse_taplo_output() correctly parses violation format
    - _extract_file_path_from_taplo_error() helper method edge cases
    - Empty file lists are handled correctly
    - Both check() and fix() modes work correctly

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_toml_runner.py
        # or
        python3 tools/repo_lint/tests/test_toml_runner.py

:Environment Variables:
    None. Tests are self-contained with mocked subprocess calls.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_toml_runner.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_toml_runner.py::TestTomlRunner \
            ::test_parse_taplo_output -v

:Notes:
    - Tests use unittest.mock to avoid executing actual linters
    - Tests verify command-line arguments passed to subprocess
    - Tests verify output parsing handles the correct format
    - Includes dedicated unit tests for _extract_file_path_from_taplo_error() helper
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.runners.toml_runner import (  # noqa: E402
    TomlRunner,  # noqa: E402
)  # noqa: E402


class TestTomlRunner(unittest.TestCase):
    """Test TOML runner behavior.

    :Purpose:
        Validates Taplo integration.
    """

    # pylint: disable=protected-access

    def setUp(self):
        """Set up test fixtures.

        :Purpose:
            Create TomlRunner instance with actual repo root.
        """
        # Use the actual repo root for tests to avoid subprocess issues
        repo_root_path = Path(__file__).parent.parent.parent.parent
        self.runner = TomlRunner(repo_root=repo_root_path)

    @patch("tools.repo_lint.runners.toml_runner.subprocess.run")
    def test_has_files_detects_toml(self, mock_run):
        """Test that has_files detects .toml files.

        :Purpose:
            Verify TOML file detection for .toml extension.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="pyproject.toml\ntaplo.toml\n", stderr="")

        self.assertTrue(self.runner.has_files())

    @patch("tools.repo_lint.runners.toml_runner.subprocess.run")
    def test_has_files_returns_false_when_no_files(self, mock_run):
        """Test that has_files returns False when no TOML files exist.

        :Purpose:
            Verify correct behavior when repository has no TOML files.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        self.assertFalse(self.runner.has_files())

    @patch("tools.repo_lint.runners.toml_runner.command_exists")
    def test_check_tools_detects_missing_tool(self, mock_command_exists):
        """Test that check_tools detects missing Taplo.

        :Purpose:
            Verify tool detection when Taplo is not installed.

        :param mock_command_exists: Mocked command_exists function
        """
        mock_command_exists.return_value = False

        missing_tools = self.runner.check_tools()

        self.assertEqual(missing_tools, ["taplo"])

    @patch("tools.repo_lint.runners.toml_runner.command_exists")
    def test_check_tools_returns_empty_when_installed(self, mock_command_exists):
        """Test that check_tools returns empty list when tool is installed.

        :Purpose:
            Verify correct behavior when Taplo is available.

        :param mock_command_exists: Mocked command_exists function
        """
        mock_command_exists.return_value = True

        missing_tools = self.runner.check_tools()

        self.assertEqual(missing_tools, [])

    @patch("tools.repo_lint.runners.toml_runner.subprocess.run")
    def test_run_taplo_with_config_file(self, mock_run):
        """Test that _run_taplo uses config file when present.

        :Purpose:
            Verify that taplo.toml is passed to the command.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="pyproject.toml\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # taplo
        ]

        self.runner._run_taplo()

        # Verify subprocess was called twice (git + taplo)
        self.assertEqual(mock_run.call_count, 2)
        # Check taplo call (second call)
        taplo_args = mock_run.call_args_list[1][0][0]
        self.assertIn("taplo", taplo_args)
        self.assertIn("--config", taplo_args)

    @patch("tools.repo_lint.runners.toml_runner.subprocess.run")
    def test_run_taplo_fix_mode(self, mock_run):
        """Test that _run_taplo uses `taplo fmt` (without --check) in fix mode.

        :Purpose:
            Verify that fix mode does NOT use --check flag.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="pyproject.toml\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # taplo
        ]

        self.runner._run_taplo(fix=True)

        # Verify subprocess was called with `taplo fmt` (no --check)
        taplo_args = mock_run.call_args_list[1][0][0]
        self.assertIn("taplo", taplo_args)
        self.assertIn("fmt", taplo_args)
        self.assertNotIn("--check", taplo_args)

    @patch("tools.repo_lint.runners.toml_runner.subprocess.run")
    def test_run_taplo_check_mode_uses_check_flag(self, mock_run):
        """Test that _run_taplo uses `taplo fmt --check` in check mode.

        :Purpose:
            Verify that check mode adds --check flag.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="pyproject.toml\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # taplo
        ]

        self.runner._run_taplo(fix=False)

        # Verify subprocess was called with --check flag
        taplo_args = mock_run.call_args_list[1][0][0]
        self.assertIn("taplo", taplo_args)
        self.assertIn("fmt", taplo_args)
        self.assertIn("--check", taplo_args)

    def test_parse_taplo_output_single_violation(self):
        """Test parsing a single violation from Taplo output.

        :Purpose:
            Verify correct parsing of standard violation format.
        """
        stderr = 'ERROR taplo:format_files: the file is not properly formatted path="pyproject.toml"'

        violations = self.runner._parse_taplo_output("", stderr, ["pyproject.toml"])

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].file, "pyproject.toml")
        self.assertIn("not properly formatted", violations[0].message)

    def test_parse_taplo_output_multiple_violations(self):
        """Test parsing multiple violations from Taplo output.

        :Purpose:
            Verify correct parsing of multiple violations.
        """
        stderr = """ERROR taplo:format_files: the file is not properly formatted path="pyproject.toml"
ERROR taplo:format_files: the file is not properly formatted path="taplo.toml"
ERROR taplo:format_files: the file is not properly formatted path="config/settings.toml"
"""

        violations = self.runner._parse_taplo_output(
            "", stderr, ["pyproject.toml", "taplo.toml", "config/settings.toml"]
        )

        self.assertEqual(len(violations), 3)
        self.assertEqual(violations[0].file, "pyproject.toml")
        self.assertEqual(violations[1].file, "taplo.toml")
        self.assertEqual(violations[2].file, "config/settings.toml")

    def test_parse_taplo_output_skips_info_lines(self):
        """Test that INFO/WARN lines are skipped during parsing.

        :Purpose:
            Verify that info/warning lines don't create violations.
        """
        output = """INFO taplo: Starting validation
WARN taplo: Config file not found
ERROR taplo:format_files: the file is not properly formatted path="pyproject.toml"
ERROR operation failed
"""

        violations = self.runner._parse_taplo_output(output, "", ["pyproject.toml"])

        # Should only have 1 violation (the actual error), not 4
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].file, "pyproject.toml")

    def test_parse_taplo_output_handles_stderr(self):
        """Test that stderr output is parsed for violations.

        :Purpose:
            Verify that violations in stderr are captured.
        """
        stdout = ""
        stderr = 'ERROR taplo:format_files: the file is not properly formatted path="pyproject.toml"'

        violations = self.runner._parse_taplo_output(stdout, stderr, ["pyproject.toml"])

        self.assertEqual(len(violations), 1)

    def test_parse_taplo_output_empty_output(self):
        """Test parsing empty output (no violations).

        :Purpose:
            Verify correct handling of empty output.
        """
        violations = self.runner._parse_taplo_output("", "", [])

        self.assertEqual(len(violations), 0)

    def test_extract_file_path_quoted_path(self):
        """Test extracting file path with quotes.

        :Purpose:
            Verify extraction of quoted path from Taplo error line.
        """
        line = 'ERROR taplo:format_files: the file is not properly formatted path="pyproject.toml"'

        result = self.runner._extract_file_path_from_taplo_error(line)

        self.assertEqual(result, "pyproject.toml")

    def test_extract_file_path_unquoted_path(self):
        """Test extracting file path without quotes.

        :Purpose:
            Verify extraction of unquoted path from Taplo error line.
        """
        line = "ERROR taplo:format_files: the file is not properly formatted path=pyproject.toml other=data"

        result = self.runner._extract_file_path_from_taplo_error(line)

        self.assertEqual(result, "pyproject.toml")

    def test_extract_file_path_with_leading_dot_slash(self):
        """Test extracting file path with ./ prefix.

        :Purpose:
            Verify that ./ prefix is normalized away.
        """
        line = 'ERROR taplo:format_files: the file is not properly formatted path="./pyproject.toml"'

        result = self.runner._extract_file_path_from_taplo_error(line)

        self.assertEqual(result, "pyproject.toml")

    def test_extract_file_path_missing_path_attribute(self):
        """Test extracting file path when path= is missing.

        :Purpose:
            Verify None is returned when path attribute is not found.
        """
        line = "ERROR taplo:format_files: the file is not properly formatted"

        result = self.runner._extract_file_path_from_taplo_error(line)

        self.assertIsNone(result)

    def test_extract_file_path_malformed_input(self):
        """Test extracting file path from malformed input.

        :Purpose:
            Verify None is returned for malformed input that causes parsing errors.
        """
        line = "path="  # Edge case: path= at end with no value

        result = self.runner._extract_file_path_from_taplo_error(line)

        self.assertEqual(result, "")  # Empty string is returned, not None

    def test_extract_file_path_quoted_path_no_closing_quote(self):
        """Test extracting file path with opening quote but no closing quote.

        :Purpose:
            Verify graceful handling when closing quote is missing.
        """
        line = 'ERROR taplo:format_files: path="pyproject.toml'

        result = self.runner._extract_file_path_from_taplo_error(line)

        self.assertEqual(result, "pyproject.toml")

    def test_extract_file_path_nested_directory(self):
        """Test extracting file path with nested directory structure.

        :Purpose:
            Verify paths with directories are extracted correctly.
        """
        line = 'ERROR taplo:format_files: the file is not properly formatted path="config/settings.toml"'

        result = self.runner._extract_file_path_from_taplo_error(line)

        self.assertEqual(result, "config/settings.toml")

    @patch("tools.repo_lint.runners.toml_runner.subprocess.run")
    def test_run_taplo_empty_file_list(self, mock_run):
        """Test that empty file list returns success.

        :Purpose:
            Verify correct behavior when no TOML files exist.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = self.runner._run_taplo()

        self.assertTrue(result.passed)
        self.assertEqual(len(result.violations), 0)

    @patch("tools.repo_lint.runners.toml_runner.subprocess.run")
    @patch("tools.repo_lint.runners.toml_runner.command_exists")
    def test_check_returns_violations(self, mock_command_exists, mock_run):
        """Test that check() returns violations when linting fails.

        :Purpose:
            Verify check() integrates correctly with _run_taplo().

        :param mock_command_exists: Mocked command_exists function
        :param mock_run: Mocked subprocess.run
        """
        mock_command_exists.return_value = True
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="pyproject.toml\n", stderr=""),  # git ls-files
            MagicMock(
                returncode=1,
                stdout="",
                stderr='ERROR taplo:format_files: the file is not properly formatted path="pyproject.toml"',
            ),  # taplo
        ]

        results = self.runner.check()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)
        self.assertEqual(len(results[0].violations), 1)

    @patch("tools.repo_lint.runners.toml_runner.subprocess.run")
    @patch("tools.repo_lint.runners.toml_runner.command_exists")
    def test_fix_applies_fixes(self, mock_command_exists, mock_run):
        """Test that fix() calls _run_taplo with fix=True.

        :Purpose:
            Verify fix() passes the correct flag.

        :param mock_command_exists: Mocked command_exists function
        :param mock_run: Mocked subprocess.run
        """
        mock_command_exists.return_value = True
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="pyproject.toml\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # taplo
        ]

        results = self.runner.fix()

        # Verify --check flag was NOT used (fix mode)
        taplo_args = mock_run.call_args_list[1][0][0]
        self.assertNotIn("--check", taplo_args)
        self.assertIn("fmt", taplo_args)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
