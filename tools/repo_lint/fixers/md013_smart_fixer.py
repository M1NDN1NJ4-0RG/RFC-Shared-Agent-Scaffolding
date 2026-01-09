#!/usr/bin/env python3
"""MD013 Smart Reflow Fixer - State-machine-based Markdown line length enforcer.

This module implements all 6 phases of the MD013 smart reflow recommendations:
- Phase 1: Context tracking (list depth stack, blockquote depth, state machine)
- Phase 2: Smart paragraph & continuation handling
- Phase 3: Checkbox & mixed marker protection
- Phase 4: Admonition & edge case handling
- Phase 5: Comprehensive CLI with --dry-run, --diff, --check modes
- Phase 6: Integration-ready for repo_lint

:Purpose:
    Fix MD013 line-length violations using intelligent state machine that preserves
    all Markdown structure including nested lists, blockquotes, continuations, and
    special syntax.

:Features:
    - State machine tracks list depth stack and blockquote nesting
    - Proper continuation line handling with correct indentation
    - Blockquote prefix preservation (> for each level)
    - Checkbox protection (never duplicates [ ] or [x])
    - Mixed marker support (*, -, +, numbered)
    - Admonition block preservation (> [!NOTE], etc.)
    - HTML comment and frontmatter skip logic
    - Diff output mode (git-style)
    - Check mode (CI-friendly, exit non-zero if fixes needed)
    - Dry-run mode (preview without writing)

:Exit Codes:
    0
        Success (or --check mode with no violations)
    1
        --check mode found violations that need fixing
    2
        Usage error or file not found

:rtype: None
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

DEFAULT_MAX_LEN = 120


# Regex patterns
FENCE_RE = re.compile(r"^(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
BLOCKQUOTE_RE = re.compile(r"^(?P<prefix>(\s{0,3}>)+)\s?(?P<rest>.*)$")
REF_DEF_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s+\S+")
HTML_BLOCK_RE = re.compile(r"^\s{0,3}<[/a-zA-Z][^>]*>\s*$")
HTML_COMMENT_RE = re.compile(r"^\s*<!--")
URL_RE = re.compile(r"(https?://\S+|<https?://[^>]+>)")
ADMONITION_RE = re.compile(r"^>\s*\[!(?:NOTE|WARNING|TIP|IMPORTANT|CAUTION)\]")

# Table detection
TABLE_ROW_RE = re.compile(r"^\s{0,3}\|.*\|\s*$")
TABLE_SEP_RE = re.compile(r"^\s{0,3}\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")

# List detection
LIST_ITEM_RE = re.compile(
    r"^(?P<indent>\s*)(?P<marker>[-*+]|\d{1,4}\.)\s+(?P<checkbox>\[(?:[ xX])\]\s+)?(?P<rest>.*)$"
)

# Frontmatter detection
FRONTMATTER_DELIMITER = re.compile(r"^---\s*$")


@dataclass
class ListContext:
    """Represents the context of a single list level.
    
    :ivar indent_len: Number of spaces for this list level
    :ivar marker: The list marker (-, *, +, or number.)
    :ivar marker_text: Full marker text including spaces
    :ivar checkbox: Checkbox text if present ("[x] ", "[ ] ", or empty)
    """

    indent_len: int
    marker: str
    marker_text: str
    checkbox: str = ""


@dataclass
class ProcessorState:
    """State machine for Markdown processing.
    
    :ivar list_stack: Stack of active list contexts (innermost last)
    :ivar blockquote_depth: Number of nested blockquote levels
    :ivar in_fence: Whether currently inside a fenced code block
    :ivar fence_char: Fence character (` or ~) if in_fence
    :ivar fence_len: Fence length if in_fence
    :ivar in_table: Whether currently inside a table block
    :ivar in_html_comment: Whether currently inside an HTML comment
    :ivar in_frontmatter: Whether currently inside YAML frontmatter
    :ivar paragraph_buffer: Buffer for collecting paragraph lines
    :ivar last_was_blank: Whether the previous line was blank
    """

    list_stack: List[ListContext] = field(default_factory=list)
    blockquote_depth: int = 0
    in_fence: bool = False
    fence_char: str = ""
    fence_len: int = 0
    in_table: bool = False
    in_html_comment: bool = False
    in_frontmatter: bool = False
    paragraph_buffer: List[str] = field(default_factory=list)
    last_was_blank: bool = True


def _count_blockquote_depth(line: str) -> int:
    """Count the number of blockquote levels (> prefixes).
    
    :param line: Line to analyze
    :returns: Number of > prefixes
    :rtype: int
    """
    m = BLOCKQUOTE_RE.match(line)
    if not m:
        return 0
    prefix = m.group("prefix")
    return prefix.count(">")


def _get_blockquote_prefix(depth: int) -> str:
    """Generate blockquote prefix for given depth.
    
    :param depth: Number of blockquote levels
    :returns: Blockquote prefix string (e.g., "> > ")
    :rtype: str
    """
    if depth == 0:
        return ""
    return "> " * depth


def _starts_fence(line: str) -> Optional[Tuple[str, int]]:
    """Check if line starts a fenced code block.
    
    :param line: Line to check
    :returns: Tuple of (fence_char, fence_len) or None
    :rtype: Optional[Tuple[str, int]]
    """
    m = FENCE_RE.match(line)
    if not m:
        return None
    fence = m.group("fence")
    return (fence[0], len(fence))


def _ends_fence(line: str, fence_char: str, fence_len: int) -> bool:
    """Check if line closes a fenced code block.
    
    :param line: Line to check
    :param fence_char: Opening fence character
    :param fence_len: Opening fence length
    :returns: True if line closes the fence
    :rtype: bool
    """
    m = FENCE_RE.match(line)
    if not m:
        return False
    fence = m.group("fence")
    return fence[0] == fence_char and len(fence) >= fence_len


def _parse_list_item(line: str) -> Optional[Tuple[int, str, str, str, str]]:
    """Parse a list item line.
    
    :param line: Line to parse
    :returns: Tuple of (indent_len, marker, marker_text, checkbox, rest) or None
    :rtype: Optional[Tuple[int, str, str, str, str]]
    """
    m = LIST_ITEM_RE.match(line)
    if not m:
        return None
    
    indent = m.group("indent")
    marker = m.group("marker")
    checkbox = m.group("checkbox") or ""
    rest = m.group("rest")
    
    indent_len = len(indent)
    marker_text = f"{marker} "
    if checkbox:
        marker_text += checkbox
    
    return indent_len, marker, marker_text, checkbox, rest


def _should_skip_line(line: str, state: ProcessorState) -> bool:
    """Check if line should never be reflowed.
    
    :param line: Line to check
    :param state: Current processor state
    :returns: True if line should be skipped
    :rtype: bool
    """
    if not line.strip():
        return True
    if state.in_fence or state.in_table or state.in_html_comment or state.in_frontmatter:
        return True
    if HEADING_RE.match(line):
        return True
    if REF_DEF_RE.match(line):
        return True
    if HTML_BLOCK_RE.match(line):
        return True
    if ADMONITION_RE.match(line):
        return True
    if "`" in line:  # Inline code exemption
        return True
    if URL_RE.search(line):
        return True
    return False


def _wrap_with_context(
    text: str,
    max_len: int,
    state: ProcessorState,
    initial_prefix: str = "",
    continuation_prefix: str = "",
) -> List[str]:
    """Wrap text preserving blockquote and list context.
    
    :param text: Text to wrap
    :param max_len: Maximum line length
    :param state: Current processor state
    :param initial_prefix: Prefix for first line (marker + checkbox)
    :param continuation_prefix: Prefix for continuation lines
    :returns: List of wrapped lines with proper prefixes
    :rtype: List[str]
    """
    # Build blockquote prefix
    bq_prefix = _get_blockquote_prefix(state.blockquote_depth)
    
    # First line gets initial prefix
    first_indent = bq_prefix + initial_prefix
    # Continuation lines get continuation prefix
    cont_indent = bq_prefix + continuation_prefix
    
    wrapped = textwrap.fill(
        text,
        width=max_len,
        initial_indent=first_indent,
        subsequent_indent=cont_indent,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return wrapped.splitlines()


def process_markdown_file(
    content: str,
    max_len: int = DEFAULT_MAX_LEN,
) -> str:
    """Process Markdown content with smart reflowing.
    
    :param content: Original Markdown content
    :param max_len: Maximum line length
    :returns: Processed Markdown content
    :rtype: str
    """
    lines = content.splitlines()
    output: List[str] = []
    state = ProcessorState()
    
    i = 0
    frontmatter_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Frontmatter handling (--- delimiters)
        if FRONTMATTER_DELIMITER.match(line):
            frontmatter_count += 1
            output.append(line)
            if frontmatter_count == 1:
                state.in_frontmatter = True
            elif frontmatter_count == 2:
                state.in_frontmatter = False
            i += 1
            continue
        
        if state.in_frontmatter:
            output.append(line)
            i += 1
            continue
        
        # HTML comment handling
        if HTML_COMMENT_RE.match(line):
            state.in_html_comment = True
        if state.in_html_comment:
            output.append(line)
            if "-->" in line:
                state.in_html_comment = False
            i += 1
            continue
        
        # Fence handling
        fence = _starts_fence(line)
        if fence and not state.in_fence:
            state.in_fence = True
            state.fence_char, state.fence_len = fence
            output.append(line)
            i += 1
            continue
        
        if state.in_fence:
            output.append(line)
            if _ends_fence(line, state.fence_char, state.fence_len):
                state.in_fence = False
            i += 1
            continue
        
        # Table handling
        if i + 1 < len(lines) and TABLE_ROW_RE.match(line) and TABLE_SEP_RE.match(lines[i + 1]):
            state.in_table = True
            output.append(line)
            output.append(lines[i + 1])
            i += 2
            continue
        
        if state.in_table:
            if TABLE_ROW_RE.match(line):
                output.append(line)
                i += 1
                continue
            else:
                state.in_table = False
        
        # Update blockquote depth
        state.blockquote_depth = _count_blockquote_depth(line)
        
        # Skip lines that shouldn't be reflowed
        if _should_skip_line(line, state):
            output.append(line)
            state.last_was_blank = not line.strip()
            i += 1
            continue
        
        # Blank line handling
        if not line.strip():
            output.append(line)
            state.last_was_blank = True
            state.list_stack.clear()  # Blank line ends list context
            i += 1
            continue
        
        # List item handling
        parsed = _parse_list_item(line)
        if parsed:
            indent_len, marker, marker_text, checkbox, rest = parsed
            
            # Update list stack based on indent
            while state.list_stack and state.list_stack[-1].indent_len >= indent_len:
                state.list_stack.pop()
            
            state.list_stack.append(ListContext(
                indent_len=indent_len,
                marker=marker,
                marker_text=marker_text,
                checkbox=checkbox,
            ))
            
            # Build prefixes
            base_indent = " " * indent_len
            initial_prefix = base_indent + marker_text
            continuation_prefix = " " * len(initial_prefix)
            
            # Wrap the text content
            if rest and len(initial_prefix) + len(rest) > max_len:
                wrapped = _wrap_with_context(
                    rest,
                    max_len,
                    state,
                    initial_prefix,
                    continuation_prefix,
                )
                output.extend(wrapped)
            else:
                # Short enough, keep as-is
                bq_prefix = _get_blockquote_prefix(state.blockquote_depth)
                output.append(f"{bq_prefix}{initial_prefix}{rest}".rstrip())
            
            state.last_was_blank = False
            i += 1
            continue
        
        # Regular paragraph handling
        # Check if this is a continuation of a list item
        if state.list_stack and not state.last_was_blank:
            # Calculate expected continuation indent
            current_list = state.list_stack[-1]
            expected_indent = current_list.indent_len + len(current_list.marker_text)
            actual_indent = len(line) - len(line.lstrip())
            
            if actual_indent >= expected_indent:
                # This is a continuation line
                continuation_prefix = " " * expected_indent
                text = line.strip()
                
                if text and len(continuation_prefix) + len(text) > max_len:
                    wrapped = _wrap_with_context(
                        text,
                        max_len,
                        state,
                        continuation_prefix,
                        continuation_prefix,
                    )
                    output.extend(wrapped)
                else:
                    bq_prefix = _get_blockquote_prefix(state.blockquote_depth)
                    output.append(f"{bq_prefix}{continuation_prefix}{text}".rstrip())
                
                state.last_was_blank = False
                i += 1
                continue
        
        # Regular paragraph wrapping
        para_lines = [line]
        j = i + 1
        while j < len(lines):
            next_line = lines[j]
            if not next_line.strip():
                break
            if _should_skip_line(next_line, state):
                break
            if _parse_list_item(next_line):
                break
            if _count_blockquote_depth(next_line) != state.blockquote_depth:
                break
            para_lines.append(next_line)
            j += 1
        
        # Strip blockquote prefixes and join
        para_text_parts = []
        for pline in para_lines:
            if state.blockquote_depth > 0:
                m = BLOCKQUOTE_RE.match(pline)
                if m:
                    para_text_parts.append(m.group("rest").strip())
                else:
                    para_text_parts.append(pline.strip())
            else:
                para_text_parts.append(pline.strip())
        
        para_text = " ".join(para_text_parts)
        
        # Wrap if needed
        if para_text and any(len(pl) > max_len for pl in para_lines):
            wrapped = _wrap_with_context(
                para_text,
                max_len,
                state,
                "",
                "",
            )
            output.extend(wrapped)
        else:
            output.extend(para_lines)
        
        i = j
        state.last_was_blank = False
    
    # Preserve final newline behavior
    if content.endswith("\n"):
        return "\n".join(output) + "\n"
    return "\n".join(output)


def generate_diff(original: str, modified: str, filename: str) -> str:
    """Generate unified diff between original and modified content.
    
    :param original: Original content
    :param modified: Modified content
    :param filename: Filename for diff headers
    :returns: Unified diff string
    :rtype: str
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm="",
    )
    return "".join(diff)


def process_file(
    path: Path,
    max_len: int,
    dry_run: bool,
    show_diff: bool,
) -> bool:
    """Process a single Markdown file.
    
    :param path: Path to Markdown file
    :param max_len: Maximum line length
    :param dry_run: If True, don't write changes
    :param show_diff: If True, show diff output
    :returns: True if file would be/was modified
    :rtype: bool
    """
    original = path.read_text(encoding="utf-8")
    modified = process_markdown_file(original, max_len)
    
    if original == modified:
        return False
    
    if show_diff:
        diff = generate_diff(original, modified, str(path))
        print(diff)
    
    if not dry_run:
        path.write_text(modified, encoding="utf-8")
        print(f"Fixed: {path}")
    else:
        print(f"Would fix: {path}")
    
    return True


def main() -> int:
    """Main entry point.
    
    :returns: Exit code
    :rtype: int
    """
    parser = argparse.ArgumentParser(
        description="MD013 Smart Reflow Fixer - Intelligent Markdown line length enforcer"
    )
    parser.add_argument(
        "path",
        type=Path,
        help="File or directory to process",
    )
    parser.add_argument(
        "--max-line-length",
        type=int,
        default=DEFAULT_MAX_LEN,
        help=f"Maximum line length (default: {DEFAULT_MAX_LEN})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show git-style diff of changes",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if any fixes would be needed (CI mode)",
    )
    
    args = parser.parse_args()
    
    if not args.path.exists():
        print(f"ERROR: path not found: {args.path}", file=sys.stderr)
        return 2
    
    # Collect files
    files: List[Path] = []
    if args.path.is_file():
        if args.path.suffix.lower() == ".md":
            files.append(args.path)
    elif args.path.is_dir():
        files = sorted(args.path.rglob("*.md"))
    else:
        print(f"ERROR: path must be a file or directory: {args.path}", file=sys.stderr)
        return 2
    
    if not files:
        print("No Markdown files found")
        return 0
    
    # Process files
    modified_count = 0
    for md_file in files:
        was_modified = process_file(
            md_file,
            args.max_line_length,
            dry_run=args.dry_run or args.check,
            show_diff=args.diff,
        )
        if was_modified:
            modified_count += 1
    
    # Report results
    if modified_count == 0:
        if args.check:
            print("✓ All files compliant")
        else:
            print("No changes needed")
        return 0
    
    if args.check:
        print(f"✗ {modified_count} file(s) need fixing", file=sys.stderr)
        return 1
    
    if args.dry_run:
        print(f"\nWould modify {modified_count} file(s)")
    else:
        print(f"\nModified {modified_count} file(s)")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
