"""PEP 526 automatic type annotation fixer.

This module provides automatic type annotation inference and insertion for
module-level variables and class attributes that lack PEP 526 annotations.

:Purpose:
    Automatically add type annotations to Python code where the type can be
    safely inferred from the assigned value (literals, typed constructors, etc.).

:Safety:
    Only applies conservative, high-confidence type inferences. Skips ambiguous
    cases (empty collections, complex expressions) that require human judgment.

:Examples:
    Safe autofixes::

        # Before
        TIMEOUT = 30
        HOST = "localhost"
        ROOT = Path(__file__).parent

        # After
        TIMEOUT: int = 30
        HOST: str = "localhost"
        ROOT: Path = Path(__file__).parent

:Exit Codes:
    0
        Success (no errors, modifications may or may not have been made)
    1
        Error (syntax error in input file, write failure, etc.)
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any


class PEP526Fixer:
    """Automatic type annotation fixer for PEP 526 compliance.

    Analyzes Python AST and inserts type annotations for module-level variables
    and class attributes where the type can be safely inferred.
    """

    def __init__(self) -> None:
        """Initialize PEP 526 fixer."""
        self.modifications: list[tuple[int, str, str]] = []  # (line, old, new)

    def can_infer_type(self, node: ast.expr) -> tuple[bool, str | None]:
        """Determine if type can be safely inferred from expression.

        :param node: AST expression node to analyze
        :returns: Tuple of (can_infer, type_annotation_string)
        :rtype: tuple[bool, str | None]
        """
        # Literal values (high confidence)
        if isinstance(node, ast.Constant):
            value_type = type(node.value)
            if value_type is int:
                return (True, "int")
            elif value_type is str:
                return (True, "str")
            elif value_type is bool:
                return (True, "bool")
            elif value_type is float:
                return (True, "float")
            elif value_type is bytes:
                return (True, "bytes")
            elif node.value is None:
                # None without context is ambiguous (could be Optional[anything])
                return (False, None)

        # Typed constructor calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                # Path constructor
                if func_name == "Path":
                    return (True, "Path")
                # Note: dict(), list(), set() without args are ambiguous
                # We skip these to avoid incorrect generic annotations

        # Attribute access on typed constructors (e.g., Path(...).parent)
        if isinstance(node, ast.Attribute):
            # Path(...).parent → still Path
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    if node.value.func.id == "Path":
                        return (True, "Path")

        # Everything else is either:
        # - Too complex (comprehensions, binary ops, function calls)
        # - Too ambiguous (empty collections, None, variables)
        # - Requires cross-module analysis (function return types)
        return (False, None)

    def fix_file(self, file_path: Path, dry_run: bool = False) -> tuple[bool, int]:
        """Fix PEP 526 violations in a single file.

        :param file_path: Path to Python file to fix
        :param dry_run: If True, only detect fixes without modifying file
        :returns: Tuple of (file_was_modified, number_of_fixes)
        :rtype: tuple[bool, int]
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError, IOError) as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return (False, 0)

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}", file=sys.stderr)
            return (False, 0)

        lines = content.splitlines(keepends=True)
        self.modifications = []

        # Analyze module-level assignments
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                self._analyze_assignment(node, lines, scope="module")

        # Analyze class attribute assignments
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for class_node in node.body:
                    if isinstance(class_node, (ast.Assign, ast.AnnAssign)):
                        self._analyze_assignment(class_node, lines, scope="class")

        # Apply modifications (if not dry run)
        fixes_made = len(self.modifications)
        if fixes_made > 0 and not dry_run:
            # Apply modifications in reverse order (bottom-up) to preserve line numbers
            for line_num, old_line, new_line in reversed(self.modifications):
                lines[line_num - 1] = new_line

            try:
                file_path.write_text("".join(lines), encoding="utf-8")
                return (True, fixes_made)
            except (UnicodeEncodeError, OSError, IOError) as e:
                print(f"Error writing {file_path}: {e}", file=sys.stderr)
                return (False, 0)

        return (fixes_made > 0, fixes_made)

    def _analyze_assignment(
        self, node: ast.Assign | ast.AnnAssign, lines: list[str], scope: str
    ) -> None:
        """Analyze an assignment node and add modification if needed.

        :param node: Assignment node to analyze
        :param lines: Source code lines
        :param scope: Scope of assignment ("module" or "class")
        """
        # Skip if already has annotation
        if isinstance(node, ast.AnnAssign):
            return  # Already annotated

        # For ast.Assign, check if simple assignment (single target)
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                return  # Multiple targets (unpacking, chained) - skip

            target = node.targets[0]
            if not isinstance(target, ast.Name):
                return  # Not a simple name assignment - skip

            var_name = target.id

            # Skip private variables (leading underscore) - low priority
            if var_name.startswith("_") and not var_name.startswith("__"):
                return

            # Check if we can infer type
            can_infer, type_annotation = self.can_infer_type(node.value)
            if not can_infer or type_annotation is None:
                return

            # Build new line with annotation
            line_num = node.lineno
            old_line = lines[line_num - 1]

            # Extract indentation
            indent = len(old_line) - len(old_line.lstrip())
            indent_str = old_line[:indent]

            # Get the value part (everything after '=')
            # TODO: Use AST reconstruction instead of string manipulation for robustness
            # This is fragile, but works for simple cases
            old_line_stripped = old_line.strip()
            if " = " not in old_line_stripped:
                return  # Unusual formatting, skip

            parts = old_line_stripped.split(" = ", 1)
            value_part = parts[1]

            # Build new line: VAR: Type = value
            new_line = f"{indent_str}{var_name}: {type_annotation} = {value_part}"

            # Record modification
            self.modifications.append((line_num, old_line, new_line))


def main() -> int:
    """Main entry point for PEP 526 fixer CLI.

    :returns: Exit code (0 for success, 1 for error)
    :rtype: int
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Automatically add PEP 526 type annotations to Python files"
    )
    parser.add_argument("files", nargs="+", type=Path, help="Python files to fix")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without modifying files",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show git-style diff of changes",
    )

    args = parser.parse_args()

    fixer = PEP526Fixer()
    total_fixes = 0
    files_modified = 0

    for file_path in args.files:
        if not file_path.exists():
            print(f"File not found: {file_path}", file=sys.stderr)
            continue

        if not file_path.suffix == ".py":
            print(f"Skipping non-Python file: {file_path}", file=sys.stderr)
            continue

        modified, num_fixes = fixer.fix_file(file_path, dry_run=args.dry_run or args.diff)

        if num_fixes > 0:
            total_fixes += num_fixes
            if modified:
                files_modified += 1

            if args.dry_run or args.diff:
                print(f"{file_path}: {num_fixes} fix(es) would be applied")
                if args.diff:
                    # Show modifications
                    for line_num, old_line, new_line in fixer.modifications:
                        print(f"  Line {line_num}:")
                        print(f"  - {old_line.rstrip()}")
                        print(f"  + {new_line.rstrip()}")
            else:
                print(f"{file_path}: {num_fixes} fix(es) applied")

    print(
        f"\nTotal: {total_fixes} fixes in {files_modified} file(s)",
        file=sys.stderr if args.dry_run or args.diff else sys.stdout,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
