#!/usr/bin/env perl

=head1 NAME

safe-archive.pl - Non-destructive archival of failure logs with optional compression

=head1 SYNOPSIS

  # Archive all failure logs
  safe-archive.pl --all
  
  # Archive specific files
  safe-archive.pl <file1> [file2 ...]
  
  # Show help
  safe-archive.pl --help

=head1 DESCRIPTION

This script archives failure logs from the FAIL-LOGS directory to the
FAIL-ARCHIVE directory using no-clobber semantics. It never deletes or
overwrites existing files, ensuring safe archival operations.

The script supports optional compression (gzip, xz, zstd) and handles
filename collisions by automatically adding numeric suffixes.

=head1 OPTIONS

=over 4

=item B<--all>

Archive all files in the FAIL-LOGS directory. This is the most common usage.

=item B<-h>, B<--help>

Display usage information and exit with code 2.

=item B<E<lt>fileE<gt> ...>

Archive specific files by path. Files must exist or an error is raised.

=back

=head1 ARGUMENTS

=over 4

=item B<file1>, B<file2>, ...

One or more file paths to archive. Each file is moved from its current
location to the archive directory. Paths can be absolute or relative.

=back

=head1 ENVIRONMENT VARIABLES

=over 4

=item B<SAFE_FAIL_DIR>

Source directory containing failure logs. Default: C<.agent/FAIL-LOGS>

The script expects log files to exist in this directory.

=item B<SAFE_ARCHIVE_DIR>

Destination directory for archived logs. Default: C<.agent/FAIL-ARCHIVE>

The script creates this directory if it doesn't exist.

=item B<SAFE_ARCHIVE_COMPRESS>

Compression method to apply after archival. Valid values:

  - none (default) - No compression
  - gzip - Compress with gzip (requires IO::Compress::Gzip)
  - xz - Compress with xz (requires xz command in PATH)
  - zstd - Compress with zstd (requires zstd command in PATH)

Compression is applied AFTER the file is moved to the archive directory.
The original uncompressed file is removed after successful compression.

=back

=head1 EXIT CODES

=over 4

=item B<0>

Success - All files archived successfully.

=item B<1>

File operation error - Failed to move file, compress file, or file not found.
Error message printed to stderr.

=item B<2>

Usage error - Invalid arguments or help requested.

=back

=head1 NO-CLOBBER SEMANTICS

The archival process implements strict no-clobber behavior per M0-P1-I3:

=over 4

=item 1. B<Check destination>

If a file with the same basename exists in the archive directory, do NOT
overwrite it.

=item 2. B<Auto-suffix collision resolution>

Add a numeric suffix (1, 2, 3, ...) to create a unique filename:

  Original: my-log.log
  Collision detected: my-log.log exists
  New name: my-log.1.log
  
  If my-log.1.log also exists:
  New name: my-log.2.log

=item 3. B<Preserve original>

The existing file in the archive directory is never modified or deleted.

=item 4. B<Atomic move>

Files are moved (not copied) to ensure atomic filesystem operations.

=back

=head1 COMPRESSION SUPPORT

=head2 gzip

Requires: C<IO::Compress::Gzip> Perl module

Result: C<filename.log.gz>

The script attempts to load IO::Compress::Gzip at runtime. If not available,
an error is raised.

=head2 xz

Requires: C<xz> command in PATH

Result: C<filename.log.xz>

Uses multi-threaded compression (C<-T0>) and force overwrites temp file (C<-f>).

=head2 zstd

Requires: C<zstd> command in PATH

Result: C<filename.log.zst>

Uses multi-threaded compression (C<-T0>), quiet mode (C<-q>), and force
overwrites temp file (C<-f>).

=head1 SIDE EFFECTS

=over 4

=item * Moves files from SAFE_FAIL_DIR to SAFE_ARCHIVE_DIR

=item * Creates SAFE_ARCHIVE_DIR if it doesn't exist

=item * Creates SAFE_FAIL_DIR if it doesn't exist (for safety)

=item * Removes uncompressed files after successful compression

=item * Never deletes or overwrites existing archive files

=back

=head1 FILESYSTEM INTERACTIONS

=over 4

=item * B<Read:> Source directory (SAFE_FAIL_DIR)

=item * B<Write:> Destination directory (SAFE_ARCHIVE_DIR)

=item * B<Modify:> Removes source files after move (or compressed files after compression)

=item * B<Create:> Archive directory if missing, compressed files if requested

=back

=head1 PLATFORM NOTES

=head2 Unix-like (Linux, macOS)

- Uses File::Copy::move for atomic file moves
- External compression commands (xz, zstd) via system()
- Directory creation via File::Path::make_path

=head2 Windows

- File::Copy::move works on Windows NTFS
- External commands (xz.exe, zstd.exe) must be in PATH
- Path handling via File::Spec for portability

=head1 EXAMPLES

=head2 Archive All Logs (No Compression)

  $ safe-archive.pl --all
  ARCHIVED: .agent/FAIL-LOGS/fail-001.log -> .agent/FAIL-ARCHIVE/fail-001.log
  ARCHIVED: .agent/FAIL-LOGS/fail-002.log -> .agent/FAIL-ARCHIVE/fail-002.log

=head2 Archive with gzip Compression

  $ export SAFE_ARCHIVE_COMPRESS=gzip
  $ safe-archive.pl --all
  ARCHIVED: .agent/FAIL-LOGS/fail-001.log -> .agent/FAIL-ARCHIVE/fail-001.log
  # Compresses to: .agent/FAIL-ARCHIVE/fail-001.log.gz

=head2 Archive Specific File

  $ safe-archive.pl .agent/FAIL-LOGS/specific-fail.log
  ARCHIVED: .agent/FAIL-LOGS/specific-fail.log -> .agent/FAIL-ARCHIVE/specific-fail.log

=head2 Collision Handling

  $ ls .agent/FAIL-ARCHIVE/
  my-log.log
  
  $ safe-archive.pl .agent/FAIL-LOGS/my-log.log
  INFO: destination exists, using suffix: .agent/FAIL-ARCHIVE/my-log.1.log
  ARCHIVED: .agent/FAIL-LOGS/my-log.log -> .agent/FAIL-ARCHIVE/my-log.1.log

=head2 Custom Directories

  $ export SAFE_FAIL_DIR=/var/log/failures
  $ export SAFE_ARCHIVE_DIR=/archive/failures
  $ safe-archive.pl --all

=head2 xz Compression

  $ export SAFE_ARCHIVE_COMPRESS=xz
  $ safe-archive.pl --all
  # Creates .log.xz files with multi-threaded compression

=head1 CONTRACT REFERENCES

This script implements the archival behavior specified in:

=over 4

=item * M0-P1-I3: No-clobber semantics for safe archival

=item * docs/conformance-contract.md: Artifact management

=back

=head1 DIAGNOSTICS

=over 4

=item B<File not found: <path>>

The specified file does not exist. Check the path and try again.

=item B<Failed to move <src> -> <dest>: <error>>

File move operation failed. Common causes: permission denied, disk full,
source and destination on different filesystems (move requires copy+delete).

=item B<gzip compression requires IO::Compress::Gzip: <error>>

The IO::Compress::Gzip module is not installed. Install it via CPAN or
use a different compression method.

=item B<xz command not found in PATH>

The xz compression tool is not installed or not in PATH.

=item B<zstd command not found in PATH>

The zstd compression tool is not installed or not in PATH.

=item B<Invalid SAFE_ARCHIVE_COMPRESS value: <value>>

The compression method is not recognized. Use: none, gzip, xz, or zstd.

=back

=head1 SEE ALSO

=over 4

=item * L<safe-run.pl> - Create failure logs

=item * L<safe-check.pl> - Verify contract compliance

=item * L<IO::Compress::Gzip> - Perl gzip compression module

=back

=head1 AUTHOR

RFC-Shared-Agent-Scaffolding Project

=head1 LICENSE

Unlicense - See LICENSE file in repository root

=cut

use strict;
use warnings;
use File::Path qw(make_path);
use File::Basename qw(basename);
use File::Copy qw(move copy);

sub die_msg { print STDERR "ERROR: $_[0]\n"; exit 1; }

sub usage {
  print STDERR <<"USAGE";
Usage:
  scripts/perl/safe-archive.pl [--all | <file> ...]

Options:
  --all            Archive all files in the FAIL-LOGS directory.
  -h, --help       Show help.

Environment:
  SAFE_FAIL_DIR           Source directory (default: .agent/FAIL-LOGS)
  SAFE_ARCHIVE_DIR        Destination directory (default: .agent/FAIL-ARCHIVE)
  SAFE_ARCHIVE_COMPRESS   Compression: none|gzip|xz|zstd (default: none)

Notes:
  - Never deletes. Moves files without overwriting existing destination.
  - Compression is applied after move. gzip uses IO::Compress::Gzip if available; xz/zstd require external commands.
USAGE
  exit 2;
}

sub have_cmd {
  my ($cmd) = @_;
  for my $p (split(/:/, $ENV{PATH} // "")) {
    return 1 if -x "$p/$cmd";
  }
  return 0;
}

sub compress_file {
  my ($method, $path) = @_;
  $method ||= "none";
  return if $method eq "none";

  if ($method eq "gzip") {
    eval { require IO::Compress::Gzip; IO::Compress::Gzip->import(qw(gzip $GzipError)); 1 } or die_msg("gzip compression requires IO::Compress::Gzip: $@");
    my $out = "$path.gz";
    IO::Compress::Gzip::gzip($path => $out) or die_msg("gzip failed: $IO::Compress::Gzip::GzipError");
    unlink $path or die_msg("Failed to remove uncompressed after gzip: $!");
    return;
  }

  if ($method eq "xz") {
    die_msg("xz command not found in PATH") if !have_cmd("xz");
    system("xz", "-T0", "-f", $path) == 0 or die_msg("xz failed");
    return;
  }

  if ($method eq "zstd") {
    die_msg("zstd command not found in PATH") if !have_cmd("zstd");
    system("zstd", "-q", "-T0", "-f", $path) == 0 or die_msg("zstd failed");
    return;
  }

  die_msg("Invalid SAFE_ARCHIVE_COMPRESS value: $method (expected none|gzip|xz|zstd)");
}

my @argv = @ARGV;
if (!@argv || $argv[0] eq '-h' || $argv[0] eq '--help') { usage() if !@argv; usage(); }

my $fail_dir = $ENV{SAFE_FAIL_DIR} // ".agent/FAIL-LOGS";
my $archive_dir = $ENV{SAFE_ARCHIVE_DIR} // ".agent/FAIL-ARCHIVE";
my $compress = $ENV{SAFE_ARCHIVE_COMPRESS} // "none";

make_path($fail_dir) if !-d $fail_dir;
make_path($archive_dir) if !-d $archive_dir;

sub archive_one {
  my ($src) = @_;
  die_msg("File not found: $src") if !-e $src;
  my $base = basename($src);
  my $dest = "$archive_dir/$base";

  # M0-P1-I3: Auto-suffix if destination exists
  if (-e $dest) {
    my $suffix = 1;
    my ($name, $ext) = $base =~ /^(.+?)(\.[^.]+)?$/;
    $ext //= '';
    while (-e "$archive_dir/$name.$suffix$ext") {
      $suffix++;
    }
    $dest = "$archive_dir/$name.$suffix$ext";
    print STDERR "INFO: destination exists, using suffix: $dest\n";
  }
  
  move($src, $dest) or die_msg("Failed to move $src -> $dest: $!");
  print STDERR "ARCHIVED: $src -> $dest\n";
  compress_file($compress, $dest);
}

if (@argv && $argv[0] eq '--all') {
  shift @argv;
  opendir(my $dh, $fail_dir) or die_msg("Cannot open $fail_dir: $!");
  my @files = sort grep { -f "$fail_dir/$_" } readdir($dh);
  closedir($dh);
  if (!@files) {
    print STDERR "No files to archive in $fail_dir\n";
    exit 0;
  }
  for my $f (@files) { archive_one("$fail_dir/$f"); }
  exit 0;
}

usage() if !@argv;
for my $f (@argv) { archive_one($f); }
exit 0;
