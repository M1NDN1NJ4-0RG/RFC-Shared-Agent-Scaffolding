@copilot

## Fix CI Scope + Unsafe Fixture Coverage (MANDATORY)

### 0) Context

CI must NOT lint/docstring-validate the purpose-built unsafe fixtures directory:
`conformance/repo-lint/unsafe-fix-fixtures/python/`

Right now CI is picking up files it should not. Also, only Python has unsafe-fix fixtures — we need parity scaffolding for the other languages.

---

## 1) Exclude unsafe-fix fixtures from the Umbrella CI workflow (MANDATORY)

Update the umbrella workflow(s) so **ALL lint/docstring jobs** ignore:

- `conformance/repo-lint/unsafe-fix-fixtures/**`

Do this in BOTH places:
A) **Workflow path filtering** (so jobs don’t run because of fixture-only changes)

- Add `paths-ignore` (or equivalent) so changes under that directory do not trigger language lint jobs.

B) **Repo-lint runner filtering** (so even if the job runs, the tool ignores fixtures)

- Ensure `tools.repo_lint` language runners (and/or docstring validator invocations) exclude the directory from file discovery.
- Use the repo’s existing ignore/selection mechanism; do NOT invent a new naming contract.

Acceptance criteria:

- If the only changes in a PR are under `conformance/repo-lint/unsafe-fix-fixtures/**`, the umbrella workflow should not run language lint jobs.
- If the umbrella workflow runs for other reasons, repo-lint must NOT report violations from unsafe-fix fixtures.

---

## 2) Add unsafe-fix fixtures scaffolding for ALL languages (MANDATORY)

Create the missing fixture dirs (even if minimal initially):

- `conformance/repo-lint/unsafe-fix-fixtures/bash/`
- `conformance/repo-lint/unsafe-fix-fixtures/perl/`
- `conformance/repo-lint/unsafe-fix-fixtures/powershell/`
- `conformance/repo-lint/unsafe-fix-fixtures/yaml/`
- `conformance/repo-lint/unsafe-fix-fixtures/rust/` (if unsafe mode will ever apply there)

For EACH language, add at least:

- 1 fixture file that should trigger an **unsafe** fixer (or a placeholder fixture if unsafe fixers aren’t implemented for that language yet)
- A short README.md in the language folder explaining:
  - these files are intentionally non-conforming
  - they are excluded from CI lint/docstring checks
  - they are used ONLY for unsafe-mode testing

Important:

- These fixtures MUST NOT cause CI lint/docstring failures.
- If unsafe mode isn’t implemented for a language yet, add the directory + README + a placeholder fixture file and document “TODO: unsafe fixers not implemented yet”.

---

## 3) Update tests to use fixtures correctly (MANDATORY)

- Ensure unit/integration tests for unsafe mode use ONLY these fixture dirs and/or temporary workspaces.
- Do NOT run unsafe mode on real repository code.
- Add/adjust tests to confirm:
  - fixtures are excluded from `repo_lint check --ci`
  - unsafe tests still execute against fixtures locally

---

## 4) Required reporting (MANDATORY)

In the PR update comment, include:

- What workflow files were changed (paths-ignore + where)
- What repo-lint filtering was changed (what excludes where)
- List of newly added fixture directories/files per language
- Proof via commands or CI links that fixture-only changes do not trigger lint jobs and do not produce violations

Run before you stop:

- `python -m tools.repo_lint check --ci`
- full repo_lint test suite
