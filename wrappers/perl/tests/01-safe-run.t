
use strict;
use warnings;
use Test::More;
use File::Spec;
use File::Path qw(make_path);
use TestUtil qw(make_sandbox run_cmd slurp write_file make_exe);

my $sandbox = make_sandbox();
my $scripts_dir = File::Spec->catdir($sandbox, "scripts", "perl");
make_path($scripts_dir);

# Copy safe_run.pl
{
  my $src = $ENV{SRC_SAFE_RUN} || die "SRC_SAFE_RUN not set";
  my $dst = File::Spec->catfile($scripts_dir, "safe_run.pl");
  write_file($dst, slurp($src));
  make_exe($dst);
}

my $safe_run = File::Spec->catfile($scripts_dir, "safe_run.pl");
my $log_dir  = File::Spec->catdir($sandbox, ".agent", "FAIL-LOGS");
make_path($log_dir);

sub list_logs {
  opendir my $dh, $log_dir or die "opendir: $!";
  my @f = grep { /\.log$/ && -f File::Spec->catfile($log_dir,$_) } readdir($dh);
  closedir $dh;
  return sort @f;
}

# 1) Success: no artifacts
{
  my $r = run_cmd(["perl", $safe_run, "--", "perl", "-e", "print qq(hi\\n);"], cwd=>$sandbox, env=>{ SAFE_LOG_DIR => $log_dir });
  is($r->{exit}, 0, "success exit code 0");
  is_deeply([list_logs()], [], "success creates no fail logs");
}

# 2) Failure: preserves exit and writes log with both stdout+stderr
{
  my $r = run_cmd(["perl", $safe_run, "--", "perl", "-e", 'print "OUT\n"; warn "ERR\n"; exit 7;'], cwd=>$sandbox, env=>{ SAFE_LOG_DIR => $log_dir });
  is($r->{exit}, 7, "failure preserves exit code");

  my @logs = list_logs();
  ok(@logs == 1, "one fail log created");
  my $content = slurp(File::Spec->catfile($log_dir, $logs[0]));
  like($content, qr/OUT/, "log contains stdout");
  like($content, qr/ERR/, "log contains stderr");
}

# 3) Snippet lines: SAFE_SNIPPET_LINES prints tail to stderr on failure
{
  # Clear logs
  unlink File::Spec->catfile($log_dir, $_) for list_logs();

  my $prog = join("", map { "print qq(line$_\\n);" } (1..30)) . "exit 3;";
  my $r = run_cmd(["perl", $safe_run, "--", "perl", "-e", $prog], cwd=>$sandbox, env=>{ SAFE_LOG_DIR => $log_dir, SAFE_SNIPPET_LINES => 5 });
  is($r->{exit}, 3, "exit preserved");
  like($r->{stderr}, qr/line26.*line30/s, "stderr includes tail snippet lines");
  ok(-e File::Spec->catfile($log_dir, (list_logs())[0]), "fail log still created");
}

# 4) Large output: should not OOM; ensure log exists and includes last line
{
  unlink File::Spec->catfile($log_dir, $_) for list_logs();

  my $big = 'for(my $i=0;$i<200000;$i++){print "x"x50 . "\n";} print "THE_END\n"; exit 9;';
  my $r = run_cmd(["perl", $safe_run, "--", "perl", "-e", $big], cwd=>$sandbox, env=>{ SAFE_LOG_DIR => $log_dir }, timeout_sec=>30);
  is($r->{exit}, 9, "large output preserves exit");
  my @logs = list_logs();
  ok(@logs == 1, "large output produced one log");
  my $content = slurp(File::Spec->catfile($log_dir, $logs[0]));
  like($content, qr/THE_END/, "log contains last marker");
}

# 5) Event ledger: should emit events with sequence numbers
{
  unlink File::Spec->catfile($log_dir, $_) for list_logs();

  my $r = run_cmd(["perl", $safe_run, "--", "perl", "-e", 'print "out1\n"; warn "err1\n"; print "out2\n"; exit 5;'], cwd=>$sandbox, env=>{ SAFE_LOG_DIR => $log_dir });
  is($r->{exit}, 5, "exit code preserved");
  
  my @logs = list_logs();
  ok(@logs == 1, "one fail log created");
  my $content = slurp(File::Spec->catfile($log_dir, $logs[0]));
  
  # Check for event ledger markers
  like($content, qr/--- BEGIN EVENTS ---/, "log contains event ledger start marker");
  like($content, qr/--- END EVENTS ---/, "log contains event ledger end marker");
  
  # Check for standardized META events
  like($content, qr/\[SEQ=1\]\[META\] safe-run start: cmd=/, "log contains META start event with SEQ=1");
  like($content, qr/\[META\] safe-run exit: code=5/, "log contains META exit event");
  
  # Check for stdout/stderr events
  like($content, qr/\[STDOUT\] out1/, "log contains STDOUT event for out1");
  like($content, qr/\[STDOUT\] out2/, "log contains STDOUT event for out2");
  like($content, qr/\[STDERR\] err1/, "log contains STDERR event for err1");
}

# 6) Merged view: should emit merged view when SAFE_RUN_VIEW=merged
{
  unlink File::Spec->catfile($log_dir, $_) for list_logs();

  my $r = run_cmd(["perl", $safe_run, "--", "perl", "-e", 'print "line1\n"; exit 3;'], cwd=>$sandbox, env=>{ SAFE_LOG_DIR => $log_dir, SAFE_RUN_VIEW => 'merged' });
  is($r->{exit}, 3, "exit code preserved");
  
  my @logs = list_logs();
  ok(@logs == 1, "one fail log created");
  my $content = slurp(File::Spec->catfile($log_dir, $logs[0]));
  
  # Check for merged view markers
  like($content, qr/--- BEGIN MERGED \(OBSERVED ORDER\) ---/, "log contains merged view start marker");
  like($content, qr/--- END MERGED ---/, "log contains merged view end marker");
  
  # Check for merged view format with [#seq]
  like($content, qr/\[#1\]\[META\]/, "log contains merged event #1 (META start)");
  like($content, qr/\[#2\]\[STDOUT\] line1/, "log contains merged event #2 (STDOUT)");
}

done_testing();
