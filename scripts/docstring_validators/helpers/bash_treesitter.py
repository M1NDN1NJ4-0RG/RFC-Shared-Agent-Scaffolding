#!/usr/bin/env python3
# noqa: EXITCODES
"""Tree-sitter based Bash parser for symbol extraction.

This module uses tree-sitter with a pinned Bash grammar to parse Bash scripts
and extract function definitions WITHOUT executing the script (per Phase 0 Item 0.9.4).

:Purpose:
    Provide structure-aware Bash parsing for docstring validation.
    Replaces regex-based "wishful thinking" parsing.

:Environment Variables:
    None

:Examples:
    Parse a Bash script::

        from helpers.bash_treesitter import parse_bash_functions
        functions = parse_bash_functions(file_path)

:Exit Codes:
    N/A - This is a library module, not an executable script
"""

from pathlib import Path
from typing import Dict, List, Optional

try:
    import tree_sitter_bash as tsbash
    from tree_sitter import Language, Parser

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


def parse_bash_functions(file_path: Path) -> Dict[str, any]:
    """Parse Bash script and extract function definitions using tree-sitter.

    :param file_path: Path to Bash script file

    :returns: Dictionary with 'functions' list and 'errors' list
              Each function dict contains: name, line, has_doc_comment
    """
    if not TREE_SITTER_AVAILABLE:
        # tree-sitter not installed - return empty result
        return {"functions": [], "errors": ["tree-sitter-bash not installed"]}

    try:
        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Initialize parser with Bash language
        parser = Parser()
        # Use tree-sitter-bash pinned version
        bash_language = Language(tsbash.language())
        parser.set_language(bash_language)

        # Parse the file
        tree = parser.parse(bytes(content, "utf8"))

        # Extract functions
        functions = []
        errors = []

        # Query for function definitions
        # Bash tree-sitter grammar uses "function_definition" nodes
        root_node = tree.root_node

        def find_functions(node):
            """Recursively find all function_definition nodes."""
            if node.type == "function_definition":
                # Extract function name
                name_node = node.child_by_field_name("name")
                if name_node:
                    func_name = content[name_node.start_byte : name_node.end_byte]
                    func_line = name_node.start_point[0] + 1  # 0-indexed to 1-indexed

                    # Check for comment block immediately preceding the function
                    has_doc = _check_for_doc_comment(node, content, root_node)

                    functions.append(
                        {
                            "name": func_name,
                            "line": func_line,
                            "has_doc_comment": has_doc,
                        }
                    )

            # Recurse to children
            for child in node.children:
                find_functions(child)

        find_functions(root_node)

        return {"functions": functions, "errors": errors}

    except Exception as e:
        return {"functions": [], "errors": [f"Failed to parse Bash script: {str(e)}"]}


def _check_for_doc_comment(func_node, content: str, root_node) -> bool:
    """Check if a function has a documentation comment preceding it.

    Looks for comment lines immediately before the function definition.

    :param func_node: tree-sitter node for the function_definition
    :param content: File content as string
    :param root_node: Root node of the tree

    :returns: True if doc comment found, False otherwise
    """
    # Get the line before the function starts
    func_start_line = func_node.start_point[0]

    if func_start_line == 0:
        return False  # Function at start of file

    # Look for comments in the lines immediately before the function
    # Strategy: scan backwards from func_start_line to find comment nodes
    # This is a simplified approach - a more robust one would traverse the tree

    lines = content.split("\n")

    # Check lines immediately before function (up to 20 lines back)
    comment_lines = []
    for i in range(max(0, func_start_line - 20), func_start_line):
        line = lines[i].strip()
        if line.startswith("#"):
            comment_lines.append(line)
        elif line == "":
            # Empty line - continue looking
            continue
        else:
            # Non-comment, non-empty line - stop looking
            break

    # If we found comment lines, consider it documented
    # Filter out shebang
    comment_lines = [c for c in comment_lines if not c.startswith("#!")]

    return len(comment_lines) > 0
