@copilot

## Goal

Verify (and fix if needed) the **functional correctness** of the umbrella workflow: **Repo Lint and Docstring
Enforcement**.

Right now the workflow runs:

- - - ✅ Auto-Fix: Black - ✅ Detect Changed Files - ⏭️ Skips all language jobs - ✅ Consolidate Failures

This is **not acceptable** until we prove skipping is correct and the workflow reliably triggers the intended language
jobs when it should.

---

## A) Verify umbrella gating behavior (mandatory)

### 1) Confirm why language jobs are being skipped

In the umbrella workflow logs:

- - - Inspect outputs from **Detect Changed Files** - Confirm which bucket outputs are `true/false`
  (python/bash/powershell/perl/yaml/shared_tooling) - - Identify whether the skip is correct (no relevant files changed)
  OR a bug in path detection/globs/git diff base ref handling.

If it’s a bug, fix it:

- - - Ensure changed-file detection works correctly for: - PRs from same repo - PRs from forks (read-only behavior) -
  pushes to branches (if applicable) - Ensure it compares the correct refs (e.g., merge-base / PR base SHA) and not an
  empty diff.

---

## B) Fix the confusing status semantics (mandatory)

### 2) “Repo Lint: <Lang>” must FAIL when violations exist

Currently it appears the per-language jobs may be:

- - - Treating “violations found” as success, which is backwards for CI readability.

Update the umbrella workflow + repo_lint runner invocation so that:

- - - If lint/docstring violations exist, the job **exits non-zero** and the job shows **Failed** (red). - Only true
  clean runs should be green.

Constraints:

- - If you still want a “consolidate failures” step, it must run with `if: always()` so it still executes after
  failures.

---

## C) Add deterministic “violation fixtures” to test triggering + failure paths (mandatory)

### 3) Create per-language intentionally-bad fixture files (must be non-auto-fixable)

Create **five** files per language that are guaranteed to violate lint/docstring rules and are NOT auto-fixable by
Black/Ruff/shfmt/etc.

Place them under the existing conformance pattern (preferred) so they’re clearly fixtures, not product code. Example
directory (adjust if repo already has a better one):

- - `conformance/repo_lint/fixtures/violations/<language>/`

For each language, include cases that trigger:

- - - Docstring contract violation (missing required fields/sections) - A linter rule violation that is NOT auto-fixable
  - A “structure” or “contract” violation if applicable

Languages:

- - - Python - Bash - PowerShell - Perl - YAML (including a workflow YAML case if your yamllint checks those)

### 4) Add a CI-only validation mode for fixtures

We need a reliable way to force each language job to run and fail to prove the workflow works.

Implement one (choose the smallest correct option):

- - Option A (preferred): Add a workflow_dispatch input `force_all=true` that makes all language jobs run regardless of
  changed files. - Option B: Add a dedicated branch/path (fixtures dir) that sets `shared_tooling=true` or sets the
  relevant bucket true.

Either way, document it briefly in the workflow file comments.

---

## D) Validate the whole thing end-to-end (mandatory)

### 5) Prove the umbrella workflow behaves correctly

Do these tests in the PR:

1) Make a change touching ONLY a Python file → only Python job runs (plus shared_tooling if applicable) 2) Make a change
touching ONLY Markdown → only Detect + Consolidate run (no language jobs) 3) Make a change in the new violation fixtures
dir with `force_all` or equivalent → all relevant jobs run and FAIL (red) as expected

For each test, capture the run links in a short markdown verification note (repo conventions).

---

## E) Tracking + contracts (mandatory)

- - - Follow naming/contracts: - `docs/epic-repo-lint-status.md` - `docs/contributing/naming-and-style.md` - Update
  `docs/epic-repo-lint-status.md` to reflect verification + fixes (mark items `[x]`, add 1–2 short notes).

---

## Success criteria (non-negotiable)

- - - Language jobs trigger correctly based on changed files - Violations cause job failures (red), not “Succeeded” -
  Consolidate Failures still runs via `if: always()` - - We can force-run all language jobs deterministically for
  verification - Fixtures exist to prove failure paths are exercised
