#!/usr/bin/env perl
# Perl test fixtures for repo_lint docstring validation
#
# Purpose: Test missing docstrings, correct docstrings, pragma exemptions,
# and edge cases for Perl symbol discovery via PPI.

use strict;
use warnings;

# This subroutine has documentation (should pass)
# Purpose: Demonstrates properly documented subroutine
sub function_with_doc {
    return "ok";
}

# Missing docstring - should be detected
sub function_without_doc {
    return "missing";
}

# Purpose: Properly documented subroutine with parameters
# Args:
#   $arg1 - First argument
#   $arg2 - Second argument
sub multiline_function {
    my ($arg1, $arg2) = @_;
    return "$arg1 $arg2";
}

# noqa: FUNCTION
sub exempted_function {
    return "pragma exemption";
}

package TestPackage;

# Purpose: Package-scoped subroutine
sub package_function {
    return "package scope";
}

1;
