#!/usr/bin/env python3
"""
PEP 526 "Everything Violations" fixture.

This file intentionally violates variable annotation conventions across:
- Module scope
- Class scope (class vars + instance vars)
- Function locals
- Control-flow blocks (for/with/try)
- Assignment patterns (unpacking, chained, walrus)
- Legacy type comments (pre-PEP526 style)
- Misuse of typing helpers (ClassVar/Final/Optional/Union/Any, bare generics)

It also includes a "Good Examples" section at the end containing
correct patterns that should NOT be flagged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Final, List, Optional, Tuple, Union


# =============================================================================
# BAD EXAMPLES (INTENTIONAL VIOLATIONS)
# =============================================================================

# -----------------------------------------------------------------------------
# Module scope: missing annotations, bad annotations, type comments
# -----------------------------------------------------------------------------

# Missing annotations (classic)
GLOBAL_INT = 1
global_str = "no annotation"
global_list = [1, 2, 3]
global_dict = {"a": 1}
global_tuple = (1, "two")
global_bool = True
global_float = 3.14159

# Chained assignment (often hard to annotate cleanly; still a violation in strict modes)
a = b = c = 0

# Tuple unpacking without annotations
x, y = (10, 20)

# Legacy type comments instead of annotations (anti-pattern under PEP 526 enforcement)
legacy_numbers = []  # type: List[int]
legacy_map = {}      # type: Dict[str, int]

# Bare generics (invalid/undesired in strict typing)
bare_list: List = []
bare_dict: Dict = {}

# Annotation mismatch
port: int = "eighty"
names: list[str] = [1, 2, 3]  # wrong element types

# Optional misuse / mismatch
maybe_count: Optional[int] = "nope"

# Union mismatch
id_or_name: Union[int, str] = 3.14

# Any used as an escape hatch (some conventions forbid Any except with explicit TODO tags)
escape: Any = "whatever"
escape = 123

# Dangling annotation (declared but not assigned)
declared_only: int

# Final misuse (rebinding later)
IMMUTABLE: Final[int] = 123

# ClassVar at module scope (nonsense usage)
module_classvar: ClassVar[int] = 7


# -----------------------------------------------------------------------------
# Class scope: missing annotations, wrong ClassVar/Final patterns, instance attrs
# -----------------------------------------------------------------------------

class Violations:
    """Class full of PEP 526 pain."""

    # Missing class attribute annotations
    counter = 0
    tags = ["a", "b", "c"]

    # Bad ClassVar usage
    cv1: ClassVar[int] = "string mismatch"
    cv2: ClassVar = 123  # bare ClassVar

    # Final that gets rebound
    CONST: Final[str] = "hello"
    CONST = "rebinding Final"

    # Annotated class attribute with wrong type
    enabled: bool = "yes"

    # Annotated without assignment
    declared_attr: str

    def __init__(self) -> None:
        # Dynamic instance attributes without prior annotation / declaration
        self.host = "localhost"
        self.retries = 3
        self.timeout = 10

        # Type comment instance attribute (anti-pattern under strict PEP 526 rules)
        self.rate = 1.0  # type: float

        # Wrong typed instance attribute
        self.max_size: int = "huge"

        # Declared-only instance attribute (some rules forbid, some require init assignment)
        self.later: str

    def method(self) -> None:
        # Locals without annotations
        tmp = 1
        msg = "hello"
        stuff = {"k": "v"}

        # Type comment local (anti-pattern)
        legacy_local = []  # type: List[str]

        # Wrong typed local
        count: int = "ten"

        # Unpacking without annotations
        a1, a2 = (1, 2)

        # Chained assignment local
        m = n = 5

        # Walrus assignment (often unannotated)
        if (found := "yep"):
            pass

        # for-loop induced variables
        for i in range(3):
            loop_tmp = f"tmp-{i}"

        # with/as variable
        with open(__file__, "r", encoding="utf-8") as f:
            content = f.read()

        # try/except variable bindings
        try:
            risky = int("not an int")
        except Exception as e:
            err = e


# -----------------------------------------------------------------------------
# Dataclass: missing annotations are not fields; useful as fixture too
# -----------------------------------------------------------------------------

@dataclass
class BadData:
    # Missing annotation => not a dataclass field (bad under enforcement)
    x = 1

    # Wrong default type
    y: int = "wrong"

    # Bare generic
    z: List = None


# -----------------------------------------------------------------------------
# Functions: params missing, locals missing, return missing, weird patterns
# -----------------------------------------------------------------------------

def bad_function(param1, param2: int, param3: "str"):
    # param1 missing annotation, return missing annotation

    # Locals missing
    total = param2 + 1
    d = {"a": 1}
    l = [1, 2, 3]

    # Type comment
    t = None  # type: Optional[int]

    # Wrong annotations
    total2: int = "not int"

    # Unpacking
    u, v = (1, 2)

    # Chained assign
    p = q = 9

    # Walrus
    if (ok := True):
        pass

    return total


def kitchen_sink() -> None:
    # Comprehensions assigned without annotations
    comp_list = [i * i for i in range(10)]
    comp_dict = {str(i): i for i in range(10)}
    comp_set = {i for i in range(10)}

    # Annotated but mismatched generics
    typed_dict: dict[str, int] = {"a": "b"}

    # Optional wrong
    o: Optional[int] = "x"

    # Union wrong
    u: int | str = 3.14

    # Final local rebind
    local_final: Final[int] = 1
    local_final = 2  # type: ignore[misc]

    # Attribute created on ad-hoc object (dynamic attr)
    obj = type("Obj", (), {})()
    obj.dynamic = 1
    obj.dynamic = "two"

    # Legacy type comment local
    legacy = {}  # type: Dict[str, int]
    legacy["x"] = 1


# Mutating a "Final" module symbol (semantic violation)
def mutate_final() -> None:
    global IMMUTABLE
    IMMUTABLE = 999


# =============================================================================
# GOOD EXAMPLES (SHOULD NOT BE FLAGGED)
# =============================================================================

# -----------------------------------------------------------------------------
# Module scope: correct annotations + modern generics
# -----------------------------------------------------------------------------

MODULE_PORT: int = 22
MODULE_HOST: str = "example.local"
MODULE_ENABLED: bool = True
MODULE_RATIO: float = 0.25
MODULE_TAGS: list[str] = ["alpha", "beta"]
MODULE_MAP: dict[str, int] = {"a": 1, "b": 2}
MODULE_PAIR: tuple[int, str] = (1, "one")

# Optional / Union (modern)
MODULE_MAYBE: int | None = None
MODULE_ID: int | str = "abc123"

# Final constant (no rebinding!)
DEFAULT_TIMEOUT_S: Final[int] = 30

# If your contracts require Any usage to be tagged, this is how it could look:
# typing: Any (TODO: tighten)
SAFE_ESCAPE: Any = {"reason": "fixture example"}


# -----------------------------------------------------------------------------
# Class scope: correct ClassVar + instance attributes declared in __init__
# -----------------------------------------------------------------------------

class GoodExamples:
    """Clean typing patterns."""

    # Proper ClassVar usage
    version: ClassVar[str] = "1.0.0"
    supported: ClassVar[bool] = True

    # Typed class attribute that is NOT ClassVar (it’s a descriptor-like shared default)
    default_retries: int = 3

    def __init__(self, host: str, retries: int = 3) -> None:
        # Explicitly typed instance attributes
        self.host: str = host
        self.retries: int = retries
        self.timeout_s: int = DEFAULT_TIMEOUT_S
        self.labels: list[str] = []

    def add_label(self, label: str) -> None:
        self.labels.append(label)

    def compute(self, x: int, y: int) -> int:
        result: int = x + y  # local annotation
        return result


# -----------------------------------------------------------------------------
# Dataclass: correct fields are annotated
# -----------------------------------------------------------------------------

@dataclass
class GoodData:
    name: str
    count: int = 0
    tags: list[str] = None if False else []  # intentionally weird but still typed


# -----------------------------------------------------------------------------
# Functions: annotated args, return, and locals
# -----------------------------------------------------------------------------

def good_function(user: str, retries: int, maybe: Optional[str] = None) -> str:
    msg: str = f"{user}:{retries}"
    if maybe is not None:
        msg = f"{msg}:{maybe}"
    return msg


def good_unpacking() -> tuple[int, int]:
    # If your enforcement *requires* explicit annotations for unpack targets,
    # this shows the canonical pattern.
    a1: int
    a2: int
    a1, a2 = (1, 2)
    return (a1, a2)


def good_loop() -> int:
    total: int = 0
    for i in range(5):
        total += i
    return total
