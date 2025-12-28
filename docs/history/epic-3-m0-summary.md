# Epic #3 — M0 Milestone Complete ✅

**Date:** 2025-12-26  
**Status:** ALL M0 DECISION GATES FINALIZED  
**Refs:** #3

---

## M0 Decisions Summary

All M0 (Contract Clarity) decision gates have been resolved and documented. The behavioral contract is now frozen and implementation work can proceed.

### Quick Reference Table

| Stable ID | Decision | Status | Documentation |
|-----------|----------|--------|---------------|
| **M0-P1-I1** | Split stdout/stderr with `=== STDOUT ===` / `=== STDERR ===` markers | ✅ DECIDED | M0-DECISIONS.md, RFC v0.1.0 §7.1 |
| **M0-P1-I2** | `{ISO8601}-pid{PID}-{STATUS}.log` format in `.agent/FAIL-LOGS/` | ✅ DECIDED | M0-DECISIONS.md, RFC v0.1.0 §7.2 |
| **M0-P1-I3** | Hybrid no-clobber: auto-suffix default, opt-in strict mode | ✅ DECIDED | M0-DECISIONS.md, RFC v0.1.0 §7.3 |
| **M0-P2-I1** | `Authorization: Bearer <token>`, precedence: CLI > env > config > gh | ✅ DECIDED | M0-DECISIONS.md, RFC v0.1.0 §7.4 |
| **M0-P2-I2** | Exit code taxonomy: 0=success, 2=auth, 3=usage, 10-19=deps, etc. | ✅ DECIDED | M0-DECISIONS.md, RFC v0.1.0 §7.5 |

---

## M1 Implementation Status

| Stable ID | Item | Status | Notes |
|-----------|------|--------|-------|
| **M1-P1-I1** | jq Error Noise Suppression | ✅ COMPLETED | PR #4 |
| **M1-P2-I1** | Test vs Implementation Drift (Python 3) | ✅ COMPLETED | PR #8 |
| **M1-P3-I1** | Python 2 Support Policy | ✅ DECIDED | Option A: Dropped (PR #9) |
| **M1-P4-I1** | Test Runner Path Correction (Perl) | ✅ COMPLETED | PR #4 |
| **M1-P5-I1** | CI-Ready PowerShell Validation | ⬜ NOT STARTED | - |

---

## M2-M4 Status

All M2 (Conformance Infrastructure), M3 (Example Scaffold), and M4 (CI Hardening) items remain **NOT STARTED**.

---

## Key Decisions Detail

### M0-P1-I1: `safe-run` Logging Semantics
**Decision:** Split stdout and stderr (Option B)

Requirements:
- Capture stdout and stderr **separately**
- Include section markers: `=== STDOUT ===` and `=== STDERR ===`
- Preserve both streams in failure logs
- Empty streams still get markers (empty section)

### M0-P1-I2: Failure Log Naming
**Decision:** Deterministic timestamp + PID + status

Format: `20251226T020707Z-pid4821-FAIL.log`

Requirements:
- ISO 8601 UTC timestamp (YYYYMMDDTHHMMSSZ)
- Process ID for correlation
- Status: FAIL, ABORTED, or ERROR (uppercase)
- Extension: `.log`
- Directory: `.agent/FAIL-LOGS/`
- No overwrites, deterministic sorting

### M0-P1-I3: `safe-archive` No-Clobber
**Decision:** Hybrid approach

Default (auto-suffix):
- Append numeric suffix if file exists (`.2`, `.3`, etc.)
- Never overwrite existing files

Opt-in strict mode:
- Flag: `--no-clobber` or env var `SAFE_ARCHIVE_NO_CLOBBER=1`
- Exit with error if destination exists
- No file created

### M0-P2-I1: Auth & Headers
**Decision:** Bearer token with precedence chain

Header format: `Authorization: Bearer <token>`

Auth precedence (highest to lowest):
1. Explicit CLI arguments (`--token`)
2. Environment variables (`GITHUB_TOKEN`, `TOKEN`)
3. Configuration files
4. `gh auth token` command

Security:
- Never log tokens
- Exit code 2 if no auth available
- Clear error message with resolution steps

### M0-P2-I2: Exit Code Taxonomy
**Decision:** Stable exit code ranges

| Code | Meaning | Examples |
|------|---------|----------|
| 0 | Success | Operation completed |
| 1 | General failure | Unclassified error |
| 2 | Auth/permission | Missing token, 401, 403 |
| 3 | Usage/validation | Missing args, invalid input |
| 10-19 | Dependencies | Missing jq, gh, curl |
| 20-29 | Network | Timeout, connection refused |
| 30-39 | Parse | Malformed JSON |
| 40-49 | Filesystem | Permission denied, disk full |
| 50-59 | Ruleset/policy | Ruleset not found |

---

## What This Means

### For Implementers
- All M0 decisions are final and **MUST** be followed
- No implementation may deviate from these contracts
- All tests must validate M0 behaviors

### For Epic Tracker
- M0 checklist items can be marked as DECIDED
- Focus shifts to M1 implementation work
- Conformance testing (M2) can begin once implementations align

### Next Steps
1. Complete M1 implementation alignment
2. Create conformance test vectors (M2-P1-I1)
3. Enable CI enforcement (M4-P1-I1)

---

## References

- **Full Decisions:** `M0-DECISIONS.md`
- **RFC Sections:** RFC v0.1.0 sections 7.1-7.5
- **Epic Tracker:** Issue #3
- **Update Instructions:** `EPIC-3-UPDATE.md`

---

**Note:** This file serves as a quick reference for M0 decisions. For complete specifications, see `M0-DECISIONS.md` and RFC v0.1.0.

**Refs:** #3
