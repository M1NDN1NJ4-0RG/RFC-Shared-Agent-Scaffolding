"""Tests for unsafe fix mode.

:Purpose:
    Tests unsafe fix mode guards, forensics, and fixer functionality.

:Test Coverage:
    - Guard rails (--unsafe without --yes-i-know fails)
    - CI detection blocks unsafe mode
    - Patch and log generation
    - Unsafe fixer execution on test fixtures
    - Deterministic output

:Authorization:
    These tests are authorized to run unsafe mode ONLY within PR #148
    and ONLY against purpose-built test fixtures in temporary workspaces.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.repo_lint.cli import cmd_fix, create_parser


class TestUnsafeFixGuardRails(unittest.TestCase):
    """Test guard rails for unsafe fix mode."""

    def test_unsafe_without_yes_i_know_fails(self):
        """Test that --unsafe without --yes-i-know fails with exit code 2."""
        parser = create_parser()
        args = parser.parse_args(["fix", "--unsafe"])

        exit_code = cmd_fix(args)

        self.assertEqual(exit_code, 2, "Should fail with MISSING_TOOLS exit code (2)")

    def test_unsafe_with_yes_i_know_in_ci_fails(self):
        """Test that unsafe mode fails in CI environment."""
        parser = create_parser()
        args = parser.parse_args(["fix", "--unsafe", "--yes-i-know", "--ci"])

        exit_code = cmd_fix(args)

        self.assertEqual(exit_code, 2, "Should fail with MISSING_TOOLS exit code (2) in CI mode")

    def test_unsafe_with_ci_env_var_fails(self):
        """Test that unsafe mode fails when CI environment variable is set."""
        # Save original CI env var
        original_ci = os.environ.get("CI")

        try:
            # Set CI env var
            os.environ["CI"] = "true"

            parser = create_parser()
            args = parser.parse_args(["fix", "--unsafe", "--yes-i-know"])

            exit_code = cmd_fix(args)

            self.assertEqual(exit_code, 2, "Should fail with MISSING_TOOLS exit code (2) when CI=true")

        finally:
            # Restore original CI env var
            if original_ci is None:
                os.environ.pop("CI", None)
            else:
                os.environ["CI"] = original_ci

    def test_safe_fix_mode_works_normally(self):
        """Test that normal fix mode (without --unsafe) still works."""
        parser = create_parser()
        args = parser.parse_args(["fix"])

        # This should not crash - we're just testing the guard logic doesn't break normal mode
        # The actual exit code will depend on repo state, so we don't assert on it
        exit_code = cmd_fix(args)

        # Exit code should be 0, 1, 2, or 3 (valid exit codes)
        self.assertIn(exit_code, [0, 1, 2, 3], "Should return a valid exit code")


class TestUnsafeFixForensics(unittest.TestCase):
    """Test forensics generation for unsafe fix mode."""

    def setUp(self):
        """Set up temporary workspace for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()

    def tearDown(self):
        """Clean up temporary workspace."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_patch_and_log_generated(self):
        """Test that patch and log files are generated when unsafe mode runs.

        AUTHORIZED: PR #148 only, purpose-built fixture in temporary workspace.
        """
        # Copy fixture to temp workspace
        fixture_src = Path("conformance/repo-lint/unsafe-fix-fixtures/python/google_style_docstrings.py")
        if not fixture_src.exists():
            self.skipTest("Fixture not available")

        fixture_dest = self.temp_dir / "test_file.py"
        shutil.copy(fixture_src, fixture_dest)

        # Change to temp directory (so unsafe fix runs there)
        os.chdir(self.temp_dir)

        # Create minimal conformance directory structure for policy
        conformance_dir = self.temp_dir / "conformance" / "repo-lint"
        conformance_dir.mkdir(parents=True)
        policy_file = conformance_dir / "autofix-policy.json"
        policy_file.write_text('{"version": "1.0", "categories": {"safe-formatter": {"allowed": true}}}')

        # Run unsafe fix mode (AUTHORIZED for PR #148)
        parser = create_parser()
        args = parser.parse_args(["fix", "--unsafe", "--yes-i-know"])

        # Note: This may fail due to missing tools, but we're testing forensics generation
        cmd_fix(args)

        # Check that logs directory was created
        logs_dir = self.temp_dir / "logs" / "unsafe-fixes"
        self.assertTrue(logs_dir.exists(), "logs/unsafe-fixes directory should be created")

        # Check that at least one patch and log file exist
        patch_files = list(logs_dir.glob("*.patch"))
        log_files = list(logs_dir.glob("*.log"))

        self.assertGreater(len(patch_files), 0, "At least one patch file should be generated")
        self.assertGreater(len(log_files), 0, "At least one log file should be generated")

    def test_log_contains_required_fields(self):
        """Test that log file contains all required fields.

        AUTHORIZED: PR #148 only, purpose-built fixture in temporary workspace.
        """
        # Copy fixture to temp workspace
        fixture_src = Path("conformance/repo-lint/unsafe-fix-fixtures/python/google_style_docstrings.py")
        if not fixture_src.exists():
            self.skipTest("Fixture not available")

        fixture_dest = self.temp_dir / "test_file.py"
        shutil.copy(fixture_src, fixture_dest)

        # Change to temp directory
        os.chdir(self.temp_dir)

        # Create minimal policy
        conformance_dir = self.temp_dir / "conformance" / "repo-lint"
        conformance_dir.mkdir(parents=True)
        policy_file = conformance_dir / "autofix-policy.json"
        policy_file.write_text('{"version": "1.0", "categories": {"safe-formatter": {"allowed": true}}}')

        # Run unsafe fix mode (AUTHORIZED for PR #148)
        parser = create_parser()
        args = parser.parse_args(["fix", "--unsafe", "--yes-i-know"])
        cmd_fix(args)

        # Read the log file
        logs_dir = self.temp_dir / "logs" / "unsafe-fixes"
        log_files = list(logs_dir.glob("*.log"))

        if log_files:
            log_content = log_files[0].read_text()

            # Check for required fields
            self.assertIn("# Unsafe Fix Execution Log", log_content, "Should have header")
            self.assertIn("# Start:", log_content, "Should have start timestamp")
            self.assertIn("# End:", log_content, "Should have end timestamp")
            self.assertIn("# Duration:", log_content, "Should have duration")

            # Should mention safety
            self.assertIn("DANGER", log_content, "Should have danger warning")


class TestUnsafeDocstringRewriter(unittest.TestCase):
    """Test the unsafe docstring rewriter fixer."""

    def setUp(self):
        """Set up temporary workspace."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up temporary workspace."""
        shutil.rmtree(self.temp_dir)

    def test_converts_google_style_to_sphinx(self):
        """Test that Google-style docstrings are converted to Sphinx format.

        AUTHORIZED: PR #148 only, purpose-built fixture in temporary workspace.
        """
        from tools.repo_lint.unsafe_fixers import UnsafeDocstringRewriter

        # Create test file with Google-style docstring
        test_file = self.temp_dir / "test.py"
        test_file.write_text(
            '''
def example(name, count):
    """Example function.

    Args:
        name: The name parameter
        count (int): The count parameter

    Returns:
        A formatted string
    """
    return f"{name}: {count}"
'''
        )

        # Apply fixer (AUTHORIZED for PR #148)
        fixer = UnsafeDocstringRewriter()
        result = fixer.fix(test_file)

        # Check that changes were made
        self.assertIsNotNone(result, "Fixer should have made changes")
        self.assertIn("unsafe_docstring_rewrite", result.fixer_name)

        # Check that output uses Sphinx format
        output = test_file.read_text()
        self.assertIn(":param name:", output, "Should convert to :param:")
        self.assertIn(":param count:", output, "Should convert to :param:")
        self.assertIn(":returns:", output, "Should convert to :returns:")

        # Should not contain Google-style markers
        self.assertNotIn("Args:", output, "Should remove Args: section")
        self.assertNotIn("Returns:", output, "Should remove Returns: section")

    def test_no_changes_for_conformant_file(self):
        """Test that conformant files are not modified."""
        from tools.repo_lint.unsafe_fixers import UnsafeDocstringRewriter

        # Create test file with Sphinx-style docstring (already conformant)
        test_file = self.temp_dir / "test.py"
        test_file.write_text(
            '''
def example(name, count):
    """Example function.

    :param name: The name parameter
    :param count: The count parameter
    :returns: A formatted string
    """
    return f"{name}: {count}"
'''
        )

        # Apply fixer
        fixer = UnsafeDocstringRewriter()
        result = fixer.fix(test_file)

        # No changes should be made
        self.assertIsNone(result, "Fixer should not modify conformant files")


if __name__ == "__main__":
    unittest.main()
