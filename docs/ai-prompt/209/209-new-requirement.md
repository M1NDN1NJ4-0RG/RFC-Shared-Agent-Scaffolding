@copilot **MANDATORY NEXT TASK: WRITE EXTREMELY COMPREHENSIVE TESTS FOR THE BOOTSTRAPPER.**
UPDATES GO: `docs/ai-prompt/209/*` ISSUE: <https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues/209> IS WHAT WE'RE WORKING ON!

## Scope (what you are testing)

The bootstrapper script (the session-start toolchain bootstrapper you just added/updated), e.g.:

- `scripts/bootstrap-repo-lint-toolchain.sh` (or the canonical bootstrapper path in this repo)

## Requirements (no wiggle room)

1) **Add a full test suite** that validates the bootstrapper end-to-end behavior, not just “unit-ish” helper functions.
2) Tests must be **repeatable, deterministic, and runnable in CI** (non-interactive, no hanging). 3) Tests must cover
**success paths AND failure paths**, including clear assertions on: - exit codes - stdout/stderr content (key lines) -
created files/dirs (venv dirs, caches, etc.) - PATH / environment effects (only where intended)

## Minimum test coverage (MANDATORY)

### A) Repo root discovery

- - Running from repo root succeeds - Running from nested subdir succeeds - Running outside repo fails with expected
  exit code and message

### B) Venv creation + activation

- Creates `.venv/` when missing
- Reuses `.venv/` when present (idempotent)
- - Fails cleanly if venv cannot be created

### C) repo-cli installation + PATH availability

- - Installs repo-cli package in venv (or verifies already installed)
- `repo-cli --help` succeeds after bootstrap
- - Fails cleanly if install fails (expected exit code + message)

### D) Tool detection logic

For each required tool, tests must cover:

- - “already installed” path - “missing tool” path triggers installation attempt OR explicit failure message (depending
  on environment capability) Tools list: - rgrep (or fallback behavior) - black, pylint, pytest, ruff, yamllint -
  shellcheck, shfmt - pwsh + PSScriptAnalyzer - Perl::Critic + PPI

### E) End-to-end verification gate

- Bootstrapper must run `repo-cli check --ci` (or the configured gate) and:
  - - Pass scenario: exits 0 - Fail scenario: exits non-zero with actionable output

### F) Safety / non-interactive behavior

- - No prompts in CI mode
- No `sudo`/package-manager installs attempted during unit tests unless explicitly mocked/sandboxed
  (Tests should mock these calls and assert the script *would* invoke them.)

## Implementation instructions

- Create a dedicated test directory, e.g. `tools/repo_lint/tests_bootstrapper/` or `tests/bootstrapper/`.
- Use a test runner that already exists in the repo (prefer `pytest`).
- - Use fixtures that create a temporary fake repo layout where needed.
- For external commands, use **mocking** (e.g., patch `PATH` to point at stub executables) so tests do not depend on the host machine.
- - Add CI job(s) to run these tests.

## Deliverables (MANDATORY)

1) New test files + fixtures + stubs 2) CI wired to run them 3) In your PR comment, include: - the exact test command(s)
- a list of test cases added - proof the suite passes

Do not commit until the bootstrapper tests exist and PASS.
