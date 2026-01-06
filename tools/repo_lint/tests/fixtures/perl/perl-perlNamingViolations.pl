#!/usr/bin/env perl

=head1 NAME

perlNamingViolations - Test module with naming violations

=head1 DESCRIPTION

This module intentionally violates Perl naming conventions.

=cut

package perlNamingViolations;

use strict;
use warnings;

=head2 BadCamelCase

Invalid camelCase function name - violation 1

=cut

sub BadCamelCase {
    my ($arg) = @_;
    return $arg;
}

=head2 ALLUPPERCASE

All uppercase function name - violation 2

=cut

sub ALLUPPERCASE {
    return 42;
}

=head2 mixedCase_bad

Mixed case with underscore - violation 3

=cut

sub mixedCase_bad {
    my $BadVarName = "violation 4";  # Variable should be lowercase
    return $BadVarName;
}

1;
