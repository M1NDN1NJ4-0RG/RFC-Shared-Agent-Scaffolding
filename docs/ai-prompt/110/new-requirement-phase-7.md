@copilot

## Implement “Unsafe Fix Mode” for repo_lint (MANDATORY)

Add an **explicitly dangerous** optional fix mode to `tools.repo_lint` that can apply “unsafe” transformations locally,
but is **never allowed in CI**.

This pattern MUST be implemented in a way that can scale to unsafe fixers for multiple languages/tools: **Python / Perl
/ YAML / PowerShell / Bash / Rust**.

---

## 0) NEW CONTRACT: AI Constraints (MANDATORY)

Create (or extend an existing) contract doc that explicitly governs AI/agent behavior for dangerous commands.

### Requirements

- - - If a suitable contract already exists under `docs/contributing/` (contracts/agent rules), extend it. - - Otherwise
  create a new contract file under the repo’s contract docs area (follow naming conventions), e.g.: -
  `docs/contributing/ai-constraints.md` (ONLY if this fits existing patterns/contracts)

### Contract content (must be explicit, directive, and enforceable)

Add a section titled exactly:

- - - `## Dangerous Commands — AI Prohibited Without Human Permission`

This section MUST state that AI agents are **NOT ALLOWED** to run any command that performs unsafe fixes unless a human
explicitly instructs it in the current PR/thread.

Include language like:

- - - AI agents MUST NOT run `repo-lint fix --unsafe` under any circumstance. - AI agents MUST NOT run `repo-lint fix
  --unsafe --yes-i-know` under any circumstance. - - These are **human-only commands**. They require explicit human
  permission in the PR thread or issue. - If an agent believes unsafe mode is necessary, it MUST stop and comment:
  `**BLOCKED — HUMAN ACTION REQUIRED**` + @mention `@m1ndn1nj4` and propose minimal options.

Also add a list of other “dangerous” categories AI must not run without permission (keep it minimal, but include
examples):

- - - - destructive cleanup/uninstall commands (apt remove / brew uninstall, etc.) - repo history rewriting (rebase
  --onto, filter-repo, force push) - broad file renames/mass sed sweeps

Make the contract short and unambiguous. Do NOT soften the language.

### Documentation integration

- - - - Link this contract from the repo_lint docs / contributing docs where other contracts are referenced. - Ensure
  `repo-lint fix --unsafe*` docs explicitly reference this AI constraint contract.

---

## 1) CLI behavior (required)

Add support for:

- - - `repo-lint fix` - - Applies **SAFE** auto-fixes only.

- - - `repo-lint fix --unsafe` - - Enables “unsafe” fixers BUT MUST NOT run unless the extra guard is also provided.

- - - `repo-lint fix --unsafe --yes-i-know` - - This is the ONLY way to actually execute unsafe fixes.

Rules:

- - - If `--unsafe` is provided **without** `--yes-i-know`: **hard fail** with exit code **2** and an error message
  explaining this is blocked for safety. - If `--ci` is set (or we detect CI via env): any use of `--unsafe` or
  `--yes-i-know` must **hard fail** (exit code **2**) with message: **“Unsafe fixes are forbidden in CI.”** - `--unsafe`
  must be opt-in and loud. No implicit behavior.

---

## 2) Forensics are mandatory (required)

When unsafe mode runs (`--unsafe --yes-i-know`):

- - - - Always generate a unified diff **patch** file AND a **log** file, even if no changes occur. - Store artifacts
  under the repo’s canonical log strategy (follow existing patterns/contracts). - The log MUST list: - each file changed
  - each unsafe fixer applied - why it is unsafe (short reason) - start/end timestamp - tool version (if available)

Do NOT invent a new naming scheme that violates repo naming/contracts.

---

## 3) Unsafe fixer structure (required)

Implement unsafe fixers as explicitly-named units (examples):

- - - `unsafe_docstring_rewrite` - `unsafe_normalize_headers` - `unsafe_comment_block_reflow`

Requirements:

- - - Must appear in `--help` output. - - Must be logged deterministically. - Must be easy to add future allow/deny
  lists.

For now:

- - - - Build the scaffolding + **at least one real unsafe fixer** (not a no-op). It can be minimal, but it must produce
  an observable change in a controlled test fixture.

---

## 4) Documentation updates (required — extremely explicit warnings)

Update all relevant docs (repo_lint docs + contributing docs) to include:

- - - - exact command examples for safe vs unsafe - VERY STRONG WARNING language suitable for an LLM agent: - Unsafe
  mode can change behavior. - Unsafe mode must never run in CI. - Unsafe mode requires `--yes-i-know`. - - Unsafe mode
  MUST be reviewed by a human using the generated patch/log output before commit. - Unsafe mode is **human-only** for AI
  agents; link the AI constraint contract.

Include this warning verbatim in a prominent location:
> **DANGER:** `repo-lint fix --unsafe --yes-i-know` is intentionally dangerous. It may change behavior. It is forbidden in CI. Only run it locally when you accept risk, and ALWAYS review the generated patch/log before committing.

---

## 5) Testing requirements (MANDATORY, end-to-end)

### 5.1 Create purpose-built unsafe fixtures (required)

Add a deterministic test fixture directory under the repo’s existing conformance/vectors layout (use the same
conventions already used by the repo).

Create fixtures that are designed to:

- - - - violate lint/docstring/contracts in a way that SAFE fixes must NOT change - be fixable only by UNSAFE fix mode

At minimum, add one fixture each for these tool categories:

- - - - Python fixture - Bash fixture - PowerShell fixture - Perl fixture - YAML fixture - Rust fixture

NOTE: If implementing all unsafe fixers now is too large, you still MUST add fixtures and tests that prove:

- - - - the framework supports per-language unsafe fixers - only the implemented unsafe fixer(s) change files - the
  other language fixtures remain unchanged and are logged as “no-op / not implemented yet” (deterministic output)

### 5.2 Test scenario: local unsafe run (required)

Write tests that do ALL of the following:

1) Create/copy fixture into a temp workspace. 2) Run `repo-lint fix --unsafe --yes-i-know` on that workspace. 3) Assert:
- at least one file changed (for the implemented unsafe fixer) - a patch file was written - a log file was written - the
log contains the fixer name(s) and file(s) 4) Optionally re-run the safe gate to verify behavior: - `repo-lint check`
should now report fewer violations OR the expected “fixed” status for that fixture.

### 5.3 Test scenario: unsafe guard rails (required)

Add tests to prove:

- - - `repo-lint fix --unsafe` fails without `--yes-i-know` (exit code 2) - `repo-lint fix --unsafe --yes-i-know` runs
  locally - `repo-lint fix --unsafe --yes-i-know --ci` hard fails (exit code 2) - CI environment detection blocks unsafe
  even without `--ci` (set CI env var in test) - - patch/log artifacts are produced when unsafe mode runs

### 5.4 Deterministic outputs (required)

- - - - Ensure fixture line numbers / paths / ordering are deterministic. - If any test depends on file paths, use
  relative normalized paths.

---

## 6) Validation (required)

Before you stop:

- - - Run: `python -m tools.repo_lint check --ci` - - Run repo_lint unit tests - Confirm docs updated AND links correct

Do not stop until all checks pass OR escalate with:
`**BLOCKED — HUMAN ACTION REQUIRED**` + evidence + minimal options.
