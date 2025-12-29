#!/usr/bin/env perl
use strict;
use warnings;
use feature 'say';

=head1 NAME

edge_cases.pl - Test fixture with Perl edge cases for symbol discovery

=head1 SYNOPSIS

    perl edge_cases.pl [options]

=head1 DESCRIPTION

This script contains various edge cases to test the Perl PPI parser's
ability to correctly identify and validate subroutine documentation.

Tests include:

=over 4

=item * Subroutines with prototypes

=item * Multiline subroutine signatures

=item * Nested subroutines

=item * Special characters in subroutine names

=item * Various POD documentation formats

=back

=head1 ARGUMENTS

None (accepts optional command line arguments for testing)

=head1 ENVIRONMENT VARIABLES

=over 4

=item TEST_MODE

When set, fixture runs in test mode

=back

=head1 EXIT CODES

=over 4

=item 0

Success - all tests pass

=item 1

Failure - validation errors found

=back

=head1 EXAMPLES

Run the fixture:

    perl edge_cases.pl

Source for testing:

    require 'edge_cases.pl';

=cut

=head2 simple_subroutine

Simple subroutine with basic documentation.

=over 4

=item Arguments

=over 4

=item $value - Input value to process

=back

=item Returns

Processed value as string

=back

=cut

sub simple_subroutine {
    my ($value) = @_;
    return "Processing: $value";
}

=head2 subroutine_with_prototype

Subroutine with prototype declaration.

=over 4

=item Prototype

$$@ - Expects two scalars and remaining array

=item Arguments

=over 4

=item $first - First scalar argument

=item $second - Second scalar argument

=item @rest - Remaining arguments

=back

=item Returns

Combined result

=back

=cut

sub subroutine_with_prototype ($$@) {
    my ($first, $second, @rest) = @_;
    return "$first-$second-" . join(',', @rest);
}

=head2 multiline_signature

Subroutine with parameters spanning multiple lines.

=over 4

=item Arguments

=over 4

=item $param1 - First parameter with long name

=item $param2 - Second parameter

=item $param3 - Third optional parameter

=back

=item Returns

Hash reference with results

=back

=cut

sub multiline_signature {
    my (
        $param1,
        $param2,
        $param3
    ) = @_;
    
    return {
        first  => $param1,
        second => $param2,
        third  => $param3
    };
}

=head2 outer_subroutine

Outer subroutine containing nested subroutine.

Tests that the validator correctly identifies nested subroutine definitions.

=over 4

=item Arguments

=over 4

=item $outer_value - Value for outer subroutine

=back

=item Returns

Result from nested subroutine

=back

=cut

sub outer_subroutine {
    my ($outer_value) = @_;
    
    # Nested subroutine (lexical closure)
    my $inner_subroutine = sub {
        my ($inner_value) = @_;
        return "$outer_value-$inner_value";
    };
    
    return $inner_subroutine->("nested");
}

=head2 subroutine_with_special_chars_123

Subroutine with numbers and underscores in name.

Tests handling of special characters in subroutine names.

=over 4

=item Arguments

None

=item Returns

String message

=back

=cut

sub subroutine_with_special_chars_123 {
    return "Special chars in name";
}

=head2 _private_helper

Private/helper subroutine (leading underscore).

Per Phase 5.5 policy, private subroutines must still be documented
unless explicitly exempted via pragma.

=over 4

=item Arguments

=over 4

=item $value - Value to process

=back

=item Returns

Processed value

=back

=cut

sub _private_helper {
    my ($value) = @_;
    return "${value}_processed";
}

=head2 __internal_subroutine

Internal subroutine (double underscore).

Per Phase 5.5 policy, internal subroutines must be documented.

=over 4

=item Arguments

=over 4

=item $input - Input to process

=back

=item Returns

Modified input

=back

=cut

sub __internal_subroutine {
    my ($input) = @_;
    return "__internal: $input";
}

=head2 complex_parameters

Subroutine with complex parameter handling.

Demonstrates hash parameters, references, and default values.

=over 4

=item Arguments

=over 4

=item $scalar - Scalar value

=item $array_ref - Array reference

=item $hash_ref - Hash reference (optional)

=back

=item Returns

Processed result as hash reference

=back

=cut

sub complex_parameters {
    my ($scalar, $array_ref, $hash_ref) = @_;
    $hash_ref //= {};  # Default to empty hash if not provided
    
    return {
        scalar => $scalar,
        array  => $array_ref,
        hash   => $hash_ref
    };
}

=head2 method_style_sub

Method-style subroutine (expects object as first arg).

=over 4

=item Arguments

=over 4

=item $self - Object reference (blessed hash)

=item $param - Parameter to method

=back

=item Returns

Modified object

=back

=cut

sub method_style_sub {
    my ($self, $param) = @_;
    $self->{value} = $param;
    return $self;
}

=head2 subroutine_with_attributes

Subroutine with attributes (metadata).

=over 4

=item Attributes

=over 4

=item :lvalue - Can be used as lvalue

=back

=item Arguments

None (package-level access)

=item Returns

Lvalue reference

=back

=cut

our $package_var;
sub subroutine_with_attributes : lvalue {
    $package_var;
}

=head2 exported_subroutine

Subroutine intended for export.

=over 4

=item Arguments

=over 4

=item $value - Value to export-process

=back

=item Returns

Processed value ready for export

=back

=cut

sub exported_subroutine {
    my ($value) = @_;
    return uc($value);
}

# Package-level object-oriented pattern
{
    package MyClass;
    
    =head2 MyClass::new
    
    Constructor for MyClass.
    
    =over 4
    
    =item Arguments
    
    =over 4
    
    =item $class - Class name (passed automatically)
    
    =item %args - Constructor arguments as hash
    
    =back
    
    =item Returns
    
    Blessed object reference
    
    =back
    
    =cut
    
    sub new {
        my ($class, %args) = @_;
        my $self = {
            name  => $args{name}  || 'default',
            value => $args{value} || 0
        };
        return bless $self, $class;
    }
    
    =head2 MyClass::get_name
    
    Getter method for name attribute.
    
    =over 4
    
    =item Arguments
    
    =over 4
    
    =item $self - Object reference
    
    =back
    
    =item Returns
    
    Name as string
    
    =back
    
    =cut
    
    sub get_name {
        my ($self) = @_;
        return $self->{name};
    }
}

# Note: Perl doesn't have the same noqa pragma syntax
# This subroutine intentionally lacks POD for testing
sub undocumented_subroutine {
    my ($value) = @_;
    return "No POD: $value";
}

# Main execution
if (!caller) {
    say "Running Perl edge cases fixture";
    say simple_subroutine("test");
    say outer_subroutine("outer_val");
    
    my $obj = MyClass->new(name => 'TestObject', value => 42);
    say "Object name: " . $obj->get_name();
}

1;  # Return true for module loading

__END__

=head1 AUTHOR

RFC-Shared-Agent-Scaffolding Test Suite

=head1 LICENSE

Unlicense

=cut
