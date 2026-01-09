# Phase 4 Extension: PEP 526 and Docstring `:rtype:` Autofix Strategies

## Overview

This document outlines safe autofix strategies for:
1. **PEP 526**: Module-level and class attribute type annotations
2. **Docstring `:rtype:`**: Adding return type fields to docstrings

Both can be auto-fixed in many cases by leveraging existing type annotations from function signatures.

---

## Part 1: PEP 526 Autofix Strategy

### Safe Autofix Categories

#### 1. Literal Value Inference (HIGH CONFIDENCE)

**Pattern:** Variable assigned a literal value → infer type from literal

**Examples:**
```python
# Before
TIMEOUT = 30
HOST = "localhost"
ENABLED = True
RATIO = 0.25

# After (autofix)
TIMEOUT: int = 30
HOST: str = "localhost"
ENABLED: bool = True
RATIO: float = 0.25
```

**Safety:** Very high - literal type is unambiguous
**Coverage:** ~30-40% of violations (constants with literal values)

#### 2. Typed Constructor Calls (HIGH CONFIDENCE)

**Pattern:** Variable assigned result of typed constructor → use constructor return type

**Examples:**
```python
# Before
from pathlib import Path
ROOT = Path(__file__).parent
CONFIG_FILE = Path("config.yaml")

# After (autofix)
ROOT: Path = Path(__file__).parent
CONFIG_FILE: Path = Path("config.yaml")
```

**Safety:** High - Path() always returns Path
**Coverage:** ~10-15% of violations (Path and similar constructors)

#### 3. Empty Collection Literals (REQUIRES EXPLICIT TYPE)

**Pattern:** Empty collection → cannot infer element type

**Examples:**
```python
# Before
CACHE = {}
ITEMS = []

# Cannot autofix - element type unknown
# Needs human decision: dict[str, int]? dict[str, Any]? list[str]?
```

**Safety:** Cannot autofix safely
**Action:** Flag for manual annotation with suggested generic form:
- `{}` → suggest `dict[Any, Any]` or specific types
- `[]` → suggest `list[Any]` or specific type
- `set()` → suggest `set[Any]` or specific type

#### 4. Type-Annotated Function Returns (MEDIUM CONFIDENCE)

**Pattern:** Variable = function_call() where function has return type annotation

**Examples:**
```python
# Before
def get_config() -> dict[str, str]:
    return {"key": "value"}

CONFIG = get_config()

# After (autofix - if function annotation exists)
CONFIG: dict[str, str] = get_config()
```

**Safety:** Medium - requires parsing function definition
**Coverage:** ~20-30% of violations (if we implement function return type lookup)
**Implementation complexity:** Moderate (need to resolve function definitions)

### Implementation Approach

#### Option A: AST-Based Autofix Tool (Recommended)

Create a dedicated autofix tool `tools/repo_lint/fixers/pep526_fixer.py`:

**Algorithm:**
1. Parse Python file with AST
2. Find all module-level and class attribute assignments
3. For each assignment without annotation:
   - If RHS is a literal → infer type from literal (int/str/bool/float)
   - If RHS is `Path(...)` → annotate as `Path`
   - If RHS is typed function call → lookup function return type
   - Otherwise → skip (requires manual annotation)
4. Insert annotation using `ast.unparse()` or string manipulation
5. Preserve formatting (use `black` after modification)

**Example implementation sketch:**
```python
def autofix_pep526(file_path: Path) -> bool:
    """Autofix PEP 526 violations where type can be safely inferred.
    
    Returns True if modifications were made.
    """
    tree = ast.parse(file_path.read_text())
    modified = False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            # Check if already annotated
            if has_annotation(node):
                continue
            
            # Try to infer type
            if isinstance(node.value, ast.Constant):
                # Literal: can infer
                inferred_type = type(node.value.value).__name__
                add_annotation(node, inferred_type)
                modified = True
            elif isinstance(node.value, ast.Call):
                if is_path_constructor(node.value):
                    add_annotation(node, "Path")
                    modified = True
    
    if modified:
        # Write back with black formatting
        write_with_formatting(file_path, tree)
    
    return modified
```

#### Option B: Ruff Extension (Future)

Submit feature request to Ruff to support PEP 526 inference for literals.

**Timeline:** Longer term (depends on Ruff maintainers)

### Autofix Coverage Estimate

| Category | Confidence | Coverage | Implementation Effort |
|----------|-----------|----------|----------------------|
| Literals | High | 30-40% | Low (AST pattern matching) |
| Typed constructors (Path) | High | 10-15% | Low (known constructors) |
| Function return types | Medium | 20-30% | Medium (cross-reference lookup) |
| Empty collections | N/A (manual) | 0% | N/A |
| Complex expressions | Low | 0% | N/A |

**Total safe autofix coverage: 40-65% of PEP 526 violations**

---

## Part 2: Docstring `:rtype:` Autofix Strategy

### Safe Autofix: Copy from Function Annotation

**Pattern:** Function has `-> T` annotation but docstring lacks `:rtype:` → copy annotation to docstring

### Algorithm

1. Parse Python file with AST
2. For each function definition:
   - Check if has return annotation (and not `-> None`)
   - Check if docstring exists
   - Check if docstring has `:rtype:` field
   - If annotation exists but `:rtype:` missing → ADD IT
3. Convert annotation AST to string
4. Insert `:rtype: <type>` into docstring before last line

### Type Annotation → reST Conversion

**Mapping rules:**
```python
# Simple types
int → :rtype: int
str → :rtype: str
bool → :rtype: bool
Path → :rtype: Path

# Optional (PEP 604)
str | None → :rtype: str | None
Optional[str] → :rtype: str | None

# Generics
list[int] → :rtype: list[int]
dict[str, int] → :rtype: dict[str, int]
tuple[int, str] → :rtype: tuple[int, str]

# Complex types (preserve as-is)
Generator[int, None, None] → :rtype: Generator[int, None, None]
```

### Implementation Example

```python
def autofix_docstring_rtype(file_path: Path) -> bool:
    """Add :rtype: to docstrings based on function annotations.
    
    Returns True if modifications were made.
    """
    tree = ast.parse(file_path.read_text())
    modified = False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Skip if no return annotation or returns None
            if not node.returns or is_none_annotation(node.returns):
                continue
            
            # Get docstring
            docstring = ast.get_docstring(node)
            if not docstring:
                continue  # No docstring to modify
            
            # Check if :rtype: already exists
            if ':rtype:' in docstring:
                continue  # Already has :rtype:
            
            # Convert annotation to string
            return_type = ast.unparse(node.returns)
            
            # Insert :rtype: before final line
            new_docstring = insert_rtype_field(docstring, return_type)
            replace_docstring(node, new_docstring)
            modified = True
    
    if modified:
        write_with_formatting(file_path, tree)
    
    return modified


def insert_rtype_field(docstring: str, return_type: str) -> str:
    """Insert :rtype: field into reST docstring.
    
    Inserts before the closing quotes, after any other fields.
    
    :param docstring: Original docstring content
    :param return_type: Type annotation as string
    :rtype: str
    """
    lines = docstring.split('\n')
    
    # Find insertion point (after :param:, :returns:, etc., before end)
    insert_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith(':') and not line.startswith(':rtype:'):
            insert_idx = i + 1
            break
    
    # Insert :rtype: field
    rtype_line = f"    :rtype: {return_type}"
    lines.insert(insert_idx, rtype_line)
    
    return '\n'.join(lines)
```

### Examples

**Example 1: Simple return type**
```python
# Before
def get_name() -> str:
    """Get the name.
    
    :returns: The name
    """
    return "Alice"

# After (autofix)
def get_name() -> str:
    """Get the name.
    
    :returns: The name
    :rtype: str
    """
    return "Alice"
```

**Example 2: Optional return type**
```python
# Before
def find_user(user_id: int) -> User | None:
    """Find user by ID.
    
    :param user_id: User ID to search
    :returns: User if found, None otherwise
    """
    ...

# After (autofix)
def find_user(user_id: int) -> User | None:
    """Find user by ID.
    
    :param user_id: User ID to search
    :returns: User if found, None otherwise
    :rtype: User | None
    """
    ...
```

**Example 3: Complex generic**
```python
# Before
def get_mapping() -> dict[str, list[int]]:
    """Get the mapping.
    
    :returns: Mapping of keys to lists
    """
    return {}

# After (autofix)
def get_mapping() -> dict[str, list[int]]:
    """Get the mapping.
    
    :returns: Mapping of keys to lists
    :rtype: dict[str, list[int]]
    """
    return {}
```

### Safety Guarantees

1. **Only adds `:rtype:`** - never modifies existing docstring content
2. **Only when annotation exists** - never guesses types
3. **Preserves exact annotation syntax** - uses `ast.unparse()` for accuracy
4. **Skips `-> None`** - per policy, no `:rtype:` for void functions
5. **Preserves formatting** - runs `black` after modification

### Coverage Estimate

**Current state (from Phase 4.2 Stage 1):**
- 586 functions now have return type annotations (via Ruff autofix)
- Unknown how many have docstrings
- Unknown how many already have `:rtype:`

**Estimate:**
- Assume 80% of annotated functions have docstrings
- Assume 20% already have `:rtype:`
- **Potential autofix: ~370 docstrings** (586 × 0.8 × 0.8)

---

## Implementation Plan

### Phase 4.3: Implement PEP 526 Autofix Tool

**Deliverables:**
1. `tools/repo_lint/fixers/pep526_fixer.py` - AST-based fixer
2. Comprehensive unit tests with fixtures
3. Integration into `repo-lint fix` command (new `--pep526` flag)
4. Documentation in user manual

**Timeline:** 4-6 hours

### Phase 4.4: Implement Docstring `:rtype:` Autofix Tool

**Deliverables:**
1. `tools/repo_lint/fixers/docstring_rtype_fixer.py` - AST-based fixer
2. Comprehensive unit tests with fixtures
3. Integration into `repo-lint fix` command (new `--docstring-rtype` flag)
4. Documentation in user manual

**Timeline:** 3-4 hours

### Phase 4.5: Run Both Autofixes on Codebase

**Actions:**
1. Run PEP 526 autofix: `repo-lint fix --pep526`
2. Run docstring autofix: `repo-lint fix --docstring-rtype`
3. Review changes
4. Run `repo-lint check --ci` to verify
5. Commit

**Timeline:** 1-2 hours

### Phase 4.6: Manual Cleanup of Remaining Violations

**After autofixes:**
- Estimated remaining PEP 526: ~50-90 violations (35-60% reduced)
- Estimated remaining docstring: ~20-50 violations (if any complex cases)
- Estimated remaining function params: ~200-300 violations (unchanged)

**Timeline:** 8-12 hours for manual cleanup

---

## Success Criteria

- [ ] PEP 526 fixer implemented and tested
- [ ] Docstring `:rtype:` fixer implemented and tested
- [ ] Both integrated into `repo-lint fix` command
- [ ] Autofixes applied to codebase
- [ ] 80%+ of violations resolved (combination of Ruff + PEP 526 + docstring autofixes)
- [ ] All tests passing
- [ ] CI green

---

## Notes

- Autofix tools must be deterministic and safe
- Always run `black` after AST modifications to preserve formatting
- Keep autofix conservative - if uncertain, skip and flag for manual review
- Add `--dry-run` flag to preview changes before applying
- Add `--diff` flag to show what would change
