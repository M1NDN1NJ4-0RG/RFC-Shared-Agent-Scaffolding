# Auto-Merge Preflight Checklist

**Status:** Mandatory before enabling auto-merge on any PR.
**Load:** Before enabling auto-merge on a PR.

---

## Purpose

The preflight validates that:

1. Required CI checks are configured in the repository ruleset
2. The PR will not be merged prematurely (before CI completes)
3. Auto-merge is safe for this repository and branch

**Failure to run preflight = Risk of merging broken code.**

---

## Preflight Command

Use the `preflight_automerge_ruleset` script from the appropriate language bundle:

```bash
# Bash
./scripts/bash/preflight_automerge_ruleset.sh \
  --repo <owner/repo> \
  --ruleset-name "<ruleset-name>" \
  --want '["ci-check-1", "ci-check-2"]'

# Python 3
python3 ./scripts/python3/scripts/preflight_automerge_ruleset.py \
  --repo <owner/repo> \
  --ruleset-name "<ruleset-name>" \
  --want '["ci-check-1", "ci-check-2"]'

# Perl
perl ./scripts/perl/scripts/preflight_automerge_ruleset.pl \
  --repo <owner/repo> \
  --ruleset-name "<ruleset-name>" \
  --want '["ci-check-1", "ci-check-2"]'

# PowerShell
pwsh ./scripts/powershell/preflight_automerge_ruleset.ps1 \
  -Repo <owner/repo> \
  -RulesetName "<ruleset-name>" \
  -Want '["ci-check-1", "ci-check-2"]'
```

---

## Required Inputs

### `--repo` (required)

Format: `owner/repository`
Example: `M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding`

### `--ruleset-name` (required)

The exact name of the repository ruleset to validate.
Example: `Main - PR Only + Green CI`

### `--want` (required)

JSON array of required status check contexts.
Example: `'["lint", "test", "build"]'`

**How to determine required checks:**

1. Review `.github/workflows/*.yml` files
2. List all workflow job names that must pass before merge
3. Include them in the `--want` array

---

## Exit Codes

| Code | Meaning | Action |
| ------ | --------- | -------- |
| 0 | Success - All required checks present in ruleset | Proceed with auto-merge |
| 2 | Auth/permission error (401, 403) | Check GITHUB_TOKEN |
| 3 | Ruleset not found or validation error | Fix inputs, check ruleset name |
| 50-59 | Ruleset/policy error (missing required context) | Add missing check to ruleset or --want |

See M0-P2-I2 exit code taxonomy for full reference.

---

## Authentication

Preflight requires a GitHub token with `repo` scope.

**Auth precedence:**

1. `--token` CLI argument (highest priority)
2. `GITHUB_TOKEN` environment variable
3. `TOKEN` environment variable
4. `gh auth token` command output (if `gh` CLI available)

**Validation:**

- Token is never logged or printed
- Auth failure returns exit code 2
- Clear error message indicates which auth method to use

See M0-P2-I1 for auth contract details.

---

## Preflight Checklist

Before enabling auto-merge, verify:

- [ ] Preflight script executed successfully (exit code 0)
- [ ] All required CI checks listed in `--want` array
- [ ] Ruleset name matches exactly (case-sensitive)
- [ ] Repository name in `owner/repo` format
- [ ] GitHub token has sufficient permissions
- [ ] `.agent/auto-merge.enabled` feature flag created (if using feature flags)

---

## What Preflight Validates

### ✅ Checks Performed

1. **Ruleset exists:** Ruleset with specified name is configured
2. **Ruleset is active:** Enforcement is `active` (not `disabled` or `evaluate`)
3. **Required status checks rule:** Ruleset contains `required_status_checks` rule
4. **All contexts present:** Every context in `--want` is present in ruleset
5. **Auth works:** GitHub API responds with valid data (not 401/403)

### ❌ NOT Checked

- Whether CI workflows are actually running
- Whether checks will pass
- Whether PR is ready to merge
- Whether branch is up-to-date

**Preflight only validates the ruleset configuration, not PR readiness.**

---

## Common Failures

### "Ruleset not found"

**Cause:** Ruleset name doesn't match exactly (case-sensitive).
**Fix:** Check exact ruleset name in GitHub repo settings > Rules > Rulesets.

### "Missing required context: test"

**Cause:** `--want` includes `"test"` but ruleset doesn't require it.
**Fix:** Either add `test` to ruleset or remove from `--want` array.

### "Auth failure: Bad credentials"

**Cause:** Invalid or missing GitHub token.
**Fix:** Set valid `GITHUB_TOKEN` environment variable or use `gh auth login`.

---

## After Preflight Success

**You may now:**

1. Enable auto-merge on the PR: `gh pr merge --auto --squash <PR-number>`
2. Wait for CI (using `21_AUTO_MERGE_WAITING.md` constants)
3. Monitor for merge completion

**Do not:**

- Skip preflight and enable auto-merge blindly
- Assume CI will block merges (it won't without ruleset validation)

---

**Version:** 1.0
**Last Updated:** 2025-12-26
**Refs:** RFC v0.1.0 section 5.3, M0-P2-I1, M0-P2-I2
