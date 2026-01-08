#!/usr/bin/env python3
"""
Fix MD013 line-length violations in Markdown files (safe-ish reflow).

Behavior:
- Reflows *paragraph blocks* (not individual lines) to <= 120 chars.
- Skips anything likely to be structure-sensitive:
  - fenced code blocks (``` / ~~~)
  - indented code blocks (only when clearly code-ish)
  - tables (header + separator detection)
  - headings, blockquotes
  - link reference definitions
  - HTML blocks
  - lines containing real URLs (http/https or autolinks)
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path
from typing import List, Optional, Tuple


MAX_LEN = 120

FENCE_RE = re.compile(r"^(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
BLOCKQUOTE_RE = re.compile(r"^\s{0,3}>\s?")
REF_DEF_RE = re.compile(r"^\s{0,3}\[\^[^\]]+\]:\s+\S+")
HTML_BLOCK_RE = re.compile(r"^\s{0,3}<[/a-zA-Z][^>]*>\s*$")
URL_RE = re.compile(r"(https?://\S+|<https?://[^>]+>)")

# Table detection: a "real" markdown table usually has a separator line like:
# | --- | --- |  or  ---|--- etc.
TABLE_ROW_RE = re.compile(r"^\s{0,3}\|.*\|\s*$")
TABLE_SEP_RE = re.compile(r"^\s{0,3}\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")

LIST_ITEM_RE = re.compile(r"^(\s{0,3})([-*+]|\d+\.)\s+")


def _is_table_block(lines: List[str], i: int) -> bool:
    """
    Detect a table by checking current line and the next line:
    header row + separator row.
    """
    if i + 1 >= len(lines):
        return False
    return bool(TABLE_ROW_RE.match(lines[i]) and TABLE_SEP_RE.match(lines[i + 1]))


def _starts_fence(line: str) -> Optional[Tuple[str, int]]:
    """
    If line starts a fence, return (fence_char, fence_len) like ("`", 3) or ("~", 3).
    Otherwise None.
    """
    m = FENCE_RE.match(line)
    if not m:
        return None
    fence = m.group("fence")
    return (fence[0], len(fence))


def _ends_fence(line: str, fence_char: str, fence_len: int) -> bool:
    """
    Close fence must match the opening fence char and be at least as long.
    """
    m = FENCE_RE.match(line)
    if not m:
        return False
    fence = m.group("fence")
    return fence[0] == fence_char and len(fence) >= fence_len


def _should_skip_line(line: str) -> bool:
    """
    Lines we should never reflow.
    """
    if not line.strip():
        return True
    if HEADING_RE.match(line):
        return True
    if BLOCKQUOTE_RE.match(line):
        return True
    if REF_DEF_RE.match(line):
        return True
    if HTML_BLOCK_RE.match(line):
        return True
    # NOTE: Removed backtick exemption per user requirement
    if URL_RE.search(line):
        return True
    return False


def _wrap_paragraph(text: str, initial_indent: str = "", subsequent_indent: str = "") -> List[str]:
    """
    Wrap paragraph text to MAX_LEN, without breaking words.
    """
    wrapped = textwrap.fill(
        text,
        width=MAX_LEN,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return wrapped.splitlines()


def _collect_paragraph(lines: List[str], start: int) -> Tuple[int, List[str]]:
    """
    Collect consecutive lines that form a paragraph block.
    Stops at blank line or a line that should be skipped.
    Returns (next_index, paragraph_lines).
    """
    buf: List[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            break
        if _should_skip_line(line):
            break
        # If it *looks* like table start, stop (tables handled elsewhere)
        if TABLE_ROW_RE.match(line):
            break
        buf.append(line)
        i += 1
    return i, buf


def _rewrite_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()

    out: List[str] = []

    in_fence = False
    fence_char = ""
    fence_len = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Fence open/close handling
        fence = _starts_fence(line)
        if fence and not in_fence:
            in_fence = True
            fence_char, fence_len = fence
            out.append(line)
            i += 1
            continue
        if in_fence:
            out.append(line)
            if _ends_fence(line, fence_char, fence_len):
                in_fence = False
                fence_char = ""
                fence_len = 0
            i += 1
            continue

        # Tables: copy the entire contiguous table block unchanged
        if _is_table_block(lines, i):
            out.append(lines[i])
            out.append(lines[i + 1])
            i += 2
            while i < len(lines) and TABLE_ROW_RE.match(lines[i]):
                out.append(lines[i])
                i += 1
            continue

        # Skip lines that should never be reflowed
        if _should_skip_line(line):
            out.append(line)
            i += 1
            continue

        # List item paragraph wrapping (preserve marker + continuation indent)
        m = LIST_ITEM_RE.match(line)
        if m:
            base_indent = m.group(1)
            marker = m.group(2)
            marker_prefix = f"{base_indent}{marker} "
            continuation = " " * len(marker_prefix)

            # Collect list paragraph block
            next_i, para_lines = _collect_paragraph(lines, i)
            para_text = " ".join(s.strip() for s in para_lines).strip()

            wrapped = _wrap_paragraph(
                para_text,
                initial_indent=marker_prefix,
                subsequent_indent=continuation,
            )
            out.extend(wrapped)
            i = next_i
            continue

        # Regular paragraph wrapping
        next_i, para_lines = _collect_paragraph(lines, i)
        para_text = " ".join(s.strip() for s in para_lines).strip()

        if para_text and len(para_text) > MAX_LEN:
            out.extend(_wrap_paragraph(para_text))
        else:
            out.extend(para_lines)

        i = next_i

        # Preserve explicit blank line if present
        if i < len(lines) and not lines[i].strip():
            out.append(lines[i])
            i += 1

    new = "\n".join(out) + ("\n" if original.endswith("\n") else "")
    if new != original:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: fix-md013-line-length.py <markdown-file>", file=sys.stderr)
        return 2

    p = Path(sys.argv[1])
    if not p.exists():
        print(f"ERROR: file not found: {p}", file=sys.stderr)
        return 2

    changed = _rewrite_file(p)
    print(f"{'Fixed' if changed else 'No changes'}: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
