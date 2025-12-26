#!/usr/bin/env perl
# safe-archive.pl (Perl)
# Non-destructively archive failure logs from .agent/FAIL-LOGS to .agent/FAIL-ARCHIVE using no-clobber semantics.
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

  if (-e $dest) {
    print STDERR "SKIP: destination exists (no-clobber): $dest\n";
    return;
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
