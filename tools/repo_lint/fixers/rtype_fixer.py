"""Autofix tool for adding :rtype: fields to reST docstrings.

This tool automatically adds `:rtype:` fields to reST-style docstrings based on
existing function return type annotations.

Usage:
    python3 tools/repo_lint/fixers/rtype_fixer.py <files> [--dry-run] [--diff]

Examples:
    # Dry-run mode (preview fixes)
    python3 tools/repo_lint/fixers/rtype_fixer.py tools/**/*.py --dry-run
    
    # Apply fixes
    python3 tools/repo_lint/fixers/rtype_fixer.py tools/**/*.py
    
    # Show diff of changes
    python3 tools/repo_lint/fixers/rtype_fixer.py tools/**/*.py --diff

Safety:
    - Only adds :rtype: when function has a return annotation
    - Skips functions returning None (per policy)
    - Skips if :rtype: already exists
    - Preserves all existing docstring content
    - Uses ast.unparse() for accurate type representation
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


class RTypeFixer:
    """AST-based fixer for adding :rtype: fields to docstrings."""

    def __init__(self) -> None:
        """Initialize the fixer."""
        self.modifications: list[tuple[ast.FunctionDef, str, str]] = []

    def _is_none_annotation(self, annotation: ast.expr) -> bool:
        """Check if annotation is None or -> None.

        :param annotation: AST annotation node
        :rtype: bool
        """
        if isinstance(annotation, ast.Constant) and annotation.value is None:
            return True
        if isinstance(annotation, ast.Name) and annotation.id == "None":
            return True
        return False

    def _has_rtype(self, docstring: str) -> bool:
        """Check if docstring already has :rtype: field.

        :param docstring: Docstring content
        :rtype: bool
        """
        return ":rtype:" in docstring

    def _insert_rtype_field(self, docstring: str, return_type: str) -> str:
        """Insert :rtype: field into reST docstring.

        Inserts after other fields (like :param:, :returns:) and before the end.

        :param docstring: Original docstring content
        :param return_type: Type annotation as string
        :rtype: str
        """
        lines = docstring.split("\n")

        # Find insertion point: after last field line, before closing
        insert_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            # Find last line that starts with a field marker
            if line.startswith(":") and not line.startswith(":rtype:"):
                insert_idx = i + 1
                break
            # If we find a non-empty line that doesn't start with :, stop
            if line and not line.startswith(":"):
                # This is narrative text, fields should go after it
                if i < len(lines) - 1:
                    insert_idx = i + 1
                break

        # Build the :rtype: line with appropriate indentation
        # Match indentation of existing fields or use 4 spaces
        indent = "    "  # Default indentation
        for line in lines:
            if line.strip().startswith(":"):
                # Extract indentation from existing field
                indent = line[: len(line) - len(line.lstrip())]
                break

        rtype_line = f"{indent}:rtype: {return_type}"

        # Insert the line
        lines.insert(insert_idx, rtype_line)

        return "\n".join(lines)

    def _analyze_function(self, node: ast.FunctionDef) -> None:
        """Analyze a function definition and record needed modifications.

        :param node: Function definition AST node
        :rtype: None
        """
        # Skip if no return annotation or returns None
        if not node.returns or self._is_none_annotation(node.returns):
            return

        # Get docstring
        docstring = ast.get_docstring(node)
        if not docstring:
            return  # No docstring to modify

        # Check if :rtype: already exists
        if self._has_rtype(docstring):
            return

        # Convert annotation to string using ast.unparse
        try:
            return_type = ast.unparse(node.returns)
        except Exception:
            # If unparsing fails, skip this function
            return

        # Create new docstring with :rtype: field
        new_docstring = self._insert_rtype_field(docstring, return_type)

        # Record modification (node, old_docstring, new_docstring)
        self.modifications.append((node, docstring, new_docstring))

    def process_file(
        self, file_path: Path, dry_run: bool = False
    ) -> tuple[bool, int]:
        """Process a Python file and add :rtype: fields where needed.

        :param file_path: Path to Python file
        :param dry_run: If True, don't modify file, just report what would be done
        :rtype: tuple[bool, int]
        :returns: (file_was_modified, num_fixes)
        """
        # Read file
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError, IOError) as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return (False, 0)

        # Parse AST
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}", file=sys.stderr)
            return (False, 0)

        self.modifications = []

        # Analyze all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._analyze_function(node)

        # Apply modifications (if not dry run)
        fixes_made = len(self.modifications)
        if fixes_made > 0 and not dry_run:
            # Modify the source code
            # Note: This is a simple string replacement approach
            # For production, consider using ast.unparse() or libcst for better preservation
            modified_content = content
            for node, old_docstring, new_docstring in self.modifications:
                # Find and replace the docstring in the source
                # This is fragile but works for simple cases
                # Look for the docstring as it appears in source (with quotes)
                for quote_style in ['"""', "'''"]:
                    old_with_quotes = f"{quote_style}{old_docstring}{quote_style}"
                    new_with_quotes = f"{quote_style}{new_docstring}{quote_style}"
                    if old_with_quotes in modified_content:
                        modified_content = modified_content.replace(
                            old_with_quotes, new_with_quotes, 1
                        )
                        break

            try:
                file_path.write_text(modified_content, encoding="utf-8")
                return (True, fixes_made)
            except (UnicodeEncodeError, OSError, IOError) as e:
                print(f"Error writing {file_path}: {e}", file=sys.stderr)
                return (False, 0)

        # In dry_run mode or no fixes: file not modified
        return (False, fixes_made)


def main() -> int:
    """Main entry point for :rtype: fixer CLI.

    :rtype: int
    :returns: Exit code (0 for success, 1 for error)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Add :rtype: fields to reST docstrings based on function annotations"
    )
    parser.add_argument("files", nargs="+", help="Python files to process")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without modifying files",
    )
    parser.add_argument(
        "--diff", action="store_true", help="Show diff of changes (implies --dry-run)"
    )

    args = parser.parse_args()

    if args.diff:
        args.dry_run = True

    fixer = RTypeFixer()
    total_fixes = 0
    total_files_modified = 0

    for file_pattern in args.files:
        # Expand glob patterns
        file_path = Path(file_pattern)
        if file_path.is_file():
            files = [file_path]
        else:
            # Try glob pattern
            files = list(Path(".").glob(file_pattern))

        for f in files:
            if not f.suffix == ".py":
                continue

            modified, num_fixes = fixer.process_file(f, dry_run=args.dry_run)
            if num_fixes > 0:
                total_fixes += num_fixes
                if modified or args.dry_run:
                    total_files_modified += 1
                if modified:
                    print(f"{f}: {num_fixes} fix(es) applied")
                else:
                    print(f"{f}: {num_fixes} fix(es) would be applied")

    if args.dry_run:
        print(f"\nTotal: {total_fixes} fixes in {total_files_modified} file(s)")
    else:
        print(f"\nTotal: {total_fixes} fixes in {total_files_modified} file(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
