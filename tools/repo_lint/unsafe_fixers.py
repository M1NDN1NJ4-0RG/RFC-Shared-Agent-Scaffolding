# noqa: EXITCODES

"""Unsafe fixers for repo_lint.

from __future__ import annotations


:Purpose:
    Implements unsafe fixers that can modify code behavior or semantics.
    These fixers are ONLY enabled with --unsafe --yes-i-know flags and
    are FORBIDDEN in CI.

:Unsafe Fixers:
    - unsafe_docstring_rewrite: Rewrites docstrings to match repo conventions
    - (More fixers can be added here in the future)

:Safety:
    - All unsafe fixers MUST be explicitly named
    - All unsafe fixers MUST log why they are unsafe
    - All unsafe fixers MUST generate forensic artifacts (patch + log)
    - AI agents MUST NOT run unsafe fixers without human permission

:Environment Variables:
    None - all configuration is passed as function parameters.

:Exit Codes:
    N/A - This is a library module, not an executable.

:Examples:
    Apply unsafe fixers to a file::

        from pathlib import Path
        from tools.repo_lint.unsafe_fixers import apply_unsafe_fixes

        files = [Path("example.py")]
        results = apply_unsafe_fixes(files)

        for result in results:
            print(f"Fixed: {result.file_path}")
            print(f"Fixer: {result.fixer_name}")
            print(f"Why unsafe: {result.why_unsafe}")

:See Also:
    - docs/contributing/ai-constraints.md - AI safety constraints
    - Phase 7 requirements in new-requirement-phase-7.md
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Protocol


class UnsafeFixer(Protocol):
    """Protocol for unsafe fixers.

    All unsafe fixers must implement this interface:
    - can_fix(file_path): Check if fixer applies to this file
    - fix(file_path): Apply the unsafe fix and return result
    """

    def can_fix(self, file_path: Path) -> bool:
        """Check if this fixer can fix the given file.

        :param file_path: Path to file to check
        :returns: True if this fixer applies to this file
        """
        ...  # pylint: disable=unnecessary-ellipsis

    def fix(self, file_path: Path) -> Optional["UnsafeFixerResult"]:
        """Apply the unsafe fix to the file.

        :param file_path: Path to file to fix
        :returns: Result of the fix operation, or None if no changes made
        """
        ...  # pylint: disable=unnecessary-ellipsis


@dataclass
class UnsafeFixerResult:
    """Result from running an unsafe fixer.

    :param fixer_name: Name of the unsafe fixer that ran
    :param file_path: Path to the file that was modified
    :param changes_made: Human-readable description of changes
    :param why_unsafe: Explanation of why this fixer is unsafe
    :param before_content: File content before fix (for patch generation)
    :param after_content: File content after fix (for patch generation)
    """

    fixer_name: str
    file_path: Path
    changes_made: str
    why_unsafe: str
    before_content: str
    after_content: str


class UnsafeDocstringRewriter:
    """Unsafe fixer that rewrites docstrings to match repo conventions.

    :Purpose:
        Rewrites Python docstrings to use Sphinx-style :param: and :returns:
        instead of other formats (Google-style, NumPy-style, etc.).

    :Why Unsafe:
        This can change the semantic meaning of documentation by
        reformatting parameter descriptions or return value descriptions.
        It may also incorrectly parse complex docstrings.

    :Usage:
        Only use with explicit human permission via --unsafe --yes-i-know.
    """

    def __init__(self):
        """Initialize the unsafe docstring rewriter."""
        self.name = "unsafe_docstring_rewrite"
        self.why_unsafe = (
            "Rewrites docstring format which may change semantic meaning "
            + "or incorrectly parse complex documentation"
        )

    def can_fix(self, file_path: Path) -> bool:
        """Check if this fixer can process the given file.

        :param file_path: Path to check
        :returns: True if file is a Python file
        """
        return file_path.suffix == ".py"

    def fix(self, file_path: Path) -> Optional[UnsafeFixerResult]:
        """Apply unsafe docstring rewriting to a Python file.

        :param file_path: Path to Python file to fix
        :returns: UnsafeFixerResult if changes were made, None otherwise
        """
        if not file_path.exists():
            return None

        before_content = file_path.read_text()
        after_content = self._rewrite_docstrings(before_content)

        if before_content == after_content:
            return None  # No changes needed

        # Write changes to file
        file_path.write_text(after_content)

        return UnsafeFixerResult(
            fixer_name=self.name,
            file_path=file_path,
            changes_made="Rewrote docstrings to Sphinx :param:/:returns: format",
            why_unsafe=self.why_unsafe,
            before_content=before_content,
            after_content=after_content,
        )

    def _rewrite_docstrings(self, content: str) -> str:
        """Rewrite Google-style docstrings to Sphinx format.

        :param content: File content to process
        :returns: Content with rewritten docstrings
        """
        # This is a minimal implementation - just handles simple cases
        # Real implementation would need proper AST parsing

        lines = content.split("\n")
        result_lines = []
        in_docstring = False
        in_args_section = False
        in_returns_section = False

        for line in lines:
            # Detect docstring start/end
            if '"""' in line:
                if not in_docstring:
                    in_docstring = True
                elif line.strip() == '"""' or line.rstrip().endswith('"""'):
                    in_docstring = False
                    in_args_section = False
                    in_returns_section = False

            # Convert Google-style Args: to :param:
            if in_docstring and "Args:" in line:
                in_args_section = True
                continue  # Skip the "Args:" line

            if in_docstring and in_args_section:
                # Match "    name: description" or "    name (type): description"
                match = re.match(r"^(\s+)(\w+)(\s*\(.*?\))?\s*:\s*(.+)$", line)
                if match:
                    indent, param_name, _param_type, description = match.groups()
                    # Convert to Sphinx format
                    result_lines.append(f"{indent}:param {param_name}: {description}")
                    continue
                if line.strip() and not line.strip().startswith(":"):
                    # End of Args section
                    in_args_section = False

            # Convert Google-style Returns: to :returns:
            if in_docstring and "Returns:" in line:
                in_returns_section = True
                continue  # Skip the "Returns:" line

            if in_docstring and in_returns_section:
                # Next non-empty line is the return description
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    description = line.strip()
                    result_lines.append(f"{' ' * indent}:returns: {description}")
                    in_returns_section = False
                    continue

            result_lines.append(line)

        return "\n".join(result_lines)


# Registry of all unsafe fixers
UNSAFE_FIXERS: List[UnsafeFixer] = [
    UnsafeDocstringRewriter(),
]


def get_unsafe_fixers() -> List[UnsafeFixer]:
    """Get all registered unsafe fixers.

    :returns: List of unsafe fixer instances
    """
    return UNSAFE_FIXERS


def apply_unsafe_fixes(file_paths: List[Path]) -> List[UnsafeFixerResult]:
    """Apply all unsafe fixers to the given files.

    :param file_paths: List of file paths to process
    :returns: List of results from fixers that made changes
    """
    results = []

    for file_path in file_paths:
        for fixer in get_unsafe_fixers():
            if fixer.can_fix(file_path):
                result = fixer.fix(file_path)
                if result:
                    results.append(result)

    return results
