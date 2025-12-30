#!/usr/bin/env perl
use strict;
use warnings;

# Test fixture: intentionally bad Perl code

# Subroutine without POD documentation (violates repo contract)
sub function_without_docstring {
    my ($param1, $param2) = @_;
    return $param1 + $param2;
}

# Perl::Critic: ProhibitExplicitReturnUndef (not auto-fixable)
sub bad_return {
    my $value = shift;
    return undef if !defined $value;  ## no critic (ProhibitExplicitReturnUndef) - Remove this to trigger violation
    return $value;
}

# Another function missing docs
sub another_function {
    print "test\n";
}

# Perl::Critic: RequireUseWarnings is satisfied above,
# but we can add other non-auto-fixable issues

1;
