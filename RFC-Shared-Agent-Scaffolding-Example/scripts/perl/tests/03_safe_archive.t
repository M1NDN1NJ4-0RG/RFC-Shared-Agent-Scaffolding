
use strict;
use warnings;
use Test::More;
use File::Spec;
use File::Path qw(make_path);
use TestUtil qw(make_sandbox slurp write_file make_exe run_cmd);

my $sandbox = make_sandbox();
my $scripts_dir = File::Spec->catdir($sandbox, "scripts", "perl");
make_path($scripts_dir);

my $src = $ENV{SRC_SAFE_ARCHIVE} || die "SRC_SAFE_ARCHIVE not set";
my $safe_archive = File::Spec->catfile($scripts_dir, "safe-archive.pl");
write_file($safe_archive, slurp($src));
make_exe($safe_archive);

my $fail_dir = File::Spec->catdir($sandbox, ".agent", "FAIL-LOGS");
my $arch_dir = File::Spec->catdir($sandbox, ".agent", "FAIL-ARCHIVE");
make_path($fail_dir);
make_path($arch_dir);

# Create fail logs, including spaces in name
write_file(File::Spec->catfile($fail_dir, "a fail-FAIL.log"), "A\n");
write_file(File::Spec->catfile($fail_dir, "b-FAIL.log"), "B\n");

# 1) --all move, no compression
{
  my $r = run_cmd(["perl", $safe_archive, "--all"], cwd=>$sandbox, env=>{ SAFE_FAIL_DIR=>$fail_dir, SAFE_ARCHIVE_DIR=>$arch_dir, SAFE_ARCHIVE_COMPRESS=>"none" });
  is($r->{exit}, 0, "archive exit 0");

  ok(!-e File::Spec->catfile($fail_dir, "a fail-FAIL.log"), "removed from FAIL-LOGS");
  ok(-e File::Spec->catfile($arch_dir, "a fail-FAIL.log"), "moved to archive (spaces preserved)");
  ok(-e File::Spec->catfile($arch_dir, "b-FAIL.log"), "moved second");
}

# 2) no-clobber: if target exists, should not overwrite, should create suffixed file
{
  # Put back a file in fail dir with same name
  make_path($fail_dir);
  write_file(File::Spec->catfile($fail_dir, "b-FAIL.log"), "NEW\n");
  # Create existing file in archive
  write_file(File::Spec->catfile($arch_dir, "b-FAIL.log"), "OLD\n");

  my $r = run_cmd(["perl", $safe_archive, "--all"], cwd=>$sandbox, env=>{ SAFE_FAIL_DIR=>$fail_dir, SAFE_ARCHIVE_DIR=>$arch_dir, SAFE_ARCHIVE_COMPRESS=>"none" });
  is($r->{exit}, 0, "archive exit 0 even with collisions");

  my $old = slurp(File::Spec->catfile($arch_dir, "b-FAIL.log"));
  is($old, "OLD\n", "existing archive file not overwritten");

  # Find new file with suffix
  opendir my $dh, $arch_dir or die $!;
  my @cands = grep { /^b-FAIL\.\d+\.log$/ } readdir($dh);
  closedir $dh;
  ok(@cands >= 1, "created suffixed file for collision");
  my $newc = slurp(File::Spec->catfile($arch_dir, $cands[0]));
  is($newc, "NEW\n", "suffixed file contains new content");
}

done_testing();
