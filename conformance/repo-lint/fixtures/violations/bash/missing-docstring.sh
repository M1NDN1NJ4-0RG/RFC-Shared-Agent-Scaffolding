#!/usr/bin/env bash
#
# Test fixture: intentionally bad Bash code

# Function without docstring (violates repo contract)
function_without_docstring() {
  echo "hello"
}

# ShellCheck SC2034: unused variable (not auto-fixable)
UNUSED_VAR="value"

# ShellCheck SC2086: unquoted variable (not auto-fixable without changing semantics)
function bad_quoting() {
  local file=$1
  cat $file
}

# Missing docstring for this function too
another_function() {
  echo "test"
}
