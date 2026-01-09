#!/usr/bin/env python3
"""Comprehensive unit tests for MD013 smart fixer.

Tests all 6 phases of the smart reflow implementation including state machine,
blockquote handling, list nesting, continuations, and edge cases.

:rtype: None
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.repo_lint.fixers import md013_smart_fixer


class TestMD013SmartFixer(unittest.TestCase):
    """Test suite for MD013 smart reflow fixer."""

    def setUp(self) -> None:
        """Create temporary directory for test files.
        
        :rtype: None
        """
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up temporary directory.
        
        :rtype: None
        """
        self.temp_dir.cleanup()

    def _process(self, content: str) -> str:
        """Process content through the smart fixer.
        
        :param content: Markdown content to process
        :returns: Processed content
        :rtype: str
        """
        return md013_smart_fixer.process_markdown_file(content, max_len=120)

    # Phase 1: Context Tracking Tests

    def test_blockquote_single_level(self) -> None:
        """Single-level blockquote should preserve > prefix.
        
        :rtype: None
        """
        content = (
            "> This is a very long blockquote line that exceeds the maximum "
            "line length and should be wrapped with > prefix on each line\n"
        )
        result = self._process(content)
        lines = result.splitlines()
        # All lines should start with >
        for line in lines:
            self.assertTrue(line.startswith("> "), f"Line should start with '> ': {line}")

    def test_blockquote_nested(self) -> None:
        """Nested blockquotes should preserve all > prefixes.
        
        :rtype: None
        """
        content = (
            "> > This is a nested blockquote that is very long and exceeds "
            "the maximum line length limit and needs wrapping\n"
        )
        result = self._process(content)
        lines = result.splitlines()
        # All lines should start with > >
        for line in lines:
            self.assertTrue(line.startswith("> > "), f"Line should start with '> > ': {line}")

    def test_list_depth_stack_basic(self) -> None:
        """List depth stack should track nesting correctly.
        
        :rtype: None
        """
        content = (
            "- Top level\n"
            "  - Nested level that is very long and exceeds maximum line length and should be wrapped\n"
        )
        result = self._process(content)
        self.assertIn("- Top level", result)
        self.assertIn("  - Nested level", result)

    def test_list_continuation_lines(self) -> None:
        """List continuation lines should maintain proper indentation.
        
        :rtype: None
        """
        content = (
            "- First line of item\n"
            "  This is a continuation that is very long and exceeds the maximum line length limit\n"
        )
        result = self._process(content)
        lines = result.splitlines()
        # Continuation lines should maintain indent
        for line in lines[1:]:
            self.assertTrue(line.startswith("  "), f"Continuation should be indented: {line}")

    # Phase 2: Smart Paragraph & Continuation Handling

    def test_lazy_continuation_detection(self) -> None:
        """Lazy continuations should be detected and wrapped correctly.
        
        :rtype: None
        """
        content = (
            "- Item with text\n"
            "  Continuation paragraph that is indented and very long exceeding the maximum line length\n"
        )
        result = self._process(content)
        # Should preserve the structure
        self.assertIn("- Item with text", result)
        self.assertIn("Continuation", result)

    def test_multi_paragraph_list_item(self) -> None:
        """Multi-paragraph list items should be handled correctly.
        
        :rtype: None
        """
        content = (
            "- First paragraph\n"
            "\n"
            "  Second paragraph in same item\n"
        )
        result = self._process(content)
        # Blank line should be preserved
        self.assertIn("\n\n", result)

    # Phase 3: Checkbox & Mixed Marker Protection

    def test_checkbox_never_duplicated(self) -> None:
        """Checkboxes should never be duplicated on wrapped lines.
        
        :rtype: None
        """
        content = (
            "- [ ] This is a very long task item that exceeds the maximum line "
            "length and should be wrapped without duplicating the checkbox\n"
        )
        result = self._process(content)
        # Should have exactly one checkbox
        self.assertEqual(result.count("- [ ]"), 1, "Should have exactly one checkbox")

    def test_checkbox_checked_preserved(self) -> None:
        """Checked checkboxes should be preserved correctly.
        
        :rtype: None
        """
        content = (
            "- [x] Completed task with very long text that exceeds the maximum "
            "line length and needs wrapping\n"
        )
        result = self._process(content)
        self.assertIn("- [x]", result)
        self.assertEqual(result.count("- [x]"), 1)

    def test_mixed_bullet_markers(self) -> None:
        """Mixed bullet markers (*, -, +) should all be handled.
        
        :rtype: None
        """
        content = (
            "- Dash item with very long text exceeding limit\n"
            "* Star item with very long text exceeding limit\n"
            "+ Plus item with very long text exceeding limit\n"
        )
        result = self._process(content)
        self.assertIn("- ", result)
        self.assertIn("* ", result)
        self.assertIn("+ ", result)

    def test_numbered_list_markers(self) -> None:
        """Numbered list markers should be preserved.
        
        :rtype: None
        """
        content = (
            "1. First item with very long text that exceeds the maximum line length\n"
            "2. Second item with very long text that exceeds the maximum line length\n"
        )
        result = self._process(content)
        self.assertIn("1. ", result)
        self.assertIn("2. ", result)

    # Phase 4: Admonition & Edge Cases

    def test_admonition_preserved(self) -> None:
        """Admonition blocks should be preserved unchanged.
        
        :rtype: None
        """
        content = (
            "> [!NOTE]\n"
            "> This is a note admonition with very long text that should not be reflowed\n"
        )
        result = self._process(content)
        self.assertIn("[!NOTE]", result)

    def test_html_comment_preserved(self) -> None:
        """HTML comments should be preserved unchanged.
        
        :rtype: None
        """
        content = (
            "<!-- This is a very long HTML comment that exceeds the maximum line length -->\n"
        )
        result = self._process(content)
        self.assertEqual(result, content)

    def test_frontmatter_preserved(self) -> None:
        """YAML frontmatter should be preserved unchanged.
        
        :rtype: None
        """
        content = (
            "---\n"
            "title: Very Long Title That Exceeds Maximum Line Length\n"
            "---\n"
        )
        result = self._process(content)
        self.assertEqual(result, content)

    def test_fenced_code_preserved(self) -> None:
        """Fenced code blocks should be preserved.
        
        :rtype: None
        """
        content = (
            "```python\n"
            "def very_long_function_name_that_exceeds_limit(param1, param2):\n"
            "    return param1 + param2\n"
            "```\n"
        )
        result = self._process(content)
        self.assertEqual(result, content)

    def test_table_preserved(self) -> None:
        """Tables should be preserved unchanged.
        
        :rtype: None
        """
        content = (
            "| Column 1 with very long header | Column 2 |\n"
            "| ------------------------------- | -------- |\n"
            "| Data 1 very long exceeding max  | Data 2   |\n"
        )
        result = self._process(content)
        self.assertEqual(result, content)

    # Phase 5: CLI Features (tested via process_file)

    def test_process_file_no_changes(self) -> None:
        """Files with no violations should not be modified.
        
        :rtype: None
        """
        content = "Short line.\n"
        test_file = self.temp_path / "test.md"
        test_file.write_text(content, encoding="utf-8")
        
        modified = md013_smart_fixer.process_file(test_file, 120, dry_run=False, show_diff=False)
        self.assertFalse(modified)
        self.assertEqual(test_file.read_text(encoding="utf-8"), content)

    def test_process_file_with_changes(self) -> None:
        """Files with violations should be modified.
        
        :rtype: None
        """
        content = (
            "This is a very long paragraph line that definitely and absolutely exceeds the maximum "
            "line length limit of one hundred twenty characters and should be wrapped appropriately.\n"
        )
        test_file = self.temp_path / "test.md"
        test_file.write_text(content, encoding="utf-8")
        
        modified = md013_smart_fixer.process_file(test_file, 120, dry_run=False, show_diff=False)
        self.assertTrue(modified)
        result = test_file.read_text(encoding="utf-8")
        self.assertNotEqual(result, content)
        # All lines should be <= 120
        for line in result.splitlines():
            self.assertLessEqual(len(line), 120)

    def test_dry_run_mode(self) -> None:
        """Dry-run mode should not modify files.
        
        :rtype: None
        """
        content = (
            "This is a very long paragraph line that definitely and absolutely exceeds the maximum "
            "line length limit of one hundred twenty characters and should be wrapped appropriately.\n"
        )
        test_file = self.temp_path / "test.md"
        test_file.write_text(content, encoding="utf-8")
        
        modified = md013_smart_fixer.process_file(test_file, 120, dry_run=True, show_diff=False)
        self.assertTrue(modified)
        # File should be unchanged
        self.assertEqual(test_file.read_text(encoding="utf-8"), content)

    # Phase 6: Complex Real-World Scenarios

    def test_nested_list_with_blockquote(self) -> None:
        """Nested lists inside blockquotes should work correctly.
        
        :rtype: None
        """
        content = (
            "> - Item inside blockquote with very long text that exceeds maximum line length\n"
            ">   - Nested item also with very long text that exceeds the maximum line length\n"
        )
        result = self._process(content)
        lines = result.splitlines()
        # All lines should start with >
        for line in lines:
            self.assertTrue(line.startswith("> "), f"Should have blockquote prefix: {line}")

    def test_version_history_structure(self) -> None:
        """Complex version history structure should be preserved.
        
        :rtype: None
        """
        content = (
            "- **v1.0** (2025-12-26): Initial release\n"
            "  - Feature A: Very long description that exceeds the maximum line length\n"
            "  - Feature B: Another long description exceeding the limit\n"
            "- **v2.0** (2026-01-01): Major update\n"
        )
        result = self._process(content)
        # Should have 2 top-level items
        top_level = [line for line in result.splitlines() if line.startswith("- **v")]
        self.assertEqual(len(top_level), 2)
        
        # Should have nested items
        nested = [line for line in result.splitlines() if line.startswith("  - Feature")]
        self.assertEqual(len(nested), 2)

    def test_deterministic_output(self) -> None:
        """Running fixer twice should produce identical output.
        
        :rtype: None
        """
        content = (
            "- Very long list item that exceeds maximum line length and will be wrapped\n"
        )
        first_result = self._process(content)
        second_result = self._process(first_result)
        self.assertEqual(first_result, second_result)

    def test_final_newline_preserved(self) -> None:
        """Final newline should be preserved.
        
        :rtype: None
        """
        content_with_newline = "Short line.\n"
        result = self._process(content_with_newline)
        self.assertTrue(result.endswith("\n"))
        
        content_without_newline = "Short line."
        result = self._process(content_without_newline)
        self.assertFalse(result.endswith("\n"))

    def test_inline_code_exemption(self) -> None:
        """Lines with inline code should be preserved.
        
        :rtype: None
        """
        content = (
            "This line has `inline_code` and is very long exceeding the maximum line length\n"
        )
        result = self._process(content)
        self.assertEqual(result, content)

    def test_url_exemption(self) -> None:
        """Lines with URLs should be preserved.
        
        :rtype: None
        """
        content = (
            "Check https://example.com/very/long/url for information exceeding limit\n"
        )
        result = self._process(content)
        self.assertEqual(result, content)

    def test_heading_preserved(self) -> None:
        """Headings should be preserved unchanged.
        
        :rtype: None
        """
        content = (
            "# This is a very long heading that exceeds the maximum line length\n"
        )
        result = self._process(content)
        self.assertEqual(result, content)

    def test_link_reference_preserved(self) -> None:
        """Link reference definitions should be preserved.
        
        :rtype: None
        """
        content = (
            "[id]: https://example.com/very/long/url/exceeding/limit\n"
        )
        result = self._process(content)
        self.assertEqual(result, content)

    def test_empty_file(self) -> None:
        """Empty files should remain empty.
        
        :rtype: None
        """
        content = ""
        result = self._process(content)
        self.assertEqual(result, "")

    def test_blank_lines_preserved(self) -> None:
        """Blank lines should be preserved.
        
        :rtype: None
        """
        content = "Line 1\n\nLine 2\n"
        result = self._process(content)
        self.assertIn("\n\n", result)


if __name__ == "__main__":
    unittest.main()
