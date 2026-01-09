#!/usr/bin/env python3
"""PEP 526 "Everything Violations" fixture.

This file intentionally violates *variable annotation* conventions (PEP 526) across:
- Module scope (globals/constants)
- Class scope (class vars + instance vars)
- Function locals
- Control-flow blocks (for/with/try)
- Assignment patterns (unpacking, chained, walrus)
- Legacy type comments (pre-PEP 526 style)

It also includes a "Good Examples" section at the end containing correct patterns
that should NOT be flagged.

:Purpose:
    Test fixture for PEP 526 type annotation enforcement. Contains intentional
    *missing variable annotations* (and legacy type comments) to verify the
    checker detects them correctly.

:Environment Variables:
    None

:Examples:
    Used by test suite::

        from tools.repo_lint.checkers.pep526_checker import PEP526Checker
        checker = PEP526Checker(config)
        violations = checker.check_file('pep526_everything_violations.py')

:Exit Codes:
    0
        Success (N/A for fixture)
    1
        Failure (N/A for fixture)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# =============================================================================
# BAD EXAMPLES (INTENTIONAL PEP 526 VIOLATIONS: MISSING VARIABLE ANNOTATIONS)
# =============================================================================

# -----------------------------------------------------------------------------
# Module scope: missing annotations + legacy type comments
# -----------------------------------------------------------------------------

# Missing annotations (classic)
GLOBAL_INT = 1
global_str = "no annotation"
global_list = [1, 2, 3]
global_dict = {"a": 1}
global_tuple = (1, "two")
global_bool = True
global_float = 3.14159

# Chained assignment (unannotated targets)
a = b = c = 0

# Tuple unpacking without annotations
x, y = (10, 20)

# Legacy type comments instead of annotations (anti-pattern under PEP 526 enforcement)
legacy_numbers = []  # type: List[int]
legacy_map = {}  # type: Dict[str, int]


# -----------------------------------------------------------------------------
# Class scope: missing annotations (class vars + instance vars)
# -----------------------------------------------------------------------------


class Violations:
    """Class full of PEP 526 pain (missing variable annotations only)."""

    # Missing class attribute annotations
    counter = 0
    tags = ["a", "b", "c"]

    def __init__(self) -> None:
        """Initialize Violations with intentional PEP 526 violations.

        Demonstrates missing annotations on instance attributes.
        """
        # Instance attributes created without annotations
        self.host = "localhost"
        self.retries = 3
        self.timeout_s = 10

    def method(self) -> None:
        """Method with intentional PEP 526 violations.

        Demonstrates missing annotations on local variables and in control-flow.
        """
        # Locals without annotations
        tmp = 1
        msg = "hello"
        stuff = {"k": "v"}

        # Unpacking without annotations
        a1, a2 = (1, 2)

        # Chained assignment local
        m = n = 5

        # Walrus assignment (unannotated target)
        if found := "yep":
            _ = found

        # for-loop induced variables (unannotated targets)
        for i in range(3):
            loop_tmp = f"tmp-{i}"
            _ = loop_tmp

        # with/as variable (unannotated target)
        with open(__file__, "r", encoding="utf-8") as f:
            content = f.read()
            _ = content

        # try/except variable bindings (unannotated targets)
        try:
            risky = int("not an int")
            _ = risky
        except ValueError as e:
            err = e
            _ = err


# -----------------------------------------------------------------------------
# Dataclass: missing annotations are not fields; useful as fixture too
# -----------------------------------------------------------------------------


@dataclass
class BadData:
    """Dataclass with intentional PEP 526 violations (missing annotations)."""

    # Missing annotation => not a dataclass field (bad under PEP 526 enforcement)
    x = 1

    # These are properly annotated and should not be flagged by a PEP 526 checker
    y: int = 2
    z: List[int] = field(default_factory=list)


# -----------------------------------------------------------------------------
# Functions: keep signature annotations clean; violate via locals only
# -----------------------------------------------------------------------------


def bad_function(param1: int, param2: int, param3: str) -> int:
    """Function with intentional PEP 526 violations.

    Demonstrates missing annotations on local variables (not function signature).

    :param param1: First parameter
    :param param2: Second parameter
    :param param3: Third parameter
    :returns: Total value
    :rtype: int
    """
    total = param1 + param2  # missing local annotation
    d = {"a": 1}  # missing local annotation
    l = [1, 2, 3]  # missing local annotation

    # Legacy type comment local (anti-pattern under PEP 526 enforcement)
    t = None  # type: Optional[int]
    _ = t

    return total + len(param3) + len(d) + len(l)


def kitchen_sink() -> None:
    """Function with various PEP 526 variable annotation violations.

    Demonstrates missing annotations on comprehensions and other patterns.
    """
    # Comprehensions assigned without annotations
    comp_list = [i * i for i in range(10)]
    comp_dict = {str(i): i for i in range(10)}
    comp_set = {i for i in range(10)}

    _ = (comp_list, comp_dict, comp_set)


# =============================================================================
# GOOD EXAMPLES (SHOULD NOT BE FLAGGED)
# =============================================================================

# -----------------------------------------------------------------------------
# Module scope: correct annotations (modern built-in generics)
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


# -----------------------------------------------------------------------------
# Class scope: instance attributes declared with annotations in __init__
# -----------------------------------------------------------------------------


class GoodExamples:
    """Clean PEP 526 variable annotation patterns."""

    counter: int = 0
    tags: list[str] = ["ok"]

    def __init__(self, host: str, retries: int = 3) -> None:
        """Initialize GoodExamples with properly annotated attributes.

        :param host: Hostname
        :param retries: Number of retries
        """
        self.host: str = host
        self.retries: int = retries
        self.timeout_s: int = 30
        self.labels: list[str] = []

    def compute(self, x: int, y: int) -> int:
        """Compute sum of two integers.

        :param x: First integer
        :param y: Second integer
        :returns: Sum of x and y
        :rtype: int
        """
        result: int = x + y  # local annotation
        return result


# -----------------------------------------------------------------------------
# Dataclass: correct fields are annotated
# -----------------------------------------------------------------------------


@dataclass
class GoodData:
    """Dataclass with correct type annotations."""

    name: str
    count: int = 0
    tags: list[str] = field(default_factory=list)


# -----------------------------------------------------------------------------
# Functions: annotated locals / unpacking / loops / with / try
# -----------------------------------------------------------------------------


def good_unpacking() -> tuple[int, int]:
    """Demonstrate proper unpacking with annotations.

    :returns: Tuple of two integers
    :rtype: tuple[int, int]
    """
    a1: int
    a2: int
    a1, a2 = (1, 2)
    return (a1, a2)


def good_loop() -> int:
    """Sum numbers in a loop with proper annotations.

    :returns: Sum of numbers
    :rtype: int
    """
    total: int = 0
    for i in range(5):
        total += i
    return total


def good_control_flow() -> None:
    """Demonstrate typed variables in control-flow blocks."""
    found: str | None = None
    if found := "yep":
        _ = found

    for i in range(3):
        loop_tmp: str = f"tmp-{i}"
        _ = loop_tmp

    with open(__file__, "r", encoding="utf-8") as f:
        content: str = f.read()
        _ = content

    try:
        risky: int = int("123")
        _ = risky
    except ValueError as e:
        err: ValueError = e
        _ = err
