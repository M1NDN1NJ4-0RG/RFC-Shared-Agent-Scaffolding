# Phase 3.3: Custom PEP 526 Checker - Design Document

**Issue:** #278  
**Phase:** 3.3 - Implement missing enforcement in `repo_lint`  
**Status:** Design Complete  
**Date:** 2026-01-08

---

## Requirements Summary

### What Needs to Be Checked

Per `docs/contributing/python-typing-policy.md`:

1. **Module-level assignments** (MANDATORY baseline):
   - All module-level variable assignments MUST have type annotations
   - Exception: imports, type aliases, and constants with obvious literal values may be exempt

2. **Class attributes** (MANDATORY baseline):
   - All class attribute declarations MUST have type annotations
   - Both class variables (`ClassVar[T]`) and instance variables need annotations

3. **Empty literals** (MANDATORY):
   - `{}`, `[]`, `set()`, `dict()`, `list()`, `tuple()` MUST be annotated

4. **None initializations** (MANDATORY):
   - Variables initialized to `None` MUST use `Optional[T]` annotation

5. **Function-local variables** (OPTIONAL NOW, FUTURE):
   - Parser MUST detect local variables but enforcement is configurable
   - Will be enabled later via `--strict-typing` flag or "new/changed code only"

### NEW REQUIREMENT: Repository-wide Detection

**Critical:** The AST parser MUST support detecting variable annotations at ALL scopes:
- Module-level assignments
- Class attributes (class-level)
- Instance attributes (in `__init__` and other methods)
- Function-local variables
- Comprehension variables
- Exception handler variables

**Implementation approach:** Build broad detection capability, then use configuration to control which scopes are enforced.

### What Ruff Already Handles

Ruff ANN* rules already enforce:
- Function parameter annotations (ANN001, ANN002, ANN003)
- Function return type annotations (ANN201, ANN202, ANN204, ANN206)
- `*args` and `**kwargs` annotations

**Conclusion:** Custom checker ONLY needs to handle variable annotations (PEP 526).

---

## AST Detection Strategy

### AST Node Types to Analyze

1. **`ast.AnnAssign`** - Annotated assignments (PEP 526)
   ```python
   x: int = 5  # Has annotation ✅
   ```

2. **`ast.Assign`** - Regular assignments (potential violations)
   ```python
   x = 5  # Missing annotation ❌
   ```

3. **`ast.AugAssign`** - Augmented assignments (e.g., `+=`)
   ```python
   x += 1  # Not a violation (assumes x already annotated)
   ```

4. **Context tracking** - Determine scope:
   - `ast.Module` → module-level scope
   - `ast.ClassDef` → class scope (class attributes)
   - `ast.FunctionDef` / `ast.AsyncFunctionDef` → function-local scope
   - Track nesting level to distinguish scopes

### Violation Detection Logic

```python
class PEP526Checker(ast.NodeVisitor):
    def __init__(self, scope_config):
        self.scope_config = scope_config  # Which scopes to enforce
        self.current_scope = []  # Stack: ['module', 'class', 'function']
        self.violations = []
    
    def visit_Assign(self, node):
        # Detect unannotated assignments
        scope = self.get_current_scope()
        
        if not self.should_check_scope(scope):
            return  # Skip if scope not enforced
        
        # Check each target in the assignment
        for target in node.targets:
            if self.is_simple_name(target):
                # Simple variable assignment without annotation
                if self.requires_annotation(target, node.value, scope):
                    self.violations.append({
                        'type': 'missing-annotation',
                        'scope': scope,
                        'line': node.lineno,
                        'col': node.col_offset,
                        'target': ast.unparse(target),
                        'message': f'Variable "{ast.unparse(target)}" missing type annotation'
                    })
    
    def visit_AnnAssign(self, node):
        # Annotated assignment - this is correct
        # Could validate annotation quality here (future)
        pass
    
    def should_check_scope(self, scope):
        """Check if this scope is enabled in config."""
        if scope == 'module':
            return self.scope_config.get('module_level', True)
        elif scope == 'class':
            return self.scope_config.get('class_attributes', True)
        elif scope == 'function':
            return self.scope_config.get('local_variables', False)  # Optional
        elif scope == 'instance':
            return self.scope_config.get('instance_attributes', False)  # Future
        return False
    
    def requires_annotation(self, target, value, scope):
        """Determine if this assignment requires annotation."""
        # Always require for module-level and class attributes (if enabled)
        if scope in ('module', 'class') and self.should_check_scope(scope):
            return True
        
        # Special patterns that ALWAYS require annotation:
        if self.is_empty_literal(value):
            return True  # {}, [], set(), etc.
        
        if self.is_none_literal(value):
            return True  # x = None
        
        return False
    
    def is_empty_literal(self, node):
        """Check if value is an empty literal."""
        if isinstance(node, ast.List) and len(node.elts) == 0:
            return True  # []
        if isinstance(node, ast.Dict) and len(node.keys) == 0:
            return True  # {}
        if isinstance(node, ast.Set) and len(node.elts) == 0:
            return True  # set()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ('list', 'dict', 'set', 'tuple') and not node.args:
                    return True  # list(), dict(), set(), tuple()
        return False
    
    def is_none_literal(self, node):
        """Check if value is None."""
        return isinstance(node, ast.Constant) and node.value is None
```

### Scope Tracking Implementation

```python
def visit_Module(self, node):
    self.current_scope.append('module')
    self.generic_visit(node)
    self.current_scope.pop()

def visit_ClassDef(self, node):
    self.current_scope.append('class')
    self.generic_visit(node)
    self.current_scope.pop()

def visit_FunctionDef(self, node):
    self.current_scope.append('function')
    self.generic_visit(node)
    self.current_scope.pop()

def visit_AsyncFunctionDef(self, node):
    # Same as FunctionDef
    self.current_scope.append('function')
    self.generic_visit(node)
    self.current_scope.pop()

def get_current_scope(self):
    """Return current scope context."""
    if not self.current_scope:
        return 'module'
    if 'function' in self.current_scope:
        if self.current_scope[-1] == 'function':
            return 'function'
        # Inside a method
        return 'instance' if 'class' in self.current_scope else 'function'
    if 'class' in self.current_scope:
        return 'class'
    return 'module'
```

---

## Configuration Interface

### Scope Configuration (pyproject.toml)

```toml
[tool.repo_lint.python.type_annotations]
# Which scopes to enforce PEP 526 annotations
module_level = true          # MANDATORY baseline
class_attributes = true      # MANDATORY baseline
local_variables = false      # OPTIONAL (future: --strict-typing)
instance_attributes = false  # OPTIONAL (future)

# Special patterns (always enforced regardless of scope)
require_empty_literal_annotations = true
require_none_annotations = true

# Per-file ignores (gradual rollout)
per_file_ignores = [
    "tests/*.py:PEP526",
    "scripts/legacy/*.py:PEP526"
]
```

### CLI Flags

```bash
# Check with default config
repo-lint check --ci

# Enable strict typing (all scopes)
repo-lint check --ci --strict-typing

# Report-only mode for type annotations
repo-lint check --ci --report-only=type-annotations

# Per-scope overrides
repo-lint check --ci --check-local-vars
```

---

## Integration with repo-lint

### File Location

```
tools/repo_lint/checkers/
├── __init__.py
├── pep526_checker.py      # Main AST checker
└── pep526_config.py       # Configuration handling
```

### Python Runner Integration

Modify `tools/repo_lint/runners/python_runner.py`:

```python
from tools.repo_lint.checkers.pep526_checker import PEP526Checker

class PythonRunner(BaseRunner):
    def run_type_annotation_check(self, files):
        """Run PEP 526 type annotation checker."""
        config = self.load_pep526_config()
        checker = PEP526Checker(config)
        
        violations = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source, filename=file_path)
                checker.check_file(tree, file_path)
                violations.extend(checker.get_violations())
            except SyntaxError as e:
                # Skip files with syntax errors
                continue
        
        return violations
    
    def check(self, files):
        """Run all Python checks."""
        # ... existing ruff, black, pylint checks ...
        
        # Add PEP 526 check
        if self.config.get('check_type_annotations', True):
            type_violations = self.run_type_annotation_check(files)
            self.violations.extend(type_violations)
        
        return self.violations
```

---

## Violation Output Format

### Violation Object Structure

```python
{
    'type': 'missing-annotation',
    'scope': 'module',  # or 'class', 'function', 'instance'
    'file': 'tools/repo_lint/cli.py',
    'line': 42,
    'column': 4,
    'target': 'MAX_RETRIES',
    'message': 'Variable "MAX_RETRIES" missing type annotation (PEP 526)',
    'rule': 'PEP526-module',  # For per-rule ignores
    'severity': 'error'
}
```

### CI Report Format

```
PEP 526 Type Annotation Violations
==================================

tools/repo_lint/cli.py
  Line 42, Column 4: Variable "MAX_RETRIES" missing type annotation (PEP 526-module)
  Line 58, Column 4: Variable "cache" missing type annotation (PEP 526-module)

tools/repo_lint/runners/base.py
  Line 25, Column 8: Class attribute "enabled" missing type annotation (PEP 526-class)

Summary:
  3 violations in 2 files
  Module-level: 2
  Class attributes: 1
```

---

## Testing Strategy

### Unit Tests (`tools/repo_lint/tests/test_pep526_checker.py`)

1. **Scope detection tests:**
   - Test module-level detection
   - Test class attribute detection
   - Test function-local detection (future)
   - Test nested scopes (class inside function, etc.)

2. **Violation detection tests:**
   - Missing annotation on module-level variable
   - Missing annotation on class attribute
   - Empty literal without annotation
   - None initialization without annotation
   - Annotated assignments (should pass)

3. **Configuration tests:**
   - Scope enable/disable
   - Per-file ignores
   - Special pattern detection

4. **Integration tests:**
   - Run on sample Python files
   - Verify violation output format
   - Test with syntax errors (graceful handling)

### Test Fixtures

Create fixture files:
- `fixtures/pep526/missing_module_annotations.py`
- `fixtures/pep526/missing_class_annotations.py`
- `fixtures/pep526/empty_literals.py`
- `fixtures/pep526/correct_annotations.py`

---

## Implementation Phases

### Phase 3.3.1: Design ✅ COMPLETE (this document)

### Phase 3.3.2: Implement checker
1. Create `pep526_checker.py` with AST visitor
2. Create `pep526_config.py` for configuration
3. Add scope tracking and violation detection
4. Handle edge cases (imports, type aliases, etc.)

### Phase 3.3.3: Add configuration support
1. Define pyproject.toml schema
2. Implement per-file-ignores
3. Add CLI flags for scope overrides
4. Document configuration in user manual

### Phase 3.3.4: Comprehensive unit tests
1. Write 20+ unit tests covering all scenarios
2. Create test fixtures
3. Verify 100% pass rate
4. Test edge cases and error handling

### Phase 3.3.5: Integration with `repo-lint check --ci`
1. Integrate into PythonRunner
2. Update CLI to support type annotation checks
3. Add to CI workflow
4. Verify end-to-end flow

---

## Edge Cases to Handle

1. **Imports:**
   ```python
   from typing import List  # Not a violation (import)
   ```

2. **Type aliases:**
   ```python
   StrList = list[str]  # Not a violation (type alias)
   ```

3. **Tuple unpacking:**
   ```python
   x, y = 1, 2  # Not a violation (unpacking)
   ```

4. **Constants with obvious values:**
   ```python
   __version__ = "1.0.0"  # Maybe exempt? (config option)
   ```

5. **Property setters:**
   ```python
   @property
   def value(self): ...
   
   @value.setter
   def value(self, val):  # val should be annotated
       self._value = val
   ```

6. **Comprehensions:**
   ```python
   result = [x for x in range(10)]  # Not a violation (comprehension)
   ```

---

## Future Enhancements

1. **Auto-fix support:**
   - Infer simple types (int, str, bool from literals)
   - Suggest `Any` with tag for unknown types
   - Add `Optional[T]` for None initializations

2. **Type quality checks:**
   - Detect overly-broad `Any` usage
   - Suggest more specific types
   - Validate `Final` vs mutable usage

3. **Integration with mypy:**
   - Cross-reference with mypy errors
   - Use mypy type inference for suggestions

4. **--strict-typing mode:**
   - Enable all scopes (including local variables)
   - Stricter empty literal checks
   - Require `Final` for constants

---

## Summary

This design provides:

✅ **Repository-wide detection capability** (all scopes supported)  
✅ **Configurable enforcement scope** (only baseline enforced initially)  
✅ **AST-based implementation** (safe, deterministic)  
✅ **Integration with existing repo-lint infrastructure**  
✅ **Comprehensive testing strategy**  
✅ **Future-proof architecture** (can expand to local vars, auto-fix, etc.)

**Next:** Proceed to Phase 3.3.2 - Implement the checker.
