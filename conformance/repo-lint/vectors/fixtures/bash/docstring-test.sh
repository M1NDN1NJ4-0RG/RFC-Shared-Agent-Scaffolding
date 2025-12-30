#!/usr/bin/env bash
# Bash test fixtures for repo_lint docstring validation
#
# Purpose: Test missing docstrings, correct docstrings, pragma exemptions,
# and edge cases for Bash symbol discovery via tree-sitter.

# This function has a docstring (should pass)
# Purpose: Demonstrates properly documented function
function_with_doc() {
	echo "ok"
}

function_without_doc() {
	# Missing docstring - should be detected
	echo "missing"
}

# Purpose: Properly documented function
# Args:
#   $1 - First argument
#   $2 - Second argument
multiline_function() {
	local arg1="$1"
	local arg2="$2"
	echo "$arg1 $arg2"
}

# noqa: FUNCTION
exempted_function() {
	echo "pragma exemption"
}

# Nested function test
# Purpose: Outer function
outer_function() {
	# Purpose: Inner function (nested)
	inner_function() {
		echo "nested"
	}
	inner_function
}
