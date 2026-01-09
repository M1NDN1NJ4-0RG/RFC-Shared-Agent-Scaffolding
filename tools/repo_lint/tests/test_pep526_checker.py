"""Unit tests for PEP 526 type annotation checker.

Tests the AST-based PEP 526 checker for detecting missing variable annotations
at module-level, class attributes, and optionally function-local scope.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from tools.repo_lint.checkers.pep526_checker import PEP526Checker
from tools.repo_lint.checkers.pep526_config import get_default_config


class TestPEP526Checker:
    """Test PEP526Checker functionality."""

    def test_module_level_missing_annotation(self):
        """Test detection of missing annotation at module level."""
        code = """
x = 5
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 1
        assert violations[0]["scope"] == "module"
        assert violations[0]["target"] == "x"
        assert "missing type annotation" in violations[0]["message"].lower()

        Path(f.name).unlink()

    def test_module_level_with_annotation(self):
        """Test that annotated module-level variables pass."""
        code = """
x: int = 5
y: str = "hello"
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 0

        Path(f.name).unlink()

    def test_class_attribute_missing_annotation(self):
        """Test detection of missing annotation in class attributes."""
        code = """
class MyClass:
    x = 5
    y = "hello"
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 2
        assert all(v["scope"] == "class" for v in violations)
        targets = {v["target"] for v in violations}
        assert targets == {"x", "y"}

        Path(f.name).unlink()

    def test_class_attribute_with_annotation(self):
        """Test that annotated class attributes pass."""
        code = """
class MyClass:
    x: int = 5
    y: str = "hello"
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 0

        Path(f.name).unlink()

    def test_empty_literal_requires_annotation(self):
        """Test that empty literals always require annotation."""
        code = """
empty_list = []
empty_dict = {}
empty_set = set()
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 3
        targets = {v["target"] for v in violations}
        assert targets == {"empty_list", "empty_dict", "empty_set"}

        Path(f.name).unlink()

    def test_none_literal_requires_annotation(self):
        """Test that None initializations always require annotation."""
        code = """
value = None
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 1
        assert violations[0]["target"] == "value"

        Path(f.name).unlink()

    def test_function_local_not_enforced_by_default(self):
        """Test that function-local variables are not enforced by default."""
        code = """
def func():
    x = 5
    y = "hello"
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 0  # local_variables disabled by default

        Path(f.name).unlink()

    def test_function_local_with_config_enabled(self):
        """Test that function-local variables are enforced when enabled."""
        code = """
def func():
    x = 5
    y = "hello"
"""
        config = get_default_config()
        config["local_variables"] = True
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 2
        targets = {v["target"] for v in violations}
        assert targets == {"x", "y"}

        Path(f.name).unlink()

    def test_is_simple_name_detects_simple_vars(self):
        """Test is_simple_name correctly identifies simple variable names."""
        code = """
x = 5
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 1  # Simple name detected

        Path(f.name).unlink()

    def test_is_simple_name_rejects_unpacking(self):
        """Test is_simple_name rejects tuple unpacking."""
        code = """
x, y = 1, 2
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 0  # Unpacking not flagged

        Path(f.name).unlink()

    def test_is_simple_name_rejects_attribute_assignment(self):
        """Test is_simple_name rejects attribute assignments."""
        code = """
class MyClass:
    def __init__(self):
        self.x = 5
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 0  # Attribute assignment not flagged

        Path(f.name).unlink()

    def test_is_simple_name_rejects_subscript_assignment(self):
        """Test is_simple_name rejects subscript assignments."""
        code = """
lst = [1, 2, 3]
lst[0] = 5
"""
        config = get_default_config()
        config["local_variables"] = True
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        # Should only flag `lst` assignment, not `lst[0]`
        assert len(violations) == 1
        assert violations[0]["target"] == "lst"

        Path(f.name).unlink()

    def test_syntax_error_handling(self):
        """Test that syntax errors are handled gracefully."""
        code = """
def func(
    # Syntax error: unclosed parenthesis
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 0  # Syntax errors skipped

        Path(f.name).unlink()

    def test_scope_tracking_module(self):
        """Test scope tracking at module level."""
        code = """
x = 5
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 1
        assert violations[0]["scope"] == "module"

        Path(f.name).unlink()

    def test_scope_tracking_class(self):
        """Test scope tracking in class body."""
        code = """
class MyClass:
    x = 5
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 1
        assert violations[0]["scope"] == "class"

        Path(f.name).unlink()

    def test_scope_tracking_function(self):
        """Test scope tracking in function body."""
        code = """
def func():
    x = 5
"""
        config = get_default_config()
        config["local_variables"] = True
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 1
        assert violations[0]["scope"] == "function"

        Path(f.name).unlink()

    def test_config_module_level_disabled(self):
        """Test that module-level checking can be disabled."""
        code = """
x = 5
"""
        config = get_default_config()
        config["module_level"] = False
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 0

        Path(f.name).unlink()

    def test_config_class_attributes_disabled(self):
        """Test that class attribute checking can be disabled."""
        code = """
class MyClass:
    x = 5
"""
        config = get_default_config()
        config["class_attributes"] = False
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 0

        Path(f.name).unlink()

    def test_multiple_violations_same_file(self):
        """Test detecting multiple violations in the same file."""
        code = """
x = 5
y = "hello"

class MyClass:
    a = 1
    b = 2

def func():
    z = 10
"""
        config = get_default_config()
        config["local_variables"] = True
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        # Should find: x, y (module), a, b (class), z (function)
        assert len(violations) == 5

        Path(f.name).unlink()

    def test_violation_format(self):
        """Test that violation objects have correct format."""
        code = """
x = 5
"""
        config = get_default_config()
        checker = PEP526Checker(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            violations = checker.check_file(f.name)

        assert len(violations) == 1
        v = violations[0]

        # Check required fields
        assert "type" in v
        assert "scope" in v
        assert "file" in v
        assert "line" in v
        assert "column" in v
        assert "target" in v
        assert "message" in v
        assert "rule" in v
        assert "severity" in v

        # Check values
        assert v["type"] == "missing-annotation"
        assert v["severity"] == "error"
        assert v["rule"] == "PEP526-module"

        Path(f.name).unlink()
