#!/usr/bin/env perl
# safe-run.pl - Thin invoker for Rust canonical safe-run tool
#
# This wrapper discovers and invokes the Rust canonical implementation.
# It does NOT reimplement any contract logic.
#
# Binary Discovery Order (per docs/wrapper-discovery.md):
#   1. SAFE_RUN_BIN env var (if set)
#   2. ./rust/target/release/safe-run (dev mode, relative to repo root)
#   3. ./dist/<os>/<arch>/safe-run (CI artifacts)
#   4. PATH lookup (system installation)
#   5. Error with actionable instructions (exit 127)

use strict;
use warnings;
use File::Basename qw(dirname);
use File::Spec;
use Cwd qw(abs_path);

# Determine repository root (walk up from script location)
sub find_repo_root {
    my $script_dir = dirname(abs_path(__FILE__));
    my $dir = $script_dir;
    
    while ($dir ne '/') {
        if (-f File::Spec->catfile($dir, 'RFC-Shared-Agent-Scaffolding-v0.1.0.md') || 
            -d File::Spec->catdir($dir, '.git')) {
            return $dir;
        }
        $dir = dirname($dir);
    }
    
    return undef;
}

my $REPO_ROOT = find_repo_root();

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

# Binary discovery cascade
sub find_safe_run_binary {
    # 1. Environment override
    if (defined $ENV{SAFE_RUN_BIN} && $ENV{SAFE_RUN_BIN} ne '') {
        return $ENV{SAFE_RUN_BIN};
    }
    
    # 2. Dev mode: ./rust/target/release/safe-run (relative to repo root)
    if (defined $REPO_ROOT) {
        my $dev_bin = File::Spec->catfile($REPO_ROOT, 'rust', 'target', 'release', 'safe-run');
        if (-x $dev_bin) {
            return $dev_bin;
        }
    }
    
    # 3. CI artifact: ./dist/<os>/<arch>/safe-run
    if (defined $REPO_ROOT && $PLATFORM ne 'unknown/unknown') {
        my @parts = split('/', $PLATFORM);
        my $ci_bin = File::Spec->catfile($REPO_ROOT, 'dist', @parts, 'safe-run');
        if (-x $ci_bin) {
            return $ci_bin;
        }
    }
    
    # 4. PATH lookup
    my $which_output = `which safe-run 2>/dev/null`;
    chomp $which_output if defined $which_output;
    if (defined $which_output && $which_output ne '' && -x $which_output) {
        return $which_output;
    }
    
    # 5. Not found
    return undef;
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
    print STDERR "ERROR: Failed to execute $binary: $!\n";
    exit 127;
};
