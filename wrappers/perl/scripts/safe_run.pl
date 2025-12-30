#!/usr/bin/env perl

=head1 NAME

safe_run.pl - Thin invoker for Rust canonical safe-run tool

=head1 SYNOPSIS

  # Basic usage - execute a command with failure logging
  safe_run.pl -- <command> [args...]
  
  # Optional leading "--" separator
  safe_run.pl <command> [args...]
  
  # Examples
  safe_run.pl -- echo "Hello, world!"
  safe_run.pl -- perl my-script.pl
  safe_run.pl npm test

=head1 DESCRIPTION

This Perl wrapper discovers and invokes the Rust canonical implementation of
the safe-run tool. It does NOT reimplement any contract logic - it is purely
a thin invoker that handles binary discovery and argument pass-through.

The safe-run tool executes commands with enhanced failure logging. On success
(exit code 0), no artifacts are created. On failure (non-zero exit), a
detailed log file is written to the configured log directory with complete
stdout/stderr capture, event sequencing, and metadata.

=head1 BINARY DISCOVERY

The wrapper searches for the Rust canonical binary in the following order
(per docs/wrapper-discovery.md):

=over 4

=item 1. B<SAFE_RUN_BIN> environment variable

If set, uses this path without validation. Use for testing, CI overrides,
or custom installations.

=item 2. B<./rust/target/release/safe-run> (dev mode)

Relative to repository root. Use for local development and testing Rust changes.

=item 3. B<./dist/E<lt>osE<gt>/E<lt>archE<gt>/safe-run> (CI artifacts)

Platform-specific paths:
  - Linux: ./dist/linux/x86_64/safe-run
  - macOS (Intel): ./dist/macos/x86_64/safe-run
  - macOS (ARM): ./dist/macos/aarch64/safe-run
  - Windows: ./dist/windows/x86_64/safe-run.exe

=item 4. B<PATH> lookup

Searches for 'safe-run' in system PATH (system-wide installation).

=item 5. B<Error with instructions> (exit 127)

If no binary is found, prints actionable error message with installation
instructions and exits with code 127 (command not found).

=back

=head1 ENVIRONMENT VARIABLES

=head2 Wrapper Control

=over 4

=item B<SAFE_RUN_BIN>

Override binary discovery. If set, this path is used for the Rust canonical
tool without further searching.

Example:

  export SAFE_RUN_BIN=/custom/path/to/safe-run
  safe_run.pl -- echo "test"

=back

=head2 Canonical Tool Configuration

These environment variables are passed through to the Rust canonical tool
and control its runtime behavior:

=over 4

=item B<SAFE_LOG_DIR>

Directory for failure log artifacts. Default: C<.agent/FAIL-LOGS>

The tool creates this directory if it doesn't exist.

=item B<SAFE_SNIPPET_LINES>

Number of tail lines to emit to stderr on failure for quick diagnosis.
Default: 0 (disabled)

The snippet is printed after "command failed ... log:" line for convenience.
Full output is always in the log file. Set to 0 to disable snippet output.
Note: Extremely large values may produce noisy stderr.

Example:

  export SAFE_SNIPPET_LINES=10
  safe_run.pl -- failing-command

=item B<SAFE_RUN_VIEW>

Output format mode. Valid values: C<ledger> (default), C<merged>

  - ledger: Split sections + event ledger with sequence numbers
  - merged: Temporal ordering of stdout/stderr without metadata

See docs/conformance-contract.md for format specifications.

=back

=head1 EXIT CODES

The wrapper preserves the Rust canonical tool's exit code, which in turn
preserves the child process exit code:

=over 4

=item B<0>

Success - command executed with exit code 0. No artifacts created.

=item B<1-255>

Failure - command exited with non-zero code. Failure log created in SAFE_LOG_DIR.

=item B<127>

Binary not found - Rust canonical tool could not be located. Check error
message for installation instructions.

=item B<128+N> (Unix-like)

Signal termination - command was terminated by signal N.
Examples: 130 (SIGINT), 137 (SIGKILL), 143 (SIGTERM)

=back

=head1 PLATFORM NOTES

=head2 Unix-like (Linux, macOS)

- Uses standard shebang (#!/usr/bin/env perl)
- Platform detection via C<$^O> and C<uname -m>
- Signal handling preserved through exec

=head2 Windows

- Automatically appends .exe extension for binary lookup
- Platform detection via C<$^O> matching MSWin/cygwin/msys
- Windows exit codes preserved as-is

=head1 CONTRACT REFERENCES

This wrapper implements the discovery protocol specified in:

=over 4

=item * docs/wrapper-discovery.md - Binary discovery rules

=item * docs/conformance-contract.md - Output format contract (M0-v0.1.0)

=item * RFC-Shared-Agent-Scaffolding-v0.1.0.md - Complete specification

=back

Conformance test vectors: conformance/vectors.json

=head1 SIDE EFFECTS

=over 4

=item * Creates SAFE_LOG_DIR if it doesn't exist (via Rust tool)

=item * Writes failure log files with pattern: safe-run-YYYYMMDD-HHMMSS-<random>.log

=item * No artifacts created on success

=item * No modification or interpretation of command arguments

=back

=head1 EXAMPLES

=head2 Basic Success Case

  $ safe_run.pl -- echo "Hello"
  Hello
  $ echo $?
  0

No artifacts created.

=head2 Basic Failure Case

  $ safe_run.pl -- perl -e 'exit 42'
  $ echo $?
  42
  $ ls .agent/FAIL-LOGS/
  safe-run-20240115-103000-a3f9b2.log

=head2 Custom Binary Location

  $ export SAFE_RUN_BIN=/opt/safe-run/bin/safe-run
  $ safe_run.pl -- npm test

=head2 Custom Log Directory

  $ export SAFE_LOG_DIR=/var/log/agent-failures
  $ safe_run.pl -- make test

=head2 Snippet Lines Configuration

  $ export SAFE_SNIPPET_LINES=5
  $ safe_run.pl -- ./long-failing-script.sh
  # Last 5 lines of output printed to stderr for quick diagnosis

=head2 Merged View Mode

  $ export SAFE_RUN_VIEW=merged
  $ safe_run.pl -- ./script-with-interleaved-output.sh
  # Failure log shows stdout/stderr in temporal order

=head1 SEE ALSO

=over 4

=item * L<safe-archive.pl> - Archive failure logs with optional compression

=item * L<safe-check.pl> - Minimal self-test for safe-run contract

=item * L<preflight-automerge-ruleset.pl> - GitHub ruleset validation

=back

=head1 AUTHOR

RFC-Shared-Agent-Scaffolding Project

=head1 LICENSE

Unlicense - See LICENSE file in repository root

=cut

use strict;
use warnings;
use File::Basename qw(dirname);
use File::Spec;
use Cwd qw(abs_path);

=head2 find_repo_root

Determines repository root by walking up from script location.

Returns:
    Path to the repository root directory

=cut

# Determine repository root (walk up from script location)
sub find_repo_root {
    my $script_dir = dirname(abs_path(__FILE__));
    my $dir = $script_dir;
    my $rootdir = File::Spec->rootdir();
    
    while ($dir ne $rootdir) {
        if (-f File::Spec->catfile($dir, 'RFC-Shared-Agent-Scaffolding-v0.1.0.md') || 
            -d File::Spec->catdir($dir, '.git')) {
            return $dir;
        }
        my $parent = dirname($dir);
        last if $parent eq $dir;  # Reached filesystem root
        $dir = $parent;
    }
    
    return;
}

my $REPO_ROOT = find_repo_root();

=head2 detect_platform

Detects the current OS and architecture.

Returns:
    Platform string in format "os/arch" (e.g., "linux/x86_64")

=cut

# Detect OS and architecture for CI artifact path
sub detect_platform {
    my $os = 'unknown';
    my $arch = 'unknown';
    
    # Detect OS
    if ($^O eq 'linux') {
        $os = 'linux';
    } elsif ($^O eq 'darwin') {
        $os = 'macos';
    } elsif ($^O =~ /^(MSWin|cygwin|msys)/i) {
        $os = 'windows';
    }
    
    # Detect architecture
    my $machine = `uname -m 2>/dev/null`;
    chomp $machine if defined $machine;
    
    if ($machine =~ /^(x86_64|amd64)$/) {
        $arch = 'x86_64';
    } elsif ($machine =~ /^(aarch64|arm64)$/) {
        $arch = 'aarch64';
    }
    
    return "$os/$arch";
}

my $PLATFORM = detect_platform();

=head2 find_safe_run_binary

Finds the safe-run binary using a discovery cascade.

Returns:
    Path to the safe-run binary

=cut

# Binary discovery cascade
sub find_safe_run_binary {
    my $is_windows = ($^O =~ /^(MSWin|cygwin|msys)/i);
    
    # 1. Environment override
    if (defined $ENV{SAFE_RUN_BIN} && $ENV{SAFE_RUN_BIN} ne '') {
        return $ENV{SAFE_RUN_BIN};
    }
    
    # 2. Dev mode: ./rust/target/release/safe-run (relative to repo root)
    # On Windows, check for both safe-run and safe-run.exe
    if (defined $REPO_ROOT) {
        my $dev_bin = File::Spec->catfile($REPO_ROOT, 'rust', 'target', 'release', 'safe-run');
        if (-x $dev_bin) {
            return $dev_bin;
        }
        if ($is_windows) {
            my $dev_bin_exe = File::Spec->catfile($REPO_ROOT, 'rust', 'target', 'release', 'safe-run.exe');
            if (-x $dev_bin_exe) {
                return $dev_bin_exe;
            }
        }
    }
    
    # 3. CI artifact: ./dist/<os>/<arch>/safe-run
    # On Windows, check for both safe-run and safe-run.exe
    if (defined $REPO_ROOT && $PLATFORM ne 'unknown/unknown') {
        my @parts = split('/', $PLATFORM);
        my $ci_bin = File::Spec->catfile($REPO_ROOT, 'dist', @parts, 'safe-run');
        if (-x $ci_bin) {
            return $ci_bin;
        }
        if ($is_windows) {
            my $ci_bin_exe = File::Spec->catfile($REPO_ROOT, 'dist', @parts, 'safe-run.exe');
            if (-x $ci_bin_exe) {
                return $ci_bin_exe;
            }
        }
    }
    
    # 4. PATH lookup
    my $which_output = `which safe-run 2>/dev/null`;
    chomp $which_output if defined $which_output;
    if (defined $which_output && $which_output ne '' && -x $which_output) {
        return $which_output;
    }
    
    # 5. Not found
    return;
}

# Main execution
my $binary = find_safe_run_binary();

if (!defined $binary) {
    print STDERR <<'EOF';
ERROR: Rust canonical tool not found.

Searched locations:
  1. SAFE_RUN_BIN env var (not set or invalid)
  2. ./rust/target/release/safe-run (not found)
  3. ./dist/<os>/<arch>/safe-run (not found)
  4. PATH lookup (not found)

To install:
  1. Clone the repository
  2. cd rust/
  3. cargo build --release

Or download a pre-built binary from:
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/releases

For more information, see:
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/blob/main/docs/rust-canonical-tool.md
EOF
    exit 127;
}

# Parse arguments: handle optional "--" separator
my @args = @ARGV;
if (@args > 0 && $args[0] eq '--') {
    shift @args;
}

# Invoke the Rust canonical tool with all arguments passed through
# The 'run' subcommand is required by the Rust CLI structure
exec($binary, 'run', @args) or do {
    # If exec fails, check if it's a permission issue vs not found
    if ($! =~ /permission denied/i) {
        print STDERR "ERROR: Permission denied executing $binary: $!\n";
        exit 126;
    } else {
        print STDERR "ERROR: Failed to execute $binary: $!\n";
        exit 127;
    }
};
