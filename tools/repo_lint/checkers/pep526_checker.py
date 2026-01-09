"""AST-based checker for PEP 526 variable type annotations.

:Purpose:
    Detects missing type annotations on variable assignments at various scopes
    (module-level, class attributes, instance attributes, function-local).
    Enforces the Python typing policy defined in docs/contributing/python-typing-policy.md.

:Scope Detection:
    - Module-level: Variables assigned at module scope
    - Class attributes: Variables assigned in class body
    - Instance attributes: Variables assigned in __init__ and other methods (optional)
    - Function-local: Variables assigned inside functions (optional)

:Enforcement Policy:
    - Module-level and class attributes: MANDATORY (baseline)
    - Empty literals ({}, [], set(), etc.): MANDATORY (always require annotation)
    - None initializations: MANDATORY (always require Optional[T])
    - Function-local variables: OPTIONAL (configurable, disabled by default)

:Exit Codes:
    N/A - Returns list of violations

:Examples:
    Check a file for missing annotations::

        checker = PEP526Checker({'module_level': True, 'class_attributes': True})
        violations = checker.check_file('path/to/file.py')
        for violation in violations:
            print(f"{violation['file']}:{violation['line']} - {violation['message']}")
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional


class PEP526Checker(ast.NodeVisitor):
    """AST visitor that detects missing PEP 526 type annotations.

    :param scope_config: Configuration dict controlling which scopes to enforce
    :type scope_config: dict

    :Scope Config Keys:
        - module_level (bool): Enforce annotations on module-level variables
        - class_attributes (bool): Enforce annotations on class attributes
        - local_variables (bool): Enforce annotations on function-local variables
        - instance_attributes (bool): Enforce annotations on instance attributes

    :Violation Format:
        Each violation is a dict with keys:
        - type: 'missing-annotation'
        - scope: 'module', 'class', 'function', or 'instance'
        - file: Path to the file
        - line: Line number
        - column: Column offset
        - target: Variable name
        - message: Human-readable error message
        - rule: Rule ID for per-rule ignores
        - severity: 'error'
    """

    def __init__(self, scope_config: Dict[str, bool]) -> None:
        """Initialize PEP526Checker with scope configuration.

        :param scope_config: Dict controlling which scopes to enforce
        """
        self.scope_config = scope_config
        self.current_scope: List[str] = []  # Stack: ['module', 'class', 'function']
        self.violations: List[Dict[str, Any]] = []
        self.current_file: Optional[str] = None

    def check_file(self, filepath: str | Path) -> List[Dict[str, Any]]:
        """Check a Python file for missing type annotations.

        :param filepath: Path to Python file to check
        :returns: List of violation dictionaries
        :rtype: list[dict]

        :raises:
            OSError: If file cannot be read
            SyntaxError: If file has syntax errors (returns empty list instead)
        """
        self.current_file = str(filepath)
        self.violations = []
        self.current_scope = []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=str(filepath))
            self.visit(tree)
        except SyntaxError:
            # Skip files with syntax errors - they'll be caught by other tools
            return []

        return self.violations

    def visit_Module(self, node: ast.Module) -> None:
        """Visit module node and track module scope.

        :param node: Module AST node
        """
        self.current_scope.append("module")
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition and track class scope.

        :param node: ClassDef AST node
        """
        self.current_scope.append("class")
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition and track function scope.

        :param node: FunctionDef AST node
        """
        self.current_scope.append("function")
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition and track function scope.

        :param node: AsyncFunctionDef AST node
        """
        self.current_scope.append("function")
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment node and check for missing annotations.

        :param node: Assign AST node
        """
        scope = self.get_current_scope()

        if not self.should_check_scope(scope):
            self.generic_visit(node)
            return

        # Check each target in the assignment
        for target in node.targets:
            if self.is_simple_name(target):
                # Simple variable assignment without annotation
                if self.requires_annotation(target, node.value, scope):
                    self.violations.append(
                        {
                            "type": "missing-annotation",
                            "scope": scope,
                            "file": self.current_file,
                            "line": node.lineno,
                            "column": node.col_offset,
                            "target": ast.unparse(target),
                            "message": f'Variable "{ast.unparse(target)}" missing type annotation (PEP 526)',
                            "rule": f"PEP526-{scope}",
                            "severity": "error",
                        }
                    )

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit annotated assignment node (these are correct).

        :param node: AnnAssign AST node

        :Note:
            Could validate annotation quality here in future
        """
        self.generic_visit(node)

    def get_current_scope(self) -> str:
        """Return current scope context.

        :returns: Current scope ('module', 'class', 'function', or 'instance')
        :rtype: str
        """
        if not self.current_scope:
            return "module"
        if "function" in self.current_scope:
            if self.current_scope[-1] == "function":
                return "function"
            # Inside a method (function inside class)
            return "instance" if "class" in self.current_scope else "function"
        if "class" in self.current_scope:
            return "class"
        return "module"

    def should_check_scope(self, scope: str) -> bool:
        """Check if this scope is enabled in config.

        :param scope: Scope name ('module', 'class', 'function', 'instance')
        :returns: True if scope should be checked
        :rtype: bool
        """
        if scope == "module":
            return self.scope_config.get("module_level", True)
        elif scope == "class":
            return self.scope_config.get("class_attributes", True)
        elif scope == "function":
            return self.scope_config.get("local_variables", False)  # Optional
        elif scope == "instance":
            return self.scope_config.get("instance_attributes", False)  # Future
        return False

    def requires_annotation(self, target: ast.AST, value: ast.AST, scope: str) -> bool:
        """Determine if this assignment requires annotation.

        :param target: Assignment target node
        :param value: Assignment value node
        :param scope: Current scope
        :returns: True if annotation is required
        :rtype: bool
        """
        # Always require for module-level and class attributes (if enabled)
        if scope in ("module", "class") and self.should_check_scope(scope):
            return True

        # Special patterns that ALWAYS require annotation
        if self.is_empty_literal(value):
            return True  # {}, [], set(), etc.

        if self.is_none_literal(value):
            return True  # x = None

        return False

    def is_empty_literal(self, node: ast.AST) -> bool:
        """Check if value is an empty literal.

        :param node: AST node to check
        :returns: True if node is empty literal
        :rtype: bool

        :Empty Literals:
            - [] (empty list)
            - {} (empty dict)
            - set() (empty set)
            - list(), dict(), tuple() (constructor calls with no args)
        """
        if isinstance(node, ast.List) and len(node.elts) == 0:
            return True  # []
        if isinstance(node, ast.Dict) and len(node.keys) == 0:
            return True  # {}
        if isinstance(node, ast.Set) and len(node.elts) == 0:
            return True  # set() - Note: {} is dict, not set
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ("list", "dict", "set", "tuple") and not node.args:
                    return True  # list(), dict(), set(), tuple()
        return False

    def is_none_literal(self, node: ast.AST) -> bool:
        """Check if value is None.

        :param node: AST node to check
        :returns: True if node is None literal
        :rtype: bool
        """
        return isinstance(node, ast.Constant) and node.value is None

    def is_simple_name(self, target: ast.AST) -> bool:
        """Check if target is a simple variable name.

        This helper distinguishes simple variable assignments from:
        - Tuple unpacking: x, y = 1, 2
        - Attribute assignments: self.x = 1
        - Subscript assignments: obj[key] = 1

        :param target: AST node representing assignment target
        :returns: True if target is a simple name (ast.Name), False otherwise
        :rtype: bool
        """
        if isinstance(target, ast.Name):
            return True  # Simple variable: x = 1

        # Reject unpacking patterns
        if isinstance(target, (ast.Tuple, ast.List)):
            return False  # x, y = 1, 2 or [x, y] = [1, 2]

        # Reject attribute assignments
        if isinstance(target, ast.Attribute):
            return False  # self.x = 1 or obj.attr = 1

        # Reject subscript assignments
        if isinstance(target, ast.Subscript):
            return False  # obj[key] = 1 or lst[0] = 1

        return False  # Any other node type

    def get_violations(self) -> List[Dict[str, Any]]:
        """Get list of violations found during checking.

        :returns: List of violation dictionaries
        :rtype: list[dict]
        """
        return self.violations
