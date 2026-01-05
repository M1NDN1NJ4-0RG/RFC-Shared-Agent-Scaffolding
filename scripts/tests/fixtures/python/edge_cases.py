#!/usr/bin/env python3
"""Test fixture with Python edge cases for symbol discovery.

This module contains various edge cases to test the Python AST parser's
ability to correctly identify and validate function and class documentation.

:Purpose:
    Test Python validator symbol discovery for:
    - Multiline function signatures
    - Nested functions
    - Special characters in names
    - Async functions
    - Complex parameter signatures

:Environment Variables:
    TEST_MODE
        When set, fixture runs in test mode

:Examples:
    Import and use this fixture::

        from fixtures.python import edge_cases
        edge_cases.outer_function()

:Exit Codes:
    0
        Success - all tests pass
    1
        Failure - validation errors found
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional, Union


class SimpleClass:
    """A simple class for testing class documentation."""

    def __init__(self, value: int):
        """Initialize the class.

        :param value: Initial value to store
        """
        self.value = value


class ComplexClass:
    """Class with various method types to test symbol discovery.

    This class includes instance methods, class methods, static methods,
    properties, and async methods.
    """

    def __init__(
        self,
        name: str,
        count: int,
        optional: Optional[str] = None,
    ):
        """Initialize with multiline signature.

        :param name: Object name
        :param count: Initial count
        :param optional: Optional parameter that extends to multiple lines
        """
        self.name = name
        self.count = count
        self.optional = optional

    def instance_method(self, param: str) -> str:
        """Regular instance method.

        :param param: Input parameter
        :returns: Modified parameter
        """
        return param.upper()

    @classmethod
    def class_method(cls, value: int) -> "ComplexClass":
        """Class method for alternative construction.

        :param value: Value to use
        :returns: New instance of ComplexClass
        """
        return cls(name="default", count=value)

    @staticmethod
    def static_method(a: int, b: int) -> int:
        """Static method for utility operations.

        :param a: First operand
        :param b: Second operand
        :returns: Sum of a and b
        """
        return a + b

    @property
    def computed_value(self) -> int:
        """Property that computes a value.

        :returns: Computed integer value
        """
        return self.count * 2

    async def async_method(self, delay: float) -> None:
        """Async method for asynchronous operations.

        :param delay: Time to wait in seconds
        """
        await asyncio.sleep(delay)


# pylint: disable=keyword-arg-before-vararg  # Intentional test fixture
def function_with_multiline_signature(
    first_param: str,
    second_param: int,
    third_param: Optional[Dict[str, Any]] = None,
    *args: str,
    keyword_only: bool = False,
    **kwargs: Any,
) -> Union[str, int]:
    """Function with complex multiline signature.

    Tests that the validator correctly handles functions with parameters
    spanning multiple lines, including *args, **kwargs, and keyword-only args.

    :param first_param: First parameter
    :param second_param: Second parameter
    :param third_param: Optional dict parameter
    :param args: Variable positional arguments
    :param keyword_only: Keyword-only parameter
    :param kwargs: Variable keyword arguments
    :returns: Either string or int depending on inputs
    """
    if keyword_only:
        return str(first_param)
    return second_param


async def async_function(
    url: str,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """Async function for testing async def support.

    :param url: URL to fetch
    :param timeout: Timeout in seconds
    :returns: Response data as dictionary
    """
    await asyncio.sleep(0.1)
    return {"url": url, "status": 200}


def outer_function(x: int) -> Callable[[int], int]:
    """Outer function containing nested function.

    Tests that the validator correctly identifies and validates nested
    function documentation.

    :param x: Value for outer function
    :returns: Inner function closure
    """

    def inner_function(y: int) -> int:
        """Inner nested function.

        :param y: Value to add
        :returns: Sum of x and y
        """
        return x + y

    return inner_function


# pylint: disable=non-ascii-name  # Intentional test fixture for unicode handling
def function_with_special_chars_λ(param_with_émoji: str) -> str:
    """Function with unicode characters in name.

    Tests handling of special characters and unicode in both function
    names and parameter names.

    :param param_with_émoji: Parameter with unicode characters
    :returns: Processed string
    """
    return param_with_émoji.upper()


def exempted_function():  # noqa: D103
    pass


def _private_function(value: int) -> int:
    """Private function (leading underscore).

    Per Phase 3 Sub-Item 3.7.3, private functions MUST still be documented
    unless explicitly exempted via pragma.

    :param value: Input value
    :returns: Modified value
    """
    return value * 2


def __dunder_function__(item: Any) -> str:  # noqa: N807
    """Dunder function (double underscore).

    Per Phase 3 Sub-Item 3.7.3, dunder functions MUST still be documented.
    This is an intentional test fixture for dunder-style naming.

    :param item: Item to process
    :returns: String representation
    """
    return str(item)


def function_with_decorator_stack(arg: str) -> str:
    """Function with multiple decorators (intentionally not decorated here for simplicity).

    :param arg: Argument to process
    :returns: Processed argument
    """
    return arg.strip()


def function_returns_none() -> None:
    """Function that explicitly returns None.

    Note: Functions with return type annotation of None don't require :returns:.
    """
    print("This function has no return value")


def function_no_params() -> int:
    """Function with no parameters.

    :returns: A constant value
    """
    return 42


class _PrivateClass:
    """Private class (leading underscore).

    Per Phase 3 Sub-Item 3.7.3, private classes MUST be documented unless
    explicitly exempted via pragma.
    """

    def method(self, x: int) -> int:
        """Method in private class.

        :param x: Input value
        :returns: Modified value
        """
        return x + 1


# Test that validator handles code after all definitions
if __name__ == "__main__":
    print("Running edge cases fixture")
    obj = ComplexClass("test", 10)
    print(f"Computed value: {obj.computed_value}")
