@copilot

## Goal

Fix the cross-language docstring validation contamination in the umbrella workflow by implementing **Route 2**: runner-level scoping via a **language selector** in the docstring validator.

Also: Update the umbrella workflow to **always** preserve logs (success OR failure) by uploading them as artifacts and committing them into the repo under the required path format.

---

## Part 1 — Docstring Validation Scoping (Route 2)

### 1) Add a language scope flag to the docstring validator

Update `scripts/validate_docstrings.py` to accept a language selector, e.g.:

- `--language python`
- `--language bash`
- `--language perl`
- `--language powershell`
- (optional) `--language all` as the default current behavior

Rules:

- `--language <lang>` MUST restrict scanning to that language’s files only (based on extensions and/or known directories).
- Deterministic in CI.
- Do NOT implement a “pass hundreds of --file args” approach as the primary solution.

### 2) Update repo_lint runners to call validator with language scoping

Update `tools/repo_lint` language runners so they invoke the validator like:

- Python runner -> `scripts/validate_docstrings.py --language python`
- Bash runner -> `... --language bash`
- Perl runner -> `... --language perl`
- PowerShell runner -> `... --language powershell`

### 3) Preserve contracts

Follow repo contracts strictly:

- `docs/epic-repo-lint-status.md`
- `docs/contributing/naming-and-style.md`

---

## Part 2 — Umbrella Workflow Logging + Repo Commit (Always)

### 4) Always capture logs from the umbrella workflow

Update the umbrella workflow so it **always** captures and persists logs from:

- Auto-Fix: Black
- Detect Changed Files
- Each language job (Python/Bash/PowerShell/Perl/YAML)
- Vector/Conformance tests
- Consolidate Failures

### 5) Required repo log path format

Commit logs to the repository at:

`/logs/umbrella-ci-logs-phase-6/YYYY-MM-DD-#######/.*`

Where:

- `YYYY-MM-DD` = run date (UTC is fine, but be consistent)
- `#######` = unique run identifier (prefer `GITHUB_RUN_ID` or `GITHUB_RUN_NUMBER`)
- Include all relevant output files (stdout/stderr captures, diffs, summaries, JSON if available)

### 6) Artifact upload is also required

Even though we commit logs, ALSO upload the same directory as a workflow artifact for easy download.

### 7) Commit behavior requirements

- Must run **regardless of success/failure** (`if: always()` for log gather + artifact + commit steps)
- Must not cause bot loops:
  - Do NOT create an infinite re-trigger cycle
  - Use your existing bot-loop guard patterns (actor + commit message marker) as needed
- Use minimal permissions:
  - `contents: write` only where required, scoped to the logging commit job/step
- If a commit cannot be performed (e.g., fork PR), then:
  - upload artifacts
  - and write a clear workflow summary message explaining why repo commit was skipped

---

## Verification (mandatory)

### A) Prove docstring scoping is correct

Run umbrella workflow (or equivalent local simulation) and confirm:

- Python runner reports ONLY Python docstring violations (no bash/perl/pwsh fixtures)
- Bash/Perl/PowerShell runners report ONLY their own language docstring violations

### B) Prove logs persist on both pass and fail

- Trigger a run that passes and confirm logs committed under the required path
- Trigger a run that fails and confirm logs are STILL committed under the required path
- Confirm artifact upload includes the same directory content

### C) Regression coverage

Add/update a test or vector check to fail if any runner reports docstring violations outside its language scope.

---

## Tracking (mandatory)

Update `docs/epic-repo-lint-status.md`:

- Mark the relevant Phase 6 sub-items `[x]` once verified
- Add 1–2 short notes: what changed + where

---

## Deliverable

Push commits that:

- implement `--language` scoping in `scripts/validate_docstrings.py`
- update each runner to use it
- update umbrella workflow to always persist logs (commit + artifact) in the required path
- add regression coverage
- ensure the umbrella workflow runs are now correct and auditable
