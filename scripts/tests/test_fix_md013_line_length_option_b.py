#!/usr/bin/env python3
# pylint: disable=implicit-str-concat
# fmt: off
"""Unit tests for fix_md013_line_length_option_b.py script.

This module provides comprehensive test coverage for the list-aware MD013 fixer,
ensuring it reflows list items safely while preserving markers and structure.

:Purpose:
    Ensures the script correctly handles all Markdown variants without mangling:
    - Lists (bullets, numbered, task lists, nested) with rewrapping
    - Code blocks (fenced and indented)
    - Tables
    - Blockquotes, headings, link references
    - Inline code and URLs in lists
    - Newline behavior
    - Deterministic output

:Environment Variables:
    None. Tests are self-contained and use temporary files.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest scripts/tests/test_fix_md013_line_length_option_b.py -v

    Run specific test::

        python3 -m pytest scripts/tests/test_fix_md013_line_length_option_b.py::test_bullet_list_wrapping -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module under test
import fix_md013_line_length_option_b as fixer  # pylint: disable=wrong-import-position


class TestOptionB(unittest.TestCase):  # pylint: disable=too-many-public-methods
    """Test suite for fix_md013_line_length_option_b.py."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def _write_and_process(self, content: str) -> str:
        """Write content to temp file, process it, and return result.

        :param content: Markdown content to process
        :returns: Processed content after running the fixer
        """
        test_file = self.temp_path / "test.md"
        test_file.write_text(content, encoding="utf-8")
        fixer._rewrite_file(test_file)  # pylint: disable=protected-access
        return test_file.read_text(encoding="utf-8")

    def test_plain_paragraph_wrapping(self):
        """Plain paragraphs exceeding MAX_LEN should be wrapped."""
        content = (
            "This is a very long line that definitely exceeds the maximum line "
            "length limit of 120 characters and should be wrapped by the script.\n"
        )
        result = self._write_and_process(content)
        lines = result.splitlines()
        # Should be split into multiple lines
        self.assertGreater(len(lines), 1)
        # No line should exceed MAX_LEN
        for line in lines:
            self.assertLessEqual(len(line), 120)

    def test_plain_paragraph_already_compliant(self):
        """Paragraphs already within limit should not be changed."""
        content = "Short line.\nAnother short line.\n"
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_bullet_list_wrapping(self):
        """Long bullet list items should be wrapped while preserving marker."""
        content = (
            "- This is a very long bullet list item that exceeds the maximum "
            "line length and should be wrapped with proper continuation indent\n"
        )
        result = self._write_and_process(content)
        lines = result.splitlines()
        # Should be multiple lines
        self.assertGreater(len(lines), 1)
        # First line should start with bullet marker
        self.assertTrue(lines[0].startswith("- "))
        # Continuation lines should be indented
        if len(lines) > 1:
            self.assertTrue(lines[1].startswith("  "))
        # No line should exceed MAX_LEN
        for line in lines:
            self.assertLessEqual(len(line), 120)

    def test_numbered_list_wrapping(self):
        """Long numbered list items should be wrapped while preserving marker."""
        content = (
            "1. This is a very long numbered list item that exceeds the maximum "
            "line length and should be wrapped with proper continuation indent\n"
        )
        result = self._write_and_process(content)
        lines = result.splitlines()
        # Should be multiple lines
        self.assertGreater(len(lines), 1)
        # First line should start with number marker
        self.assertTrue(lines[0].startswith("1. "))
        # Continuation lines should be indented (3 spaces for "1. ")
        if len(lines) > 1:
            self.assertTrue(lines[1].startswith("   "))

    def test_task_list_wrapping(self):
        """Long task list items should be wrapped while preserving checkbox."""
        content = (
            "- [ ] This is a very long unchecked task item that exceeds the "
            "maximum line length and should be wrapped with checkbox preserved\n"
        )
        result = self._write_and_process(content)
        lines = result.splitlines()
        # Should be multiple lines
        self.assertGreater(len(lines), 1)
        # First line should have checkbox
        self.assertTrue(lines[0].startswith("- [ ] "))
        # Continuation lines should be indented (6 spaces for "- [ ] ")
        if len(lines) > 1:
            self.assertTrue(lines[1].startswith("      "))

    def test_task_list_checked_wrapping(self):
        """Checked task items should preserve [x] checkbox."""
        content = (
            "- [x] This is a very long checked task item that exceeds the "
            "maximum line length and should be wrapped\n"
        )
        result = self._write_and_process(content)
        lines = result.splitlines()
        # Should have [x] checkbox
        self.assertTrue(lines[0].startswith("- [x] "))

    def test_task_list_uppercase_x_wrapping(self):
        """Task items with uppercase X should preserve [X] checkbox."""
        content = (
            "- [X] This is a very long checked task item with uppercase X that " "exceeds the maximum line length\n"
        )
        result = self._write_and_process(content)
        lines = result.splitlines()
        # Should have [X] checkbox
        self.assertTrue(lines[0].startswith("- [X] "))

    def test_short_list_item_unchanged(self):
        """Short list items should not be wrapped."""
        content = "- Short item\n"
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_empty_list_item(self):
        """Empty list items should be preserved."""
        content = "- \n"
        result = self._write_and_process(content)
        self.assertEqual(result.strip(), "-")

    def test_list_with_inline_code_preserved(self):
        """List items with inline code should not be wrapped (safety)."""
        content = (
            "- This is a list item with `inline_code` that is very long and " "exceeds the maximum line length limit\n"
        )
        result = self._write_and_process(content)
        # Should be preserved unchanged due to inline code
        self.assertEqual(result, content)

    def test_list_with_url_preserved(self):
        """List items with URLs should not be wrapped (safety)."""
        content = (
            "- Check out https://example.com/very/long/url for more information "
            "that exceeds the line limit\n"
        )
        result = self._write_and_process(content)
        # Should be preserved unchanged due to URL
        self.assertEqual(result, content)

    def test_list_continuation_with_code_preserved(self):
        """List with continuation containing code should be preserved."""
        content = (
            "- First line\n"
            "  continuation with `code` that is very long and exceeds limit\n"
        )
        result = self._write_and_process(content)
        # Should preserve original due to code in continuation
        self.assertIn("First line", result)
        self.assertIn("`code`", result)

    def test_nested_lists_wrapping(self):
        """Nested lists should wrap correctly with proper indentation."""
        content = (
            "- Top level item\n"
            "  - Nested item that is very long and exceeds the maximum line "
            "length and should be wrapped\n"
        )
        result = self._write_and_process(content)
        # The nested item should be wrapped
        # First line should have the top-level item
        self.assertIn("- Top level item", result)
        # Should have nested marker somewhere
        self.assertIn("- Nested item", result)

    def test_fenced_code_block_backticks_preserved(self):
        """Fenced code blocks with backticks should be preserved byte-identical."""
        content = (
            "```python\n"
            "def very_long_function_name_that_exceeds_line_length("
            "param1, param2, param3):\n"
            "    return param1 + param2 + param3\n"
            "```\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_fenced_code_block_tildes_preserved(self):
        """Fenced code blocks with tildes should be preserved byte-identical."""
        content = (
            "~~~bash\n"
            "echo 'This is a very long command line that exceeds the maximum "
            "line length limit'\n"
            "~~~\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_indented_code_block_preserved(self):
        """Indented code blocks (4 spaces/tab) should be preserved."""
        content = (
            "    def indented_function_with_very_long_name_exceeding_limit():\n"
            "        return 'indented code block'\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_table_preserved(self):
        """Tables (header + separator + rows) should be preserved byte-identical."""
        content = (
            "| Column 1 with very long header text | Column 2 | Column 3 |\n"
            "| ------------------------------------ | -------- | -------- |\n"
            "| Data 1 with very long text exceeding limit | Data 2 | Data 3 |\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_blockquote_preserved(self):
        """Blockquotes should be preserved unchanged."""
        content = (
            "> This is a very long blockquote line that exceeds the maximum "
            "line length but should remain unchanged\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_headings_preserved(self):
        """All heading levels should be preserved unchanged."""
        content = (
            "# This is a very long heading level 1 that exceeds the maximum "
            "line length\n"
            "## Heading 2 with long text exceeding the limit\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_link_reference_definitions_preserved(self):
        """Link reference definitions should be preserved unchanged."""
        content = (
            "[id]: https://example.com/very/long/url/that/exceeds/the/"
            "maximum/line/length/limit\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_html_blocks_preserved(self):
        """HTML blocks should be preserved unchanged."""
        content = (
            "<div class='container' style='width: 100%; "
            "background-color: red;'>Content</div>\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_final_newline_preserved(self):
        """Files ending with newline should preserve it."""
        content = "Short paragraph.\n"
        result = self._write_and_process(content)
        self.assertTrue(result.endswith("\n"))

    def test_no_final_newline_preserved(self):
        """Files without final newline should preserve that."""
        content = "Short paragraph."
        result = self._write_and_process(content)
        self.assertFalse(result.endswith("\n"))

    def test_empty_file(self):
        """Empty files should remain empty."""
        content = ""
        result = self._write_and_process(content)
        self.assertEqual(result, "")

    def test_single_blank_line(self):
        """Single blank line files should be preserved."""
        content = "\n"
        result = self._write_and_process(content)
        self.assertEqual(result, "\n")

    def test_deterministic_output(self):
        """Running script twice should produce identical output."""
        content = (
            "- This is a very long list item that exceeds the maximum line "
            "length and will be wrapped by the script on first run.\n"
        )
        test_file = self.temp_path / "test.md"
        test_file.write_text(content, encoding="utf-8")

        # First run
        fixer._rewrite_file(test_file)  # pylint: disable=protected-access
        first_result = test_file.read_text(encoding="utf-8")

        # Second run
        fixer._rewrite_file(test_file)  # pylint: disable=protected-access
        second_result = test_file.read_text(encoding="utf-8")

        self.assertEqual(first_result, second_result)

    def test_no_list_marker_duplication(self):
        """Ensure list markers are not duplicated (historical bug check)."""
        content = (
            "1. First item with very long text that should not cause marker "
            "duplication when wrapped\n"
        )
        result = self._write_and_process(content)
        # Should not have "1. 1. " or similar
        self.assertNotIn("1. 1. ", result)
        # Should have exactly one "1. " at the start
        self.assertEqual(result.count("1. "), 1)

    def test_no_checkbox_breakage(self):
        """Ensure checkbox syntax is not broken (historical bug check)."""
        content = (
            "- [x] Task with very long description exceeding line limit that "
            "needs wrapping\n"
        )
        result = self._write_and_process(content)
        # Should still have valid checkbox
        self.assertIn("- [x]", result)
        # Should not have broken syntax like "- - [x]" or "[x] [x]"
        self.assertNotIn("- - [x]", result)
        self.assertNotIn("[x] [x]", result)
        # Should have exactly one checkbox
        self.assertEqual(result.count("- [x]"), 1)

    def test_no_list_collapse(self):
        """Ensure multiple list items don't collapse into one (historical bug check)."""
        content = "- First item\n" "- Second item\n" "- Third item\n"
        result = self._write_and_process(content)
        # Should have three separate list items
        self.assertEqual(result.count("- "), 3)

    def test_mixed_list_markers(self):
        """Lists with different markers should all be handled correctly."""
        content = (
            "- Bullet item with very long text that exceeds maximum line length\n"
            "* Asterisk item with very long text that exceeds maximum line length\n"
            "+ Plus item with very long text that exceeds maximum line length\n"
        )
        result = self._write_and_process(content)
        # Each marker type should still be present
        self.assertIn("- ", result)
        self.assertIn("* ", result)
        self.assertIn("+ ", result)

    def test_blank_lines_between_list_items(self):
        """Blank lines between list items should be preserved."""
        content = "- First item\n" "\n" "- Second item\n"
        result = self._write_and_process(content)
        lines = result.splitlines(keepends=True)
        # Should have blank line
        self.assertIn("\n", lines)

    def test_parse_list_prefix(self):
        """Test _parse_list_prefix function directly."""
        # Bullet list
        result = fixer._parse_list_prefix("- Item text")  # pylint: disable=protected-access
        self.assertIsNotNone(result)
        self.assertEqual(result[1], "-")

        # Numbered list
        result = fixer._parse_list_prefix("1. Item text")  # pylint: disable=protected-access
        self.assertIsNotNone(result)
        self.assertEqual(result[1], "1.")

        # Task list
        result = fixer._parse_list_prefix("- [ ] Task text")  # pylint: disable=protected-access
        self.assertIsNotNone(result)
        self.assertEqual(result[2], "[ ] ")

        # Not a list
        result = fixer._parse_list_prefix("Regular text")  # pylint: disable=protected-access
        self.assertIsNone(result)

    def test_list_with_multiple_paragraphs_stops_at_blank(self):
        """List items should stop at blank lines (no multi-paragraph support)."""
        content = "- First paragraph of item\n" "\n" "  Second paragraph should not be part of item\n"
        result = self._write_and_process(content)
        # Should preserve structure
        self.assertIn("\n\n", result)

    def test_version_history_nested_list_structure(self):
        """Nested list structure like Version History should be preserved exactly.

        This is a regression test for the bug where nested list items were
        incorrectly treated as continuations of their parent item.
        """
        content = (
            "- **v1.0** (2025-12-26): Initial conformance vectors for M2-P1-I1\n"
            "  - safe_run: 5 vectors (success, failure, SIGINT, custom log dir, snippet)\n"
            "  - preflight_automerge_ruleset: 4 vectors (success, auth fail, ruleset not found, missing context)\n"
            "  - safe_archive: 4 vectors (success, compression, no-clobber default, no-clobber strict)\n"
        )
        result = self._write_and_process(content)
        lines = result.splitlines()

        # First line should be the parent item (may be wrapped if too long)
        self.assertTrue(lines[0].startswith("- **v1.0**"))

        # Nested items should start with "  - " (2 space indent + dash)
        nested_lines = [
            line
            for line in lines
            if line.strip().startswith("- safe_run:")
            or line.strip().startswith("- preflight_automerge_ruleset:")
            or line.strip().startswith("- safe_archive:")
        ]

        # Should have 3 nested items preserved as separate lines, not mangled into parent
        self.assertEqual(len(nested_lines), 3, f"Expected 3 nested list items, got {len(nested_lines)}: {nested_lines}")

        # Each nested item should maintain its "  - " prefix (2 space indent)
        for line in nested_lines:
            self.assertTrue(line.startswith("  - "), f"Nested item should start with '  - ', got: {line}")


if __name__ == "__main__":
    unittest.main()
