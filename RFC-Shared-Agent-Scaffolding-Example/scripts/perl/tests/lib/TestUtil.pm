
package TestUtil;

=head1 NAME

TestUtil - Common testing utilities for Perl safe-run tests

=head1 SYNOPSIS

  use TestUtil qw(make_sandbox run_cmd slurp write_file make_exe);
  
  # Create isolated test environment
  my $sandbox = make_sandbox();
  
  # Write test files
  write_file("$sandbox/test.pl", "print 'hello'");
  make_exe("$sandbox/test.pl");
  
  # Execute commands
  my $result = run_cmd(["perl", "test.pl"], cwd => $sandbox);
  
  # Read results
  my $content = slurp("$sandbox/output.txt");

=head1 DESCRIPTION

This module provides common testing utilities used across the Perl test
suite for safe-run, safe-archive, safe-check, and preflight scripts.

All utilities are designed for isolated, reproducible testing in temporary
sandboxes that are automatically cleaned up after tests complete.

=head1 EXPORTED FUNCTIONS

The following functions are available for export:

  use TestUtil qw(make_sandbox run_cmd slurp write_file make_exe);

=head2 make_sandbox

  my $sandbox = make_sandbox();
  my $sandbox = make_sandbox(cleanup => 0);

Creates a temporary directory for test isolation.

B<Parameters:>

=over 4

=item * C<cleanup> - Boolean (default: 1). If true, directory is removed when
Perl exits. If false, directory persists for debugging.

=back

B<Returns:> Absolute path to the temporary directory

B<Side Effects:>

=over 4

=item * Creates directory in system temp location (TMPDIR)

=item * Directory name: C<agentops-perltest-XXXXXX> (random suffix)

=item * Registers cleanup handler if cleanup=1

=back

B<Example:>

  my $sandbox = make_sandbox();
  # Do test work in $sandbox
  # Directory automatically deleted at exit

  my $debug_sandbox = make_sandbox(cleanup => 0);
  print "Debug sandbox: $debug_sandbox\n";
  # Directory persists for inspection

=head2 write_file

  write_file($path, $content);

Writes content to a file, creating parent directories as needed.

B<Parameters:>

=over 4

=item * C<$path> - Absolute or relative file path

=item * C<$content> - Binary or text content to write

=back

B<Returns:> The file path (for chaining)

B<Side Effects:>

=over 4

=item * Creates parent directories if they don't exist

=item * Overwrites existing file

=item * Dies on filesystem errors (permission denied, disk full, etc.)

=back

B<Example:>

  write_file("$sandbox/data/test.txt", "Hello\n");
  write_file("$sandbox/binary.dat", "\x00\x01\x02");

=head2 slurp

  my $content = slurp($path);

Reads entire file into a string.

B<Parameters:>

=over 4

=item * C<$path> - File path to read

=back

B<Returns:> File content as string (binary mode)

B<Side Effects:>

=over 4

=item * Opens file in binary mode

=item * Dies if file doesn't exist or can't be read

=back

B<Example:>

  my $log = slurp(".agent/FAIL-LOGS/fail.log");
  like($log, qr/ERROR/, "log contains error marker");

=head2 make_exe

  make_exe($path);

Makes a file executable (chmod 0755).

B<Parameters:>

=over 4

=item * C<$path> - Path to file to make executable

=back

B<Returns:> None

B<Side Effects:>

=over 4

=item * Sets file permissions to 0755 (rwxr-xr-x)

=item * Dies if chmod fails

=back

B<Platform Notes:>

=over 4

=item * Unix-like: Sets execute bits as expected

=item * Windows: May be a no-op depending on filesystem

=back

B<Example:>

  write_file("$sandbox/script.sh", "#!/bin/bash\necho hi");
  make_exe("$sandbox/script.sh");
  system("$sandbox/script.sh");  # Now executable

=head2 run_cmd

  my $result = run_cmd(\@cmd, %opts);

Executes a command and captures stdout, stderr, and exit code.

B<Parameters:>

=over 4

=item * C<\@cmd> - Array ref of command and arguments

Example: C<["perl", "-e", "print 'hello'"]>

=item * C<%opts> - Optional hash of:

=over 4

=item * C<cwd> - Change to this directory before executing

=item * C<env> - Hash ref of additional environment variables

=item * C<timeout_sec> - Maximum execution time (default: 20 seconds)

=back

=back

B<Returns:> Hash ref with:

=over 4

=item * C<stdout> - Captured stdout as string

=item * C<stderr> - Captured stderr as string

=item * C<exit> - Exit code (0-255)

=item * C<sig> - Signal number if terminated by signal (0 if normal exit)

=item * C<pid> - Process ID

=back

B<Side Effects:>

=over 4

=item * Spawns child process via IPC::Open3

=item * Changes directory if C<cwd> specified (restored after)

=item * Merges additional environment variables if C<env> specified

=item * Kills process with SIGKILL if timeout exceeded

=back

B<Example:>

  my $r = run_cmd(
    ["perl", "script.pl"],
    cwd => $sandbox,
    env => { DEBUG => 1 },
    timeout_sec => 30
  );
  
  is($r->{exit}, 0, "command succeeded");
  like($r->{stdout}, qr/SUCCESS/, "output contains success marker");
  is($r->{stderr}, "", "no errors");

B<Timeout Behavior:>

If the command doesn't complete within C<timeout_sec>, the function:

=over 4

=item 1. Sends SIGKILL to the process

=item 2. Returns partial stdout/stderr captured before timeout

=item 3. Sets C<exit> to the process exit status (typically 0 when terminated by a signal)

=item 4. Sets C<sig> to the terminating signal number (9 for SIGKILL); callers should check C<sig> to detect timeouts or signal-based termination

=back

=head1 IMPLEMENTATION DETAILS

=head2 Temporary Directory Location

Temporary directories are created in the system temp location:

=over 4

=item * Unix-like: C<$TMPDIR> or C</tmp>

=item * Windows: C<%TEMP%> or C<C:\Temp>

=back

=head2 Command Execution

The C<run_cmd> function uses IPC::Open3 for full control over stdin/stdout/stderr:

=over 4

=item * stdin: Closed immediately (no input)

=item * stdout: Captured via non-blocking reads

=item * stderr: Captured separately via non-blocking reads

=item * Polling: IO::Select with 0.2 second timeout per iteration

=back

This design prevents deadlocks when child processes produce large output
on both streams.

=head2 Signal Handling

The module does NOT install global signal handlers. Signal handling is
left to the test harness and individual tests.

=head1 SIDE EFFECTS

=over 4

=item * Creates temporary directories in system temp location

=item * Spawns child processes for command execution

=item * Changes current directory temporarily if C<cwd> specified in run_cmd

=item * Modifies local %ENV copy if C<env> specified in run_cmd

=item * Kills processes with SIGKILL on timeout

=back

=head1 ERROR HANDLING

All functions die on errors with descriptive messages:

=over 4

=item * C<make_sandbox>: Dies if tempdir creation fails

=item * C<write_file>: Dies if open/write/close fails

=item * C<slurp>: Dies if open/read/close fails

=item * C<make_exe>: Dies if chmod fails

=item * C<run_cmd>: Dies if chdir fails, but NOT if command fails (captures exit code)

=back

Use standard Perl error handling:

  eval {
    write_file("/read-only/file", "data");
    1;
  } or do {
    warn "Failed to write file: $@";
  };

=head1 TESTING PHILOSOPHY

This module follows these testing principles:

=over 4

=item * B<Isolation:> Each test gets a fresh sandbox

=item * B<Reproducibility:> No reliance on global state or existing files

=item * B<Cleanup:> Temporary resources are removed automatically

=item * B<Observability:> Full capture of stdout/stderr/exit codes

=item * B<Safety:> Timeouts prevent hung tests

=back

=head1 EXAMPLES

=head2 Basic Test Pattern

  use Test::More;
  use TestUtil qw(make_sandbox run_cmd write_file make_exe);
  
  my $sandbox = make_sandbox();
  
  # Setup
  write_file("$sandbox/script.pl", <<'SCRIPT');
  print "Hello\n";
  exit 0;
  SCRIPT
  make_exe("$sandbox/script.pl");
  
  # Execute
  my $r = run_cmd(["perl", "script.pl"], cwd => $sandbox);
  
  # Verify
  is($r->{exit}, 0, "script succeeded");
  like($r->{stdout}, qr/Hello/, "output correct");
  
  done_testing();

=head2 Testing Environment Variables

  my $r = run_cmd(
    ["perl", "-e", 'print $ENV{MY_VAR}'],
    env => { MY_VAR => "test123" }
  );
  
  is($r->{stdout}, "test123", "env var passed through");

=head2 Testing Timeouts

  my $r = run_cmd(
    ["perl", "-e", 'sleep 60'],
    timeout_sec => 2
  );
  
  isnt($r->{exit}, 0, "command was killed");
  cmp_ok($r->{sig}, '>', 0, "terminated by signal");

=head2 Debug Mode (No Cleanup)

  my $sandbox = make_sandbox(cleanup => 0);
  
  # Run failing test
  my $r = run_cmd(["perl", "broken.pl"], cwd => $sandbox);
  
  # On failure, sandbox persists for inspection
  if ($r->{exit} != 0) {
    warn "Test failed. Sandbox: $sandbox\n";
    warn "Stderr: $r->{stderr}\n";
  }

=head1 DEPENDENCIES

=over 4

=item * L<File::Temp> - Temporary directory creation

=item * L<File::Spec> - Portable path manipulation

=item * L<File::Path> - Directory creation

=item * L<IPC::Open3> - Command execution with stdio capture

=item * L<IO::Select> - Non-blocking stream reading

=item * L<POSIX> - Signal constants and time functions

=item * L<Symbol> - Anonymous glob generation (C<Symbol::gensym>)
=back

All dependencies are core Perl modules (included with Perl 5.10+).

=head1 SEE ALSO

=over 4

=item * L<Test::More> - TAP testing framework

=item * L<IPC::Open3> - Low-level command execution

=item * L<File::Temp> - Temporary file/directory creation

=back

=head1 AUTHOR

RFC-Shared-Agent-Scaffolding Project

=head1 LICENSE

Unlicense - See LICENSE file in repository root

=cut

use strict;
use warnings;
use Exporter 'import';
use File::Temp qw(tempdir);
use File::Spec;
use Cwd qw(getcwd);
use POSIX qw(strftime);

our @EXPORT_OK = qw(make_sandbox run_cmd slurp write_file make_exe);

sub make_sandbox {
  my (%opts) = @_;
  my $dir = tempdir("agentops-perltest-XXXXXX", TMPDIR => 1, CLEANUP => ($opts{cleanup}//1));
  return $dir;
}

sub write_file {
  my ($path, $content) = @_;
  my ($vol,$dirs,$file) = File::Spec->splitpath($path);
  my $dpath = File::Spec->catpath($vol,$dirs,'');
  if ($dpath && !-d $dpath) {
    require File::Path;
    File::Path::make_path($dpath);
  }
  open my $fh, ">", $path or die "open(>): $path: $!";
  binmode($fh);
  print {$fh} $content;
  close $fh or die "close: $!";
  return $path;
}

sub slurp {
  my ($path) = @_;
  open my $fh, "<", $path or die "open(<): $path: $!";
  binmode($fh);
  local $/;
  my $c = <$fh>;
  close $fh;
  return $c;
}

sub make_exe {
  my ($path) = @_;
  chmod(0755, $path) or die "chmod: $path: $!";
}

# Run a command and capture stdout/stderr/exit.
# Args: (cmd_arrayref, %opts)
# opts: cwd, env_hashref, timeout_sec
sub run_cmd {
  my ($cmd, %opts) = @_;
  my $cwd = $opts{cwd};
  my $env = $opts{env} || {};
  my $timeout = $opts{timeout_sec} || 20;

  require IPC::Open3;
  require IO::Select;
  require Symbol;

  my $oldcwd;
  if (defined $cwd) {
    $oldcwd = getcwd();
    chdir($cwd) or die "chdir($cwd): $!";
  }

  local %ENV = (%ENV, %$env);

  my $err = Symbol::gensym();
  my $pid = IPC::Open3::open3(my $in, my $out, $err, @$cmd);
  close $in;

  my $sel = IO::Select->new();
  $sel->add($out);
  $sel->add($err);

  my $stdout = "";
  my $stderr = "";

  my $start = time();
  while ($sel->count) {
    if (time() - $start > $timeout) {
      kill 'KILL', $pid;
      last;
    }
    my @ready = $sel->can_read(0.2);
    for my $fh (@ready) {
      my $buf;
      my $n = sysread($fh, $buf, 8192);
      if (!defined $n || $n == 0) {
        $sel->remove($fh);
        next;
      }
      if (fileno($fh) == fileno($out)) {
        $stdout .= $buf;
      } else {
        $stderr .= $buf;
      }
    }
  }

  waitpid($pid, 0);
  my $exit = $? >> 8;
  my $sig  = $? & 127;

  if (defined $oldcwd) {
    chdir($oldcwd) or die "chdir(back): $!";
  }

  return { stdout=>$stdout, stderr=>$stderr, exit=>$exit, sig=>$sig, pid=>$pid };
}

1;
