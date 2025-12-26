#!/usr/bin/env perl
use strict;
use warnings;

use File::Path qw(make_path);
use File::Spec;
use File::Temp qw(tempfile);
use IO::Select;
use IPC::Open3;
use Symbol qw(gensym);

# Enable autoflush on STDOUT/STDERR so output appears immediately
$| = 1;
select(STDERR); $| = 1; select(STDOUT);

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
my $view_mode = $ENV{SAFE_RUN_VIEW} // '';

# M0-P1-I1: Separate temp files for stdout and stderr
my ($tmp_stdout_fh, $tmp_stdout_path) = tempfile('safe-run-stdout-XXXXXX', TMPDIR => 1, UNLINK => 0);
my ($tmp_stderr_fh, $tmp_stderr_path) = tempfile('safe-run-stderr-XXXXXX', TMPDIR => 1, UNLINK => 0);
binmode($tmp_stdout_fh);
binmode($tmp_stderr_fh);

# Event ledger: track observed-order events with sequence numbers
my @event_ledger;
my $seq = 0;

sub emit_event {
  my ($stream, $text) = @_;
  $seq++;
  push @event_ledger, {seq => $seq, stream => $stream, text => $text};
}

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

# Build properly quoted command string for META event (POSIX shell-style quoting)
# Use String::ShellQuote if available, otherwise simple quoting
my $cmd_str;
eval {
  require String::ShellQuote;
  $cmd_str = String::ShellQuote::shell_quote(@argv);
  1;
} or do {
  # Fallback: simple quoting (good enough for most cases)
  my @quoted;
  for my $arg (@argv) {
    if ($arg =~ /^[a-zA-Z0-9_\-\.\/=]+$/) {
      push @quoted, $arg;
    } else {
      my $q = $arg;
      $q =~ s/'/'\\''/g;
      push @quoted, "'$q'";
    }
  }
  $cmd_str = join(' ', @quoted);
};

# Emit start event
emit_event('META', "safe-run start: cmd=\"$cmd_str\"");

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
  # M0-P1-I2: ISO8601 timestamp format
  my ($sec,$min,$hour,$mday,$mon,$year) = gmtime();
  my $ts = sprintf("%04d%02d%02dT%02d%02d%02dZ", $year+1900, $mon+1, $mday, $hour, $min, $sec);
  my $pid = $$;
  my $fail_path = File::Spec->catfile($safe_log_dir, "${ts}-pid${pid}-ERROR.log");
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

# Line buffers for event ledger (accumulate partial lines)
my $stdout_buf = '';
my $stderr_buf = '';

sub _emit_lines {
  my ($buf_ref, $stream, $final) = @_;
  my @lines = split(/\n/, $$buf_ref, -1);
  
  if ($final) {
    # Process all lines
    for my $line (@lines) {
      emit_event($stream, $line) if length($line) > 0;
    }
    $$buf_ref = '';
  } else {
    # Keep last partial line in buffer
    $$buf_ref = pop @lines;
    for my $line (@lines) {
      emit_event($stream, $line);
    }
  }
}

# Read loop
while ($sel->count && !$aborted) {
  my @ready = $sel->can_read(0.25);
  for my $fh (@ready) {
    my $buf;
    my $bytes = sysread($fh, $buf, 8192);

    if (!defined $bytes) {
      # transient read error; ignore
      next;
    }

    if ($bytes == 0) {
      # EOF: emit any remaining buffered lines
      if ($fh == $out) {
        _emit_lines(\$stdout_buf, 'STDOUT', 1);
      } else {
        _emit_lines(\$stderr_buf, 'STDERR', 1);
      }
      $sel->remove($fh);
      next;
    }

    # M0-P1-I1: Tee to separate temp files based on stream
    if ($fh == $out) {
      print {$tmp_stdout_fh} $buf;
      print STDOUT $buf;
      # Emit events for complete lines
      $stdout_buf .= $buf;
      _emit_lines(\$stdout_buf, 'STDOUT', 0);
    } else {
      print {$tmp_stderr_fh} $buf;
      print STDERR $buf;
      # Emit events for complete lines
      $stderr_buf .= $buf;
      _emit_lines(\$stderr_buf, 'STDERR', 0);
    }

    # Tail buffering line-ish: best effort split
    if ($snippet_lines && $snippet_lines > 0) {
      my @parts = split(/\n/, $buf, -1);
      for my $p (@parts) {
        _push_tail($p . "\n") if length($p);
      }
    }
  }
}

close $tmp_stdout_fh;
close $tmp_stderr_fh;

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

# Emit exit event
emit_event('META', "safe-run exit: code=$exit_code");

# If we were interrupted, treat as aborted regardless of child status.
if ($aborted) {
  make_path($safe_log_dir) unless -d $safe_log_dir;
  # M0-P1-I2: ISO8601 timestamp format
  my ($sec,$min,$hour,$mday,$mon,$year) = gmtime();
  my $ts = sprintf("%04d%02d%02dT%02d%02d%02dZ", $year+1900, $mon+1, $mday, $hour, $min, $sec);
  my $pid = $$;
  my $fail_path = File::Spec->catfile($safe_log_dir, "${ts}-pid${pid}-ABORTED.log");
  
  # M0-P1-I1: Combine with section markers + event ledger
  open my $outf, '>', $fail_path or die "cannot write $fail_path: $!";
  binmode($outf);
  print {$outf} "=== STDOUT ===\n";
  if (-f $tmp_stdout_path) {
    open my $in, '<', $tmp_stdout_path or die "cannot read $tmp_stdout_path: $!";
    binmode($in);
    my $buf;
    while (read($in, $buf, 8192)) { print {$outf} $buf; }
    close $in;
  }
  print {$outf} "\n=== STDERR ===\n";
  if (-f $tmp_stderr_path) {
    open my $in, '<', $tmp_stderr_path or die "cannot read $tmp_stderr_path: $!";
    binmode($in);
    my $buf;
    while (read($in, $buf, 8192)) { print {$outf} $buf; }
    close $in;
  }
  
  # Event ledger
  print {$outf} "\n--- BEGIN EVENTS ---\n";
  for my $evt (@event_ledger) {
    printf {$outf} "[SEQ=%d][%s] %s\n", $evt->{seq}, $evt->{stream}, $evt->{text};
  }
  print {$outf} "--- END EVENTS ---\n";
  
  # Optional merged view
  if ($view_mode eq 'merged') {
    print {$outf} "\n--- BEGIN MERGED (OBSERVED ORDER) ---\n";
    for my $evt (@event_ledger) {
      printf {$outf} "[#%d][%s] %s\n", $evt->{seq}, $evt->{stream}, $evt->{text};
    }
    print {$outf} "--- END MERGED ---\n";
  }
  
  close $outf;
  
  unlink $tmp_stdout_path;
  unlink $tmp_stderr_path;
  
  print STDERR "\n[safe-run] ABORTED ($got_signal). Partial log saved to: $fail_path\n";
  exit($exit_code || 130);
}

# Success: remove temp files, no artifacts.
if ($exit_code == 0) {
  unlink $tmp_stdout_path;
  unlink $tmp_stderr_path;
  exit 0;
}

# Failure: create log with M0-P1-I1 section markers + event ledger
make_path($safe_log_dir) unless -d $safe_log_dir;
# M0-P1-I2: ISO8601 timestamp format
my ($sec,$min,$hour,$mday,$mon,$year) = gmtime();
my $ts = sprintf("%04d%02d%02dT%02d%02d%02dZ", $year+1900, $mon+1, $mday, $hour, $min, $sec);
my $pid = $$;
my $fail_path = File::Spec->catfile($safe_log_dir, "${ts}-pid${pid}-FAIL.log");

# M0-P1-I1: Combine with section markers + event ledger
open my $outf, '>', $fail_path or die "cannot write $fail_path: $!";
binmode($outf);
print {$outf} "=== STDOUT ===\n";
if (-f $tmp_stdout_path) {
  open my $in, '<', $tmp_stdout_path or die "cannot read $tmp_stdout_path: $!";
  binmode($in);
  my $buf;
  while (read($in, $buf, 8192)) { print {$outf} $buf; }
  close $in;
}
print {$outf} "\n=== STDERR ===\n";
if (-f $tmp_stderr_path) {
  open my $in, '<', $tmp_stderr_path or die "cannot read $tmp_stderr_path: $!";
  binmode($in);
  my $buf;
  while (read($in, $buf, 8192)) { print {$outf} $buf; }
  close $in;
}

# Event ledger
print {$outf} "\n--- BEGIN EVENTS ---\n";
for my $evt (@event_ledger) {
  printf {$outf} "[SEQ=%d][%s] %s\n", $evt->{seq}, $evt->{stream}, $evt->{text};
}
print {$outf} "--- END EVENTS ---\n";

# Optional merged view
if ($view_mode eq 'merged') {
  print {$outf} "\n--- BEGIN MERGED (OBSERVED ORDER) ---\n";
  for my $evt (@event_ledger) {
    printf {$outf} "[#%d][%s] %s\n", $evt->{seq}, $evt->{stream}, $evt->{text};
  }
  print {$outf} "--- END MERGED ---\n";
}

close $outf;

unlink $tmp_stdout_path;
unlink $tmp_stderr_path;

print STDERR "\n[safe-run] Command failed (exit $exit_code). Log saved to: $fail_path\n";

if ($snippet_lines && $snippet_lines > 0 && @tail) {
  print STDERR "\n[safe-run] Tail snippet (last $snippet_lines lines):\n";
  print STDERR @tail;
}

exit $exit_code;
