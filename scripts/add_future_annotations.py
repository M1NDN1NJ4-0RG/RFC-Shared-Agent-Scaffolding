#!/usr/bin/env python3
"""Add 'from __future__ import annotations' to Python files safely.

This script walks the repository and adds the future import to all Python files
in the correct location, respecting shebangs, encoding cookies, and module docstrings.

:Purpose:
    Enables PEP 563 postponed evaluation of annotations repo-wide, which improves
    type hinting performance and allows forward references without quotes.

:Implementation:
    Uses Python's tokenize module (NOT regex) to safely parse and insert the import
    at the correct location. The script is idempotent and never modifies files that
    already contain the import.

:Usage:
    Check which files would be modified::

        python3 scripts/add_future_annotations.py --check

    Apply changes to all eligible files::

        python3 scripts/add_future_annotations.py --apply

    Apply with verbose output::

        python3 scripts/add_future_annotations.py --apply --verbose

:Arguments:
    --check
        Dry-run mode. Exit 0 if no changes needed, exit 1 if changes would be made.
        Does not modify any files.
    --apply
        Apply changes to all eligible files.
    --verbose
        Print each file that is checked or modified.

:Exit Codes:
    0
        Success (--apply) or no changes needed (--check)
    1
        Changes would be made (--check only) or validation error
    2
        Invalid arguments or internal error

:Environment Variables:
    None. Script operates on current directory and repository structure.

:Examples:
    Check which files would be modified::

        python3 scripts/add_future_annotations.py --check --verbose

    Apply changes::

        python3 scripts/add_future_annotations.py --apply

:Notes:
    - Skips virtualenvs, build directories, and git internals
    - Preserves shebang lines, encoding cookies, and module docstrings
    - Never creates duplicate imports
    - Never reorders existing imports except to insert this one line
"""

from __future__ import annotations

import argparse
import io
import sys
import tokenize
from pathlib import Path
from typing import List, Tuple

# Directories to skip when walking the repository
SKIP_DIRS = {
    ".venv",
    ".venv-lint",
    ".tox",
    "site-packages",
    "dist",
    "build",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "egg-info",
}


def should_skip_file(file_path: Path) -> bool:
    """Check if a file should be skipped based on path components.

    :param file_path: Path to check
    :return: True if file should be skipped
    """
    # Skip if any parent directory is in SKIP_DIRS
    for part in file_path.parts:
        if part in SKIP_DIRS or part.endswith(".egg-info"):
            return True
    return False


def has_future_import(content: str) -> bool:
    """Check if content already has 'from __future__ import annotations'.

    :param content: File content to check
    :return: True if import exists anywhere in file
    """
    # Quick check: look for the import anywhere in the file
    # This covers all valid forms including multi-line imports
    lines = content.split("\n")
    for line in lines:
        stripped = line.strip()
        if "from __future__ import" in stripped and "annotations" in stripped:
            return True
    return False


def find_insertion_point(content: str) -> Tuple[int, int]:
    """Find the correct line and column to insert the future import.

    Uses tokenize to safely parse shebang, encoding, and docstring.

    :param content: File content as string
    :return: Tuple of (line_number, column) for insertion (1-indexed line)
    """
    if not content.strip():
        # Empty file - insert at line 1
        return 1, 0

    # Tokenize the content
    tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))

    # Track what we've seen
    seen_encoding = False
    insert_line = 1
    insert_col = 0

    # First, check for shebang and encoding in comments
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if i == 1 and stripped.startswith("#!"):
            insert_line = i + 1
        elif not seen_encoding and stripped.startswith("#") and ("coding" in stripped or "encoding" in stripped):
            seen_encoding = True
            insert_line = i + 1
        elif not stripped.startswith("#"):
            # No more header comments
            break

    # Now look for module docstring using tokens
    for i, token in enumerate(tokens):
        if token.type == tokenize.STRING:
            # This could be a module docstring
            # It's a module docstring if it's the first statement
            # Check if there are only ENCODING, NEWLINE, NL, COMMENT, or INDENT tokens before it
            is_module_docstring = True
            for prev_token in tokens[:i]:
                if prev_token.type not in (
                    tokenize.ENCODING,
                    tokenize.NEWLINE,
                    tokenize.NL,
                    tokenize.COMMENT,
                    tokenize.INDENT,
                    tokenize.DEDENT,
                ):
                    is_module_docstring = False
                    break

            if is_module_docstring:
                # Insert after the docstring
                # The docstring ends at token.end[0], insert after it
                insert_line = token.end[0] + 1
                insert_col = 0
            break

    # If we haven't found a docstring but we've seen headers, use that position
    # Otherwise, insert at line 1 (or after headers if they exist)
    return insert_line, insert_col


def add_future_import(content: str) -> str:
    """Add 'from __future__ import annotations' at the correct location.

    :param content: Original file content
    :return: Modified content with import added
    """
    if has_future_import(content):
        return content

    insert_line, _ = find_insertion_point(content)
    lines = content.split("\n")

    # Handle the case where we need to insert at a line that doesn't exist yet
    while len(lines) < insert_line:
        lines.append("")

    # Build the import statement
    import_stmt = "from __future__ import annotations"

    # Insert the import at the correct position
    # PEP 8: Exactly one blank line between module docstring and first import
    if insert_line > len(lines):
        # Append to end (shouldn't happen but handle it)
        lines.append("")
        lines.append(import_stmt)
    else:
        # Insert at the specified line
        if 1 < insert_line <= len(lines):
            # insert_line points to the line after the docstring
            # Check what's at that position and before
            line_before = lines[insert_line - 2] if insert_line >= 2 else ""
            current_line = lines[insert_line - 1] if insert_line <= len(lines) else ""

            # If current line is blank, insert import there and keep the spacing
            if not current_line.strip():
                # There's already a blank line - insert the import after it
                lines.insert(insert_line, import_stmt)
            elif line_before.strip():
                # Previous line has content (docstring end), add blank line then import
                lines.insert(insert_line - 1, "")
                lines.insert(insert_line, import_stmt)
            else:
                # Previous line is blank, just insert import
                lines.insert(insert_line - 1, import_stmt)
        else:
            # Insert at the beginning
            lines.insert(0, import_stmt)

        # Ensure blank line after import if there's content following
        # Find where the import actually ended up
        import_idx = lines.index(import_stmt)
        next_idx = import_idx + 1
        if next_idx < len(lines) and lines[next_idx].strip():
            # There's content immediately after, insert blank line
            lines.insert(next_idx, "")

    return "\n".join(lines)


def process_file(file_path: Path, apply: bool, verbose: bool) -> bool:
    """Process a single Python file.

    :param file_path: Path to Python file
    :param apply: If True, write changes; if False, only check
    :param verbose: If True, print status messages
    :return: True if file was/would be modified
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            original_content = f.read()
    except UnicodeDecodeError:
        # Skip files that can't be decoded as UTF-8
        if verbose:
            print(f"Skipping {file_path}: Cannot decode as UTF-8")
        return False
    except Exception as e:
        if verbose:
            print(f"Skipping {file_path}: {e}")
        return False

    # Check if modification needed
    if has_future_import(original_content):
        if verbose:
            print(f"Skipping {file_path}: Already has future import")
        return False

    # Generate modified content
    modified_content = add_future_import(original_content)

    if modified_content == original_content:
        # No change (shouldn't happen if has_future_import is correct)
        return False

    # Apply or report
    if apply:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
        if verbose:
            print(f"Modified: {file_path}")
    else:
        if verbose:
            print(f"Would modify: {file_path}")

    return True


def find_python_files(root: Path) -> List[Path]:
    """Find all Python files in the repository.

    :param root: Repository root path
    :return: List of Python file paths
    """
    python_files = []
    for py_file in root.rglob("*.py"):
        if not should_skip_file(py_file):
            python_files.append(py_file)
    return python_files


def main() -> int:
    """Main entry point.

    :return: Exit code
    """
    parser = argparse.ArgumentParser(description="Add 'from __future__ import annotations' to Python files")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check which files would be modified (exit 1 if changes needed)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.check and not args.apply:
        print("Error: Must specify either --check or --apply", file=sys.stderr)
        return 2

    if args.check and args.apply:
        print("Error: Cannot specify both --check and --apply", file=sys.stderr)
        return 2

    # Find repository root (current directory or walk up to find .git)
    root = Path.cwd()
    while root != root.parent:
        if (root / ".git").exists():
            break
        root = root.parent

    if not (root / ".git").exists():
        print("Error: Not in a git repository", file=sys.stderr)
        return 2

    # Find Python files
    python_files = find_python_files(root)

    if args.verbose:
        print(f"Found {len(python_files)} Python files")

    # Process files
    modified_count = 0
    for py_file in python_files:
        if process_file(py_file, apply=args.apply, verbose=args.verbose):
            modified_count += 1

    # Report results
    if args.check:
        if modified_count > 0:
            print(f"{modified_count} file(s) would be modified")
            return 1
        else:
            print("No changes needed")
            return 0
    else:  # apply
        print(f"Modified {modified_count} file(s)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
