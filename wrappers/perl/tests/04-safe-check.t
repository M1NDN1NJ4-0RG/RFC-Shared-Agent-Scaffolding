
use strict;
use warnings;
use Test::More;
use File::Spec;
use File::Path qw(make_path);
use TestUtil qw(make_sandbox slurp write_file make_exe run_cmd);

my $sandbox = make_sandbox();
my $scripts_dir = File::Spec->catdir($sandbox, "scripts", "perl");
make_path($scripts_dir);

for my $pair (
  ["safe_run.pl", $ENV{SRC_SAFE_RUN}],
  ["safe_archive.pl", $ENV{SRC_SAFE_ARCHIVE}],
  ["safe_check.pl", $ENV{SRC_SAFE_CHECK}],
) {
  my ($name,$src) = @$pair;
  die "missing env for $name" unless $src;
  my $dst = File::Spec->catfile($scripts_dir, $name);
  write_file($dst, slurp($src));
  make_exe($dst);
}

make_path(File::Spec->catdir($sandbox, ".agent", "FAIL-LOGS"));
make_path(File::Spec->catdir($sandbox, ".agent", "FAIL-ARCHIVE"));

my $safe_check = File::Spec->catfile($scripts_dir, "safe_check.pl");
my $r = run_cmd(["perl", $safe_check], cwd=>$sandbox);
is($r->{exit}, 0, "safe-check passes in clean sandbox");
like($r->{stdout}, qr/OK:/, "prints OK lines");

done_testing();
