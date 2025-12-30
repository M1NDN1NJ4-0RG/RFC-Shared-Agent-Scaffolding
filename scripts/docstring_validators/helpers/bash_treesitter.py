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
from typing import Any, Dict

try:
    import tree_sitter_bash as tsbash
    from tree_sitter import Language, Parser

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


def parse_bash_functions(file_path: Path) -> Dict[str, Any]:
    """Parse Bash script and extract function definitions using tree-sitter.

    :param file_path: Path to Bash script file

    :returns: Dictionary with 'functions' list and 'errors' list
              Each function dict contains: name, line, has_doc_comment
    """
    if not TREE_SITTER_AVAILABLE:
        # tree-sitter not installed - return empty result
        return {"functions": [], "errors": ["tree-sitter-bash not installed"]}

    try:
        # Read file content as bytes (tree-sitter works with bytes)
        with open(file_path, "rb") as f:
            content_bytes = f.read()

        # Also read as text for display/comment checking
        try:
            content_text = content_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            return {"functions": [], "errors": [f"File contains invalid UTF-8 encoding: {e}"]}

        # Initialize parser with Bash language
        # Handle both tree-sitter < 0.25 and >= 0.25 API versions
        parser = Parser()
        lang_obj = Language(tsbash.language())

        # Try newer API first (0.25+), fallback to older API
        if hasattr(parser, "language"):
            parser.language = lang_obj
        elif hasattr(parser, "set_language"):
            parser.set_language(lang_obj)
        else:
            return {"functions": [], "errors": ["Unsupported tree-sitter API version"]}

        # Parse the file (pass bytes directly)
        tree = parser.parse(content_bytes)

        # Extract functions
        functions = []
        errors = []

        # Query for function definitions
        # Bash tree-sitter grammar uses "function_definition" nodes
        root_node = tree.root_node

        def find_functions(node):
            """Recursively find all function_definition nodes.

            :param node: Tree-sitter node to search
            :type node: tree_sitter.Node
            """
            if node.type == "function_definition":
                # Extract function name - it's a "word" child node, not a named field
                func_name = None
                for child in node.children:
                    if child.type == "word":
                        # Extract name using byte offsets
                        func_name = content_bytes[child.start_byte : child.end_byte].decode("utf-8").strip()
                        break

                if not func_name:
                    # Couldn't extract name, skip
                    for child in node.children:
                        find_functions(child)
                    return

                func_line = node.start_point[0] + 1  # 0-indexed to 1-indexed

                # Check for comment block immediately preceding the function
                has_doc = _check_for_doc_comment(node, content_text)

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


def _check_for_doc_comment(func_node, content: str) -> bool:
    """Check if a function has a documentation comment preceding it.

    Looks for comment lines immediately before the function definition.

    :param func_node: tree-sitter node for the function_definition
    :param content: File content as string

    :returns: True if doc comment found, False otherwise
    """
    # Get the line before the function starts
    func_start_line = func_node.start_point[0]

    if func_start_line == 0:
        return False  # Function at start of file

    # Look for comments in the lines immediately before the function
    lines = content.split("\n")

    # Check lines immediately before function (up to 10 lines back)
    # Reduced from 20 to avoid incorrectly associating comments from previous functions
    comment_lines = []
    for i in range(max(0, func_start_line - 10), func_start_line):
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
