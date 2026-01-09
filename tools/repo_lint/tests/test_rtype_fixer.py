"""Comprehensive unit tests for docstring :rtype: autofix tool.

This module tests the :rtype: fixer that automatically adds reST :rtype: fields
to function docstrings based on their return type annotations.

:Purpose:
    Validate safe :rtype: inference and docstring enhancement behavior.

:Test Coverage:
    - Basic type inference (str, int, bool, etc.)
    - Complex types (Optional, Union, List, Dict)
    - Already has :rtype: skip logic
    - Functions returning None skip logic
    - Functions without docstrings skip logic
    - Smart insertion after existing fields
    - Indentation preservation
    - Edge cases (decorators, async functions, methods)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from tools.repo_lint.fixers.rtype_fixer import RTypeFixer


class TestRTypeFixerBasicInference:
    """Test basic type inference capabilities."""

    def test_simple_str_return(self) -> None:
        """Should add :rtype: str for str return annotation."""
        code = '''
def get_name() -> str:
    """Get the name.
    
    :returns: The name
    """
    return "Alice"
'''
        expected = '''
def get_name() -> str:
    """Get the name.
    
    :returns: The name
    :rtype: str
    """
    return "Alice"
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        assert result.strip() == expected.strip()

    def test_simple_int_return(self) -> None:
        """Should add :rtype: int for int return annotation."""
        code = '''
def get_count() -> int:
    """Get the count.
    
    :returns: The count
    """
    return 42
'''
        expected = '''
def get_count() -> int:
    """Get the count.
    
    :returns: The count
    :rtype: int
    """
    return 42
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        assert result.strip() == expected.strip()

    def test_bool_return(self) -> None:
        """Should add :rtype: bool for bool return annotation."""
        code = '''
def is_valid() -> bool:
    """Check if valid.
    
    :returns: True if valid
    """
    return True
'''
        expected = '''
def is_valid() -> bool:
    """Check if valid.
    
    :returns: True if valid
    :rtype: bool
    """
    return True
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        assert result.strip() == expected.strip()


class TestRTypeFixerComplexTypes:
    """Test complex type annotation handling."""

    def test_optional_type(self) -> None:
        """Should handle Optional types correctly."""
        code = '''
from typing import Optional

def get_value() -> Optional[str]:
    """Get optional value.
    
    :returns: The value or None
    """
    return None
'''
        expected = '''
from typing import Optional

def get_value() -> Optional[str]:
    """Get optional value.
    
    :returns: The value or None
    :rtype: Optional[str]
    """
    return None
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        assert result.strip() == expected.strip()

    def test_list_type(self) -> None:
        """Should handle List types correctly."""
        code = '''
from typing import List

def get_items() -> List[str]:
    """Get list of items.
    
    :returns: The items
    """
    return []
'''
        expected = '''
from typing import List

def get_items() -> List[str]:
    """Get list of items.
    
    :returns: The items
    :rtype: List[str]
    """
    return []
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        assert result.strip() == expected.strip()

    def test_dict_type(self) -> None:
        """Should handle Dict types correctly."""
        code = '''
from typing import Dict

def get_config() -> Dict[str, int]:
    """Get configuration.
    
    :returns: Configuration dict
    """
    return {}
'''
        expected = '''
from typing import Dict

def get_config() -> Dict[str, int]:
    """Get configuration.
    
    :returns: Configuration dict
    :rtype: Dict[str, int]
    """
    return {}
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        assert result.strip() == expected.strip()


class TestRTypeFixerSkipLogic:
    """Test skip logic for various scenarios."""

    def test_skip_none_return(self) -> None:
        """Should skip functions returning None (per policy)."""
        code = '''
def process() -> None:
    """Process something.
    
    Does the processing.
    """
    pass
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        # Should be unchanged
        assert result.strip() == code.strip()

    def test_skip_already_has_rtype(self) -> None:
        """Should skip if :rtype: already exists."""
        code = '''
def get_name() -> str:
    """Get the name.
    
    :returns: The name
    :rtype: str
    """
    return "Alice"
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        # Should be unchanged
        assert result.strip() == code.strip()

    def test_skip_no_docstring(self) -> None:
        """Should skip functions without docstrings."""
        code = """
def get_name() -> str:
    return "Alice"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        # Should be unchanged
        assert result.strip() == code.strip()

    def test_skip_no_annotation(self) -> None:
        """Should skip functions without return type annotation."""
        code = '''
def get_name():
    """Get the name.
    
    :returns: The name
    """
    return "Alice"
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        # Should be unchanged
        assert result.strip() == code.strip()


class TestRTypeFixerInsertion:
    """Test smart insertion logic."""

    def test_insert_after_param(self) -> None:
        """Should insert :rtype: after :param: fields."""
        code = '''
def add(a: int, b: int) -> int:
    """Add two numbers.
    
    :param a: First number
    :param b: Second number
    :returns: Sum of a and b
    """
    return a + b
'''
        expected = '''
def add(a: int, b: int) -> int:
    """Add two numbers.
    
    :param a: First number
    :param b: Second number
    :returns: Sum of a and b
    :rtype: int
    """
    return a + b
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        assert result.strip() == expected.strip()

    def test_insert_after_returns(self) -> None:
        """Should insert :rtype: after :returns: field."""
        code = '''
def get_name() -> str:
    """Get the name.
    
    :returns: The name
    """
    return "Alice"
'''
        expected = '''
def get_name() -> str:
    """Get the name.
    
    :returns: The name
    :rtype: str
    """
    return "Alice"
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        assert result.strip() == expected.strip()

    def test_preserves_indentation(self) -> None:
        """Should preserve docstring indentation."""
        code = '''
class MyClass:
    def get_name(self) -> str:
        """Get the name.
        
        :returns: The name
        """
        return "Alice"
'''
        expected = '''
class MyClass:
    def get_name(self) -> str:
        """Get the name.
        
        :returns: The name
        :rtype: str
        """
        return "Alice"
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        assert result.strip() == expected.strip()


class TestRTypeFixerEdgeCases:
    """Test edge cases and special scenarios."""

    def test_method_in_class(self) -> None:
        """Should handle class methods correctly."""
        code = '''
class Calculator:
    def add(self, a: int, b: int) -> int:
        """Add two numbers.
        
        :param a: First number
        :param b: Second number
        :returns: Sum
        """
        return a + b
'''
        expected = '''
class Calculator:
    def add(self, a: int, b: int) -> int:
        """Add two numbers.
        
        :param a: First number
        :param b: Second number
        :returns: Sum
        :rtype: int
        """
        return a + b
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        assert result.strip() == expected.strip()

    def test_multiple_functions(self) -> None:
        """Should handle multiple functions in one file."""
        code = '''
def get_name() -> str:
    """Get name.
    
    :returns: Name
    """
    return "Alice"

def get_age() -> int:
    """Get age.
    
    :returns: Age
    """
    return 30
'''
        expected = '''
def get_name() -> str:
    """Get name.
    
    :returns: Name
    :rtype: str
    """
    return "Alice"

def get_age() -> int:
    """Get age.
    
    :returns: Age
    :rtype: int
    """
    return 30
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            fixer.process_file(Path(f.name))

            result = Path(f.name).read_text()
            Path(f.name).unlink()

        assert result.strip() == expected.strip()

    def test_dry_run_mode(self) -> None:
        """Should not modify file in dry-run mode."""
        code = '''
def get_name() -> str:
    """Get name.
    
    :returns: Name
    """
    return "Alice"
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            modified, num_fixes = fixer.process_file(Path(f.name), dry_run=True)

            content = Path(f.name).read_text()
            Path(f.name).unlink()

        # File should be unchanged in dry-run mode
        assert content.strip() == code.strip()
        # But should report fixes were needed
        assert modified is False  # File not modified
        assert num_fixes == 1  # But 1 fix was needed


class TestRTypeFixerErrorHandling:
    """Test error handling."""

    def test_nonexistent_file(self) -> None:
        """Should return False for nonexistent files."""
        fixer = RTypeFixer()
        modified, num_fixes = fixer.process_file(Path("/nonexistent/file.py"))
        assert modified is False
        assert num_fixes == 0

    def test_syntax_error(self) -> None:
        """Should handle syntax errors gracefully."""
        code = '''
def broken( -> str:
    """Broken function."""
    pass
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            fixer = RTypeFixer()
            modified, num_fixes = fixer.process_file(Path(f.name))
            Path(f.name).unlink()

        # Should return (False, 0) for syntax errors
        assert modified is False
        assert num_fixes == 0
