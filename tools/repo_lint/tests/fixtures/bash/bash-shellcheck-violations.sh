#!/usr/bin/env bash
#:Title: Test Bash Script for ShellCheck Violations
#:Brief: This script intentionally contains ShellCheck violations
#:Functions:
#  - test_function: Function with shellcheck violations
#:Inputs: None
#:Outputs: None

# Violation 1: SC2086 - Double quote to prevent globbing and word splitting
test_function() {
    local my_var="hello world"
    echo $my_var
}

# Violation 2: SC2155 - Declare and assign separately
test_declare() {
    local result=$(false)
    echo "$result"
}

# Violation 3: SC2034 - Variable appears unused
unused_var="not used anywhere"

# Violation 4: SC2164 - Use 'cd ... || exit' in case cd fails
change_dir() {
    cd /tmp
    pwd
}
