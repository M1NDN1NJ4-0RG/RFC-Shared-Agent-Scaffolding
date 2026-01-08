#!/usr/bin/env python3
# pylint: disable=wrong-import-position  # Test file needs special setup
"""Unit tests for Rust docstring validator.

:Purpose:
    Validates that the Rust docstring validator correctly enforces
    docstring contracts for Rust module documentation.

:Test Coverage:
    - Module documentation validation (//! comments)
    - Required sections (Purpose, Examples)
    - Exit Behavior/Exit Codes for main.rs
    - Missing documentation detection

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_rust_validator.py
        # or
        python3 tools/repo_lint/tests/test_rust_validator.py

:Environment Variables:
    None. Tests are self-contained.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_rust_validator.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_rust_validator.py::TestRustValidator \
            ::test_valid_module_docs -v

:Notes:
    - Tests use real docstring validation logic (no mocking of validators)
    - Tests verify exact error messages and missing sections
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.docstrings.rust_validator import (  # noqa: E402
    RustValidator,  # noqa: E402
)  # noqa: E402


class TestRustValidator(unittest.TestCase):
    """Test Rust docstring validator behavior.

    :Purpose:
        Validates Rust docstring contract enforcement.
    """

    def test_valid_module_docs(self):
        """Test that valid module documentation passes validation.

        :Purpose:
            Verify complete module docs with all required sections pass.
        """
        content = """//! Test module
//!
//! # Purpose
//!
//! This module provides test functionality.
//!
//! # Examples
//!
//! ```rust
//! use test_module;
//! ```

pub fn test_function() {}
"""
        errors = RustValidator.validate(Path("lib.rs"), content)
        self.assertEqual(len(errors), 0, f"Expected no errors, got: {errors}")

    def test_missing_module_docs(self):
        """Test that missing module documentation is detected.

        :Purpose:
            Verify files without //! comments are flagged.
        """
        content = """/// Regular doc comment
pub fn test_function() {}
"""
        errors = RustValidator.validate(Path("lib.rs"), content)
        self.assertEqual(len(errors), 1)
        self.assertIn("module documentation (//!)", errors[0].missing_sections)

    def test_missing_purpose_section(self):
        """Test that missing Purpose section is detected.

        :Purpose:
            Verify module docs without Purpose are flagged.
        """
        content = """//! Test module
//!
//! # Examples
//!
//! ```rust
//! use test_module;
//! ```

pub fn test_function() {}
"""
        errors = RustValidator.validate(Path("lib.rs"), content)
        self.assertEqual(len(errors), 1)
        self.assertIn("# Purpose", errors[0].missing_sections)

    def test_missing_examples_section(self):
        """Test that missing Examples section is detected.

        :Purpose:
            Verify module docs without Examples are flagged.
        """
        content = """//! Test module
//!
//! # Purpose
//!
//! This module provides test functionality.

pub fn test_function() {}
"""
        errors = RustValidator.validate(Path("lib.rs"), content)
        self.assertEqual(len(errors), 1)
        self.assertIn("# Examples", errors[0].missing_sections)

    def test_main_rs_requires_exit_section(self):
        """Test that main.rs requires Exit Behavior or Exit Codes.

        :Purpose:
            Verify main.rs files must document exit behavior.
        """
        content = """//! Main binary
//!
//! # Purpose
//!
//! This is the main entry point.
//!
//! # Examples
//!
//! ```bash
//! cargo run
//! ```

fn main() {}
"""
        errors = RustValidator.validate(Path("main.rs"), content)
        # Should have 1 error for missing Exit Behavior/Exit Codes
        self.assertEqual(len(errors), 1)
        self.assertIn("# Exit Behavior or # Exit Codes", errors[0].missing_sections)

    def test_main_rs_with_exit_behavior(self):
        """Test that main.rs with Exit Behavior passes.

        :Purpose:
            Verify main.rs with proper exit documentation passes.
        """
        content = """//! Main binary
//!
//! # Purpose
//!
//! This is the main entry point.
//!
//! # Exit Behavior
//!
//! - 0: Success
//! - 1: Failure
//!
//! # Examples
//!
//! ```bash
//! cargo run
//! ```

fn main() {}
"""
        errors = RustValidator.validate(Path("main.rs"), content)
        self.assertEqual(len(errors), 0, f"Expected no errors, got: {errors}")


if __name__ == "__main__":
    unittest.main()
