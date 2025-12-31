#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup
"""Unit tests for deterministic output format.

:Purpose:
    Validates Phase 2.5 Rich UI output format stability:
    - Rich table output format is stable and deterministic
    - Violation reporting format is consistent (Rich tables and panels)
    - Summary format is consistent (Rich panels)
    - CI mode output is deterministic

:Test Coverage:
    - report_results() produces deterministic output for violations
    - report_results() produces deterministic summary format
    - Violation objects have stable string representation
    - Summary counts are accurate
    - Output does not include unstable fields (timestamps, random data)
    - CI mode ensures deterministic rendering

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_output_format.py
        # or
        python3 tools/repo_lint/tests/test_output_format.py

:Environment Variables:
    None. Tests are self-contained with fixtures.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_output_format.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_output_format.py::TestOutputFormat::test_violation_format_stable -v

:Notes:
    - Tests use fixtures to ensure deterministic output
    - Tests verify output format stability over time
    - Tests ensure no random/unstable data in output
    - Tests use CI mode to ensure deterministic Rich table rendering
    - Updated for Phase 2.5 Rich UI migration
"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.common import LintResult, Violation  # noqa: E402
from tools.repo_lint.reporting import report_results  # noqa: E402


class TestOutputFormat(unittest.TestCase):
    """Test output format stability for Phase 2.5 Rich UI.

    :Purpose:
        Validates deterministic Rich table/panel output format for violations and summaries.
        Tests use CI mode to ensure deterministic rendering without terminal-specific formatting.
    """

    def setUp(self):
        """Set up test fixtures.

        :Purpose:
            Create fixture violations and results for testing.
        """
        # Create fixture violations
        self.violation1 = Violation(
            tool="ruff",
            file="test.py",
            line=10,
            message="Line too long (85 > 120 characters)",
        )
        self.violation2 = Violation(
            tool="pylint",
            file="test.py",
            line=20,
            message="Missing function docstring",
        )
        self.violation3 = Violation(
            tool="shellcheck",
            file="test.sh",
            line=5,
            message="Quote to prevent word splitting",
        )

    def test_violation_format_stable(self):
        """Test that Violation string representation is stable.

        :Purpose:
            Verify format_violation() produces deterministic output.
        """
        from tools.repo_lint.reporting import format_violation

        # Test violation with line
        v1_str = format_violation(self.violation1)
        expected1 = "test.py:10: [ruff] Line too long (85 > 120 characters)"
        self.assertEqual(v1_str, expected1, "Violation format should be deterministic")

        # Test violation without line
        v2_nolink = Violation(tool="pylint", file="test.py", line=None, message="Module docstring missing")
        v2_str = format_violation(v2_nolink)
        expected2 = "test.py: [pylint] Module docstring missing"
        self.assertEqual(v2_str, expected2, "Violation format without line should be deterministic")

    def test_no_violations_output(self):
        """Test output format when no violations found.

        :Purpose:
            Verify report_results() produces deterministic output for success case.
        """
        # Capture output
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = report_results([], verbose=False, ci_mode=True)

        # Verify exit code
        self.assertEqual(exit_code, 0)  # SUCCESS

        # Verify output - Rich table format with Summary section
        output_text = output.getvalue()
        self.assertIn("Summary", output_text)
        self.assertIn("Exit Code: 0 (SUCCESS)", output_text)

    def test_violations_output_format(self):
        """Test output format when violations found.

        :Purpose:
            Verify report_results() produces deterministic output for violations.
        """
        # Create results with violations
        results = [
            LintResult(tool="ruff", passed=False, violations=[self.violation1]),
            LintResult(tool="pylint", passed=False, violations=[self.violation2]),
        ]

        # Capture output
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = report_results(results, verbose=False, ci_mode=True)

        # Verify exit code
        self.assertEqual(exit_code, 1)  # VIOLATIONS

        # Verify output contains violations in Rich table format
        output_text = output.getvalue()
        # Check for Rich table headers and data
        self.assertIn("test.py", output_text)
        self.assertIn("10", output_text)  # Line number
        self.assertIn("Line too long", output_text)
        self.assertIn("20", output_text)  # Line number  
        self.assertIn("Missing function docstring", output_text)
        # Check summary section
        self.assertIn("Total Violations: 2", output_text)

    def test_summary_count_accuracy(self):
        """Test that summary counts violations accurately.

        :Purpose:
            Verify report_results() counts violations correctly.
        """
        # Create results with multiple violations
        results = [
            LintResult(tool="ruff", passed=False, violations=[self.violation1]),
            LintResult(tool="pylint", passed=False, violations=[self.violation2]),
            LintResult(tool="shellcheck", passed=False, violations=[self.violation3]),
        ]

        # Capture output
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = report_results(results, verbose=False, ci_mode=True)

        # Verify exit code
        self.assertEqual(exit_code, 1)  # VIOLATIONS

        # Verify count in Rich table Summary section
        output_text = output.getvalue()
        self.assertIn("Total Violations: 3", output_text)

    def test_verbose_output_includes_passed(self):
        """Test that verbose mode includes passed checks.

        :Purpose:
            Verify report_results() includes passed checks in verbose mode.
        """
        # Create results with passed and failed
        results = [
            LintResult(tool="black", passed=True, violations=[]),
            LintResult(tool="ruff", passed=False, violations=[self.violation1]),
        ]

        # Capture output in verbose mode
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = report_results(results, verbose=True, ci_mode=True)

        # Verify exit code
        self.assertEqual(exit_code, 1)  # VIOLATIONS

        # Verify both passed and failed are shown in Rich table
        output_text = output.getvalue()
        # Both tools should appear in the results table
        self.assertIn("black", output_text.lower())
        self.assertIn("ruff", output_text.lower())

    def test_output_contains_no_unstable_fields(self):
        """Test that output contains no timestamps or random data.

        :Purpose:
            Verify report_results() output is deterministic without timestamps.
        """
        # Create results
        results = [
            LintResult(tool="ruff", passed=False, violations=[self.violation1]),
        ]

        # Capture output twice with CI mode for stability
        output1 = io.StringIO()
        output2 = io.StringIO()

        with redirect_stdout(output1):
            report_results(results, verbose=False, ci_mode=True)

        with redirect_stdout(output2):
            report_results(results, verbose=False, ci_mode=True)

        # Verify outputs are identical (deterministic)
        # Note: Rich table rendering should be deterministic in CI mode
        self.assertEqual(output1.getvalue(), output2.getvalue(), "Output should be deterministic")

    def test_multiple_violations_same_file(self):
        """Test output format for multiple violations in same file.

        :Purpose:
            Verify grouped violations are formatted consistently.
        """
        # Create multiple violations in same file
        v1 = Violation(tool="ruff", file="test.py", line=10, message="Line too long")
        v2 = Violation(tool="ruff", file="test.py", line=20, message="Trailing whitespace")

        results = [
            LintResult(tool="ruff", passed=False, violations=[v1, v2]),
        ]

        # Capture output
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = report_results(results, verbose=False, ci_mode=True)

        # Verify exit code
        self.assertEqual(exit_code, 1)  # VIOLATIONS

        # Verify both violations are shown in Rich table
        output_text = output.getvalue()
        self.assertIn("test.py", output_text)
        self.assertIn("10", output_text)  # Line number
        self.assertIn("20", output_text)  # Line number
        self.assertIn("Total Violations: 2", output_text)


if __name__ == "__main__":
    unittest.main()
