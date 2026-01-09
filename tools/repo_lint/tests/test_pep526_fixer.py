"""Comprehensive unit tests for PEP 526 autofix tool.

This module tests the PEP 526 fixer that automatically adds type annotations
to module-level variables and class attributes.

:Purpose:
    Validate safe type inference and annotation insertion behavior.

:Test Coverage:
    - Literal type inference (int, str, bool, float, bytes)
    - Path constructor detection
    - Already-annotated variable skip logic
    - Ambiguous case skip logic ([], {}, None)
    - Private variable skip logic
    - Class attribute detection
    - Edge cases (multiple targets, chained assignment, unpacking)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tools.repo_lint.fixers.pep526_fixer import PEP526Fixer


class TestPEP526FixerLiteralInference:
    """Test literal type inference capabilities."""

    def test_int_literal_inference(self) -> None:
        """Test inference of int type from integer literal."""
        code = "TIMEOUT = 30\n"
        expected = "TIMEOUT: int = 30\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 1

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_str_literal_inference(self) -> None:
        """Test inference of str type from string literal."""
        code = 'HOST = "localhost"\n'
        expected = 'HOST: str = "localhost"\n'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 1

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_bool_literal_inference(self) -> None:
        """Test inference of bool type from boolean literal."""
        code = "ENABLED = True\n"
        expected = "ENABLED: bool = True\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 1

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_float_literal_inference(self) -> None:
        """Test inference of float type from float literal."""
        code = "RATIO = 3.14\n"
        expected = "RATIO: float = 3.14\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 1

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_bytes_literal_inference(self) -> None:
        """Test inference of bytes type from bytes literal."""
        code = 'DATA = b"binary"\n'
        expected = 'DATA: bytes = b"binary"\n'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 1

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()


class TestPEP526FixerPathConstructor:
    """Test Path constructor detection and annotation."""

    def test_path_constructor_inference(self) -> None:
        """Test inference of Path type from Path() constructor."""
        code = "from pathlib import Path\nROOT = Path(__file__).parent\n"
        expected = "from pathlib import Path\nROOT: Path = Path(__file__).parent\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 1

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_path_direct_constructor(self) -> None:
        """Test inference of Path type from direct Path() call."""
        code = 'from pathlib import Path\nCONFIG_PATH = Path("config.yaml")\n'
        expected = 'from pathlib import Path\nCONFIG_PATH: Path = Path("config.yaml")\n'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 1

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()


class TestPEP526FixerSkipLogic:
    """Test skip logic for various edge cases."""

    def test_skip_already_annotated(self) -> None:
        """Test that already-annotated variables are skipped."""
        code = "PORT: int = 8080\n"
        expected = code  # No change

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is False
            assert num_fixes == 0

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_skip_empty_list(self) -> None:
        """Test that empty list literals are skipped (ambiguous type)."""
        code = "EMPTY_LIST = []\n"
        expected = code  # No change

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is False
            assert num_fixes == 0

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_skip_empty_dict(self) -> None:
        """Test that empty dict literals are skipped (ambiguous type)."""
        code = "EMPTY_DICT = {}\n"
        expected = code  # No change

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is False
            assert num_fixes == 0

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_skip_none_literal(self) -> None:
        """Test that None literals are skipped (ambiguous type)."""
        code = "DEFAULT = None\n"
        expected = code  # No change

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is False
            assert num_fixes == 0

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_skip_private_variable(self) -> None:
        """Test that private variables (leading underscore) are skipped."""
        code = "_internal = 42\n"
        expected = code  # No change

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is False
            assert num_fixes == 0

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()


class TestPEP526FixerClassAttributes:
    """Test class attribute detection and annotation."""

    def test_class_attribute_int(self) -> None:
        """Test annotation of class attributes with int literals."""
        code = "class TestClass:\n    counter = 0\n"
        expected = "class TestClass:\n    counter: int = 0\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 1

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_class_attribute_str(self) -> None:
        """Test annotation of class attributes with str literals."""
        code = 'class TestClass:\n    name = "test"\n'
        expected = 'class TestClass:\n    name: str = "test"\n'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 1

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_class_attribute_bool(self) -> None:
        """Test annotation of class attributes with bool literals."""
        code = "class TestClass:\n    active = False\n"
        expected = "class TestClass:\n    active: bool = False\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 1

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_class_skip_already_annotated(self) -> None:
        """Test that already-annotated class attributes are skipped."""
        code = "class TestClass:\n    max_retries: int = 3\n"
        expected = code  # No change

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is False
            assert num_fixes == 0

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()


class TestPEP526FixerEdgeCases:
    """Test edge cases and unusual patterns."""

    def test_multiple_fixes_in_one_file(self) -> None:
        """Test multiple annotations added in single file."""
        code = 'TIMEOUT = 30\nHOST = "localhost"\nENABLED = True\n'
        expected = 'TIMEOUT: int = 30\nHOST: str = "localhost"\nENABLED: bool = True\n'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 3

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_dry_run_mode(self) -> None:
        """Test that dry-run mode does not modify file."""
        code = "TIMEOUT = 30\n"
        expected = code  # File should not change

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=True)

            assert modified is False  # dry_run=True means no actual modification
            assert num_fixes == 1  # But it detected the fix

            result = temp_path.read_text()
            assert result == expected  # File unchanged
        finally:
            temp_path.unlink()

    def test_skip_multiple_targets(self) -> None:
        """Test that multiple target assignments are skipped."""
        code = "a = b = 42\n"
        expected = code  # No change (multiple targets)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is False
            assert num_fixes == 0

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_skip_unpacking(self) -> None:
        """Test that unpacking assignments are skipped."""
        code = "a, b = 1, 2\n"
        expected = code  # No change (unpacking)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is False
            assert num_fixes == 0

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()

    def test_preserve_indentation(self) -> None:
        """Test that indentation is preserved in class attributes."""
        code = 'class TestClass:\n    counter = 0\n    name = "test"\n'
        expected = 'class TestClass:\n    counter: int = 0\n    name: str = "test"\n'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is True
            assert num_fixes == 2

            result = temp_path.read_text()
            assert result == expected
        finally:
            temp_path.unlink()


class TestPEP526FixerErrorHandling:
    """Test error handling and robustness."""

    def test_nonexistent_file(self) -> None:
        """Test handling of nonexistent file."""
        fixer = PEP526Fixer()
        temp_path = Path("/tmp/nonexistent_file_12345.py")

        modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

        assert modified is False
        assert num_fixes == 0

    def test_syntax_error_in_file(self) -> None:
        """Test handling of files with syntax errors."""
        code = "TIMEOUT = \n"  # Syntax error

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = Path(f.name)

        try:
            fixer = PEP526Fixer()
            modified, num_fixes = fixer.fix_file(temp_path, dry_run=False)

            assert modified is False
            assert num_fixes == 0
        finally:
            temp_path.unlink()
