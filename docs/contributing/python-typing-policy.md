# Python Typing Policy

**Status:** Canonical source of truth for Python type annotation requirements (Issue #278) **Last Updated:** 2026-01-07
**Enforcement:** Planned (report-only mode initially, then enforcing)

## Overview

This document defines the mandatory Python type annotation requirements for the RFC-Shared-Agent-Scaffolding repository.
These standards ensure type safety, IDE support, and documentation completeness across all Python code.

**Key Principle:** All Python code must include type annotations for functions, module-level variables, and class
attributes. Type annotations serve both as machine-checkable contracts and as inline documentation.

---

## Scope of Type Annotations

### Module-Level Assignments (MANDATORY BASELINE)

**Requirement:** All module-level variable assignments MUST include type annotations using PEP 526 syntax.

**Rationale:** Module-level variables are part of the public API and must be explicitly typed for clarity and IDE
support.

**Syntax:**

```python
# ✅ Correct - explicit type annotation
MAX_RETRIES: int = 3
DEFAULT_TIMEOUT: float = 30.0
CONFIG_PATH: Path = Path("config.yaml")

# ❌ Wrong - no type annotation
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0
CONFIG_PATH = Path("config.yaml")
```

**Special cases:**

- **Constants:** Use `Final[T]` for immutable constants (Python 3.8+)

  ```python
  from typing import Final

  MAX_CONNECTIONS: Final[int] = 100
  API_VERSION: Final[str] = "v1.0.0"
  ```

- - **Optional module-level variables:**

  ```python
  from typing import Optional

  current_session: Optional[Session] = None
  ```

### Class Attributes (MANDATORY BASELINE)

**Requirement:** All class attributes MUST include type annotations using PEP 526 syntax.

**Rationale:** Class attributes define the structure of classes and must be explicitly typed for maintainability.

**Syntax:**

```python
class Config:
    # ✅ Correct - explicit type annotations
    name: str
    enabled: bool
    retry_count: int = 3
    timeout: Optional[float] = None

    def __init__(self, name: str, enabled: bool = True) -> None:
        self.name = name
        self.enabled = enabled
```

**Special cases:**

- **Class variables vs. instance variables:** Use `ClassVar[T]` for class-level variables

  ```python
  from typing import ClassVar

  class Counter:
      instances: ClassVar[int] = 0  # Shared across all instances
      name: str  # Instance variable

      def __init__(self, name: str) -> None:
          Counter.instances += 1
          self.name = name
  ```

### Local Variables (OPTIONAL FOR NOW)

**Requirement:** Local variable annotations are OPTIONAL for now. They may be enforced later via `--strict-typing` mode or "new/changed code only" policy.

**Recommended practice:** Annotate local variables when:

- - Type is not obvious from context - Variable is initialized to a generic value (e.g., empty list/dict) - Variable
  type changes or is reused with different types (anti-pattern, but if it exists)

**Examples:**

```python
def process_data(data: dict) -> list:
    # Optional but recommended - ambiguous empty literal
    results: list[dict] = []

    # Optional - type is obvious from context
    count = 0
    name = data.get("name", "")

    # Recommended - type not obvious
    config: Optional[Config] = load_config()

    return results
```

---

## Required Annotation Patterns

These patterns MUST always be annotated to avoid ambiguity and potential bugs.

### Empty Literals (MANDATORY)

**Requirement:** Empty container literals MUST be annotated with their intended type.

**Rationale:** Empty literals are ambiguous and can lead to type inference issues.

**Examples:**

```python
# ✅ Correct - explicit type annotations
empty_list: list[str] = []
empty_dict: dict[str, int] = {}
empty_set: set[int] = set()

# ❌ Wrong - ambiguous empty literals
empty_list = []
empty_dict = {}
empty_set = set()

# ✅ Also correct - using constructors with type hints
from typing import Dict, List, Set

empty_list: List[str] = list()
empty_dict: Dict[str, int] = dict()
empty_set: Set[int] = set()
```

### None Initializations (MANDATORY)

**Requirement:** Variables initialized to `None` that will be assigned a value later MUST use `Optional[T]` type annotation.

**Rationale:** `None` initializations are a common bug factory when the intended type is unclear.

**Examples:**

```python
from typing import Optional

# ✅ Correct - explicit Optional type
current_user: Optional[User] = None
session: Optional[Session] = None

# ❌ Wrong - no type annotation
current_user = None
session = None

# Later assignment
if authenticated:
    current_user = User.load(user_id)
```

### Public Configuration Variables (MANDATORY)

**Requirement:** All public configuration variables/constants MUST be annotated.

**Rationale:** Configuration values are part of the public API and must be explicitly typed.

**Examples:**

```python
from typing import Final

# ✅ Correct - configuration constants with types
DEBUG: Final[bool] = False
LOG_LEVEL: Final[str] = "INFO"
MAX_WORKERS: Final[int] = 4
ALLOWED_EXTENSIONS: Final[tuple[str, ...]] = (".py", ".sh", ".pl")

# ❌ Wrong - no type annotations
DEBUG = False
LOG_LEVEL = "INFO"
```

---

## Fallback Types (When Exact Type is Unknown)

### Prefer Real Types

**Requirement:** Use real, specific types wherever possible. Custom types, classes, and domain-specific types are
encouraged.

**Examples:**

```python
# ✅ Preferred - specific types
def process_user(user: User) -> UserResult:
    ...

def validate_config(config: AppConfig) -> ValidationResult:
    ...

# ⚠️ Acceptable fallback (when truly unknown)
def process_data(data: Any) -> Any:  # typing: Any (TODO: tighten)
    ...
```

### Using `Any` (Allowed with Tag)

**Requirement:** `Any` is ALLOWED but MUST be explicitly tagged for future tightening.

**Syntax:**

```python
from typing import Any

def legacy_handler(data: Any) -> Any:  # typing: Any (TODO: tighten)
    """Handle legacy data format.

    :param data: Legacy data structure (format varies)
    :returns: Processed result

    NOTE: Type should be tightened once data format is standardized.
    """
    ...
```

**Tag format:** `# typing: Any (TODO: tighten)`

**When to use `Any`:**

- - Working with truly dynamic data (JSON APIs with varying schemas) - Interfacing with untyped third-party libraries -
  Temporary solution during migration (must be tracked and resolved)

### Using `object` (Rare)

**Requirement:** Use `object` ONLY when you truly mean "unknown opaque thing" and `Any` would be misleading.

**Rationale:** `object` is more restrictive than `Any` (only base object methods available) and should be used intentionally.

**Examples:**

```python
# ✅ Correct - truly opaque reference
def store_opaque_handle(handle: object) -> None:
    """Store opaque handle for later reference.

    NOTE: Handle is never accessed, only stored and returned.
    """
    ...

# ❌ Wrong - should use Any (data is accessed/processed)
def process_unknown(data: object) -> None:
    result = data.transform()  # Type error! object has no 'transform'
```

---

## Function Annotations

### All Functions MUST Be Annotated (MANDATORY)

**Requirement:** Every function and method MUST have:

1. 1. Type annotations for every parameter (including keyword-only)
2. Return type annotation (including explicit `-> None`)

**Rationale:** Function signatures are contracts that enable type checking, IDE support, and documentation.

**Examples:**

```python
# ✅ Correct - complete annotations
def add(a: int, b: int) -> int:
    return a + b

def greet(name: str, prefix: str = "Hello") -> str:
    return f"{prefix}, {name}!"

def process_data(data: dict[str, Any]) -> None:
    print(data)
    # No return statement -> explicit -> None required

# ❌ Wrong - missing annotations
def add(a, b):  # Missing param and return annotations
    return a + b

def greet(name, prefix="Hello"):  # Missing annotations
    return f"{prefix}, {name}!"

def process_data(data):  # Missing annotations
    print(data)
```

### Explicit `-> None` Required (MANDATORY)

**Requirement:** Functions that return nothing MUST use explicit `-> None` annotation.

**Rationale:** Explicit `-> None` makes the intent clear and prevents accidental return value expectations.

**Examples:**

```python
# ✅ Correct - explicit -> None
def log_message(message: str) -> None:
    print(message)

def update_cache(key: str, value: Any) -> None:
    cache[key] = value

# ❌ Wrong - no return type
def log_message(message: str):
    print(message)
```

### `*args` and `**kwargs` Typing (DEFAULT POLICY)

**Requirement:** Use `*args: Any, **kwargs: Any` as the default.

**Rationale:** Simple, pragmatic approach that covers most cases. Advanced `Unpack[...]` syntax is optional for later.

**Default syntax:**

```python
from typing import Any

# ✅ Default approach - Any for args/kwargs
def wrapper_function(*args: Any, **kwargs: Any) -> None:
    underlying_function(*args, **kwargs)

def flexible_handler(name: str, *args: Any, **kwargs: Any) -> dict:
    return {"name": name, "args": args, "kwargs": kwargs}
```

**Advanced syntax (OPTIONAL):**

```python
from typing import Unpack, TypedDict

class UserKwargs(TypedDict):
    age: int
    email: str

def create_user(name: str, **kwargs: Unpack[UserKwargs]) -> User:
    ...
```

**Note:** Advanced `Unpack[...]` typing may be adopted later for specific high-value cases, but is NOT required initially.

---

## Optional / Union Syntax (Maximum Compatibility)

### Prefer `Optional[T]` (RECOMMENDED)

**Requirement:** `Optional[T]` is PREFERRED for broad compatibility (Python 3.8+).

**Rationale:** Maintains compatibility with older Python versions and existing codebases.

**Syntax:**

```python
from typing import Optional

# ✅ Preferred - Optional[T]
def find_user(user_id: int) -> Optional[User]:
    ...

config: Optional[dict] = None

# ⚠️ Allowed but not preferred - PEP 604 syntax
def find_user(user_id: int) -> User | None:
    ...

config: dict | None = None
```

### PEP 604 `T | None` (ALLOWED BUT NOT PREFERRED)

**Policy:** PEP 604 union syntax (`T | None`) is ALLOWED but NOT preferred.

**Avoid churn rule:** Only update `Optional[T]` → `T | None` when touching code for another reason. Do NOT create "syntax cleanup" PRs.

**Rationale:** Avoid unnecessary churn while allowing modern syntax in new code.

---

## Docstring `:rtype:` Policy

### Require `:rtype:` for Non-None Returns (MANDATORY)

**Requirement:** Functions/methods that return a non-None value MUST include `:rtype:` in their reST docstring.

**Rationale:** Docstring `:rtype:` provides human-readable documentation that complements machine-readable type annotations.

**Examples:**

```python
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers.

    :param a: First number
    :param b: Second number
    :returns: Sum of a and b
    :rtype: int
    """
    return a + b

def find_user(user_id: int) -> Optional[User]:
    """Find user by ID.

    :param user_id: User identifier
    :returns: User object if found, None otherwise
    :rtype: Optional[User]
    """
    return users.get(user_id)
```

### Do NOT Require `:rtype:` for `-> None` (MANDATORY)

**Requirement:** Functions that return `None` MUST NOT include `:rtype:` in their docstring.

**Rationale:** `-> None` is self-documenting in the signature; adding `:rtype: None` is redundant clutter.

**Examples:**

```python
# ✅ Correct - no :rtype: for -> None
def log_message(message: str) -> None:
    """Log a message to stdout.

    :param message: Message to log
    """
    print(message)

# ❌ Wrong - unnecessary :rtype: None
def log_message(message: str) -> None:
    """Log a message to stdout.

    :param message: Message to log
    :rtype: None  # ← DO NOT ADD THIS
    """
    print(message)
```

### Generators and Iterators

**Requirement:** Document generator/iterator return types using proper generic types.

**Examples:**

```python
from typing import Iterator, Generator

def generate_numbers(n: int) -> Iterator[int]:
    """Generate numbers from 0 to n-1.

    :param n: Upper limit (exclusive)
    :returns: Iterator of integers
    :rtype: Iterator[int]
    """
    for i in range(n):
        yield i

def process_lines(filename: str) -> Generator[str, None, None]:
    """Read and process lines from a file.

    :param filename: Path to file
    :returns: Generator of processed lines
    :rtype: Generator[str, None, None]
    """
    with open(filename) as f:
        for line in f:
            yield line.strip()
```

---

## Edge Cases and Special Patterns

### Comprehensions

**Policy:** Comprehensions do NOT require explicit type annotations (type is inferred from context).

**Examples:**

```python
# ✅ No annotation needed - type inferred
numbers = [int(x) for x in strings]
user_map = {u.id: u.name for u in users}

# ⚠️ If assigning to a variable with complex type, annotate the variable
from typing import Dict, List

# Annotation on variable, not comprehension
processed: List[Dict[str, Any]] = [
    {"id": x.id, "data": x.data} for x in items
]
```

### Unpacking Assignments

**Policy:** Unpacking assignments do NOT require individual element annotations (type is inferred).

**Examples:**

```python
# ✅ No annotation needed - type inferred from function return
status, message = validate_input(data)

# ✅ If needed, annotate with tuple type
result: tuple[int, str] = validate_input(data)
status, message = result
```

### `global` and `nonlocal`

**Policy:** Variables used with `global`/`nonlocal` should be annotated at their original declaration site, not at the `global`/`nonlocal` statement.

**Examples:**

```python
# Module level
counter: int = 0

def increment() -> None:
    global counter  # No annotation here
    counter += 1
```

### Dynamic Attribute Injection

**Policy:** Avoid dynamic attribute injection when possible. If unavoidable, document in docstring and use `setattr` with type comment.

**Examples:**

```python
# ⚠️ Discouraged - dynamic attributes
def add_dynamic_attr(obj: Any, name: str, value: Any) -> None:
    """Add dynamic attribute to object.

    NOTE: Dynamic attributes bypass type checking.
    """
    setattr(obj, name, value)

# ✅ Preferred - use proper class attributes or TypedDict
class DynamicConfig(TypedDict, total=False):
    name: str
    value: int
```

---

## Enforcement Strategy

### Phase 1: Measurement (Report-Only)

**Status:** Current phase

- - Run Ruff ANN* rules in report-only mode - Collect baseline violations (722 errors as of 2026-01-07) - No CI failures
  yet

### Phase 2: Gradual Rollout

**Planned:**

- - Enable Ruff ANN* rules for NEW code only (via CI diff) - Allow existing violations to be fixed incrementally -
  Provide autofix suggestions where safe

### Phase 3: Full Enforcement

**Target:**

- - All Python code MUST pass Ruff ANN* checks - CI fails on new violations - Baseline violations tracked and resolved

---

## Tooling and Enforcement

### Linting Tools

**Primary enforcement:** Ruff ANN* rules (flake8-annotations)

**Enabled rules:**

- `ANN001` - Missing type annotation for function argument
- `ANN201` - Missing return type annotation for public function
- `ANN202` - Missing return type annotation for private function
- `ANN204` - Missing return type annotation for special method
- `ANN206` - Missing return type annotation for class method
- `ANN002` - Missing type annotation for `*args`
- `ANN003` - Missing type annotation for `**kwargs`
- `ANN401` - Dynamically typed expressions (Any) discouraged (warning only)

**Configuration:** `pyproject.toml`

### IDE Support

**Recommended:** Use IDEs with Python type checking support:

- - VS Code with Pylance - PyCharm (built-in) - mypy for CLI type checking

### Future: Type Checker Integration

**Planned:** Integrate `mypy` for full static type checking (beyond annotation presence).

---

## Examples

### Complete Example: Module with Full Annotations

```python
#!/usr/bin/env python3
"""User management module.

:Purpose:
    Provides user CRUD operations with type-safe interfaces.
"""

from __future__ import annotations

from typing import Optional, Final
from pathlib import Path

# Module-level constants
MAX_USERNAME_LENGTH: Final[int] = 50
DEFAULT_ROLE: Final[str] = "user"

# Module-level variable
active_users: dict[int, User] = {}


class User:
    """Represents a user in the system."""

    # Class attributes
    id: int
    username: str
    role: str

    def __init__(self, id: int, username: str, role: str = DEFAULT_ROLE) -> None:
        """Initialize a new user.

        :param id: User identifier
        :param username: User's username
        :param role: User's role (default: 'user')
        """
        self.id = id
        self.username = username
        self.role = role

    def to_dict(self) -> dict[str, Any]:
        """Convert user to dictionary.

        :returns: User data as dictionary
        :rtype: dict[str, Any]
        """
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
        }


def create_user(id: int, username: str, role: str = DEFAULT_ROLE) -> User:
    """Create a new user.

    :param id: User identifier
    :param username: User's username
    :param role: User's role
    :returns: Created user object
    :rtype: User
    """
    user = User(id, username, role)
    active_users[id] = user
    return user


def find_user(id: int) -> Optional[User]:
    """Find user by ID.

    :param id: User identifier
    :returns: User if found, None otherwise
    :rtype: Optional[User]
    """
    return active_users.get(id)


def delete_user(id: int) -> None:
    """Delete user by ID.

    :param id: User identifier
    """
    active_users.pop(id, None)
```

---

## References

- [PEP 526 – Syntax for Variable Annotations](https://peps.python.org/pep-0526/)
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)
- [PEP 604 – Allow writing union types as X | Y](https://peps.python.org/pep-0604/)
- [typing — Support for type hints (Python docs)](https://docs.python.org/3/library/typing.html)
- [Ruff ANN rules documentation](https://docs.astral.sh/ruff/rules/#flake8-annotations-ann)
- - [docs/contributing/docstring-contracts/python.md](./docstring-contracts/python.md) - Python docstring contract

---

**Version:** 1.0.0
**Issue:** #278
**Status:** Initial policy definition (enforcement pending)
