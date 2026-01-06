#!/usr/bin/env perl

=head1 NAME

perl_perlcritic_violations - Test module with Perl::Critic violations

=head1 DESCRIPTION

This module intentionally contains Perl::Critic policy violations.

=cut

package PerlCriticTest;

use strict;
use warnings;

=head2 test_function

Test function with perlcritic violations

=cut

# Violation 1: ProhibitExcessComplexity - too many branches
sub test_function {
    my ($x) = @_;
    if ($x == 1) { return 1; }
    elsif ($x == 2) { return 2; }
    elsif ($x == 3) { return 3; }
    elsif ($x == 4) { return 4; }
    elsif ($x == 5) { return 5; }
    elsif ($x == 6) { return 6; }
    elsif ($x == 7) { return 7; }
    elsif ($x == 8) { return 8; }
    elsif ($x == 9) { return 9; }
    elsif ($x == 10) { return 10; }
    else { return 0; }
}

=head2 bad_args

Function using @_ directly - violation 2

=cut

sub bad_args {
    print $_[0];
}

=head2 bad_vars

Function using punctuation variables - violation 3

=cut

sub bad_vars {
    my $data = $_;
    return $data;
}

1;
