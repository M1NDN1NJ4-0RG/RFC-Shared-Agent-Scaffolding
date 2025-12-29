#!/usr/bin/env perl
use strict;
use warnings;
use JSON::PP;
use PPI;
use File::Basename;

=head1 NAME

parse_perl_ppi.pl - Parse Perl scripts using PPI and extract symbol information

=head1 SYNOPSIS

    perl scripts/docstring_validators/helpers/parse_perl_ppi.pl <file.pl>

=head1 DESCRIPTION

This script uses PPI (Perl Parsing Interface) to parse Perl scripts and extract
symbol information (subroutines, their locations, and associated POD documentation)
WITHOUT executing the script.

Outputs JSON with subroutine definitions and their documentation status for docstring validation.

Per Phase 0 Item 0.9.5: Perl symbol discovery MUST use PPI plus a structure-aware
fallback strategy (E2) for edge cases (no regex-only parsing).

=head1 ARGUMENTS

File path to Perl script to parse (positional argument)

=head1 OUTPUT

JSON object with structure:

    {
      "subs": [
        {
          "name": "sub_name",
          "line": 42,
          "has_pod": true,
          "pod_sections": ["NAME", "SYNOPSIS"]
        }
      ],
      "errors": []
    }

=head1 ENVIRONMENT VARIABLES

None

=head1 EXIT CODES

=over 4

=item 0

Success (valid JSON output)

=item 1

Parse error or file not found

=back

=head1 EXAMPLES

Parse a Perl script:

    perl parse_perl_ppi.pl myscript.pl

=head1 DEPENDENCIES

Requires PPI and JSON::PP Perl modules

=cut

# Check command line argument
if (@ARGV != 1) {
    my $error_obj = {
        subs => [],
        errors => ["Usage: $0 <file.pl>"]
    };
    print encode_json($error_obj), "\n";
    exit 1;
}

my $file_path = $ARGV[0];

# Check file exists
unless (-f $file_path) {
    my $error_obj = {
        subs => [],
        errors => ["File not found: $file_path"]
    };
    print encode_json($error_obj), "\n";
    exit 1;
}

# Parse the file using PPI
my $document = PPI::Document->new($file_path);

unless ($document) {
    my $error_obj = {
        subs => [],
        errors => ["Failed to parse file: $file_path"]
    };
    print encode_json($error_obj), "\n";
    exit 1;
}

# Extract subroutine definitions
my @subs = ();
my @errors = ();

# Find all subroutine statements
my $sub_nodes = $document->find('PPI::Statement::Sub');

if ($sub_nodes) {
    foreach my $sub (@$sub_nodes) {
        # Get subroutine name
        my $name = $sub->name;
        next unless $name;  # Skip anonymous subs

        # Get line number
        my $line = $sub->line_number;

        # Check for POD documentation near this sub
        my ($has_pod, $pod_sections) = check_pod_for_sub($document, $sub, $name);

        push @subs, {
            name => $name,
            line => $line,
            has_pod => $has_pod ? JSON::PP::true : JSON::PP::false,
            pod_sections => $pod_sections
        };
    }
}

# Output result as JSON
my $result = {
    subs => \@subs,
    errors => \@errors
};

print encode_json($result), "\n";
exit 0;

# Helper: Check for POD documentation associated with a subroutine
sub check_pod_for_sub {
    my ($document, $sub_node, $sub_name) = @_;

    my $has_pod = 0;
    my @sections = ();

    # Strategy: Look for POD blocks in the document
    # Check both:
    # 1. POD blocks immediately preceding the sub
    # 2. POD blocks anywhere that mention the sub name

    # Find all POD nodes
    my $pod_nodes = $document->find('PPI::Token::Pod');
    return (0, []) unless $pod_nodes;

    my $sub_line = $sub_node->line_number;

    foreach my $pod (@$pod_nodes) {
        my $pod_content = $pod->content;
        my $pod_line = $pod->line_number;

        # Check if this POD is "near" the sub (within 10 lines before)
        my $is_near = ($pod_line < $sub_line && $sub_line - $pod_line <= 10);

        # Check if POD mentions the sub name
        my $mentions_sub = ($pod_content =~ /\b\Q$sub_name\E\b/);

        if ($is_near || $mentions_sub) {
            $has_pod = 1;

            # Extract POD sections present (=head1, =head2, =item, etc.)
            if ($pod_content =~ /^=head1\s+NAME/m) { push @sections, "=head1 NAME" unless grep { $_ eq "=head1 NAME" } @sections; }
            if ($pod_content =~ /^=head1\s+SYNOPSIS/m) { push @sections, "=head1 SYNOPSIS" unless grep { $_ eq "=head1 SYNOPSIS" } @sections; }
            if ($pod_content =~ /^=head1\s+DESCRIPTION/m) { push @sections, "=head1 DESCRIPTION" unless grep { $_ eq "=head1 DESCRIPTION" } @sections; }
            if ($pod_content =~ /^=head2/m) { push @sections, "=head2" unless grep { $_ eq "=head2" } @sections; }
            if ($pod_content =~ /^=item/m) { push @sections, "=item" unless grep { $_ eq "=item" } @sections; }
        }
    }

    return ($has_pod, \@sections);
}
