#!/usr/bin/env perl
# Intentional naming convention violations for Perl.
#
# This file intentionally violates Perl naming conventions.
# It uses kebab-case instead of snake_case to test naming enforcement.

use strict;
use warnings;

# This file name itself (naming-violations.pl) violates snake_case
# Expected: naming_violations.pl
# Actual: naming-violations.pl (kebab-case - WRONG for Perl)

sub ThisSubShouldBeSnakeCase {
    # Subroutine names should be snake_case, not PascalCase
    return 1;
}

my $VariableInPascalCase = "wrong";  # Variables should be snake_case

sub normal_function {
    # This is correct snake_case naming
    return 1;
}

1;
