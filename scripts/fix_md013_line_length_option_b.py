#!/usr/bin/env python3
"""
fix_md013_line_length_option_b.py

Markdown MD013 (line-length) fixer with **list-aware wrapping**.

Option B strategy: reflow plain paragraphs *and* list items safely-ish.

It will still skip structure-sensitive markdown:

- Fenced code blocks (``` / ~~~)
- Indented code blocks (4 spaces or tab) when not in a list context
- Tables (header + separator detection, plus contiguous table rows)
- Headings (# ...)
- Blockquotes (> ...)
- Link reference definitions ([id]: url)
- HTML block lines (<tag>...</tag>)
- Any line containing backticks (inline code exemption)
- Any line containing URLs (http/https or <http...>)

List handling:
- Detects list items (bullets, numbered, and task lists).
- Rewraps the *text payload* of the list item to <= 120 chars.
- Preserves the list marker and checkbox prefix exactly.
- Uses a deterministic continuation indent.

Limitations (intentional safety):
- Does NOT attempt to reflow multi-paragraph list items (items with blank lines inside).
- Treats continuation lines as part of the item only when they are indented beyond the marker.

Usage:
    python3 fix_md013_line_length_option_b.py <path>

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

# Lists:
# - Bullet or numbered marker
# - Optional task checkbox immediately after marker
LIST_ITEM_PREFIX_RE = re.compile(r"^(?P<indent>\s{0,3})(?P<marker>[-*+]|\d{1,4}\.)\s+")
TASK_BOX_RE = re.compile(r"^\[(?P<state>[ xX])\]\s+")


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
    """Treat 4-space (or tab) indented lines as code blocks (outside lists)."""
    return line.startswith("    ") or line.startswith("\t")


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
    return False


def _wrap_text(
    text: str,
    *,
    initial_indent: str = "",
    subsequent_indent: str = "",
) -> List[str]:
    """Wrap text to MAX_LEN, without breaking words."""
    wrapped = textwrap.fill(
        text,
        width=MAX_LEN,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return wrapped.splitlines()


def _parse_list_prefix(line: str) -> Optional[Tuple[str, str, str, str]]:
    """
    Parse list prefix components.

    Returns:
        (base_indent, marker, checkbox, text)

    Where:
        base_indent: leading spaces (0..3)
        marker: "-", "*", "+", or "1."
        checkbox: "" or "[ ] " / "[x] " (including trailing space)
        text: remaining text after marker (+ optional checkbox)
    """
    m = LIST_ITEM_PREFIX_RE.match(line)
    if not m:
        return None

    base_indent = m.group("indent")
    marker = m.group("marker")
    rest = line[m.end() :]

    checkbox = ""
    tb = TASK_BOX_RE.match(rest)
    if tb:
        checkbox = rest[: tb.end()]
        rest = rest[tb.end() :]

    return base_indent, marker, checkbox, rest.rstrip("\n")


def _is_new_list_item(line: str) -> bool:
    return _parse_list_prefix(line) is not None


def _collect_list_item(lines: List[str], start: int) -> Tuple[int, str, str, str, str]:
    """
    Collect a list item starting at `start`.

    Returns:
        (next_index, base_indent, marker, checkbox, payload_text)

    Notes:
      - Stops at blank line (does not support multi-paragraph items).
      - Continuation lines are included only if they are indented beyond the marker prefix.
      - Stops if a new list item at same-or-less indent starts.
    """
    parsed = _parse_list_prefix(lines[start])
    if not parsed:
        return start + 1, "", "", "", lines[start]

    base_indent, marker, checkbox, first_text = parsed
    prefix = f"{base_indent}{marker} {checkbox}"
    prefix_len = len(prefix)

    parts: List[str] = [first_text.strip()] if first_text.strip() else []
    i = start + 1

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            break

        # Structural boundaries => stop item
        if _starts_fence(line) or _is_table_block(lines, i) or HEADING_RE.match(line) or BLOCKQUOTE_RE.match(line):
            break
        if REF_DEF_RE.match(line) or HTML_BLOCK_RE.match(line):
            break

        # New list item at same-or-less indent => stop
        if _is_new_list_item(line):
            next_parsed = _parse_list_prefix(line)
            if next_parsed:
                next_indent = len(next_parsed[0])
                if next_indent <= len(base_indent):
                    break

        # Continuation line: must be indented sufficiently
        indent_len = len(line) - len(line.lstrip(" "))
        if indent_len >= prefix_len:
            cont = line.strip()
            # Safety: if continuation includes inline code or URL, keep original list block as-is.
            # We'll signal by returning the original payload unmodified by embedding a marker.
            if "`" in cont or URL_RE.search(cont):
                return start + 1, base_indent, marker, checkbox, "__DO_NOT_TOUCH_LIST_ITEM__"
            parts.append(cont)
            i += 1
            continue

        # Anything else: stop item
        break

    payload_text = " ".join(p for p in parts if p).strip()
    return i, base_indent, marker, checkbox, payload_text


def _collect_paragraph(lines: List[str], start: int) -> Tuple[int, List[str]]:
    """
    Collect consecutive lines that form a plain paragraph block.
    Stops at blank line or any structure-sensitive line.
    """
    buf: List[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            break
        if _should_skip_line(line):
            break
        if _is_indented_code(line):
            break
        if TABLE_ROW_RE.match(line):
            break
        if _is_new_list_item(line):
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

        # Tables: copy contiguous table block unchanged
        if _is_table_block(lines, i):
            out.append(lines[i])
            out.append(lines[i + 1])
            i += 2
            while i < len(lines) and TABLE_ROW_RE.match(lines[i]):
                out.append(lines[i])
                i += 1
            continue

        # Skip lines that should never be reflowed
        if _should_skip_line(line) or _is_indented_code(line):
            out.append(line)
            i += 1
            continue

        # List item wrapping
        if _is_new_list_item(line):
            next_i, base_indent, marker, checkbox, payload = _collect_list_item(lines, i)

            # If we detected unsafe content for this list item, copy original line(s) unchanged.
            if payload == "__DO_NOT_TOUCH_LIST_ITEM__":
                out.extend(lines[i:next_i])
                i = next_i

                # Preserve following blank line if present
                if i < len(lines) and not lines[i].strip():
                    out.append(lines[i])
                    i += 1
                continue

            prefix = f"{base_indent}{marker} {checkbox}"
            subsequent = " " * len(prefix)

            if payload and len(prefix) + 1 + len(payload) > MAX_LEN:
                out.extend(_wrap_text(payload, initial_indent=prefix, subsequent_indent=subsequent))
            else:
                # Keep item as-is (but normalize single-space after prefix)
                out.append(f"{prefix}{payload}".rstrip())

            i = next_i

            # Preserve following blank line if present
            if i < len(lines) and not lines[i].strip():
                out.append(lines[i])
                i += 1
            continue

        # Regular paragraph wrapping
        next_i, para_lines = _collect_paragraph(lines, i)
        para_text = " ".join(s.strip() for s in para_lines).strip()

        if para_text and len(para_text) > MAX_LEN and any(len(l) > MAX_LEN for l in para_lines):
            out.extend(_wrap_text(para_text))
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
        print("Usage: fix_md013_line_length_option_b.py <file-or-directory>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])
    if not root.exists():
        print(f"ERROR: path not found: {root}", file=sys.stderr)
        return 2
    if not (root.is_file() or root.is_dir()):
        print(f"ERROR: path must be a file or directory: {root}", file=sys.stderr)
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
