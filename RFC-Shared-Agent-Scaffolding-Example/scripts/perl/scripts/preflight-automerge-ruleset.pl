#!/usr/bin/env perl
# preflight-automerge-ruleset.pl (Perl)
# Verifies a GitHub Ruleset enforces required status checks on ~DEFAULT_BRANCH.
# Exit codes: 0 ok, 1 precheck fail, 2 auth/permission issue, 3 usage error.
# Security: never prints token values.

use strict;
use warnings;
use JSON::PP;
use HTTP::Tiny;
use Getopt::Long qw(GetOptions);

sub die_usage { print STDERR $_[0] . "\n"; exit 3; }
sub warn_msg { print STDERR "WARN: $_[0]\n"; }
sub info { print STDERR "INFO: $_[0]\n"; }

my ($repo, $ruleset_id, $ruleset_name, $want_json, $api_version);
$api_version = "2022-11-28";

sub usage {
  print STDERR <<"USAGE";
Usage:
  scripts/perl/preflight-automerge-ruleset.pl --repo OWNER/REPO [--ruleset-id ID | --ruleset-name NAME] --want '["lint","test"]'

Auth:
  Prefers gh api if available. Otherwise uses TOKEN or GITHUB_TOKEN env vars.
USAGE
  exit 3;
}

sub have_cmd {
  my ($cmd) = @_;
  for my $p (split(/:/, $ENV{PATH} // "")) { return 1 if -x "$p/$cmd"; }
  return 0;
}

sub gh_api {
  my ($endpoint) = @_;
  open(my $fh, "-|", "gh", "api",
       "-H", "Accept: application/vnd.github+json",
       "-H", "X-GitHub-Api-Version: $api_version",
       $endpoint) or return undef;
  my $json = do { local $/; <$fh> };
  close($fh);
  return $json;
}

sub http_get {
  my ($url) = @_;
  my $token = $ENV{TOKEN} // $ENV{GITHUB_TOKEN} // "";
  die_usage("No auth available: set TOKEN/GITHUB_TOKEN or authenticate with gh") if $token eq "";
  my $http = HTTP::Tiny->new();
  my $res = $http->get($url, {
    headers => {
      "Accept" => "application/vnd.github+json",
      "Authorization" => "token $token",
      "X-GitHub-Api-Version" => $api_version,
      "User-Agent" => "agent-ops-preflight",
    }
  });
  return $res;
}

sub parse_json {
  my ($s) = @_;
  my $json = JSON::PP->new->utf8->decode($s);
  return $json;
}

sub classify_auth {
  my ($obj) = @_;
  return 0 if ref($obj) ne 'HASH';
  my $m = $obj->{message} // "";
  return ($m =~ /(Bad credentials|Requires authentication|Resource not accessible|Forbidden|Must have admin rights|Not Found)/i) ? 1 : 0;
}

GetOptions(
  "repo=s" => \$repo,
  "ruleset-id=s" => \$ruleset_id,
  "ruleset-name=s" => \$ruleset_name,
  "want=s" => \$want_json,
  "api-version=s" => \$api_version,
  "help|h" => sub { usage() },
) or usage();

usage() if !$repo || !$want_json || (!$ruleset_id && !$ruleset_name);

my $want;
eval {
  $want = parse_json($want_json);
  1;
} or die_usage("--want must be a JSON array of strings");
die_usage("--want must be a JSON array") if ref($want) ne 'ARRAY';
for my $v (@$want) { die_usage("--want must be array of strings") if ref($v) ne ''; }

# Fetch rulesets list
my $rulesets_raw;
my $rulesets_obj;
if (have_cmd("gh")) {
  $rulesets_raw = gh_api("repos/$repo/rulesets");
  if (!defined $rulesets_raw) { warn_msg("Failed to call gh api"); exit 2; }
  eval { $rulesets_obj = parse_json($rulesets_raw); 1 } or do { warn_msg("Invalid JSON from gh"); exit 2; };
} else {
  my $res = http_get("https://api.github.com/repos/$repo/rulesets");
  if (!$res->{success}) {
    my $body = $res->{content} // "";
    my $obj = eval { parse_json($body) };
    if ($obj && classify_auth($obj)) { warn_msg("Auth/permission error while fetching rulesets"); exit 2; }
    warn_msg("Failed to fetch rulesets (HTTP $res->{status})");
    exit 1;
  }
  $rulesets_obj = parse_json($res->{content});
}

# Select ruleset id if by name
if (!$ruleset_id) {
  my $found;
  for my $rs (@$rulesets_obj) {
    next if ref($rs) ne 'HASH';
    if (($rs->{name} // "") eq $ruleset_name) { $found = $rs->{id}; last; }
  }
  die_usage("Ruleset not found by name: $ruleset_name") if !$found;
  $ruleset_id = $found;
}

# Fetch ruleset details
my $rs_raw;
my $rs_obj;
if (have_cmd("gh")) {
  $rs_raw = gh_api("repos/$repo/rulesets/$ruleset_id");
  if (!defined $rs_raw) { warn_msg("Failed to call gh api"); exit 2; }
  eval { $rs_obj = parse_json($rs_raw); 1 } or do { warn_msg("Invalid JSON from gh"); exit 2; };
} else {
  my $res = http_get("https://api.github.com/repos/$repo/rulesets/$ruleset_id");
  if (!$res->{success}) {
    my $body = $res->{content} // "";
    my $obj = eval { parse_json($body) };
    if ($obj && classify_auth($obj)) { warn_msg("Auth/permission error while fetching ruleset"); exit 2; }
    warn_msg("Failed to fetch ruleset (HTTP $res->{status})");
    exit 1;
  }
  $rs_obj = parse_json($res->{content});
}

# Enforcement must be active
my $enf = $rs_obj->{enforcement} // "";
if ($enf ne "active") {
  warn_msg("Ruleset enforcement is not active (enforcement=$enf)");
  exit 1;
}

# Must include ~DEFAULT_BRANCH
my $includes = $rs_obj->{conditions}{ref_name}{include} // [];
my $targets_default = 0;
if (ref($includes) eq 'ARRAY') {
  for my $v (@$includes) { $targets_default = 1 if ($v // "") eq "~DEFAULT_BRANCH"; }
}
if (!$targets_default) {
  warn_msg("Ruleset does not target ~DEFAULT_BRANCH");
  exit 1;
}

# Gather required contexts
my %got;
if (ref($rs_obj->{rules}) eq 'ARRAY') {
  for my $rule (@{$rs_obj->{rules}}) {
    next if ref($rule) ne 'HASH';
    next if ($rule->{type} // "") ne "required_status_checks";
    my $checks = $rule->{parameters}{required_status_checks} // [];
    next if ref($checks) ne 'ARRAY';
    for my $c (@$checks) {
      next if ref($c) ne 'HASH';
      my $ctx = $c->{context} // "";
      $got{$ctx} = 1 if $ctx ne "";
    }
  }
}

# Compare want - got
my @missing = grep { !$got{$_} } @$want;
if (@missing) {
  warn_msg("Ruleset missing required status check contexts");
  info("want: " . encode_json($want));
  info("got : " . encode_json([sort keys %got]));
  exit 1;
}

info("PRECHECK_OK: ruleset enforces required CI contexts on default branch; auto-merge flow is safe.");
exit 0;
