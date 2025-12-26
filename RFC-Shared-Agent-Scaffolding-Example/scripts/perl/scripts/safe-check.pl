#!/usr/bin/env perl
use strict;
use warnings;

use File::Path qw(make_path remove_tree);
use File::Spec;
use Cwd qw(abs_path);

# -----------------------------------------------------------------------------
# safe-check.pl
#
# Minimal self-test for the Perl safe-run contract.
# - Verifies:
#   * success produces no artifacts
#   * failure produces a fail log file
#   * exit codes are preserved
# -----------------------------------------------------------------------------

sub die_bad { print STDERR "safe-check.pl: $_[0]\n"; exit 1; }

my $root = File::Spec->catdir('.agent');
my $logs = File::Spec->catdir($root, 'FAIL-LOGS');

# Start clean
remove_tree($root, { error => \my $err });
make_path($logs);

my $safe_run = File::Spec->catfile('scripts','perl','safe-run.pl');
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

print "safe-check.pl: OK:\n";
exit 0;
