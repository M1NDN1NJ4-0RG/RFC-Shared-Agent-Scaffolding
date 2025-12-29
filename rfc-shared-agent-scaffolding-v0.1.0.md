# RFC: Sharded Agent Scaffolding & Journaling for Long-Running AI Coding Workflows (v0.1.0)

**Status:** Implemented (iterated)  
**Audience:** Humans collaborating with LLM-based coding agents (Claude Code, Codex, etc.)  
**Primary Environment:** GitHub repositories with PR-based workflows, CI gating, and auto-merge  
**Motivation:** Reliability, continuity, safety, and human-error resistance in long-running agent sessions

---

## 0. Executive Summary

This RFC defines a restartable, failure-resilient operating model for AI coding agents.

Version 8 adds an important lens: the system is not “bureaucratic rigor” for its own sake. It is **operational scar tissue** from running constrained agents (small context, rigid output limits, cheaper/free tiers) alongside more capable agents. In practice, the scaffolding acts as a **compatibility layer** (a “hypervisor”) that allows:

- **Constrained agents** (e.g., small context windows, strict output limits) to function safely via sharding, journaling, stop conditions, and serialized handoff files.
- **More capable agents** to unlock “higher gears” (e.g., CI-gated auto-merge) because safety proofs are explicit and persistent on disk.

v8 also introduces:
- an explicit **Token Budget / Runway Check** before starting large work items,
- and a diagnostic loop for the **“npm ci --ignore-scripts” trap**.

---

## 0.1. Canonical Implementation (v0.1.1 Update)

**Status:** Active (as of 2024)  
**Implementation:** Rust Canonical Tool

As of v0.1.1, the contract behaviors defined in this RFC are **canonically implemented in Rust**. The Rust canonical tool (`rust/src/`) is the single source of truth for:

- Event ledger format and emission
- Merged view mode
- Exit code forwarding and signal handling
- Artifact generation and no-clobber semantics
- Command execution behaviors (safe-run, safe-check, safe-archive)

**Language-specific wrappers** (Bash, Perl, Python3, PowerShell) are now **thin invokers** that discover and execute the Rust binary. They:

1. Locate the Rust binary via deterministic discovery rules (see `docs/architecture/wrapper-discovery.md`)
2. Pass through all arguments without modification
3. Forward exit codes from the Rust tool
4. Provide actionable error messages if the Rust binary is not available

**Rationale:**

Maintaining four independent implementations led to:
- Drift risk across regex dialects, buffering, exit codes
- N×maintenance burden for behavior changes
- Complex cross-platform conformance testing
- YAML/Bash/JavaScript escaping issues in CI

The Rust canonical tool provides:
- ✅ One implementation = one source of truth
- ✅ Cross-platform consistency via Rust stdlib
- ✅ Type safety and compile-time guarantees
- ✅ Thin wrappers = reduced maintenance surface

**Documentation:**

- [Rust Canonical Tool](./docs/architecture/rust-canonical-tool.md)
- [Wrapper Discovery Rules](./docs/architecture/wrapper-discovery.md)
- [Conformance Contract](./docs/usage/conformance-contract.md)

---

## 1. Problem Statement

LLM-based coding agents can perform multi-day refactors and CI-gated workflows, but without an operational model, their work is fragile:

- Sessions are volatile.
- Context is finite.
- Humans misconfigure repositories.
- Instruction files and trackers grow without bound.
- Smaller agents can truncate outputs or silently “finish” partial edits.

Reliability requires treating agents like fallible workers with volatile memory and bounded output.

---

## 2. Observational Trigger (Empirical Epiphany)

Testing on a large refactor (~9,200 LOC monolithic JS → modular TS) showed recovery depends on **externalized state discipline**, not model intelligence.

Large context windows delay—but do not eliminate—the need to chunk. When trackers exceed a single message, chunking becomes inevitable.

---

## 3. Core Design Principles

1. **Shard instructions** to prevent monolithic growth.
2. **Journal state to disk**; treat memory as volatile.
3. **Fail closed**; prove safety before acting.
4. **Checkpoint failures**; errors become resumable state.
5. **Avoid destructive operations**; preserve auditability.
6. **Serialize progress explicitly** to survive truncation and context loss.

---

## 4. The “Universal Agent OS” Lens (New)

This framework behaves like a minimal “operating system” for agents—supplying executive function that many models lack:

- planning and chunking,
- durable state,
- “safe mode” vs “fast mode” gates,
- and explicit feature flags persisted on disk.

### 4.1 Codex Scars: Managing the Token Economy

Constrained agents can:
- cut off mid-task,
- hallucinate file endings,
- or drop existing code when context falls out.

**Mitigation pattern:** explicit stop conditions and serialized continuation.

- Work is broken into bounded items.
- The agent is required to stop at a boundary and provide a deterministic continuation prompt (or journal state) before output truncation becomes fatal.

### 4.2 Bootloader / Feature Flag Logic

A robust “boot chain” allows graceful downgrade:

- No `.git` → safe mode (snapshot/patch only).
- Git present but policy unproven → manual PR flow.
- Policy proven (preflight pass) + feature flag present → auto-merge flow permitted.

Feature flags implemented as files (e.g., `.agent/auto-merge.enabled`) persist across context resets and agent swaps.

### 4.3 Anti-Hallucination File System

Snapshot/patch patterns (e.g., patch files, version logs) reduce blast radius when an agent forgets which file it’s editing or truncates content.

Hard safety defaults:
- keep default branch untouchable,
- prefer throwaway branches for changes,
- record diffs and checkpoints.

### 4.4 Interchangeable Agents via Handoff Files

A standardized serialized memory format (handoff files and journals) allows:
- starting work with a cheaper/constrained agent,
- pausing at a safe boundary,
- resuming with a more capable agent without re-reading long chat history.

---

## 5. Implementation Pattern (Recap)

### 5.1 Reference Layout

```
CLAUDE.md
.docs/agent/
  10_SAFETY_COMMANDS.md
  20_GIT_WORKFLOW.md
  21_AUTO_MERGE_WAITING.md
  22_AUTOMERGE_PREFLIGHT.md
  30_JOURNALING.md
  40_HANDOFF_PROTOCOL.md
.agent/
  CURRENT.md
  REMAINING_WORK.md
  PR_LOG.md
  FAIL-LOGS/
  FAIL-ARCHIVE/
scripts/
  safe-run.sh
  safe-archive.sh
  safe-check.sh
  preflight_automerge_ruleset.sh
```

---

## 6. Failure Pause Ritual (Normative)

On any non-zero exit from build/test/verify commands, the agent MUST:
1. Write a FAILURE PAUSE block into `CURRENT.md`.
2. Persist stdout/stderr to `.agent/FAIL-LOGS/`.
3. Stop unless explicitly instructed to continue.

Logging is fail-only.

---

## 7. Safe Wrapper Execution Contract (Normative)

**Status:** Finalized (see `M0-DECISIONS.md` for authoritative M0 decision gates)

Wrappers MUST be used for critical commands. They must:
- run commands verbatim,
- preserve exit codes,
- produce artifacts on failure,
- and have no success-path side effects.

### 7.1 Logging Semantics (M0-P1-I1)

**Decision:** Split stdout and stderr

`safe-run` MUST:
- Capture stdout and stderr separately
- Include clear section markers in log files (`=== STDOUT ===`, `=== STDERR ===`)
- Preserve both streams in their entirety in failure logs
- Preserve exit codes regardless of output format

#### 7.1.1 Hybrid Logging Fidelity Contract (Enhanced)

**Status:** EPIC Follow-up - Logging Fidelity Extension

This section extends M0-P1-I1 with deterministic cross-stream ordering guarantees and human-friendly merged views.

**Motivation:** While split stdout/stderr sections (M0-P1-I1) preserve per-stream ordering, they do not guarantee temporal interleaving across streams due to OS scheduling and buffering differences. This enhancement provides:
1. A contractually guaranteed **observed-order event ledger** with global sequence numbers
2. An optional **merged view** for human readability
3. Cross-language conformance on event ordering semantics

**Stream Terminology:**
- **stdout stream**: Bytes emitted by the child process on stdout
- **stderr stream**: Bytes emitted by the child process on stderr  
- **meta stream**: Wrapper-generated informational lines (start/end markers, exit code, etc.)

**Observed Order Definition:**
The order in which the wrapper receives bytes/lines/chunks from stdout/stderr pipes. This is subject to OS scheduling and buffering, so it is not "ground truth emission-time order," but it is the only order we can contractually guarantee without merging streams in the child process.

**Requirements:**

**A) Split Sections (M0-P1-I1 - Unchanged)**

All implementations MUST continue to emit the M0-compliant split sections with existing markers:

1. A `STDOUT` section:
   ```
   === STDOUT ===
   ...stdout content...
   
   ```

2. A `STDERR` section:
   ```
   === STDERR ===
   ...stderr content...
   ```

Per-stream ordering MUST be preserved. Content MUST NOT be lost. No stdout content may appear in the STDERR section and vice versa.

**Note:** The M0 format uses `=== STDOUT ===` and `=== STDERR ===` markers. These MUST be preserved for backward compatibility.

**B) Event Ledger (NEW - Required)**

All implementations MUST also emit an **Event Ledger** section:

```
--- BEGIN EVENTS ---
[SEQ=1][META] safe-run start: cmd="<command>"
[SEQ=2][STDOUT] <line1>
[SEQ=3][STDERR] <line1>
[SEQ=4][STDOUT] <line2>
[SEQ=5][META] safe-run exit: code=<N>
--- END EVENTS ---
```

**Event Record Format:**
```
[SEQ=<seq>][<stream>] <text>
```

Where:
- `<seq>`: Monotonically increasing integer starting at 1
- `<stream>`: One of `STDOUT`, `STDERR`, `META`
- `<text>`: The exact text payload for that event (single line, no trailing newline in the format)

**Event Ledger Rules:**
- `seq` MUST be strictly increasing by 1 across all events
- `seq` MUST reflect the wrapper's observed order across ALL streams (stdout/stderr/meta)
- Every line/chunk emitted into the split STDOUT/STDERR sections MUST correspond to one or more `STDOUT`/`STDERR` events in the ledger
- Wrapper-generated markers and exit summary MUST appear as `META` events in the ledger

**Standardized META Lines:**

To ensure cross-language conformance, the following META event text MUST match exactly:

1. **Start event** (MUST be seq=1 unless there are earlier meta events):
   ```
   safe-run start: cmd="<command>"
   ```
   
   Where `<command>` is the full command being executed, encoded using a **standardized POSIX shell-style quoting scheme**:
   
   - Implementations MUST produce the same `<command>` text for the same logical command line.
   - The command line is represented as a single string where arguments are joined by a single space character (`U+0020`).
   - Each argument is quoted using the same rules as POSIX shell single-quoting and Python's `shlex.quote()`:
     - Arguments containing only alphanumeric characters, underscores, hyphens, periods, slashes, or equals signs MAY be left unquoted.
     - All other arguments MUST be enclosed in single quotes (`'`).
     - A single quote (`'`) within an argument MUST be encoded as `'\''` (close quote, escaped quote, open quote).
   - Bash implementations SHOULD use `printf '%q'` for each argument.
   - Python implementations SHOULD use `shlex.quote()` for each argument.
   
   **Examples (normative):**
   - Command: `echo hi`
     - `<command>`: `echo hi`
   - Command: `bash -c "echo 'hello world'"`
     - `<command>`: `bash -c 'echo '"'"'hello world'"'"''`
   - Command: `python script.py --flag "value with spaces"`
     - `<command>`: `python script.py --flag 'value with spaces'`

2. **Exit event** (MUST be the final META event):
   ```
   safe-run exit: code=<exit_code>
   ```
   Where `<exit_code>` is the integer exit code.

**C) Optional Merged View (NEW - Optional)**

Implementations MAY support an optional mode that emits a merged transcript in `seq` order, derived from the Event Ledger.

**Activation:** Via CLI flag (e.g., `--merged` or `--view merged`) OR environment variable (e.g., `SAFE_RUN_VIEW=merged`)

When enabled, implementations MUST emit:

```
--- BEGIN MERGED (OBSERVED ORDER) ---
[#1][META] safe-run start: cmd="<command>"
[#2][STDOUT] <line1>
[#3][STDERR] <line1>
[#4][STDOUT] <line2>
[#5][META] safe-run exit: code=<N>
--- END MERGED ---
```

**Merged View Format:**
```
[#<seq>][<stream>] <text>
```

**Notes:**
- This merged view represents **observed-order**, not guaranteed emission-time interleaving
- The merged view MUST be identical across languages given the same observed event ordering
- Default behavior MUST include split sections + event ledger; merged view is optional
- If an implementation supports output control (split-only / merged-only / both), it MUST be documented and tested

**Non-Goals:**
- We do NOT attempt to reconstruct the child process's true emission-time ordering across stdout/stderr
- We do NOT require identical timestamps across platforms (timestamps are informational only if present)

### 7.2 Failure Log Naming (M0-P1-I2)

**Decision:** Deterministic, non-overwriting naming

Log files MUST follow this format: `{ISO8601_TIMESTAMP}-pid{PID}-{STATUS}.log`

Example: `20251226T020707Z-pid4821-FAIL.log`

Requirements:
- Timestamp in ISO 8601 format with timezone (UTC recommended)
- PID included for correlation
- Status one of: `FAIL`, `ABORTED`, `ERROR`
- Directory: `.agent/FAIL-LOGS/`
- No random suffixes

### 7.3 Archive No-Clobber Semantics (M0-P1-I3)

**Decision:** Hybrid approach

**Default:** Auto-suffix behavior
- If destination exists, append numeric suffix (e.g., `.2`, `.3`)
- Continue incrementing until unique filename found

**Opt-in:** Strict no-clobber (fail fast)
- Flag: `--no-clobber` or `SAFE_ARCHIVE_NO_CLOBBER=1`
- Exit with error if destination exists

### 7.4 Authentication & Headers (M0-P2-I1)

**Decision:** Precedence A with Bearer token format

**Auth precedence (highest to lowest):**
1. Explicit CLI arguments
2. Environment variables (`GITHUB_TOKEN`, `TOKEN`)
3. Configuration files
4. `gh auth` token

**Header format:** `Authorization: Bearer <token>`

Token values MUST never be logged. If no auth available, exit with code 2.

### 7.5 Exit Code Taxonomy (M0-P2-I2)

**Decision:** Stable exit code ranges

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General failure |
| 2 | Auth/permission error |
| 3 | Usage/validation error |
| 10-19 | Dependency errors |
| 20-29 | Network errors |
| 30-39 | Parse errors |
| 40-49 | File system errors |
| 50-59 | Ruleset/policy errors |

See `M0-DECISIONS.md` for complete specification.

Wrapper failure fallback remains mandatory.

### 7.6 Script Naming Conventions

**Decision:** Kebab-case required for script surfaces only

Script files in this repository MUST use kebab-case naming (lowercase letters and digits separated by hyphens only). This rule applies **only to script surfaces** (executable entrypoints), not to language-specific source files.

**Scope — Script Surfaces (kebab-case REQUIRED):**
- Script surfaces in `wrappers/*`
- Wrapper scripts in `wrappers/*`
- Applies to executable/script file extensions: `.sh`, `.bash`, `.zsh`, `.pl`, `.py`, `.ps1`

**Scope — Language Sources (language-specific conventions REQUIRED):**
- Rust source files (`.rs`) MUST use **snake_case** per Rust ecosystem conventions
- Other language sources follow their respective ecosystem conventions
- These are **explicitly excluded** from kebab-case enforcement

**Format (script surfaces only):**
- Filename stem (excluding extension) MUST match: `^[a-z0-9]+(?:-[a-z0-9]+)*$`
- ✅ Valid: `safe-run.sh`, `test-helpers.ps1`, `preflight-automerge-ruleset.pl`
- ❌ Invalid: `safe_run.sh`, `SafeRun.ps1`, `testHelpers.py`
- **Note:** As of Phase 5.5, Perl scripts use snake_case (e.g., `safe_run.pl`), not kebab-case. This document reflects historical conventions.

**Format (Rust sources):**
- Filename stem MUST use snake_case per Rust conventions
- ✅ Valid: `safe_run.rs`, `mod.rs`, `cli.rs`
- ❌ Invalid: `safe-run.rs`, `SafeRun.rs`

**Rationale:**
- **Script surfaces:** Consistent naming prevents path drift across language implementations, reduces cognitive load, simplifies CI automation, aligns with cross-OS/cross-language portability
- **Rust sources:** Follow Rust ecosystem conventions (Cargo/module expectations, standard style guidelines)
- **Goal:** Clarity and correctness, not aesthetic purity

**Enforcement:**
- CI workflow (`naming-kebab-case.yml`) MUST enforce kebab-case for script surfaces only
- PRs with non-conforming script filenames MUST fail CI
- Rust (`.rs`) files are explicitly excluded from kebab-case checks

**Exceptions:**
- Language-mandated files (e.g., `__init__.py`, `Cargo.toml`) are exempt
- Files outside script surfaces are not subject to kebab-case requirement
- All language source files follow their respective ecosystem conventions

---

## 8. New: Token Budget / Runway Check (Normative for Constrained Agents)

Constrained agents often cannot reliably introspect their remaining context. To prevent starting work that will likely truncate mid-edit, agents MUST perform a **runway check** before beginning large refactor items.

### 8.1 Rule

Before starting a work item that involves editing a file or diff larger than a threshold (default: 300 lines), the agent MUST:

- estimate whether it can complete the item *and* produce a complete patch/output within its remaining budget,
- and if uncertain, STOP and request a fresh session or narrower scope.

### 8.2 Practical heuristic

If:
- file is > 300 lines **and**
- the agent’s remaining message budget is plausibly < ~4k tokens (or unknown),
then:

- DO NOT start the edit.
- Instead, propose:
  - splitting into smaller chunks,
  - or extracting only the relevant function/region,
  - or switching to patch-based/snapshot mode.

This prevents “half-edits” and hallucinated endings.

---

## 9. New: Diagnostic Loop for `npm ci --ignore-scripts`

Using `npm ci --ignore-scripts` can be a safe default, but it can also cause confusing downstream failures if dependencies rely on postinstall scripts (native modules, generated files, etc.).

### 9.1 Rule

If:
- `npm ci --ignore-scripts` succeeds,
- but builds/tests fail with missing modules, missing generated artifacts, or “module not found” errors,

then the agent MUST perform a diagnostic loop:

1. Identify the missing artifact/module.
2. Check whether it is typically produced by:
   - `postinstall`,
   - `prepare`,
   - `install`,
   - native build steps.
3. If evidence indicates postinstall is required:
   - STOP and ask the user whether scripts may be enabled for install in this repository context,
   - or propose a safer alternative (e.g., allowlist scripts, run install in a sandbox, or CI-only execution).

This prevents circular “build failed” loops that constrained agents misinterpret.

---

## 10. Metrics (Recap + Optional Expansion)

Suggested metrics now explicitly include:
- wrapper-invoked vs raw command ratio,
- number of restarts that avoided recomputation due to archived logs,
- time-to-resume after failure,
- and failure artifact completeness.

---

## 11. TL;DR

This framework is a “prosthetic frontal cortex” for agents.

It provides:
- executive function (chunking, stop conditions),
- durable state (journals),
- safety inhibition (fail closed),
- and compatibility across constrained and capable models.

Reliability comes from explicit state, not from hope, memory, or “bigger context windows.”

This is not overengineering.

This is survival engineering.
