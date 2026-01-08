#!/usr/bin/env python3
"""
fix_md013_line_length_option_a.py

Safe-ish fixer for markdownlint MD013 (line-length) violations.

Option A strategy: **do not touch structure-sensitive markdown**.
This script will only reflow *plain paragraph blocks* (non-list, non-table, non-code)
to <= 120 characters. It will **skip**:

- Fenced code blocks (``` / ~~~)
- Indented code blocks (4 spaces or tab) when not in a list
- Tables (header + separator detection, plus contiguous table rows)
- Headings (# ...)
- Blockquotes (> ...)
- Link reference definitions ([id]: url)
- HTML block lines (<tag>...</tag>)
- Any line containing backticks (inline code exemption)
- Any line containing URLs (http/https or <http...>)
- Entire list blocks (bullets, numbered lists, task lists) including their continuations

Usage:
    python3 fix_md013_line_length_option_a.py <path>

Where <path> may be:
- a single .md file
- a directory (recursively processes *.md)

Exit codes:
    0 success (even if no changes)
    2 usage / input errors
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


MAX_LEN = 120

FENCE_RE = re.compile(r"^(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
BLOCKQUOTE_RE = re.compile(r"^\s{0,3}>\s?")
REF_DEF_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s+\S+")
HTML_BLOCK_RE = re.compile(r"^\s{0,3}<[/a-zA-Z][^>]*>\s*$")
URL_RE = re.compile(r"(https?://\S+|<https?://[^>]+>)")

# Table detection: header row + separator row.
TABLE_ROW_RE = re.compile(r"^\s{0,3}\|.*\|\s*$")
TABLE_SEP_RE = re.compile(r"^\s{0,3}\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")

# Lists: bullets, numbered, and task lists.
LIST_ITEM_RE = re.compile(r"^(\s{0,3})([-*+]|\d{1,4}\.)\s+")
TASK_LIST_RE = re.compile(r"^(\s{0,3})([-*+]|\d{1,4}\.)\s+\[[ xX]\]\s+")


def _starts_fence(line: str) -> Optional[Tuple[str, int]]:
    """If line starts a fence, return (fence_char, fence_len)."""
    m = FENCE_RE.match(line)
    if not m:
        return None
    fence = m.group("fence")
    return (fence[0], len(fence))


def _ends_fence(line: str, fence_char: str, fence_len: int) -> bool:
    """Close fence must match the opening fence char and be at least as long."""
    m = FENCE_RE.match(line)
    if not m:
        return False
    fence = m.group("fence")
    return fence[0] == fence_char and len(fence) >= fence_len


def _is_table_block(lines: List[str], i: int) -> bool:
    """Detect a table by checking current line and the next line: header + separator."""
    if i + 1 >= len(lines):
        return False
    return bool(TABLE_ROW_RE.match(lines[i]) and TABLE_SEP_RE.match(lines[i + 1]))


def _is_indented_code(line: str) -> bool:
    """
    Treat 4-space (or tab) indented lines as code blocks.
    This intentionally does NOT try to be clever inside lists; list blocks are skipped entirely
    by Option A.
    """
    return line.startswith("    ") or line.startswith("\t")


def _is_list_item(line: str) -> bool:
    """True if this line starts a list item (including task lists)."""
    return bool(LIST_ITEM_RE.match(line) or TASK_LIST_RE.match(line))


def _should_skip_line(line: str) -> bool:
    """Lines we should never reflow."""
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
    if "`" in line:  # inline-code exemption (repo decision)
        return True
    if URL_RE.search(line):
        return True
    if _is_indented_code(line):
        return True
    return False


def _wrap_paragraph(text: str) -> List[str]:
    """Wrap paragraph text to MAX_LEN, without breaking words."""
    wrapped = textwrap.fill(
        text,
        width=MAX_LEN,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return wrapped.splitlines()


def _collect_paragraph(lines: List[str], start: int) -> Tuple[int, List[str]]:
    """
    Collect consecutive lines that form a plain paragraph block.
    Stops at blank line or any structure-sensitive line.
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
        if TABLE_ROW_RE.match(line):
            break
        if _is_list_item(line):
            break
        buf.append(line)
        i += 1
    return i, buf


def _copy_list_block(lines: List[str], i: int) -> Tuple[int, List[str]]:
    """
    Copy a list item and its immediate continuation lines unchanged.
    Option A: we skip list blocks entirely to avoid mangling bullets/checkboxes.
    """
    out: List[str] = []
    first = lines[i]
    m = TASK_LIST_RE.match(first) or LIST_ITEM_RE.match(first)
    if not m:
        return i, out

    base_indent = m.group(1)
    out.append(first)
    i += 1

    # Continuations are usually indented. We keep them until a blank line or a new list item
    # at the same/better indent or a structural boundary.
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            break
        if _is_list_item(line) and len(line) - len(line.lstrip(" ")) <= len(base_indent):
            break
        fence = _starts_fence(line)
        if fence:
            break
        if _is_table_block(lines, i):
            break
        if HEADING_RE.match(line) or BLOCKQUOTE_RE.match(line) or REF_DEF_RE.match(line) or HTML_BLOCK_RE.match(line):
            break
        out.append(line)
        i += 1

    return i, out


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

        # Tables: copy contiguous table block unchanged
        if _is_table_block(lines, i):
            out.append(lines[i])
            out.append(lines[i + 1])
            i += 2
            while i < len(lines) and TABLE_ROW_RE.match(lines[i]):
                out.append(lines[i])
                i += 1
            continue

        # Lists: copy list item blocks unchanged
        if _is_list_item(line):
            next_i, copied = _copy_list_block(lines, i)
            out.extend(copied)
            i = next_i
            # Preserve following blank line if present
            if i < len(lines) and not lines[i].strip():
                out.append(lines[i])
                i += 1
            continue

        # Skip lines that should never be reflowed
        if _should_skip_line(line):
            out.append(line)
            i += 1
            continue

        # Regular paragraph wrapping
        next_i, para_lines = _collect_paragraph(lines, i)
        para_text = " ".join(s.strip() for s in para_lines).strip()

        # Only reflow if the paragraph is too long *and* at least one original
        # line actually exceeds MAX_LEN, to avoid rewrapping already-compliant
        # formatting.
        if para_text and len(para_text) > MAX_LEN and any(len(line) > MAX_LEN for line in para_lines):
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


def _iter_md_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        if path.suffix.lower() == ".md":
            yield path
        return
    for p in sorted(path.rglob("*.md")):
        yield p


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: fix_md013_line_length_option_a.py <file-or-directory>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])
    if not root.exists():
        print(f"ERROR: path not found: {root}", file=sys.stderr)
        return 2

    changed_any = False
    for md in _iter_md_files(root):
        changed = _rewrite_file(md)
        if changed:
            changed_any = True
            print(f"Fixed: {md}")
    if not changed_any:
        print("No changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
