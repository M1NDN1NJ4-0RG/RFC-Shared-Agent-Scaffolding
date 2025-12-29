#!/usr/bin/env perl

=head1 NAME

run_tests.pl - Language-native test runner for Perl wrappers

=head1 SYNOPSIS

  # Run from wrapper directory
  ./run_tests.pl
  perl run_tests.pl

  # Run from repository root
  perl wrappers/perl/run_tests.pl

  # Run with custom binary path
  SAFE_RUN_BIN=/path/to/safe-run ./run_tests.pl

=head1 DESCRIPTION

Language-native test runner that executes all Perl tests for the
safe_run/safe_check/safe_archive wrapper implementations. This runner is
functionally equivalent to run-tests.sh but provides a native Perl
interface.

B<Implementation Strategy:> Thin wrapper around existing run-tests.sh
(Phase 5 decision). Sets up environment (SAFE_RUN_BIN, working directory)
and delegates to the proven Bash runner. Future enhancement: migrate to
fully native implementation (see docs/future-work.md FW-011).

=head1 ENVIRONMENT VARIABLES

=over 4

=item B<SAFE_RUN_BIN>

Path to Rust canonical binary.

Default: {repo_root}/rust/target/release/safe-run

Auto-detected from repository structure (2 levels up from wrapper directory).

Example:

  export SAFE_RUN_BIN=/custom/path/to/safe-run
  ./run_tests.pl

=back

=head1 EXIT CODES

=over 4

=item B<0>

All tests passed

=item B<1>

One or more tests failed

=item B<2>

Prerequisites not met (bash not found)

=back

=head1 EXAMPLES

Run all Perl tests:

  ./run_tests.pl

Run with custom binary path:

  SAFE_RUN_BIN=/path/to/safe-run ./run_tests.pl

Run from repository root:

  perl wrappers/perl/run_tests.pl

=head1 NOTES

=over 4

=item *

Requires Perl 5.10+

=item *

Requires bash to be available (thin wrapper implementation)

=item *

Requires Rust canonical binary to be built

=item *

Sets SAFE_RUN_BIN environment variable for tests

=item *

Functionally equivalent to run-tests.sh (strict parity)

=back

=head1 SEE ALSO

=over 4

=item *

run-tests.sh: Bash test runner (delegated to by this script)

=item *

docs/testing/test-runner-contract.md: Parity contract specification

=item *

docs/future-work.md: FW-011 (future native implementation)

=back

=cut

use strict;
use warnings;
use v5.10;
use File::Basename qw(dirname);
use File::Spec;
use Cwd qw(abs_path);

# Find repository root (2 levels up from wrapper directory)
sub find_repo_root {
    my ($wrapper_dir) = @_;
    # Wrapper directory structure: repo_root/wrappers/perl/
    # So repo root is 2 levels up
    return File::Spec->catdir($wrapper_dir, '..', '..');
}

# Set up test environment variables
sub setup_environment {
    my ($wrapper_dir) = @_;
    
    # Find repository root
    my $repo_root = abs_path(find_repo_root($wrapper_dir));
    
    # Set SAFE_RUN_BIN if not already set
    unless (exists $ENV{SAFE_RUN_BIN}) {
        my $rust_binary = File::Spec->catfile($repo_root, 'rust', 'target', 'release', 'safe-run');
        $ENV{SAFE_RUN_BIN} = $rust_binary;
    }
}

# Check if bash is available
sub check_prerequisites {
    # Try to run bash --version
    my $output = `bash --version 2>/dev/null`;
    return $? == 0;
}

# Execute the test suite via run-tests.sh
sub run_tests {
    my ($wrapper_dir) = @_;
    
    # Check prerequisites
    unless (check_prerequisites()) {
        warn "ERROR: bash not found\n";
        warn "\n";
        warn "This test runner requires bash to be available.\n";
        warn "Install bash, then re-run this script.\n";
        warn "\n";
        warn "Note: Future enhancement will remove bash dependency.\n";
        warn "See docs/future-work.md FW-011 for details.\n";
        return 2;
    }
    
    # Set up environment
    setup_environment($wrapper_dir);
    
    # Path to run-tests.sh
    my $bash_runner = File::Spec->catfile($wrapper_dir, 'run-tests.sh');
    
    unless (-f $bash_runner) {
        warn "ERROR: $bash_runner not found\n";
        return 2;
    }
    
    # Run the Bash test runner
    # Change to wrapper directory and run
    my $orig_dir = abs_path('.');
    chdir($wrapper_dir) or die "Cannot chdir to $wrapper_dir: $!";
    
    my $exit_code = system('bash', $bash_runner);
    
    # Restore original directory
    chdir($orig_dir) or die "Cannot chdir to $orig_dir: $!";
    
    # Extract actual exit code from system() return value
    # system() returns: ($? >> 8) is the actual exit code
    return $exit_code >> 8;
}

# Main entry point
sub main {
    # Get wrapper directory (where this script lives)
    my $script_path = abs_path(__FILE__);
    my $wrapper_dir = dirname($script_path);
    
    # Run tests
    return run_tests($wrapper_dir);
}

# Execute main and exit with its return code
exit main();
