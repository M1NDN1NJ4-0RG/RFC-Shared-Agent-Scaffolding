#!/usr/bin/perl
# Test fixture for perlcritic violations

use strict;
use warnings;

# ProhibitPunctuationVars: avoid punctuation variables
my $x = $_;
print $!;

# RequireUseStrict: missing use strict (handled above)
# RequireUseWarnings: missing use warnings (handled above)

# ProhibitBarewordFileHandles: use lexical filehandles
open(FH, '<', 'file.txt');
print <FH>;
close(FH);

# ProhibitTwoArgOpen: use three-arg open
open(FILE, "< $filename");

# RequireCheckedSyscalls: check return values
print "data";
close FILE;

# ProhibitStringyEval: avoid string eval
my $code = 'print "hello"';
eval $code;

# RequireLocalizedPunctuationVars: localize special vars
$/ = "\n\n";

# ProhibitPackageVars: avoid package variables
our $global_var = 1;

# RequireArgUnpacking: unpack @_ at start
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
sub no_unpack {
    my $result = $_[0] + $_[1];
    return $result;
}

# ProhibitExcessMainComplexity: too much logic in main
for my $i (1..10) {
    if ($i % 2) {
        if ($i > 5) {
            print $i;
        }
    }
}

# RequireFinalReturn: missing explicit return
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
sub no_return {
    my ($x) = @_;
    $x + 1;
}

# ProhibitPostfixControls: avoid unless/if at end
print "test" unless $debug;
do_something() if $condition;

# RequireCarping: use Carp instead of warn/die
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
sub may_fail {
    my ($input) = @_;
    die "error" if !$input;
}

# RequireBriefOpen: filehandle open too long
open my $fh, '<', 'file.txt';
my @lines = <$fh>;
# ... lots of code ...
close $fh;

# ProhibitCascadingIfElse: too many elsif
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
sub cascading {
    my ($x) = @_;
    if ($x == 1) {
        return "one";
    } elsif ($x == 2) {
        return "two";
    } elsif ($x == 3) {
        return "three";
    } elsif ($x == 4) {
        return "four";
    } elsif ($x == 5) {
        return "five";
    }
}

# RequireInterpolationOfMetachars: use single quotes
my $str = "no vars here";

# ProhibitMagicNumbers: avoid magic numbers
if ($count > 42) {
    print "magic";
}

# ProhibitComplexRegexes: regex too complex
if ($input =~ /^(?:foo|bar|baz)(?:\d{3}|\w{4,8})(?:[A-Z]+)?$/) {
    print "match";
}

# RequireVersionVar: missing VERSION
# (should be: our $VERSION = '1.00';)

# RequirePodSections: missing POD sections
# (NAME, SYNOPSIS, etc.)

# ProhibitUnusedVariables: variable assigned but not used
my $unused = 10;

# RequireExtendedFormatting: use /x for complex regex
if ($text =~ /\d{3}-\d{2}-\d{4}/) {
    print "ssn";
}

# ProhibitEmptyQuotes: use q{} instead of ''
my $empty = '';

# ProhibitNoisyQuotes: use q() for non-interpolating
my $simple = "simple";
