#!/usr/bin/env python3
"""Unit tests for Markdown runner (markdownlint-cli2).

:Purpose:
    Validates that the Markdown runner correctly integrates with markdownlint-cli2.

:Test Coverage:
    - has_files() detects Markdown files (.md extension)
    - check_tools() detects missing markdownlint-cli2
    - _run_markdownlint() runs with correct arguments
    - _run_markdownlint() passes --fix flag in fix mode
    - _parse_markdownlint_output() correctly parses violation format
    - Empty file lists are handled correctly
    - Both check() and fix() modes work correctly

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_markdown_runner.py
        # or
        python3 tools/repo_lint/tests/test_markdown_runner.py

:Environment Variables:
    None. Tests are self-contained with mocked subprocess calls.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_markdown_runner.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_markdown_runner.py::TestMarkdownRunner \
            ::test_parse_markdownlint_output -v

:Notes:
    - Tests use unittest.mock to avoid executing actual linters
    - Tests verify command-line arguments passed to subprocess
    - Tests verify output parsing handles the correct format
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.runners.markdown_runner import (
    MarkdownRunner,
)  # noqa: E402  # pylint: disable=wrong-import-position


class TestMarkdownRunner(unittest.TestCase):
    """Test Markdown runner behavior.

    :Purpose:
        Validates markdownlint-cli2 integration.
    """

    # pylint: disable=protected-access

    def setUp(self):
        """Set up test fixtures.

        :Purpose:
            Create MarkdownRunner instance with actual repo root.
        """
        # Use the actual repo root for tests to avoid subprocess issues
        repo_root_path = Path(__file__).parent.parent.parent.parent
        self.runner = MarkdownRunner(repo_root=repo_root_path)

    @patch("tools.repo_lint.runners.markdown_runner.subprocess.run")
    def test_has_files_detects_md(self, mock_run):
        """Test that has_files detects .md files.

        :Purpose:
            Verify Markdown file detection for .md extension.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="README.md\ndocs/guide.md\n", stderr="")

        self.assertTrue(self.runner.has_files())

    @patch("tools.repo_lint.runners.markdown_runner.subprocess.run")
    def test_has_files_returns_false_when_no_files(self, mock_run):
        """Test that has_files returns False when no Markdown files exist.

        :Purpose:
            Verify correct behavior when repository has no Markdown files.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        self.assertFalse(self.runner.has_files())

    @patch("tools.repo_lint.runners.markdown_runner.command_exists")
    def test_check_tools_detects_missing_tool(self, mock_command_exists):
        """Test that check_tools detects missing markdownlint-cli2.

        :Purpose:
            Verify tool detection when markdownlint-cli2 is not installed.

        :param mock_command_exists: Mocked command_exists function
        """
        mock_command_exists.return_value = False

        missing_tools = self.runner.check_tools()

        self.assertEqual(missing_tools, ["markdownlint-cli2"])

    @patch("tools.repo_lint.runners.markdown_runner.command_exists")
    def test_check_tools_returns_empty_when_installed(self, mock_command_exists):
        """Test that check_tools returns empty list when tool is installed.

        :Purpose:
            Verify correct behavior when markdownlint-cli2 is available.

        :param mock_command_exists: Mocked command_exists function
        """
        mock_command_exists.return_value = True

        missing_tools = self.runner.check_tools()

        self.assertEqual(missing_tools, [])

    @patch("tools.repo_lint.runners.markdown_runner.subprocess.run")
    def test_run_markdownlint_with_config_file(self, mock_run):
        """Test that _run_markdownlint uses config file when present.

        :Purpose:
            Verify that .markdownlint-cli2.jsonc is passed to the command.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="README.md\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # markdownlint-cli2
        ]

        self.runner._run_markdownlint()

        # Verify subprocess was called twice (git + markdownlint-cli2)
        self.assertEqual(mock_run.call_count, 2)
        # Check markdownlint-cli2 call (second call)
        markdownlint_args = mock_run.call_args_list[1][0][0]
        self.assertIn("markdownlint-cli2", markdownlint_args)
        self.assertIn("--config", markdownlint_args)

    @patch("tools.repo_lint.runners.markdown_runner.subprocess.run")
    def test_run_markdownlint_fix_mode(self, mock_run):
        """Test that _run_markdownlint passes --fix flag in fix mode.

        :Purpose:
            Verify that fix mode adds the --fix flag to the command.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="README.md\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # markdownlint-cli2
        ]

        self.runner._run_markdownlint(fix=True)

        # Verify subprocess was called with --fix flag
        markdownlint_args = mock_run.call_args_list[1][0][0]
        self.assertIn("--fix", markdownlint_args)

    @patch("tools.repo_lint.runners.markdown_runner.subprocess.run")
    def test_run_markdownlint_check_mode_no_fix_flag(self, mock_run):
        """Test that _run_markdownlint does not pass --fix in check mode.

        :Purpose:
            Verify that check mode (fix=False) does not add --fix flag.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="README.md\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # markdownlint-cli2
        ]

        self.runner._run_markdownlint(fix=False)

        # Verify subprocess was NOT called with --fix flag
        markdownlint_args = mock_run.call_args_list[1][0][0]
        self.assertNotIn("--fix", markdownlint_args)

    def test_parse_markdownlint_output_single_violation(self):
        """Test parsing a single violation from markdownlint-cli2 output.

        :Purpose:
            Verify correct parsing of standard violation format.
        """
        output = "README.md:7:81 error MD013/line-length Line length [Expected: 120; Actual: 185]"

        violations = self.runner._parse_markdownlint_output(output, "")

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].file, "README.md")
        self.assertEqual(violations[0].line, 7)
        self.assertIn("MD013", violations[0].message)

    def test_parse_markdownlint_output_multiple_violations(self):
        """Test parsing multiple violations from markdownlint-cli2 output.

        :Purpose:
            Verify correct parsing of multiple violations.
        """
        output = """README.md:7:81 error MD013/line-length Line length [Expected: 120; Actual: 185]
docs/guide.md:10:1 error MD022/blanks-around-headings Headings should be surrounded by blank lines
CONTRIBUTING.md:15:5 warning MD040/fenced-code-language Fenced code blocks should have a language"""

        violations = self.runner._parse_markdownlint_output(output, "")

        self.assertEqual(len(violations), 3)
        self.assertEqual(violations[0].file, "README.md")
        self.assertEqual(violations[1].file, "docs/guide.md")
        self.assertEqual(violations[2].file, "CONTRIBUTING.md")

    def test_parse_markdownlint_output_skips_summary_lines(self):
        """Test that summary lines are skipped during parsing.

        :Purpose:
            Verify that header/summary lines don't create violations.
        """
        output = """markdownlint-cli2 v0.20.0 (markdownlint v0.40.0)
Finding: README.md
Linting: 1 file(s)
Summary: 1 error(s)
README.md:7:81 error MD013/line-length Line length"""

        violations = self.runner._parse_markdownlint_output(output, "")

        # Should only have 1 violation (the actual error), not 5
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].file, "README.md")

    def test_parse_markdownlint_output_handles_stderr(self):
        """Test that stderr output is also parsed for violations.

        :Purpose:
            Verify that violations in stderr are captured.
        """
        stdout = "README.md:7:81 error MD013/line-length Line length"
        stderr = "docs/guide.md:10:1 error MD022/blanks-around-headings Headings should be"

        violations = self.runner._parse_markdownlint_output(stdout, stderr)

        self.assertEqual(len(violations), 2)

    def test_parse_markdownlint_output_empty_output(self):
        """Test parsing empty output (no violations).

        :Purpose:
            Verify correct handling of empty output.
        """
        violations = self.runner._parse_markdownlint_output("", "")

        self.assertEqual(len(violations), 0)

    @patch("tools.repo_lint.runners.markdown_runner.subprocess.run")
    def test_run_markdownlint_empty_file_list(self, mock_run):
        """Test that empty file list returns success.

        :Purpose:
            Verify correct behavior when no Markdown files exist.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = self.runner._run_markdownlint()

        self.assertTrue(result.passed)
        self.assertEqual(len(result.violations), 0)

    @patch("tools.repo_lint.runners.markdown_runner.subprocess.run")
    @patch("tools.repo_lint.runners.markdown_runner.command_exists")
    def test_check_returns_violations(self, mock_command_exists, mock_run):
        """Test that check() returns violations when linting fails.

        :Purpose:
            Verify check() integrates correctly with _run_markdownlint().

        :param mock_command_exists: Mocked command_exists function
        :param mock_run: Mocked subprocess.run
        """
        mock_command_exists.return_value = True
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="README.md\n", stderr=""),  # git ls-files
            MagicMock(
                returncode=1,
                stdout="README.md:7:81 error MD013/line-length Line length",
                stderr="",
            ),  # markdownlint-cli2
        ]

        results = self.runner.check()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)
        self.assertEqual(len(results[0].violations), 1)

    @patch("tools.repo_lint.runners.markdown_runner.subprocess.run")
    @patch("tools.repo_lint.runners.markdown_runner.command_exists")
    def test_fix_applies_fixes(self, mock_command_exists, mock_run):
        """Test that fix() calls _run_markdownlint with fix=True.

        :Purpose:
            Verify fix() passes the correct flag.

        :param mock_command_exists: Mocked command_exists function
        :param mock_run: Mocked subprocess.run
        """
        mock_command_exists.return_value = True
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="README.md\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # markdownlint-cli2
        ]

        results = self.runner.fix()

        # Verify --fix flag was used
        markdownlint_args = mock_run.call_args_list[1][0][0]
        self.assertIn("--fix", markdownlint_args)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
