# Copilot Work Plan — Fail‑Fast Hardening for `bootstrap-repo-lint-toolchain.sh`

> **Target file:** `scripts/bootstrap-repo-lint-toolchain.sh` (or wherever this script lives in-repo)  
> **Scope:** Make failures *deterministic*, *fail-fast*, and *exit with the intended custom error codes* instead of random underlying command exit codes.

---

## Mission

The script already uses:

- `set -euo pipefail`
- a `die()` helper with **specific exit codes**
- staged “Phase” flow

…but there are multiple places where:
1) failures escape `die()` and exit with the wrong code,  
2) failures are only warned (non-fatal) when they should be fatal, and  
3) fail-fast is **too aggressive** in the wrong place (fragile logging pipelines can kill the run).

The goal is to harden the script so it **always fails with the correct message + exit code** and never “falls through” into a partially-installed zombie environment.

---

## Global Rules (MANDATORY)

### G0 — Preserve intent and structure
- Do **not** delete large blocks of functionality.
- Keep the overall “Phase” structure and existing exit codes unless a new deterministic exit code is explicitly required.
- Improve fail-fast behavior without turning the script into a different tool.

### G1 — Every external command must either:
- be wrapped so errors go through `die()` with the correct custom exit code, **or**
- be explicitly allowed to fail (only for *truly optional* behavior) and annotated with `|| true` (plus a comment).

### G2 — Logging must never kill the bootstrap
Any command used only to compute a version string / display formatting must **never** terminate the script.  
If you parse output with `grep`, `awk`, `head`, etc., protect it from `pipefail` and `-e` by using:
- `... || true`, or
- an `awk` that exits cleanly even if it finds nothing, or
- a helper that converts “no match” into empty output (non-fatal).

### G3 — Exit codes must be deterministic
If we say “PowerShell toolchain failed → exit 17”, then **every failure path** inside that toolchain must end with **exit 17**, not `wget`’s exit code, not `apt-get`’s exit code, not `dpkg`’s exit code.

### G4 — Temporary files must be cleaned up
Use `trap` where appropriate (example: `packages-microsoft-prod.deb`) so failures don’t leave garbage behind.

---

## Phase 0 — Preflight: Rename + Relocate the User Manual and Update References

### 0.1 Rename the bootstrapper user manual
**Goal:** Standardize the manual’s name so it clearly communicates scope and avoids ambiguous `bootstrapper.md`.

**Required changes:**
- Rename:
  - `docs/tools/repo-lint/bootstrapper-toolchain-user-manual.md`
- To:
  - `bootstrapper-toolchain-user-manual.md`

### 0.2 Move the manual to an appropriate, stable location
**Goal:** Place the manual where humans will actually find it.

**Implementation Requirements (locked decision):**
- **Use Option A (Docs-centric):** Move the manual to:
  - `docs/repo-lint/bootstrapper-toolchain-user-manual.md`

**Acceptance Criteria:**
- The original `docs/tools/repo-lint/bootstrapper-toolchain-user-manual.md` path no longer exists.
- The manual content is preserved (no accidental truncation).
- The new manual location is **linked** from high-signal entrypoints where appropriate, including at minimum:
  - `CONTRIBUTING.md`
  - any repo-lint / tooling overview docs
  - any docs index/navigation pages that reference bootstrap/toolchain setup

### 0.3 Update all repo references to the new name/location
**Goal:** No broken links, no stale references.

**Implementation Requirements:**
- Update all references across the repo that mention:
  - `docs/tools/repo-lint/bootstrapper-toolchain-user-manual.md`
  - `bootstrapper.md`
- Ensure markdown links, docs indices, READMEs, scripts, comments, and CI references point to the new path:
  - `docs/repo-lint/bootstrapper-toolchain-user-manual.md`
- Additionally, ensure the new manual is discoverable by adding links from other docs where it is useful, including:
  - `CONTRIBUTING.md`
  - any repo-lint / tooling overview docs

**Acceptance Criteria:**
- A repo-wide search finds **zero** remaining references to the old path/name.
- All updated links resolve correctly.

---

## Phase 1 — Add Standardized “Fail‑Fast Wrappers” and Safe Logging Helpers

### 1.1 Add a `run_or_die()` helper
**Implement a helper** that runs a command and converts failure into `die()` with a consistent message and the desired exit code.

**Requirements:**
- Accept an exit code as first arg.
- Accept a human-friendly message or auto-generate one.
- Print the failing command in the error message (useful for CI logs).

**Example behavior (you may implement differently):**
- `run_or_die 17 "Installing PowerShell prerequisites failed" sudo apt-get install -y ...`

**Acceptance Criteria:**
- No more “naked” external install commands in toolchain installers.

---

### 1.2 Add a `try_run()` helper for optional steps
Optional steps (only truly optional!) can use a helper that returns non-zero without killing the script.

**Use cases:**
- “Attempt install, but fallback is allowed”
- “Try to extract a version string for display”

---

### 1.3 Add a `safe_version()` helper (or equivalent)
Any version parsing should not be able to terminate the script.

**Problem patterns to eliminate:**
- `cmd | grep ... | awk ...` (can die via `pipefail`)
- `grep` “no match” causing hard exit

**Acceptance Criteria:**
- Version parsing is non-fatal everywhere.
- The bootstrap continues even if a version string can’t be derived.

---

## Phase 2 — Fix Fail‑Fast Gaps and Wrong Exit Codes (Function-by-Function)

### 2.1 `activate_venv()` — Activation mismatch is warn-only
**Current issue:** If activation doesn’t actually switch `python3` to `.venv/bin/python3`, the script only warns and continues, risking installs into the wrong environment.

#### 2.1-A Make activation mismatch fatal
**Make activation mismatch fatal** by default.

**Implementation Requirements:**
- If `command -v python3` does **not** equal `$venv_path/bin/python3`, call:
  - `die "Virtual environment activation failed (python3 does not point to venv)" 11`

**Acceptance Criteria:**
- We never proceed past activation if we’re not actually in the venv.

---

### 2.2 `install_repo_lint()` — pip upgrade is not wrapped
**Current issue:** `python3 -m pip install --upgrade pip setuptools wheel` is not guarded. If it fails, `set -e` exits with a non-custom code.

#### 2.2-A Wrap and map exit codes
Wrap the pip-upgrade step so failure exits through `die()` with the intended code.

**Implementation Requirements:**
- Use `run_or_die` or an explicit `if ! ...; then die ...; fi`
- Choose a consistent code:
  - Use `13` (repo-lint install failure bucket) unless you have a strong reason to introduce a new code.

**Acceptance Criteria:**
- pip upgrade failure yields a clean error message and deterministic exit code.

---

### 2.3 `install_powershell_tools()` — multiple naked commands + wrong exit codes
**Current issue:** apt/wget/dpkg steps can fail and exit immediately with arbitrary codes, bypassing `die ... 17`.

#### 2.3-A Wrap each step with `run_or_die 17`
Break the apt-based install into logical steps and wrap each:

- apt update  
- install prereqs  
- download MS repo package  
- dpkg install  
- apt update  
- install powershell  

#### 2.3-B Add `trap` cleanup for downloaded deb
Use `trap` to delete `packages-microsoft-prod.deb` on exit/failure.

#### 2.3-C Make `wget` failure obvious
If the download URL breaks, the error message must clearly say:
- which URL was attempted,
- and which step failed.

**Acceptance Criteria:**
- Any failure during PowerShell installation exits **17** with a clear message.
- No leftover `.deb` file after failure.

---

### 2.4 `install_perl_tools()` — cpanm failures bypass intended failure aggregation
**Current issue:** `cpanm` calls are not wrapped. With `set -e`, any failure terminates instantly, preventing:
- population of `failed_tools[]`
- the “Manual installation required” guidance
- exit code `18`

#### 2.4-A Prevent `set -e` from short-circuiting cpanm error collection
Wrap each install so:
- if `cpanm ...` fails → append to `failed_tools` and continue to attempt remaining installs.

#### 2.4-B Ensure final failure path uses `die ... 18`
At end of function, if any `failed_tools`:
- print manual remediation hints
- `die "Perl toolchain installation incomplete" 18`

**Acceptance Criteria:**
- A failing `cpanm` does not cause an early unhandled exit.
- The function exits with **18** and prints actionable remediation.

---

### 2.5 `install_shell_tools()` — fragile version pipelines can kill the script
**Current issue:** Version parsing pipelines can fail and terminate the run (wrong kind of fail-fast).

#### 2.5-A Replace pipeline version parsing with safe extraction
Replace things like:
- `shellcheck --version | grep "^version:" | awk '{print $2}'`

with a safe alternative that never terminates the script if parsing fails:
- `awk '/^version:/ {print $2; found=1} END {exit 0}'`
- or `... || true`

#### 2.5-B Ensure fallback install attempts do not bypass `die 16`
Any fallback attempt (e.g., snap) must:
- be wrapped and failure must correctly lead to `die 16` after the function prints guidance.

**Acceptance Criteria:**
- Logging cannot terminate bootstrap.
- Shell tool failures exit **16** only through `die()`.

---

### 2.6 `install_rgrep()` — ripgrep must be REQUIRED (no grep fallback)
**Current issue:** The script currently treats ripgrep as optional in behavior (warn + continue) even though it is described as “required” in places.

#### 2.6-A Enforce ripgrep as a hard requirement
Ripgrep (`rg`) is **mandatory** for this repository/tooling. There must be **no** silent fallback to plain `grep`.

**Implementation Requirements:**
- If `rg` is not present at runtime, the script must attempt to install it.
- If installation fails **or** `rg` is still not available after install attempts, the script must exit via `die()`.

#### 2.6-B Use a deterministic exit code for ripgrep failure
**Locked decision:** Introduce a dedicated exit code: **`21`** or one that's not used already for ripgrep installation / availability failure.

**Implementation Requirements:**
- Add exit code `21` to the script’s documented exit code list/usage output.
- Update any docs that summarize bootstrapper exit codes to include `21`.
- Extend `scripts/tests/test_bootstrap_repo_lint_toolchain.py` to assert exit code `21` for the relevant failure paths.

**Error Messaging Requirements:**
- On failure, print a clear message that ripgrep is required and include:
  - the OS path taken (brew/apt/etc.),
  - the failing command (where safe),
  - and a manual remediation snippet (install command) per platform.

**Acceptance Criteria:**
- If `rg` cannot be installed or discovered, the script fails fast via `die()` with the deterministic ripgrep exit code.
- Documentation/help text no longer implies ripgrep is optional.

---

### 2.7 `run_verification_gate()` — confirm exit-code contract or harden it
**Current behavior:** Treats repo-lint exit code `1` as success (“violations found, tools work”).

#### 2.7-A Confirm repo-lint exit code semantics
If repo-lint has a documented exit code contract, link/quote it in comments.

#### 2.7-B Harden against accidental false-pass (locked preference)
**Preferred approach:** Use (or extend) the existing `repo-lint doctor` command as the canonical self-test.

**Implementation Requirements:**
- If `repo-lint doctor` already exists:
  - run it as part of the verification gate in a way that clearly distinguishes:
    - operational/toolchain errors (must fail the bootstrap)
    - legitimate lint violations (acceptable depending on mode)
- If `repo-lint doctor` is incomplete:
  - extend it so it provides a deterministic self-test suitable for the bootstrapper gate.

**Acceptance Criteria:**
- The verification gate uses `repo-lint doctor` (or an improved version of it) as the primary self-test signal.
- Operational failures cannot be misclassified as “violations found”.

---

### 2.8 `install_actionlint()` — ensure PATH messaging is accurate and deterministic
**Current behavior:** Linux branch exports `PATH="$HOME/go/bin:$PATH"` for the session, installs actionlint via `go install`, then checks `command -v actionlint`.

#### 2.8-A Wrap Go install steps so failures exit via `die 20`
- installing Go (apt-get)
- `go install ...`
- verifying actionlint

#### 2.8-B Print explicit remediation when `actionlint` not found
If install succeeds but binary isn’t on PATH, error must explain:
- expected install location (`$HOME/go/bin/actionlint`)
- how to export PATH

**Acceptance Criteria:**
- Failures exit **20** through `die()`.
- Success prints usable guidance.

---

## Phase 3 — Consistency Pass Across the Entire Script

### 3.1 Eliminate “naked” external commands in install paths
Search the script for these patterns and fix them:
- `sudo apt-get ...` (not wrapped)
- `brew install ...` (not wrapped)
- `wget ...` (not wrapped)
- `dpkg -i ...` (not wrapped)
- `python3 -m pip install ...` where failure should map to a custom code
- `cpanm ...` where failure must be aggregated

**Acceptance Criteria:**
- Any command that can fail in a meaningful way is either wrapped to `die()` or intentionally non-fatal.

---

### 3.2 Normalize error messages
Ensure error messages follow:
- `[bootstrap][ERROR] <clear description of the step and failure>`

Include:
- the tool being installed,
- the package manager,
- and the command that failed (where safe).

---

### 3.3 Add cleanup traps where appropriate
At minimum:
- ensure `packages-microsoft-prod.deb` is deleted on failure or exit.

---

## Phase 4 — Documentation Updates (Keep Humans Sane)

### 4.1 Update `show_usage()` and top-of-file comments
After policy decisions (ripgrep required; strict venv), ensure:
- help text matches behavior
- comments match behavior

### 4.2 Add a short “Failure semantics” section in the header comments
Summarize:
- the role of `set -euo pipefail`
- how `run_or_die` enforces exit codes
- how optional steps are handled

---

## Phase 5 — Verification / Receipts (MANDATORY)

### 5.0 Mandatory test gate: run and extend the comprehensive toolchain tests
**Goal:** Any change to the bootstrapper must be proven safe by the canonical test suite.

**Required changes and verification:**
- After **any** additions/removals/behavior changes in the bootstrapper, verify the full suite still passes by running:
  - `python3 -m pytest scripts/tests/test_bootstrap_repo_lint_toolchain.py`
- If your changes introduce new branches, failure modes, exit codes, or helper utilities (e.g., `run_or_die`, `try_run`, safer version parsing), you must **extend**:
  - `scripts/tests/test_bootstrap_repo_lint_toolchain.py`
  to cover the new behavior.

**Test expectations (minimum):**
- deterministic exit codes for failure paths
- deterministic error messaging for key failures
- non-fatal logging/version parsing behavior
- strict venv activation behavior
- ripgrep required semantics
- PowerShell/Perl installers do not escape with random exit codes

**Acceptance Criteria:**
- `scripts/tests/test_bootstrap_repo_lint_toolchain.py` passes locally and in CI.
- Any newly introduced behavior has explicit test coverage in that file.

---

### 5.1 Local validation checklist
Run the following locally (or in CI where appropriate):
- `shellcheck` on the script (if shell toolchain enabled)
- `shfmt -d` on the script
- Execute the script in a controlled environment

### 5.2 Simulated failure tests (at least 3)
Create a small test approach (does not need to be heavy) that demonstrates deterministic exit codes. Examples:
- simulate failing `pip` (e.g., invalid index URL environment variable in a subshell)
- simulate failing `wget` (override PATH to a fake wget that returns non-zero)
- simulate failing `cpanm` (override PATH similarly)

**Acceptance Criteria:**
- Each simulation produces the intended `die()` message and correct exit code.
- Provide “receipts” using the repo’s established journaling system (do not invent a one-off location).

---

## Done Definition (MANDATORY)

This task is complete only when:

- ✅ The bootstrapper manual is renamed to `bootstrapper-toolchain-user-manual.md`, moved to the chosen stable location, and all repo references are updated (no broken links)
- ✅ All bootstrapper behavior changes are validated by `scripts/tests/test_bootstrap_repo_lint_toolchain.py`; the test suite is extended in that file for any new branches/failure modes/exit codes introduced
- ✅ All previously identified “naked command” failure paths are wrapped and mapped to correct exit codes
- ✅ Logging/version parsing cannot terminate the script
- ✅ Venv activation mismatch behavior is deterministic (fatal by default)
- ✅ ripgrep is enforced as REQUIRED (no grep fallback) and the failure path is deterministic (exit code + message)
- ✅ PowerShell/Perl installs cannot escape with random exit codes
- ✅ Verification gate semantics are either documented or hardened to prevent false-pass

---


## Notes for Implementation

- Prefer small, mechanical refactors.
- Favor readability over cleverness.
- The script is an enforcement gate: **determinism beats convenience.**


---

## Phase 6 — End-of-Work Deliverables: Script Analysis + Rust Modularization Plan

### 6.1 Produce a detailed analysis of `bootstrap-repo-lint-toolchain.sh`
**Goal:** Leave a durable, human-readable technical understanding of how the bootstrapper currently works.

**Required output:**
- Write a detailed analysis that covers:
  - the script’s control flow (major phases/functions and their call order)
  - all exit codes and what triggers them
  - the role and risks of `set -euo pipefail` in this specific script
  - how toolchain installers behave per OS (macOS/Linux, brew/apt/snap/etc.)
  - current failure modes and how the new wrappers/guards address them
  - any remaining edge cases or assumptions (network, permissions, PATH, shells)

**Acceptance Criteria:**
- The analysis is thorough enough that a new maintainer can reason about behavior and safely extend it.

---

### 6.2 Produce a detailed plan to re-implement this tool as a modular Rust binary
**Goal:** Provide a concrete, modular, maintainable path to migrate from Bash to Rust so we can add/remove tools cleanly over time.

**Required output (minimum):**
- A phased migration plan (Phase / Item / Sub-item style) that includes:
  - CLI design (subcommands, flags, help text parity with the current script)
  - configuration strategy (hard-coded defaults vs config file; and where it lives)
  - a statically-compiled tool installer registry approach (so adding/removing tools is easy)
  - OS/package-manager abstraction strategy (brew vs apt vs snap vs manual install guidance)
  - deterministic error handling and exit-code mapping strategy
  - logging strategy (structured logs + human-friendly output)
  - testing strategy (unit tests + integration tests that replace/augment `scripts/tests/test_bootstrap_repo_lint_toolchain.py`)
  - backwards compatibility plan (how to keep the Bash entrypoint until Rust is ready)

**Architecture expectations:**
**Locked recommendation:** Start with a statically-compiled installer registry (no dynamic plugins initially) plus config-driven enable/disable; keep the Bash entrypoint as a thin wrapper until Rust reaches feature parity and tests prove it.

- The Rust design must explicitly support:
  - enabling/disabling tool installers via configuration
  - adding new tools with minimal boilerplate
  - clean separation between “detect/install/verify” for each tool
  - deterministic failure semantics (no accidental fall-through)

**Acceptance Criteria:**
- The plan is detailed enough that implementation can begin without guesswork.

---
