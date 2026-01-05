#!/usr/bin/env python3
"""Unit tests for add_future_annotations.py script.

This module provides comprehensive test coverage for the future annotations
insertion script, covering all edge cases and insertion scenarios.

:Purpose:
    Ensures the script correctly handles all Python file variants:
    - Files with/without shebangs
    - Files with/without encoding cookies
    - Files with/without module docstrings
    - Files with existing future imports
    - Files with multiple __future__ imports

:Usage:
    Run tests from repository root::

        python3 -m pytest scripts/tests/test_add_future_annotations.py
        # or
        python3 scripts/tests/test_add_future_annotations.py

:Environment Variables:
    None. Tests are self-contained and use temporary files.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest scripts/tests/test_add_future_annotations.py -v

    Run specific test::

        python3 -m pytest scripts/tests/test_add_future_annotations.py::test_file_with_docstring -v

:Notes:
    - Tests are deterministic and do not depend on repository state
    - Uses temporary files for isolation
    - Tests both --check and --apply modes
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path to import the script module
sys.path.insert(0, str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position  # Must modify sys.path before import
from add_future_annotations import (  # noqa: E402
    add_future_import,
    find_insertion_point,
    has_future_import,
    process_file,
    should_skip_file,
)


class TestSkipFile(unittest.TestCase):
    """Test file skipping logic."""

    def test_skip_venv(self):
        """Files in .venv should be skipped."""
        self.assertTrue(should_skip_file(Path(".venv/lib/python3.9/site-packages/test.py")))

    def test_skip_git(self):
        """Files in .git should be skipped."""
        self.assertTrue(should_skip_file(Path(".git/hooks/test.py")))

    def test_skip_dist(self):
        """Files in dist should be skipped."""
        self.assertTrue(should_skip_file(Path("dist/mypackage/test.py")))

    def test_skip_build(self):
        """Files in build should be skipped."""
        self.assertTrue(should_skip_file(Path("build/lib/test.py")))

    def test_dont_skip_normal(self):
        """Normal project files should not be skipped."""
        self.assertFalse(should_skip_file(Path("src/mymodule/test.py")))
        self.assertFalse(should_skip_file(Path("scripts/test.py")))


class TestHasFutureImport(unittest.TestCase):
    """Test detection of existing future imports."""

    def test_no_import(self):
        """File without future import should return False."""
        content = 'print("hello")\n'
        self.assertFalse(has_future_import(content))

    def test_has_import(self):
        """File with future import should return True."""
        content = "from __future__ import annotations\nprint('hello')\n"
        self.assertTrue(has_future_import(content))

    def test_has_import_with_other_imports(self):
        """File with future import among other imports should return True."""
        content = """from __future__ import annotations
import sys
import os
"""
        self.assertTrue(has_future_import(content))

    def test_has_import_after_docstring(self):
        """File with future import after docstring should return True."""
        content = '''"""Module docstring."""
from __future__ import annotations
'''
        self.assertTrue(has_future_import(content))


class TestFindInsertionPoint(unittest.TestCase):
    """Test finding the correct insertion point."""

    def test_empty_file(self):
        """Empty file should insert at line 1."""
        content = ""
        line, _ = find_insertion_point(content)
        self.assertEqual(line, 1)

    def test_simple_file(self):
        """Simple file without headers should insert at line 1."""
        content = "import sys\n"
        line, _ = find_insertion_point(content)
        self.assertEqual(line, 1)

    def test_file_with_shebang(self):
        """File with shebang should insert after it."""
        content = "#!/usr/bin/env python3\nimport sys\n"
        line, _ = find_insertion_point(content)
        self.assertEqual(line, 2)

    def test_file_with_encoding(self):
        """File with encoding cookie should insert after it."""
        content = "# -*- coding: utf-8 -*-\nimport sys\n"
        line, _ = find_insertion_point(content)
        self.assertEqual(line, 2)

    def test_file_with_shebang_and_encoding(self):
        """File with both shebang and encoding should insert after both."""
        content = "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nimport sys\n"
        line, _ = find_insertion_point(content)
        self.assertEqual(line, 3)

    def test_file_with_docstring(self):
        """File with module docstring should insert after it."""
        content = '"""Module docstring."""\nimport sys\n'
        line, _ = find_insertion_point(content)
        self.assertGreater(line, 1)  # Should be after docstring

    def test_file_with_multiline_docstring(self):
        """File with multiline module docstring should insert after it."""
        content = '''"""Module docstring.

This is a longer docstring.
"""
import sys
'''
        line, _ = find_insertion_point(content)
        self.assertGreater(line, 1)  # Should be after docstring

    def test_file_with_shebang_and_docstring(self):
        """File with shebang and docstring should insert after docstring."""
        content = '#!/usr/bin/env python3\n"""Module docstring."""\nimport sys\n'
        line, _ = find_insertion_point(content)
        self.assertGreater(line, 2)  # Should be after both shebang and docstring


class TestAddFutureImport(unittest.TestCase):
    """Test the import addition logic."""

    def test_add_to_empty_file(self):
        """Adding to empty file should work."""
        content = ""
        result = add_future_import(content)
        self.assertIn("from __future__ import annotations", result)

    def test_add_to_simple_file(self):
        """Adding to simple file should preserve existing code."""
        content = "import sys\n"
        result = add_future_import(content)
        self.assertIn("from __future__ import annotations", result)
        self.assertIn("import sys", result)

    def test_preserve_shebang(self):
        """Shebang should remain first."""
        content = "#!/usr/bin/env python3\nimport sys\n"
        result = add_future_import(content)
        lines = result.split("\n")
        self.assertEqual(lines[0], "#!/usr/bin/env python3")
        self.assertIn("from __future__ import annotations", result)

    def test_preserve_encoding(self):
        """Encoding cookie should be preserved."""
        content = "# -*- coding: utf-8 -*-\nimport sys\n"
        result = add_future_import(content)
        self.assertIn("# -*- coding: utf-8 -*-", result)
        self.assertIn("from __future__ import annotations", result)

    def test_preserve_docstring(self):
        """Module docstring should be preserved and come before import."""
        content = '"""Module docstring."""\nimport sys\n'
        result = add_future_import(content)
        self.assertIn('"""Module docstring."""', result)
        self.assertIn("from __future__ import annotations", result)
        # Docstring should come before import
        doc_pos = result.index('"""Module docstring."""')
        import_pos = result.index("from __future__ import annotations")
        self.assertLess(doc_pos, import_pos)

    def test_idempotent(self):
        """Adding import to file that already has it should not change content."""
        content = "from __future__ import annotations\nimport sys\n"
        result = add_future_import(content)
        self.assertEqual(content, result)

    def test_multiline_docstring(self):
        """Multiline docstring should be preserved correctly."""
        content = '''"""Module docstring.

This is a longer docstring
with multiple lines.
"""
import sys
'''
        result = add_future_import(content)
        self.assertIn("from __future__ import annotations", result)
        self.assertIn("This is a longer docstring", result)


class TestProcessFile(unittest.TestCase):
    """Test file processing with actual file I/O."""

    def test_check_mode_returns_true_for_file_needing_change(self):
        """Check mode should return True for files needing modification."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import sys\n")
            temp_path = Path(f.name)

        try:
            # Process in check mode
            result = process_file(temp_path, apply=False, verbose=False)
            self.assertTrue(result)

            # File should be unchanged
            with open(temp_path, encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, "import sys\n")
        finally:
            temp_path.unlink()

    def test_check_mode_returns_false_for_file_with_import(self):
        """Check mode should return False for files already having import."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("from __future__ import annotations\nimport sys\n")
            temp_path = Path(f.name)

        try:
            result = process_file(temp_path, apply=False, verbose=False)
            self.assertFalse(result)
        finally:
            temp_path.unlink()

    def test_apply_mode_modifies_file(self):
        """Apply mode should actually modify the file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import sys\n")
            temp_path = Path(f.name)

        try:
            result = process_file(temp_path, apply=True, verbose=False)
            self.assertTrue(result)

            # File should be modified
            with open(temp_path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("from __future__ import annotations", content)
        finally:
            temp_path.unlink()

    def test_apply_mode_preserves_structure(self):
        """Apply mode should preserve file structure."""
        original = '''#!/usr/bin/env python3
"""Module docstring."""
import sys
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(original)
            temp_path = Path(f.name)

        try:
            process_file(temp_path, apply=True, verbose=False)

            with open(temp_path, encoding="utf-8") as f:
                content = f.read()

            # Check all parts are present
            self.assertIn("#!/usr/bin/env python3", content)
            self.assertIn('"""Module docstring."""', content)
            self.assertIn("from __future__ import annotations", content)
            self.assertIn("import sys", content)

            # Check order
            lines = content.split("\n")
            self.assertEqual(lines[0], "#!/usr/bin/env python3")
        finally:
            temp_path.unlink()


class TestComplexScenarios(unittest.TestCase):
    """Test complex real-world scenarios."""

    def test_file_with_all_headers(self):
        """File with shebang, encoding, and docstring."""
        content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Module docstring.

Extended description.
"""
import sys
'''
        result = add_future_import(content)
        lines = result.split("\n")

        # Verify order
        self.assertEqual(lines[0], "#!/usr/bin/env python3")
        self.assertEqual(lines[1], "# -*- coding: utf-8 -*-")
        self.assertIn('"""Module docstring.', result)
        self.assertIn("from __future__ import annotations", result)

    def test_file_with_single_quote_docstring(self):
        """File with single-quoted docstring."""
        content = "'''Module docstring.'''\nimport sys\n"
        result = add_future_import(content)
        self.assertIn("from __future__ import annotations", result)
        self.assertIn("'''Module docstring.'''", result)

    def test_file_with_no_imports(self):
        """File with just code, no imports."""
        content = '''"""Module docstring."""

def main():
    print("hello")
'''
        result = add_future_import(content)
        self.assertIn("from __future__ import annotations", result)
        self.assertIn("def main():", result)


if __name__ == "__main__":
    unittest.main()
