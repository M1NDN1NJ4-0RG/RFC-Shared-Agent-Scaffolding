#!/bin/bash
# Missing module docstring

# Function without docstring
no_doc() {
    echo "no documentation"
}

# Function with incomplete docstring
partial_doc() {
    # Just a comment, not a proper docstring
    echo "incomplete"
}

# Function missing parameter documentation
missing_params() {
    # Summary: Does something
    local x=$1
    local y=$2
    echo $((x + y))
}

# Function missing return documentation
missing_return() {
    # Summary: Computes value
    echo 42
}

# Function missing examples
no_examples() {
    # Summary: Complex function
    # Params: $1 - input value
    # Returns: transformed value
    echo "$1"
}

# Nested function without docstring
outer_func() {
    # Outer docstring
    inner_func() {
        echo "nested"
    }
    inner_func
}

# Function with wrong docstring format
wrong_format() {
    : 'This is wrong format
    Should use # comments'
    echo "bad format"
}

# Missing usage information for complex function
complex_func() {
    # Does complex things
    local input="$1"
    local output=""
    for char in $(echo "$input" | fold -w1); do
        output="${output}${char}${char}"
    done
    echo "$output"
}

# Missing environment variable documentation
uses_env() {
    # Uses environment variables
    echo "$UNDOCUMENTED_VAR"
    echo "$ANOTHER_VAR"
}

# Missing error handling documentation
can_fail() {
    # Might fail
    risky_command
    another_risky_command
}

# Function with side effects not documented
has_side_effects() {
    # Does something
    echo "output" > /tmp/file
    export GLOBAL_VAR="value"
}

# Missing notes about complexity
complex_algorithm() {
    # Processes data
    local data="$1"
    # Complex algorithm without explanation
    result=$(echo "$data" | tr 'a-z' 'A-Z' | rev | cut -c1-10)
    echo "$result"
}
