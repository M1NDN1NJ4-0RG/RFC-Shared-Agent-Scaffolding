# Internal Symbol Naming Analysis

**Generated:** 2025-12-29
**Phase:** 4.2 - Internal Symbol Deviation Report

## Python Symbol Analysis

Checking Python functions (should be snake_case)...


## PowerShell Symbol Analysis

Checking PowerShell functions (should be PascalCase Verb-Noun)...


## Bash Symbol Analysis

Checking Bash variables (constants should be UPPER_SNAKE_CASE, locals should be lower_snake_case)...

*Note: This is a basic check for obvious violations. Manual review recommended.*


## Perl Symbol Analysis

Checking Perl conventions (to be finalized)...

Perl subroutines found:
```
wrappers/perl/scripts/preflight-automerge-ruleset.pl:458:sub die_usage { print STDERR $_[0] . "\n"; exit 3; }
wrappers/perl/scripts/preflight-automerge-ruleset.pl:459:sub warn_msg { print STDERR "WARN: $_[0]\n"; }
wrappers/perl/scripts/preflight-automerge-ruleset.pl:460:sub info { print STDERR "INFO: $_[0]\n"; }
wrappers/perl/scripts/preflight-automerge-ruleset.pl:465:sub usage {
wrappers/perl/scripts/preflight-automerge-ruleset.pl:476:sub have_cmd {
wrappers/perl/scripts/preflight-automerge-ruleset.pl:482:sub gh_api {
wrappers/perl/scripts/preflight-automerge-ruleset.pl:493:sub http_get {
wrappers/perl/scripts/preflight-automerge-ruleset.pl:509:sub parse_json {
wrappers/perl/scripts/preflight-automerge-ruleset.pl:515:sub classify_auth {
wrappers/perl/scripts/safe-archive.pl:322:sub die_msg { print STDERR "ERROR: $_[0]\n"; exit 1; }
```

*Manual review needed to determine conventions.*

## Summary

✅ **Python**: Functions appear to follow snake_case convention
✅ **PowerShell**: Functions appear to follow PascalCase/Verb-Noun convention
✅ **Bash**: Variables appear to follow UPPER_SNAKE_CASE/lower_snake_case convention
⚠️ **Perl**: Conventions need to be documented and enforced in Phase 4.4.4
