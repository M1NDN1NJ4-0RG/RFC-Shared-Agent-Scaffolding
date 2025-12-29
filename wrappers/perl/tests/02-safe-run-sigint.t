
use strict;
use warnings;
use Test::More;
use File::Spec;
use File::Path qw(make_path);
use TestUtil qw(make_sandbox slurp write_file make_exe);

require IPC::Open3;
require IO::Select;
require Symbol;

my $sandbox = make_sandbox();
my $scripts_dir = File::Spec->catdir($sandbox, "scripts", "perl");
make_path($scripts_dir);

my $src = $ENV{SRC_SAFE_RUN} || die "SRC_SAFE_RUN not set";
my $safe_run = File::Spec->catfile($scripts_dir, "safe_run.pl");
write_file($safe_run, slurp($src));
make_exe($safe_run);

my $log_dir  = File::Spec->catdir($sandbox, ".agent", "FAIL-LOGS");
make_path($log_dir);

# Set environment for safe-run to use the sandbox log directory
$ENV{SAFE_LOG_DIR} = $log_dir;

sub list_logs {
  opendir my $dh, $log_dir or die "opendir: $!";
  my @f = grep { /\.log$/ && -f File::Spec->catfile($log_dir,$_) } readdir($dh);
  closedir $dh;
  return sort @f;
}

# Spawn safe-run running a longish command that prints lines slowly.
my $err = Symbol::gensym();
my $pid = IPC::Open3::open3(my $in, my $out, $err,
  "perl", $safe_run, "--",
  "perl", "-e",
  '$|=1; for(my $i=1;$i<=100;$i++){print "tick$i\n"; select(undef,undef,undef,0.05);} exit 0;'
);
close $in;

# Wait until some output observed, then send SIGINT to wrapper.
my $sel = IO::Select->new($out);
my $seen = 0;
my $buf = "";
my $start = time();
while (time() - $start < 3) {
  my @r = $sel->can_read(0.1);
  next unless @r;
  my $n = sysread($out, my $tmp, 4096);
  last if !defined $n || $n == 0;
  $buf .= $tmp;
  if ($buf =~ /tick[1-9]/) { $seen = 1; last; }
}
ok($seen, "saw some output before interrupting");

kill 'INT', $pid;

# Drain streams and wait
while (waitpid($pid, 0) == -1) { }

my $exit = $? >> 8;
my $sig  = $? & 127;

# The wrapper should exit non-zero due to signal, but more importantly it should write ABORTED log.
my @logs = list_logs();
ok(@logs == 1, "one log produced on SIGINT");
like($logs[0], qr/ABORTED/i, "log name includes ABORTED suffix");
my $content = slurp(File::Spec->catfile($log_dir, $logs[0]));
like($content, qr/tick[1-9]/, "log contains partial output");

done_testing();
