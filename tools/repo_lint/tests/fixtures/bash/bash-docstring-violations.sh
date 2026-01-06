#!/usr/bin/env bash

# Missing function docstring - violation 1
function_without_docstring() {
    echo "no docstring"
}

# Missing script header docstring - violation 2

# Incomplete docstring - violation 3
another_function() {
    echo "incomplete"
}

# Function with no docstring at all - violation 4
third_function() {
    local x=1
    echo "$x"
}
