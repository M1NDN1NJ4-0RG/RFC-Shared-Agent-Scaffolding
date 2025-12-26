# Epic Issue #3 Update - M0 Decisions Finalized

**This file contains the updated content for Epic Issue #3 to reflect finalized M0 decisions.**

## Section to Add (Insert after "Split plan" section, before "OVERARCHING OBJECTIVE")

---

# M0 DECISIONS (FINAL) ✅

**Status:** ALL M0 DECISION GATES RESOLVED  
**Date Finalized:** 2025-12-26  
**Authority:** See `M0-DECISIONS.md` for complete specification

All M0 (Milestone 0) decision gates have been finalized and documented in the RFC v0.1.0.
The contract is now frozen and implementation work can proceed.

## Quick Reference

| Item ID | Decision | Status |
|---------|----------|--------|
| **M0-P1-I1** | Split stdout/stderr with section markers | ✅ DECIDED |
| **M0-P1-I2** | `{ISO8601}-pid{PID}-{STATUS}.log` format | ✅ DECIDED |
| **M0-P1-I3** | Hybrid: auto-suffix default, opt-in strict | ✅ DECIDED |
| **M0-P2-I1** | Bearer token, precedence: CLI > env > config > gh | ✅ DECIDED |
| **M0-P2-I2** | Exit code ranges: 0=success, 2=auth, 3=usage, 10-19=deps, etc. | ✅ DECIDED |

### M0-P1-I1: `safe-run` Logging Semantics
**Decision:** Split stdout and stderr  
- Capture streams separately
- Use `=== STDOUT ===` and `=== STDERR ===` markers
- Preserve both streams in failure logs

### M0-P1-I2: Failure Log Naming
**Decision:** Deterministic timestamp + PID + status  
- Format: `20251226T020707Z-pid4821-FAIL.log`
- Location: `.agent/FAIL-LOGS/`
- No random suffixes, no overwrites

### M0-P1-I3: `safe-archive` No-Clobber
**Decision:** Hybrid approach  
- Default: auto-append numeric suffix (`.2`, `.3`, etc.)
- Opt-in strict: `--no-clobber` or `SAFE_ARCHIVE_NO_CLOBBER=1`

### M0-P2-I1: Auth & Headers
**Decision:** Bearer token with precedence chain  
- Header: `Authorization: Bearer <token>`
- Precedence: CLI args > env vars > config files > `gh auth`
- Never log tokens; exit code 2 if no auth

### M0-P2-I2: Exit Code Taxonomy
**Decision:** Stable ranges  
- 0: Success
- 2: Auth/permission
- 3: Usage/validation
- 10-19: Dependencies
- 20-29: Network
- 30-39: Parse
- 40-49: Filesystem
- 50-59: Ruleset/policy

**Next:** Implementations must align to these contracts (M1 milestone).

---

## Updated Child Issue Tracking Table

Replace the existing table with:

| Stable ID | Title | Status | Issue Link |
|---|---|---|---|
| M0-P1-I1 | `safe-run` Logging Semantics | ✅ DECIDED | See M0-DECISIONS.md |
| M0-P1-I2 | Failure Log File Naming Scheme | ✅ DECIDED | See M0-DECISIONS.md |
| M0-P1-I3 | `safe-archive` No-Clobber Semantics | ✅ DECIDED | See M0-DECISIONS.md |
| M0-P2-I1 | Auth Method &amp; Header Semantics | ✅ DECIDED | See M0-DECISIONS.md |
| M0-P2-I2 | Exit Code Taxonomy | ✅ DECIDED | See M0-DECISIONS.md |
| M1-P1-I1 | jq Error Noise Suppression | ✅ COMPLETED | PR #4 |
| M1-P2-I1 | Test vs Implementation Drift | 🔄 IN PROGRESS | TBA |
| M1-P3-I1 | Python 2 Support Policy | ⬜ Not started | TBA |
| M1-P4-I1 | Test Runner Path Correction | ✅ COMPLETED | PR #4 |
| M1-P5-I1 | CI-Ready PowerShell Validation | ⬜ Not started | TBA |
| M2-P1-I1 | `conformance/vectors.json` | ⬜ Not started | TBA |
| M2-P2-I1 | Golden Behavior Assertions | ⬜ Not started | TBA |
| M3-P1-I1 | `.docs/agent` &amp; `.docs/journal` Availability | ⬜ Not started | TBA |
| M4-P1-I1 | Multi-Language CI Enforcement | ⬜ Not started | TBA |

---

## Updated M0-P1-I1 Checklist

Replace the checklist for M0-P1-I1 with:

**Checklist / TODO**  
- [x] DECISION GATE: Choose log format (Option A vs B) → **DECISION: Option B (Split)**
- [x] Update RFC normative language to specify the chosen format → **DONE: RFC v0.1.0 section 7.1**
- [ ] Update all implementations to match the chosen format
- [ ] Update all tests to match the chosen format
- [ ] Add at least 2 edge-case tests (binary-ish output, huge output, non-UTF8 bytes if applicable)

---

## Updated M0-P1-I2 Checklist

Replace the checklist for M0-P1-I2 with:

**Checklist / TODO**  
- [x] DECISION GATE: Decide required fields → **DECISION: ISO8601 timestamp + PID + status**
- [x] DECISION GATE: Decide extension and directory rules → **DECISION: `.log` in `.agent/FAIL-LOGS/`**
- [x] Codify allowed/forbidden patterns → **DONE: No overwrites, deterministic sort order**
- [ ] Update implementations and tests
- [ ] Add collision test (existing file with same base name)

---

## Updated M0-P1-I3 Checklist

Replace the checklist for M0-P1-I3 with:

**Checklist / TODO**  
- [x] DECISION GATE: Choose collision strategy → **DECISION: Hybrid (auto-suffix default)**
- [x] DECISION GATE: Specify return code / warning behavior → **DECISION: Exit error for strict mode**
- [x] Update RFC normative language → **DONE: RFC v0.1.0 section 7.3**
- [ ] Update implementations and tests
- [ ] Add collision test vectors and assertions

---

## Updated M0-P2-I1 Checklist

Replace the checklist for M0-P2-I1 with:

**Checklist / TODO**  
- [x] DECISION GATE: Define auth precedence → **DECISION: CLI > env > config > gh auth**
- [x] DECISION GATE: Define header format → **DECISION: `Authorization: Bearer <token>`**
- [x] DECISION GATE: Define behavior when no auth available → **DECISION: Exit code 2**
- [ ] Update implementations and tests to match contract
- [ ] Add fixture tests for 401/403 behaviors

---

## Updated M0-P2-I2 Checklist

Replace the checklist for M0-P2-I2 with:

**Checklist / TODO**  
- [x] DECISION GATE: Choose exit code map → **DECISION: Stable ranges (see M0-DECISIONS.md)**
- [x] Update RFC normative language → **DONE: RFC v0.1.0 section 7.5**
- [ ] Implement exit code mapping consistently across bundles
- [ ] Add test vectors for each failure class
- [ ] Confirm messages are informative but not brittle

---

## Instructions for Updating Epic #3

1. Add the "M0 DECISIONS (FINAL)" section after "Split plan" and before "OVERARCHING OBJECTIVE"
2. Replace the "Child Issue Tracking Table" with the updated version
3. Update the checklists for M0-P1-I1, M0-P1-I2, M0-P1-I3, M0-P2-I1, and M0-P2-I2
4. Ensure NO auto-close keywords are used (use "Refs #3" only)

---

**Note:** This update documents that M0 decision gates are complete and shifts focus to M1 implementation work.
