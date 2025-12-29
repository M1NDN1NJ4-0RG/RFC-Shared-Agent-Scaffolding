#!/usr/bin/env perl

=head1 NAME

safe_check.pl - Minimal self-test for safe-run contract compliance

=head1 SYNOPSIS

  # Run from repository root or any location with scripts/perl/safe-run.pl
  safe_check.pl

=head1 DESCRIPTION

This script provides a minimal self-test to verify that the Perl safe-run
wrapper correctly implements the M0 conformance contract. It validates the
core contract guarantees through integration testing.

The script performs the following verification tests:

=over 4

=item 1. B<Success produces no artifacts>

Executes a command that exits with code 0 and verifies that no failure
log files are created in the FAIL-LOGS directory.

=item 2. B<Failure produces fail log>

Executes a command that exits with non-zero code (37) and verifies that
exactly one failure log file is created.

=item 3. B<Exit codes are preserved>

Verifies that the wrapper preserves both success (0) and failure (37)
exit codes from the child process.

=back

=head1 TEST ENVIRONMENT

The script creates a temporary test environment:

=over 4

=item * Creates C<.agent/FAIL-LOGS> directory in current working directory

=item * Expects C<scripts/perl/safe-run.pl> to exist relative to CWD

=item * Cleans up any existing logs before running tests

=back

=head1 ENVIRONMENT VARIABLES

=over 4

=item B<SAFE_RUN_BIN>

Optional override for safe-run binary location. If not set, the safe-run.pl
wrapper will discover the binary using its standard search order.

=item B<TMPDIR>

Temporary directory location (system default if not set). Used for creating
test environments.

=back

=head1 EXIT CODES

=over 4

=item B<0>

All contract tests passed. The safe-run wrapper is functioning correctly.

=item B<1>

Contract violation detected. Error message printed to stderr explains
which test failed and what went wrong.

=back

=head1 CONTRACT VALIDATION

This test validates the following M0 specification requirements:

=over 4

=item * M0-P1-I1: Success (exit 0) produces no failure artifacts

=item * M0-P1-I2: Failure (exit non-zero) creates exactly one log file

=item * M0-P1-I3: Exit codes are preserved exactly from child process

=back

For complete contract specification, see:

=over 4

=item * docs/conformance-contract.md - Output format and behavior contract

=item * conformance/vectors.json - Complete conformance test vectors

=item * RFC-Shared-Agent-Scaffolding-v0.1.0.md - Full specification

=back

=head1 SIDE EFFECTS

=over 4

=item * Creates C<.agent/> directory in current working directory

=item * Creates C<.agent/FAIL-LOGS/> directory

=item * May leave failure log files from test execution

=item * Removes entire C<.agent/> tree at start for clean test environment

=back

=head1 DIAGNOSTICS

Error messages follow the format:

  safe_check.pl: <error description>

Common error scenarios:

=over 4

=item B<missing scripts/perl/safe-run.pl>

The safe-run.pl wrapper could not be found at the expected relative path.
Run this script from the repository root or ensure the wrapper exists.

=item B<expected exit 0 on success, got N>

The wrapper did not preserve the success exit code. This indicates a bug
in exit code forwarding.

=item B<success should not create fail logs>

The wrapper created failure log artifacts when the command succeeded.
This violates the M0 contract requirement that success produces no artifacts.

=item B<expected exit 37 on failure, got N>

The wrapper did not preserve the failure exit code (37). This indicates
a bug in exit code forwarding.

=item B<failure should create exactly one fail log>

The wrapper either created no log file or created multiple log files
when the command failed. The contract requires exactly one log per failure.

=back

=head1 EXAMPLES

=head2 Basic Usage

  $ cd /path/to/repo
  $ perl scripts/perl/safe_check.pl
  safe_check.pl: OK:
  $ echo $?
  0

=head2 Failure Case

  $ perl scripts/perl/safe_check.pl
  safe_check.pl: expected exit 0 on success, got 1
  $ echo $?
  1

=head1 TESTING STRATEGY

This script uses a "black box" integration testing approach:

=over 4

=item 1. Invoke the actual safe-run.pl wrapper (not a mock)

=item 2. Execute real Perl commands as child processes

=item 3. Verify observable behavior (exit codes, filesystem artifacts)

=item 4. No inspection of log file contents (handled by conformance tests)

=back

For comprehensive conformance testing including log format validation,
use the conformance test harness with vectors.json.

=head1 SEE ALSO

=over 4

=item * L<safe-run.pl> - The wrapper being tested

=item * L<safe-archive.pl> - Archive failure logs

=item * conformance/vectors.json - Complete test vectors

=back

=head1 AUTHOR

RFC-Shared-Agent-Scaffolding Project

=head1 LICENSE

Unlicense - See LICENSE file in repository root

=cut

use strict;
use warnings;

use File::Path qw(make_path remove_tree);
use File::Spec;
use Cwd qw(abs_path);

sub die_bad { print STDERR "safe_check.pl: $_[0]\n"; exit 1; }

my $root = File::Spec->catdir('.agent');
my $logs = File::Spec->catdir($root, 'FAIL-LOGS');

# Start clean
remove_tree($root, { error => \my $err });
make_path($logs);

my $safe_run = File::Spec->catfile('scripts','perl','safe_run.pl');
-e $safe_run or die_bad("missing $safe_run");

# 1) Success path -> no artifacts created
{
  my @before = glob(File::Spec->catfile($logs, '*'));
  my $rc = system($^X, $safe_run, '--', $^X, '-e', 'print "ok\n"; exit 0');
  my $exit = ($rc >> 8);
  $exit == 0 or die_bad("expected exit 0 on success, got $exit");
  my @after = glob(File::Spec->catfile($logs, '*'));
  scalar(@after) == scalar(@before) or die_bad('success should not create fail logs');
}

# 2) Failure path -> creates fail log + preserves exit code
{
  my @before = glob(File::Spec->catfile($logs, '*'));
  my $rc = system($^X, $safe_run, '--', $^X, '-e', 'print "nope\n"; exit 37');
  my $exit = ($rc >> 8);
  $exit == 37 or die_bad("expected exit 37 on failure, got $exit");
  my @after = glob(File::Spec->catfile($logs, '*'));
  scalar(@after) == scalar(@before) + 1 or die_bad('failure should create exactly one fail log');
}

print "safe_check.pl: OK:\n";
exit 0;
