#!/bin/bash
# Intentional naming convention violations for Bash.
#
# This file intentionally violates Bash naming conventions.
# It uses snake_case instead of kebab-case to test naming enforcement.

# This file name itself (naming_violations.sh) violates kebab-case
# Expected: naming-violations.sh
# Actual: naming_violations.sh (snake_case - WRONG for Bash)

function ThisFunctionShouldBeKebabCase() {
    # Function names should be kebab-case, not PascalCase
    echo "Wrong naming"
}

VARIABLE_IN_CAPS="wrong"  # Variables should be lowercase with underscores or kebab-case

function normal-function() {
    # This is correct kebab-case naming for bash
    echo "Correct naming"
}
