#!/usr/bin/env perl

# Missing POD documentation - violation 1

package TestModule;

# Missing function documentation - violation 2
sub function_without_docs {
    my ($arg) = @_;
    return $arg + 1;
}

# Another undocumented function - violation 3
sub another_function {
    my $x = 5;
    return $x * 2;
}

# No module documentation - violation 4
sub third_function {
    print "no docs\n";
}

1;
