#!/usr/bin/perl
# Missing module POD documentation

use strict;
use warnings;

# Subroutine without POD
sub no_pod {
    my ($x) = @_;
    return $x * 2;
}

# Subroutine with incomplete POD
sub partial_pod {
=head1 NAME

Just a name

=cut
    my ($x, $y) = @_;
    return $x + $y;
}

# Missing parameter documentation
sub missing_params {
=head1 SYNOPSIS

Does something

=cut
    my ($input, $output, $mode) = @_;
    return process($input, $output, $mode);
}

# Missing return documentation
sub missing_return {
=head1 DESCRIPTION

Computes a value based on input

=head1 PARAMETERS

=over 4

=item * $value - Input value

=back

=cut
    my ($value) = @_;
    return $value * 3;
}

# Missing examples
sub no_examples {
=head1 NAME

complex_function - Does complex things

=head1 DESCRIPTION

Performs complex operations on input

=cut
    my ($data) = @_;
    return transform($data);
}

# Wrong POD format
sub wrong_format {
    # This is a comment, not POD
    # Parameters: $x, $y
    # Returns: sum
    my ($x, $y) = @_;
    return $x + $y;
}

# Missing SYNOPSIS section
sub missing_synopsis {
=head1 NAME

function_name

=head1 DESCRIPTION

Does things

=cut
    return 42;
}

# Package without POD
package NoDocPackage;

sub method {
    my ($self) = @_;
    return $self->{value};
}

1;

# Method without POD in package
package PartialPackage;

=head1 NAME

PartialPackage - Partially documented

=cut

sub new {
    my ($class) = @_;
    return bless {}, $class;
}

# Missing POD for this method
sub process {
    my ($self, $data) = @_;
    return $data;
}

1;

# Missing AUTHOR section
sub missing_author {
=head1 NAME

tool - Command line tool

=head1 SYNOPSIS

  tool [options]

=head1 DESCRIPTION

This tool does things

=cut
    return 1;
}

# Missing LICENSE section
# Missing SEE ALSO section
# Missing version info in POD
