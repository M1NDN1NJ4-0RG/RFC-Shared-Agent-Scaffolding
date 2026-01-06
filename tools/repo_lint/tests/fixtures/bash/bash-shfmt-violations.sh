#!/usr/bin/env bash
#:Title: Test Bash Script for shfmt Violations
#:Brief: This script intentionally contains shfmt formatting violations
#:Functions:
#  - bad_formatting: Function with formatting issues
#:Inputs: None
#:Outputs: None

# Violation 1: Inconsistent indentation (tabs vs spaces)
bad_formatting() {
	echo "tab indented"
    echo "space indented"
}

# Violation 2: Missing space in if statement
test_if() {
    if[ "$1" = "test" ]; then
        echo "bad spacing"
    fi
}

# Violation 3: Bad case statement formatting
test_case(){
case "$1" in
test) echo "no indent" ;;
other) echo "also no indent" ;;
esac
}
