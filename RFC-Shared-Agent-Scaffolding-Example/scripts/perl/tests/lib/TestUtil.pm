
package TestUtil;
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
