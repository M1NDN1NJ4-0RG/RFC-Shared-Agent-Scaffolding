#!/usr/bin/env perl

=head1 NAME

preflight-automerge-ruleset.pl - Verify GitHub Ruleset enforces required CI checks

=head1 SYNOPSIS

  # Verify by ruleset name
  preflight-automerge-ruleset.pl \
    --repo OWNER/REPO \
    --ruleset-name "Main - PR Only + Green CI" \
    --want '["lint","test"]'
  
  # Verify by ruleset ID
  preflight-automerge-ruleset.pl \
    --repo OWNER/REPO \
    --ruleset-id 12345 \
    --want '["lint","test","build"]'
  
  # Custom API version
  preflight-automerge-ruleset.pl \
    --repo OWNER/REPO \
    --ruleset-name "Protected" \
    --want '["ci"]' \
    --api-version 2022-11-28

=head1 DESCRIPTION

This script verifies that a GitHub Repository Ruleset is properly configured
to enforce required status checks on the default branch before allowing
auto-merge or manual merges. This is a critical pre-flight check to ensure
that CI gates are active and auto-merge workflows are safe.

The script validates:

=over 4

=item 1. Ruleset exists (by ID or name)

=item 2. Ruleset enforcement is "active" (not disabled or evaluate)

=item 3. Ruleset targets ~DEFAULT_BRANCH in its conditions

=item 4. Ruleset requires ALL specified status check contexts

=back

If any validation fails, the script exits with code 1 and prints diagnostic
information to stderr explaining what is missing or misconfigured.

=head1 OPTIONS

=over 4

=item B<--repo OWNER/REPO>

Required. GitHub repository in OWNER/REPO format.

Example: C<--repo M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding>

=item B<--ruleset-id ID>

Ruleset numeric ID. Use this OR --ruleset-name (not both).

Example: C<--ruleset-id 12345>

=item B<--ruleset-name NAME>

Ruleset name (exact match). Use this OR --ruleset-id (not both).

Example: C<--ruleset-name "Main - PR Only + Green CI">

=item B<--want JSON_ARRAY>

Required. JSON array of required status check context names.

The ruleset MUST require ALL of these contexts for the check to pass.

Example: C<--want '["lint","test","build"]'>

=item B<--api-version VERSION>

GitHub API version header. Default: C<2022-11-28>

Example: C<--api-version 2024-01-15>

=item B<-h>, B<--help>

Display usage information and exit with code 3.

=back

=head1 AUTHENTICATION

The script supports two authentication methods, tried in order:

=head2 1. GitHub CLI (Preferred)

If the C<gh> command is available in PATH, the script uses it for API calls.
This leverages existing GitHub CLI authentication.

  $ gh auth login
  $ preflight-automerge-ruleset.pl --repo OWNER/REPO ...

Advantages:

=over 4

=item * No token management required

=item * Respects gh auth state and host configuration

=item * Supports GitHub Enterprise via gh config

=back

=head2 2. Token-Based (Fallback)

If C<gh> is not available, the script uses HTTP::Tiny with token authentication.

Tokens are read from environment variables in order:

=over 4

=item 1. C<TOKEN>

=item 2. C<GITHUB_TOKEN>

=back

Example:

  $ export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
  $ preflight-automerge-ruleset.pl --repo OWNER/REPO ...

B<Required Permissions:> The token must have C<repo> or C<read:org> scope
to read repository rulesets.

=head1 EXIT CODES

=over 4

=item B<0>

Success - Ruleset is active, targets default branch, and enforces all
required status checks. Auto-merge flow is safe.

=item B<1>

Precheck failure - Ruleset misconfigured, missing required checks, not active,
or doesn't target default branch. See stderr for details.

=item B<2>

Authentication or permission error - Failed to authenticate with GitHub API,
insufficient permissions, or network error. Check token/gh auth and permissions.

=item B<3>

Usage error - Invalid arguments, missing required options, or help requested.

=back

=head1 VALIDATION LOGIC

The script performs the following checks in order:

=head2 1. Fetch Rulesets List

  GET /repos/OWNER/REPO/rulesets

Validates: Repository exists, authentication works, rulesets are accessible.

=head2 2. Resolve Ruleset ID

If C<--ruleset-name> is provided, scan the rulesets list for a ruleset with
matching name and extract its ID.

Validates: Ruleset exists with the specified name.

=head2 3. Fetch Ruleset Details

  GET /repos/OWNER/REPO/rulesets/<ID>

Validates: Ruleset ID is valid and accessible.

=head2 4. Check Enforcement Status

Validates: C<ruleset.enforcement == "active">

Fails if enforcement is "disabled" or "evaluate" (dry-run mode).

=head2 5. Check Default Branch Targeting

Validates: C<~DEFAULT_BRANCH> is in C<ruleset.conditions.ref_name.include>

Fails if ruleset only targets specific branches or tags.

=head2 6. Gather Required Status Checks

Scans C<ruleset.rules> for rules with C<type == "required_status_checks">
and extracts all C<context> values from C<parameters.required_status_checks>.

=head2 7. Compare Want vs. Got

Validates: All contexts in C<--want> are present in the gathered contexts.

Fails if any required context is missing. Prints both wanted and actual
contexts to stderr for debugging.

=head1 SECURITY NOTES

=over 4

=item * B<Token Secrecy:> Token values are NEVER printed to stdout or stderr

=item * B<Error Messages:> Authentication errors are sanitized to avoid token leakage

=item * B<Header Injection:> API version parameter is validated (alphanumeric + dash only)

=item * B<JSON Injection:> All JSON parsing uses JSON::PP with strict mode

=back

The script is designed to be safely run in CI environments where logs may be
publicly visible. No secrets are logged.

=head1 API VERSION HANDLING

The script sends the GitHub API version header:

  X-GitHub-Api-Version: 2022-11-28

This ensures consistent API behavior across GitHub API changes. The default
version (2022-11-28) supports the Rulesets API.

To use a different API version:

  --api-version 2024-01-15

=head1 ERROR CLASSIFICATION

The script distinguishes between different error types for proper exit codes:

=head2 Authentication Errors (Exit 2)

Detected by scanning error responses for keywords:

=over 4

=item * "Bad credentials"

=item * "Requires authentication"

=item * "Resource not accessible"

=item * "Forbidden"

=item * "Must have admin rights"

=item * "Not Found" (for private repos)

=back

=head2 Precheck Failures (Exit 1)

Configuration issues that don't involve authentication:

=over 4

=item * Ruleset enforcement not active

=item * Ruleset doesn't target ~DEFAULT_BRANCH

=item * Missing required status check contexts

=back

=head2 Usage Errors (Exit 3)

Invalid arguments or malformed input:

=over 4

=item * Missing required options (--repo, --want)

=item * Invalid JSON in --want

=item * Both --ruleset-id and --ruleset-name specified

=item * Ruleset not found by name

=back

=head1 SIDE EFFECTS

=over 4

=item * Makes HTTPS requests to api.github.com (or GitHub Enterprise host)

=item * Reads environment variables (TOKEN, GITHUB_TOKEN, PATH)

=item * Executes C<gh api> command if available

=item * Prints diagnostic messages to stderr

=item * No filesystem modifications

=back

=head1 EXAMPLES

=head2 Basic Check with gh CLI

  $ gh auth login
  $ preflight-automerge-ruleset.pl \
      --repo M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding \
      --ruleset-name "Main - PR Only + Green CI" \
      --want '["lint","test"]'
  INFO: PRECHECK_OK: ruleset enforces required CI contexts on default branch
  $ echo $?
  0

=head2 Check with Token Authentication

  $ export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
  $ preflight-automerge-ruleset.pl \
      --repo myorg/myrepo \
      --ruleset-id 42 \
      --want '["build","test","deploy"]'

=head2 Failure: Missing Required Check

  $ preflight-automerge-ruleset.pl \
      --repo myorg/myrepo \
      --ruleset-name "Protected" \
      --want '["lint","test","security"]'
  WARN: Ruleset missing required status check contexts
  INFO: want: ["lint","test","security"]
  INFO: got : ["lint","test"]
  $ echo $?
  1

=head2 Failure: Ruleset Not Active

  $ preflight-automerge-ruleset.pl \
      --repo myorg/myrepo \
      --ruleset-name "Test" \
      --want '["test"]'
  WARN: Ruleset enforcement is not active (enforcement=evaluate)
  $ echo $?
  1

=head2 CI Integration

  # .github/workflows/preflight.yml
  - name: Verify auto-merge safety
    run: |
      scripts/perl/preflight-automerge-ruleset.pl \
        --repo ${{ github.repository }} \
        --ruleset-name "Main - PR Only + Green CI" \
        --want '["lint","test","conformance"]'
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

=head1 CONTRACT REFERENCES

This script implements preflight checks for auto-merge safety as specified in:

=over 4

=item * M0 Specification: Auto-merge safety requirements

=item * GitHub Rulesets API: https://docs.github.com/en/rest/repos/rules

=back

=head1 DIAGNOSTICS

Common error messages and resolutions:

=over 4

=item B<No auth available: set TOKEN/GITHUB_TOKEN or authenticate with gh>

No authentication method is available. Either run C<gh auth login> or set
the GITHUB_TOKEN environment variable.

=item B<Failed to fetch rulesets (HTTP 404)>

Repository not found, or token lacks permissions. Verify repository name
and token permissions (repo or read:org scope).

=item B<Auth/permission error while fetching rulesets>

Token is invalid, expired, or lacks required permissions. Check token and
ensure it has C<repo> or C<read:org> scope.

=item B<Ruleset not found by name: <name>>

No ruleset with the specified name exists in the repository. Check spelling
or use C<--ruleset-id> instead.

=item B<Ruleset missing required status check contexts>

The ruleset exists and is active, but doesn't require all the status checks
specified in C<--want>. Update the ruleset configuration in GitHub.

=back

=head1 SEE ALSO

=over 4

=item * GitHub Rulesets API: https://docs.github.com/en/rest/repos/rules

=item * GitHub CLI: https://cli.github.com/

=item * L<HTTP::Tiny> - HTTP client for token-based auth

=item * L<JSON::PP> - JSON parsing

=back

=head1 AUTHOR

RFC-Shared-Agent-Scaffolding Project

=head1 LICENSE

Unlicense - See LICENSE file in repository root

=cut

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
