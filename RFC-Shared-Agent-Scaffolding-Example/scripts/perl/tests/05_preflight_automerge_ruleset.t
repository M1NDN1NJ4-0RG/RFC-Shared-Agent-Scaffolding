
use strict;
use warnings;
use Test::More;
use File::Spec;
use File::Path qw(make_path);
use TestUtil qw(make_sandbox slurp write_file make_exe run_cmd);

my $sandbox = make_sandbox();
my $scripts_dir = File::Spec->catdir($sandbox, "scripts", "perl");
make_path($scripts_dir);

my $src = $ENV{SRC_PREFLIGHT} || die "SRC_PREFLIGHT not set";
my $preflight = File::Spec->catfile($scripts_dir, "preflight_automerge_ruleset.pl");
write_file($preflight, slurp($src));
make_exe($preflight);

# Create a fake `gh` in PATH that returns JSON for expected endpoints.
my $bindir = File::Spec->catdir($sandbox, "bin");
make_path($bindir);
my $gh = File::Spec->catfile($bindir, "gh");

my $gh_script = <<'GH';
#!/usr/bin/env perl
use strict; use warnings;
my @a = @ARGV;

# Minimal fake `gh api <endpoint>`
# We intentionally ignore headers and --method, just look for endpoint.
if (@a >= 2 && $a[0] eq 'api') {
  # Skip over -H header arguments to find the actual endpoint
  my $i = 1;
  while ($i < @a && $a[$i] eq '-H') {
    $i += 2;  # Skip -H and its value
  }
  my $endpoint = $a[$i];
  if ($endpoint =~ m{^repos/([^/]+/[^/]+)/rulesets$}) {
    print qq([{"id": 123, "name": "Main - PR Only + Green CI"}]\n);
    exit 0;
  }
  if ($endpoint =~ m{^repos/([^/]+/[^/]+)/rulesets/123$}) {
    # Return a ruleset with required checks: lint and test
    print qq({
      "id":123,
      "name":"Main - PR Only + Green CI",
      "enforcement":"active",
      "conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"]}},
      "rules":[
        {"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"lint"},{"context":"test"}]}}
      ]
    }\n);
    exit 0;
  }
}
print "unexpected gh args: @a\n";
exit 2;
GH
write_file($gh, $gh_script);
make_exe($gh);

# 1) Success case
{
  my $r = run_cmd(
    ["perl", $preflight, "--repo", "OWNER/REPO", "--ruleset-name", "Main - PR Only + Green CI", "--want", '["lint","test"]'],
    cwd=>$sandbox,
    env=>{ PATH => "$bindir:$ENV{PATH}" }
  );
  is($r->{exit}, 0, "preflight succeeds when checks match");
  like($r->{stderr}, qr/OK:/, "prints OK");
}

# 2) Failure case: want includes missing check
{
  my $r = run_cmd(
    ["perl", $preflight, "--repo", "OWNER/REPO", "--ruleset-name", "Main - PR Only + Green CI", "--want", '["lint","test","build"]'],
    cwd=>$sandbox,
    env=>{ PATH => "$bindir:$ENV{PATH}" }
  );
  is($r->{exit}, 1, "preflight exits 1 when missing required check");
  like($r->{stderr}, qr/missing required status check/, "stderr explains missing checks");
}

# 3) Token secrecy: ensure token not echoed
{
  my $r = run_cmd(
    ["perl", $preflight, "--repo", "OWNER/REPO", "--ruleset-name", "Main - PR Only + Green CI", "--want", '["lint","test"]'],
    cwd=>$sandbox,
    env=>{ PATH => "$bindir:$ENV{PATH}", TOKEN => "SUPER_SECRET_TOKEN_VALUE" }
  );
  unlike($r->{stdout}.$r->{stderr}, qr/SUPER_SECRET_TOKEN_VALUE/, "token never printed");
}

done_testing();
