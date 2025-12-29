#!/usr/bin/env bash
#
# edge-cases.sh - Test fixture with Bash edge cases for symbol discovery
#
# DESCRIPTION:
#   This script contains various edge cases to test the Bash tree-sitter parser's
#   ability to correctly identify and validate function documentation.
#
#   Tests include:
#   - Multiline function definitions
#   - Functions with special characters
#   - Nested functions
#   - Various function declaration styles
#   - Complex comment blocks
#
# USAGE:
#   ./edge_cases.sh [options]
#
# INPUTS:
#   None (accepts optional command line arguments for testing)
#
# OUTPUTS:
#   Exit Codes:
#     0    Success - all tests pass
#     1    Failure - validation errors found
#
# EXAMPLES:
#   # Run the fixture
#   ./edge_cases.sh
#
#   # Source for testing
#   source edge_cases.sh

# Function with standard syntax
#
# Description: Simple function with standard declaration
# Arguments:
#   $1 - Input value
# Returns:
#   0 - Success
simple_function() {
    local input="$1"
    echo "Processing: $input"
    return 0
}

# Function using 'function' keyword
#
# Description: Function declared with 'function' keyword
# Arguments:
#   $1 - Value to process
# Returns:
#   0 - Success
function keyword_function {
    echo "Keyword function: $1"
}

# Function with 'function' keyword and parentheses
#
# Description: Function using both 'function' keyword and ()
# Arguments:
#   $1 - First argument
#   $2 - Second argument
# Returns:
#   0 - Success
function both_styles_function() {
    echo "First: $1, Second: $2"
}

# Multiline function definition
#
# Description: Function with opening brace on next line
# Arguments:
#   $1 - Input parameter
# Returns:
#   0 - Success
multiline_function()
{
    # Function body with opening brace on new line
    local value="$1"
    echo "Multiline style: $value"
}

# Function with special characters in name
#
# Description: Function name with underscores and numbers
# Arguments:
#   None
# Returns:
#   0 - Success
function_with_underscores_123() {
    echo "Special chars in name"
}

# Outer function containing nested function
#
# Description: Tests nested function definition handling
# Arguments:
#   $1 - Outer parameter
# Returns:
#   Result from nested function
outer_function() {
    local outer_value="$1"
    
    # Inner nested function
    #
    # Description: Nested function inside another function
    # Arguments:
    #   $1 - Inner parameter
    # Returns:
    #   Combined value
    inner_function() {
        local inner_value="$1"
        echo "${outer_value}-${inner_value}"
    }
    
    inner_function "nested"
}

# Function with complex multi-paragraph comment
#
# Description:
#   This function has a very detailed comment block
#   spanning multiple lines and paragraphs.
#
#   It demonstrates that the parser can handle
#   extensive documentation.
#
# Arguments:
#   $1 - First parameter with detailed description
#        that spans multiple lines
#   $2 - Second parameter
#
# Returns:
#   0 - Success with normal operation
#   1 - Failure if parameters invalid
#
# Examples:
#   complex_comment_function "arg1" "arg2"
#
# Notes:
#   This is a note about usage
complex_comment_function() {
    [[ -z "$1" ]] && return 1
    echo "$1 and $2"
    return 0
}

# Private/helper function (leading underscore)
#
# Description: Helper function with underscore prefix
# Arguments:
#   $1 - Value to process
# Returns:
#   Processed value
_private_helper() {
    local value="$1"
    echo "${value}_processed"
}

# Double underscore function
#
# Description: Function with double underscore prefix
# Arguments:
#   $1 - Input
# Returns:
#   Modified input
__internal_function() {
    echo "__internal: $1"
}

# Function with inline brace (K&R style)
#
# Description: Function with opening brace on same line as declaration
# Arguments:
#   $1 - Parameter
# Returns:
#   0 - Success
kr_style_function() { echo "K&R style: $1"; }

# Function that calls nested functions
#
# Description: Demonstrates calling pattern for nested functions
# Arguments:
#   None
# Returns:
#   0 - Success
function_with_nested_calls() {
    # Local helper within this function
    #
    # Description: Local helper function
    # Arguments:
    #   $1 - Value
    # Returns:
    #   Transformed value
    local_helper() {
        echo "local: $1"
    }
    
    local_helper "test"
}

# Function with array parameters
#
# Description: Function demonstrating array handling
# Arguments:
#   $@ - All arguments treated as array
# Returns:
#   0 - Success
array_function() {
    local -a items=("$@")
    echo "Array has ${#items[@]} items"
}

# noqa: FUNCTION
function exempted_function() {
    # This function is exempted from documentation requirements
    echo "No doc required"
}

# Function with conditional execution
#
# Description: Function with complex conditional logic
# Arguments:
#   $1 - Condition flag
# Returns:
#   0 - Success
#   1 - Failure
conditional_function() {
    if [[ "$1" == "true" ]]; then
        echo "Condition met"
        return 0
    else
        echo "Condition not met"
        return 1
    fi
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Running Bash edge cases fixture"
    simple_function "test"
    keyword_function "value"
    outer_function "outer_val"
fi
