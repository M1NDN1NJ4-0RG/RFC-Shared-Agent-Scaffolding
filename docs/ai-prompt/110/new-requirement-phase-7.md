@copilot

## Implement “Unsafe Fix Mode” for repo_lint (MANDATORY)

Add an **explicitly dangerous** optional fix mode to `tools.repo_lint` that can apply “unsafe” transformations locally, but is **never allowed in CI**.

### 1) CLI behavior (required)
Add support for:

- `repo-lint fix`  
  - Applies **SAFE** auto-fixes only.

- `repo-lint fix --unsafe`  
  - Enables “unsafe” fixers BUT MUST NOT run unless the extra guard is also provided.

- `repo-lint fix --unsafe --yes-i-know`  
  - This is the ONLY way to actually execute unsafe fixes.

Rules:
- If `--unsafe` is provided **without** `--yes-i-know`: **hard fail** with exit code 2 and an error message explaining this is blocked for safety.
- If `--ci` is set (or we are in CI env): any use of `--unsafe` or `--yes-i-know` must **hard fail** (exit code 2) with a message: “Unsafe fixes are forbidden in CI.”
- `--unsafe` must be opt-in and loud. No implicit behavior.

### 2) Forensics are mandatory (required)
When unsafe mode runs (`--unsafe --yes-i-know`):
- Always generate a unified diff patch file and a log file, even if no changes occur.
- Store artifacts under the repo’s canonical log strategy (follow existing patterns).
- The log must list:
  - each file changed
  - each unsafe fixer applied
  - a short reason for why it is considered unsafe
  - start/end timestamp and tool version (if available)

If the repo already has a log path convention for repo_lint, use it. Do NOT invent a new naming scheme that violates contracts.

### 3) Unsafe fixer structure (required)
Implement unsafe fixers as explicitly-named units (e.g., `unsafe_docstring_rewrite`, `unsafe_normalize_headers`, etc.) so we can:
- list them in `--help`
- log them deterministically
- optionally allow future allow/deny lists

For now:
- Create the scaffolding + one minimal example unsafe fixer (can be a no-op placeholder if needed), but the end-to-end CLI + guardrails + logging must be real.

### 4) Documentation updates (required, extremely explicit warnings)
Update all relevant docs (README / docs for repo_lint / contributing docs) to include:
- exact command examples for safe vs unsafe
- **VERY STRONG WARNING LANGUAGE** suitable for an LLM agent:
  - Unsafe mode can change behavior.
  - Unsafe mode must never run in CI.
  - Unsafe mode requires `--yes-i-know` because it is dangerous.
  - Unsafe mode MUST be reviewed by a human via the patch/log output before commit.

Use clear, directive wording. Do not soften it.

Example wording to include verbatim somewhere prominent:
> **DANGER:** `repo-lint fix --unsafe --yes-i-know` is intentionally dangerous. It may change behavior. It is forbidden in CI. Only run it locally when you accept risk, and ALWAYS review the generated patch/log before committing.

### 5) Tests (required)
Add tests to prove:
- `fix --unsafe` fails without `--yes-i-know`
- `fix --unsafe --yes-i-know` runs locally
- `--ci` blocks any unsafe flags
- patch/log artifacts are produced when unsafe mode runs

Update existing test vectors/fixtures as needed (do NOT hand-wave failures; make them pass deterministically).

### 6) Validation (required)
Before you stop:
- Run the canonical gate: `python -m tools.repo_lint check --ci`
- Run the repo_lint unit tests
- Confirm docs were updated and links are correct

Do not end the session until all checks pass or you escalate with:
`**BLOCKED — HUMAN ACTION REQUIRED**` + evidence + minimal options.
