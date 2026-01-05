"""Test fixture for unsafe docstring rewriting.

This file contains Google-style docstrings that violate the repo's
Sphinx-style convention. It's used to test the unsafe_docstring_rewrite
fixer.

NOTE: This file is INTENTIONALLY non-conformant. Do not fix manually.
"""

from __future__ import annotations


def calculate_sum(numbers, initial_value):
    """Calculate the sum of a list of numbers.

    This function adds all numbers in the list starting from an initial value.

    Args:
        numbers: List of numbers to sum
        initial_value (int): Starting value for the sum

    Returns:
        The total sum of all numbers plus the initial value
    """
    total = initial_value
    for num in numbers:
        total += num
    return total


class DataProcessor:
    """Processes data in various formats.

    This class handles multiple data formats and provides
    transformation utilities.
    """

    def transform(self, data, format_type):
        """Transform data to a specific format.

        Args:
            data: Input data to transform
            format_type (str): Target format (json, xml, csv)

        Returns:
            Transformed data in the requested format
        """
        if format_type == "json":
            return f"JSON: {data}"
        elif format_type == "xml":
            return f"XML: {data}"
        else:
            return f"CSV: {data}"

    def validate(self, data, schema):
        """Validate data against a schema.

        Args:
            data: Data to validate
            schema (dict): Validation schema

        Returns:
            True if valid, False otherwise
        """
        # Simple validation logic
        return isinstance(data, dict) and "required_field" in data
