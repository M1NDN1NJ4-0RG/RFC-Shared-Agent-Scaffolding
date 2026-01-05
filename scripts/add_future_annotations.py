#!/usr/bin/env python3
"""
Add 'from __future__ import annotations' to Python files.

Uses AST parsing to ensure correct placement after module docstrings.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def add_future_import(file_path: Path) -> bool:
    """
    Add 'from __future__ import annotations' to a Python file.

    Returns True if the file was modified, False otherwise.
    """
    content = file_path.read_text()

    # Parse to check if already has the import
    try:
        tree = ast.parse(content)
    except SyntaxError:
        print(f"Skipping {file_path} (syntax error)")
        return False

    # Check if already has future annotations import
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "__future__" and any(alias.name == "annotations" for alias in node.names):
                return False  # Already has it

    lines = content.splitlines(keepends=True)

    # Find where to insert
    insert_line = 0

    # Skip shebang and encoding
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            if i == 0 and stripped.startswith("#!"):
                insert_line = i + 1
                continue
            if "coding:" in stripped or "coding=" in stripped:
                insert_line = i + 1
                continue
        break

    # Check for module docstring
    if tree.body and isinstance(tree.body[0], ast.Expr):
        if isinstance(tree.body[0].value, (ast.Str, ast.Constant)):
            # Module docstring exists - insert after it
            # tree.body[0].end_lineno is 1-indexed
            insert_line = tree.body[0].end_lineno

    # Insert the import
    import_line = "from __future__ import annotations\n"

    # If there's content after insert point, add blank line
    if insert_line < len(lines):
        # Check if there's already a blank line
        if insert_line < len(lines) and lines[insert_line].strip():
            import_line += "\n"

    lines.insert(insert_line, import_line)

    # Write back
    file_path.write_text("".join(lines))
    return True


def main():
    """Add future annotations to all Python files in tools/repo_lint."""
    repo_root = Path(__file__).parent.parent
    tools_dir = repo_root / "tools" / "repo_lint"

    if not tools_dir.exists():
        print(f"Error: {tools_dir} does not exist")
        sys.exit(1)

    py_files = list(tools_dir.rglob("*.py"))
    modified = []

    for py_file in py_files:
        if add_future_import(py_file):
            modified.append(py_file)
            print(f"Modified: {py_file.relative_to(repo_root)}")

    print(f"\nTotal: {len(py_files)} files, {len(modified)} modified")


if __name__ == "__main__":
    main()
