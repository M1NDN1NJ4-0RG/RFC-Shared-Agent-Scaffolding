#!/usr/bin/env python3
"""Unit tests for fix_md013_line_length_option_a.py script.

This module provides comprehensive test coverage for the conservative MD013 fixer,
ensuring it only reflows plain paragraphs while preserving all list structures.

:Purpose:
    Ensures the script correctly handles all Markdown variants without mangling:
    - Lists (bullets, numbered, task lists, nested)
    - Code blocks (fenced and indented)
    - Tables
    - Blockquotes, headings, link references
    - Inline code and URLs
    - Newline behavior

:Environment Variables:
    None. Tests are self-contained and use temporary files.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest scripts/tests/test_fix_md013_line_length_option_a.py -v

    Run specific test::

        python3 -m pytest scripts/tests/test_fix_md013_line_length_option_a.py::test_bullet_list -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module under test
import fix_md013_line_length_option_a as fixer


class TestOptionA(unittest.TestCase):
    """Test suite for fix_md013_line_length_option_a.py."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def _write_and_process(self, content: str) -> str:
        """Write content to temp file, process it, and return result."""
        test_file = self.temp_path / "test.md"
        test_file.write_text(content, encoding="utf-8")
        fixer._rewrite_file(test_file)
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

    def test_bullet_list_preserved(self):
        """Bullet lists should be preserved unchanged."""
        content = (
            "- This is a very long bullet list item that exceeds the maximum "
            "line length but should remain unchanged\n"
            "- Second item\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_numbered_list_preserved(self):
        """Numbered lists should be preserved unchanged."""
        content = (
            "1. This is a very long numbered list item that exceeds the maximum "
            "line length but should remain unchanged\n"
            "2. Second item\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_task_list_preserved(self):
        """Task lists with checkboxes should be preserved unchanged."""
        content = (
            "- [ ] This is a very long unchecked task item that exceeds the "
            "maximum line length but should remain unchanged\n"
            "- [x] Completed task\n"
            "- [X] Another completed task with uppercase X\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_nested_lists_preserved(self):
        """Nested lists with correct indentation should be preserved."""
        content = (
            "- Top level item\n"
            "  - Nested item that is very long and exceeds the maximum line "
            "length but should remain unchanged\n"
            "    - Deeply nested item\n"
            "- Another top level\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_list_with_continuation_preserved(self):
        """List items with continuation lines should be preserved."""
        content = (
            "- First line of list item\n"
            "  continuation line that is indented\n"
            "  another continuation line\n"
            "- Second list item\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

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
            "| Row 2 | Row 2 Col 2 | Row 2 Col 3 |\n"
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
            "### Heading 3\n"
            "#### Heading 4\n"
            "##### Heading 5\n"
            "###### Heading 6\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_link_reference_definitions_preserved(self):
        """Link reference definitions should be preserved unchanged."""
        content = (
            "[id]: https://example.com/very/long/url/that/exceeds/the/"
            "maximum/line/length/limit\n"
            "[another]: https://example.com\n"
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

    def test_inline_code_exemption(self):
        """Lines containing backticks (inline code) should not be reflowed."""
        content = (
            "This is a very long line with `inline_code_snippet` that exceeds "
            "the maximum line length but should remain unchanged\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_url_exemption(self):
        """Lines containing URLs should not be reflowed."""
        content = (
            "Check out https://example.com/very/long/url/path for more "
            "information about this topic that exceeds line limit\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_url_angle_bracket_exemption(self):
        """Lines containing angle-bracket URLs should not be reflowed."""
        content = (
            "Visit <https://example.com/very/long/url> for documentation "
            "that exceeds the line length limit\n"
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
            "This is a very long paragraph that exceeds the maximum line "
            "length and will be wrapped by the script on first run.\n"
        )
        test_file = self.temp_path / "test.md"
        test_file.write_text(content, encoding="utf-8")
        
        # First run
        fixer._rewrite_file(test_file)
        first_result = test_file.read_text(encoding="utf-8")
        
        # Second run
        fixer._rewrite_file(test_file)
        second_result = test_file.read_text(encoding="utf-8")
        
        self.assertEqual(first_result, second_result)

    def test_no_list_marker_duplication(self):
        """Ensure list markers are not duplicated (historical bug check)."""
        content = (
            "1. First item with very long text that should not cause marker "
            "duplication\n"
            "2. Second item\n"
        )
        result = self._write_and_process(content)
        # Should not have "1. 1. " or similar
        self.assertNotIn("1. 1. ", result)
        self.assertNotIn("2. 2. ", result)

    def test_no_checkbox_breakage(self):
        """Ensure checkbox syntax is not broken (historical bug check)."""
        content = "- [x] Task with very long description exceeding line limit\n"
        result = self._write_and_process(content)
        # Should still have valid checkbox
        self.assertIn("- [x]", result)
        # Should not have broken syntax like "- - [x]" or "[x] [x]"
        self.assertNotIn("- - [x]", result)
        self.assertNotIn("[x] [x]", result)

    def test_mixed_list_markers(self):
        """Lists with different markers should all be preserved."""
        content = (
            "- Bullet item\n"
            "* Asterisk item\n"
            "+ Plus item\n"
            "1. Numbered item\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)

    def test_blank_lines_between_paragraphs(self):
        """Blank lines between paragraphs should be preserved."""
        content = (
            "First paragraph.\n"
            "\n"
            "Second paragraph.\n"
        )
        result = self._write_and_process(content)
        self.assertEqual(result, content)


if __name__ == "__main__":
    unittest.main()
