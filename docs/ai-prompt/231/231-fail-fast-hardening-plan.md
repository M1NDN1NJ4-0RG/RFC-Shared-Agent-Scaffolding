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

The goal is to harden the script so it **always fails with the correct message + exit code** and never “falls through”
into a partially-installed zombie environment.

---

## Global Rules (MANDATORY)

### G0 — Preserve intent and structure

- Do **not** delete large blocks of functionality.
- Keep the overall “Phase” structure and existing exit codes unless a new deterministic exit code is explicitly
  required.
- Improve fail-fast behavior without turning the script into a different tool.

### G1 — Every external command must either

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

**Current issue:** The script currently treats ripgrep as optional in behavior (warn + continue) even though it is
described as “required” in places.

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
  - run it as part of the verification gate in a way that clearly distinguishes: - operational/toolchain errors (must
    fail the bootstrap) - legitimate lint violations (acceptable depending on mode)
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

**Goal:** Provide a concrete, modular, maintainable path to migrate from Bash to Rust so we can add/remove tools cleanly
over time.

**Required output (minimum):**

- A phased migration plan (Phase / Item / Sub-item style) that includes:
  - CLI design (subcommands, flags, help text parity with the current script)
  - configuration strategy (hard-coded defaults vs config file; and where it lives)
  - a statically-compiled tool installer registry approach (so adding/removing tools is easy)
  - OS/package-manager abstraction strategy (brew vs apt vs snap vs manual install guidance)
  - concurrency strategy (what can be safely parallelized; and what must remain sequential)
  - progress/UI strategy (a constantly-updating progress display that clearly shows current work)
  - deterministic error handling and exit-code mapping strategy
  - logging strategy (structured logs + human-friendly output)
  - testing strategy (unit tests + integration tests that replace/augment `scripts/tests/test_bootstrap_repo_lint_toolchain.py`)
  - backwards compatibility plan (how to keep the Bash entrypoint until Rust is ready)

**Architecture expectations:** **Locked recommendation:** Start with a statically-compiled installer registry (no
dynamic plugins initially) plus config-driven enable/disable; keep the Bash entrypoint as a thin wrapper until Rust
reaches feature parity and tests prove it.

- The Rust design must explicitly support:
  - enabling/disabling tool installers via configuration
  - adding new tools with minimal boilerplate
  - clean separation between “detect/install/verify” for each tool
  - deterministic failure semantics (no accidental fall-through)

#### 6.2-A Concurrency / Parallelism (WHERE SAFE)

**Goal:** Reduce total bootstrap time while preserving determinism and avoiding race conditions.

**Requirements:**

- Identify which operations can be parallelized safely (examples include downloading multiple independent artifacts,
  fetching package metadata, or pre-check/detect steps).
- Identify which operations must remain sequential (examples include package-manager locks, PATH mutations, environment
  activation, and installs that depend on prior steps).
- The plan must explicitly discuss:
  - process-level vs thread-level concurrency choices
  - shared resource risks (filesystem paths, temp dirs, package manager locks, caches)
  - deterministic logging/output ordering (so CI logs remain readable)
  - retry + exponential backoff strategy for network/package operations (including jitter, max attempts, and what is
    safe/unsafe to retry)
  - fallback behavior when concurrency is disabled or unsupported

**Acceptance Criteria:**

- The Rust plan contains a clear list/table of candidate steps for parallelization, with rationale for each.

---

#### 6.2-B Fancy as hell progress UI (MUST)

**Goal:** Provide a constantly updating CLI progress display so the user always knows what the bootstrapper is doing.

**Requirements:**

- Implement a high-quality, constantly-updating progress UI comparable to a multi-task `tqdm` experience (think: concurrent tasks + live updates).
- The progress UI must clearly show:
  - current phase and sub-step
  - per-tool status (pending/downloading/installing/verifying/done/failed)
  - elapsed time and (where feasible) ETA
  - errors surfaced immediately with context

**Implementation notes (not prescriptive, but likely tools):**

- Consider `indicatif` (progress bars/spinners) + a live-updating terminal UI layer (e.g., a multi-line render approach) for concurrent task status.
- Ensure the UI degrades gracefully when:
  - not running in a TTY
  - output is redirected
  - CI environments limit terminal control sequences

**Acceptance Criteria:**

- The Rust plan includes a concrete UI approach and how it behaves in TTY vs non-TTY/CI.

---

#### 6.2-C Deterministic execution plan + dependency graph

**Goal:** Make behavior explainable and concurrency-safe by explicitly modeling what will happen.

**Requirements:**

- Before performing installs/changes, compute and present a deterministic execution plan that includes:
  - what will be installed
  - what is already installed
  - what will be skipped and why
  - dependency relationships between tools/steps (a dependency graph)
- The plan must be renderable in:
  - human-readable format (default)
  - machine-readable format (`--json`, see 6.2-G)

**Acceptance Criteria:**

- The Rust plan includes an explicit dependency-graph model and how it is used to drive ordering and safe parallelism.

---

#### 6.2-D Dry-run mode (no changes)

**Goal:** Allow users/CI to preview actions without modifying the system.

**Requirements:**

- Implement `--dry-run` so the tool:
  - performs detection/preflight checks
  - prints the full deterministic plan
  - makes **no** system changes (no installs, no file writes beyond optional logs)
- Ensure `--dry-run` is compatible with all profiles and tool selections.

**Acceptance Criteria:**

- `--dry-run` produces a complete plan and exits successfully without side effects.

---

#### 6.2-E Resume / checkpointing

**Goal:** Allow recovery from partial runs without restarting from scratch.

**Requirements:**

- Implement a checkpoint/state mechanism so interrupted runs can be resumed.
- Provide a `--resume` mode that:
  - loads prior state
  - re-validates critical assumptions
  - continues from the last safe checkpoint
- Include safe invalidation rules when state is stale or incompatible.

**Acceptance Criteria:**

- The Rust plan specifies:
  - what is checkpointed
  - where state lives
  - how resume works
  - and how state is invalidated safely.

---

#### 6.2-F Caching strategy (downloads + metadata)

**Goal:** Reduce rework and speed up repeated runs while staying correct.

**Requirements:**

- Define what can be cached safely (e.g., downloaded artifacts, package metadata, detection results per run).
- Provide flags to control caching:
  - `--no-cache`
  - `--refresh` (or equivalent) to re-fetch metadata/artifacts
- Ensure cache paths are deterministic and do not conflict across concurrent tasks.

**Acceptance Criteria:**

- The Rust plan includes a cache design with safe defaults and clear invalidation rules.

---

#### 6.2-G Output modes: human-friendly + machine-readable

**Goal:** Support both interactive humans and automation.

**Requirements:**

- Support at minimum:
  - default human-friendly output
  - `--json` output mode that emits structured events and final summary
  - `--log-file <path>` to persist logs regardless of UI mode
- Ensure exit codes remain deterministic and match the defined contract.

**Acceptance Criteria:**

- The Rust plan includes a concrete event/log schema for `--json` and how logs are written alongside the progress UI.

---

#### 6.2-H Non-interactive / CI behavior (first-class)

**Goal:** Make behavior reliable when stdout is redirected or TTY is unavailable.

**Requirements:**

- Auto-detect non-TTY environments and degrade UI gracefully:
  - disable fancy progress rendering
  - avoid ANSI control sequences
  - emit periodic plain-text status updates
- Provide an explicit `--ci` mode to force deterministic, CI-friendly output.
- Always emit a clear final summary block.

**Acceptance Criteria:**

- The Rust plan explains UI/printing behavior differences between TTY, non-TTY, and `--ci`.

---

#### 6.2-I Security / supply-chain hardening (WHERE SAFE)

**Goal:** Prefer trusted installation sources and reduce supply-chain risk.

**Requirements:**

- Prefer OS package managers (brew/apt/etc.) and signed sources when available.
- When downloading artifacts directly:
  - verify checksums/signatures where feasible
  - avoid insecure patterns (e.g., unverified "curl | sh") unless there is no alternative and it is loudly documented
- Allow version pinning where appropriate (see 6.2-L).

**Acceptance Criteria:**

- The Rust plan includes concrete guidance on how downloads are verified and how unsafe installs are handled/documented.

---

#### 6.2-J Privilege model (least surprise)

**Goal:** Make privilege requirements explicit and predictable.

**Requirements:**

- Identify which steps require elevated privileges.
- Provide a preflight that summarizes privilege requirements before executing.
- Ensure failures due to missing privileges provide actionable remediation.

**Acceptance Criteria:**

- The Rust plan includes a privilege strategy and how sudo/elevation is handled per platform.

---

#### 6.2-K Configuration profiles

**Goal:** Make common use-cases easy and consistent.

**Requirements:**

- Support configuration profiles such as:
  - `minimal`, `dev`, `ci`, `full`
- Profiles must map to a deterministic set of tool installers.
- CLI flags should be able to override profile selections.

**Acceptance Criteria:**

- The Rust plan defines initial profiles and how they map to tool selections.

---

#### 6.2-L Tool version policy (pinning vs minimum versions)

**Goal:** Balance reproducibility and staying current.

**Requirements:**

- Define a version policy that supports at least:
  - minimum supported versions
  - optional exact pinning via configuration
  - upgrade behavior when a tool is below minimum

**Acceptance Criteria:**

- The Rust plan specifies how versions are chosen, where pins live, and how upgrades are decided.

---

#### 6.2-M Self-diagnostics / support bundle

**Goal:** Make failures debuggable without guesswork.

**Requirements:**

- Provide a `diagnostics` command (or equivalent) that can produce a support bundle containing:
  - OS/arch/package manager info
  - detected tools and versions
  - recent log excerpts
  - the failure step and error cause chain (when a failure occurred)

**Acceptance Criteria:**

- The Rust plan defines the diagnostics bundle content and how it is generated.

---

#### 6.2-N “Installer interface” + static registry (plugin-like without dynamic plugins)

**Goal:** Keep the codebase modular and easy to extend.

**Requirements:**

- Define a clear installer interface per tool, e.g.:
  - `detect()`
  - `install()`
  - `verify()`
  - `metadata()` (name, description, dependencies, concurrency safety flags)
- Use a statically-compiled registry to manage installers.

**Acceptance Criteria:**

- The Rust plan includes the core installer trait/interface and how new tools are added with minimal boilerplate.

---

#### 6.2-O Bootstrapper self-doctor

**Goal:** Validate bootstrapper prerequisites independent of repo-lint.

**Requirements:**

- Provide `bootstrap doctor` (or equivalent) that checks:
  - permissions/privileges
  - package manager availability
  - PATH sanity
  - network reachability (where required)
  - disk space/working directory constraints
- Ensure it prints actionable remediation.

**Acceptance Criteria:**

- The Rust plan includes a self-doctor command and what it validates.

---

#### 6.2-P Safe retries + exponential backoff (WHERE SAFE)

**Goal:** Make installs resilient to transient failures (network flakiness, temporary 5xx responses, package mirror
hiccups) without masking real problems.

**Requirements:**

- Define a unified retry policy that can be applied (where safe) to:
  - artifact downloads
  - package-manager metadata refreshes
  - external API calls (if any)
- The retry policy must explicitly define:
  - which operations are safe to retry vs unsafe (idempotency rules)
  - maximum attempts and total time budget
  - exponential backoff with jitter
  - how retries are reported in the progress UI and logs
  - how retry behavior differs in `--ci` / non-interactive modes
- For unsafe-to-retry operations (examples: non-idempotent installs, partial state mutations), the plan must require:
  - either no retries, or
  - a detection/cleanup step before retrying, with clear justification

**Acceptance Criteria:**

- The Rust plan includes a concrete retry/backoff design and explicitly lists which steps use it and which do not.

---
