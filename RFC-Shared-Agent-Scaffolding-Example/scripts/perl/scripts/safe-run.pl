#!/usr/bin/env perl
use strict;
use warnings;

use File::Path qw(make_path);
use File::Spec;
use File::Temp qw(tempfile);
use IO::Select;
use IPC::Open3;
use Symbol qw(gensym);

# -----------------------------------------------------------------------------
# safe-run.pl
#
# Contract:
# - Executes the provided command verbatim.
# - On SUCCESS: produces no artifacts.
# - On FAILURE: captures combined stdout+stderr to SAFE_LOG_DIR (default .agent/FAIL-LOGS)
#   and preserves the exit code.
# - On ABORT (SIGINT/SIGTERM): saves partial output to ...-ABORTED-fail.txt.
# -----------------------------------------------------------------------------

sub usage {
  print STDERR "Usage: safe-run.pl -- <command> [args...]\n";
  exit 2;
}

# Parse: everything after optional "--" is the command.
my @argv = @ARGV;
@argv = () unless defined $argv[0];
if (!@argv) { usage(); }
if ($argv[0] eq '--') { shift @argv; }
if (!@argv) { usage(); }

my $safe_log_dir = $ENV{SAFE_LOG_DIR} // File::Spec->catdir('.agent', 'FAIL-LOGS');
my $snippet_lines = $ENV{SAFE_SNIPPET_LINES} // 0;

# Temp file buffering (prevents OOM for huge output)
my ($tmp_fh, $tmp_path) = tempfile('safe-run-XXXXXX', TMPDIR => 1, UNLINK => 0);
binmode($tmp_fh);

my $aborted = 0;
my $got_signal;
my $child_pid;

sub _forward_signal {
  my ($sig) = @_;
  $aborted = 1;
  $got_signal = $sig;
  if (defined $child_pid) {
    # Forward to child process group if possible, else to child.
    kill $sig, $child_pid;
  }
}

$SIG{INT}  = sub { _forward_signal('INT'); };
$SIG{TERM} = sub { _forward_signal('TERM'); };

# Spawn child and stream stdout/stderr live while teeing to temp file.
my $err = gensym;
my $out;

eval {
  $child_pid = open3(undef, $out, $err, @argv);
  1;
} or do {
  my $e = $@ || 'unknown error';
  print STDERR "safe-run.pl: failed to start command: $e\n";
  # Treat as failure; write whatever we have (likely nothing).
  make_path($safe_log_dir) unless -d $safe_log_dir;
  my $fail_path = File::Spec->catfile($safe_log_dir, 'safe-run-start-fail.txt');
  open my $fh, '>', $fail_path or die "cannot write $fail_path: $!";
  print $fh "FAILED TO START: $e\n";
  close $fh;
  exit 127;
};

binmode($out);
binmode($err);

my $sel = IO::Select->new();
$sel->add($out);
$sel->add($err);

# Keep a small tail buffer for optional SAFE_SNIPPET_LINES.
my @tail;

sub _push_tail {
  my ($line) = @_;
  return if !$snippet_lines || $snippet_lines <= 0;
  push @tail, $line;
  shift @tail while @tail > $snippet_lines;
}

# Read loop
while ($sel->count) {
  my @ready = $sel->can_read(0.25);
  for my $fh (@ready) {
    my $buf;
    my $bytes = sysread($fh, $buf, 8192);

    if (!defined $bytes) {
      # transient read error; ignore
      next;
    }

    if ($bytes == 0) {
      $sel->remove($fh);
      next;
    }

    # Tee to temp file
    print {$tmp_fh} $buf;

    # Echo to console: preserve destination (stdout/stderr)
    if ($fh == $out) {
      print STDOUT $buf;
    } else {
      print STDERR $buf;
    }

    # Tail buffering line-ish: best effort split
    if ($snippet_lines && $snippet_lines > 0) {
      my @parts = split(/\n/, $buf, -1);
      for my $p (@parts) {
        _push_tail($p . "\n") if length($p);
      }
    }
  }

  last if $aborted && !$sel->count; # let the loop drain
}

close $tmp_fh;

# Wait for child
my $wait_pid = waitpid($child_pid, 0);
my $status = $?;

# Determine exit code
my $exit_code;
if ($status == -1) {
  $exit_code = 127;
} elsif ($status & 127) {
  # Died from signal
  my $sig = ($status & 127);
  $exit_code = 128 + $sig;
} else {
  $exit_code = ($status >> 8);
}

# If we were interrupted, treat as aborted regardless of child status.
if ($aborted) {
  make_path($safe_log_dir) unless -d $safe_log_dir;
  my $stamp = time();
  my $fail_path = File::Spec->catfile($safe_log_dir, "safe-run-$stamp-ABORTED-fail.txt");
  rename($tmp_path, $fail_path) or do {
    # fallback copy
    open my $in,  '<', $tmp_path  or die "cannot read $tmp_path: $!";
    open my $outf,'>', $fail_path or die "cannot write $fail_path: $!";
    binmode($in); binmode($outf);
    my $b;
    while (read($in, $b, 8192)) { print {$outf} $b; }
    close $in; close $outf;
    unlink $tmp_path;
  };
  print STDERR "\n[safe-run] ABORTED ($got_signal). Partial log saved to: $fail_path\n";
  exit($exit_code || 130);
}

# Success: remove temp file, no artifacts.
if ($exit_code == 0) {
  unlink $tmp_path;
  exit 0;
}

# Failure: move temp file to FAIL-LOGS
make_path($safe_log_dir) unless -d $safe_log_dir;
my $stamp = time();
my $fail_path = File::Spec->catfile($safe_log_dir, "safe-run-$stamp-fail.txt");
rename($tmp_path, $fail_path) or do {
  # fallback copy
  open my $in,  '<', $tmp_path  or die "cannot read $tmp_path: $!";
  open my $outf,'>', $fail_path or die "cannot write $fail_path: $!";
  binmode($in); binmode($outf);
  my $b;
  while (read($in, $b, 8192)) { print {$outf} $b; }
  close $in; close $outf;
  unlink $tmp_path;
};

print STDERR "\n[safe-run] Command failed (exit $exit_code). Log saved to: $fail_path\n";

if ($snippet_lines && $snippet_lines > 0 && @tail) {
  print STDERR "\n[safe-run] Tail snippet (last $snippet_lines lines):\n";
  print STDERR @tail;
}

exit $exit_code;
