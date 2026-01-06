#!/usr/bin/env bash
#:Title: Test Bash Script for Naming Violations
#:Brief: This script intentionally violates naming conventions
#:Functions:
#  - MyFunction: Invalid camelCase function name (violation 1)
#:Inputs: None
#:Outputs: None

# shellcheck disable=SC2148

# Invalid function name - camelCase instead of snake_case - violation 1
MyFunction() {
    echo "camelCase function name"
}

# Invalid function name - PascalCase - violation 2
PascalCaseFunc() {
    local InvalidVarName="bad"  # violation 3 - variable should be snake_case
    echo "$InvalidVarName"
}

# Another invalid function name - kebab-case is invalid in bash - violation 4
my-kebab-function() {
    echo "kebab case"
}
