# M2-P2-I1: Golden Behavior Assertions — Implementation Guide

**Status:** Implemented via CI drift detection gate  
**Date:** 2025-12-26  
**Decision Authority:** @m1ndn1nj4

---

## Decision Summary

M2-P2-I1 is implemented through a **mandatory CI drift detection gate** that enforces strict cross-language parity.

### Key Decisions

1. ✅ **CI drift detection gate is mandatory**
   - Primary enforcement mechanism for behavioral parity
   - Fails deterministically when implementations diverge
   - Runs on every PR affecting implementations or conformance vectors

2. ❌ **Do NOT exhaustively specify allowed differences**
   - No comprehensive list of platform differences
   - Exceptions added incrementally as real drift surfaces
   - Each exception must be explicitly justified and minimally scoped

3. ❌ **Do NOT create full parity test suite**
   - No standalone parity validation framework
   - Leverage existing conformance vectors
   - Incremental assertions driven by CI failures

---

## Operational Posture

**Default:** Strict parity — all implementations must produce identical behavior.

**Exception policy:**
- Exceptions are **forbidden by default**
- Exceptions require:
  1. Real drift surfaced by CI gate
  2. Explicit justification documented in-repo
  3. Minimal scope (narrowest possible allowance)
  4. Approval from maintainer

**Philosophy:** The CI drift gate is the source of truth. Let real failures drive exceptions, not speculation.

---

## Implementation

### CI Drift Gate

**Workflow:** `.github/workflows/drift-detection.yml`

**What it does:**
1. Runs conformance vectors on all language bundles
2. Captures outputs (exit codes, stdout, stderr, artifacts)
3. Compares outputs across implementations
4. Fails if outputs diverge beyond allowed tolerances

**When it runs:**
- Every PR affecting implementations (`scripts/*/`)
- Every PR affecting conformance vectors (`conformance/`)
- Push to main branch
- Manual dispatch

**Failure behavior:**
- Exits non-zero on drift
- Reports which implementations diverged
- Shows diff between outputs
- Blocks merge

---

## Allowed Differences (Minimal Initial Set)

**Currently allowed:** NONE

**Future allowances must be added here when justified.**

### How to Add an Exception

**When drift is detected:**

1. **Investigate:** Determine root cause of divergence
2. **Decide:** Is this acceptable platform difference or a bug?
   - If bug: Fix the implementation
   - If acceptable: Document and add narrow exception
3. **Document:** Add entry to `ALLOWED_DRIFT.md` (to be created when first exception needed)
4. **Update gate:** Modify drift detection to allow this specific difference
5. **Commit:** Include justification in commit message

**Example acceptable difference (hypothetical):**
- Exit signal codes (SIGTERM = 143 on Linux, 130 on macOS)
- Justification: Platform signal handling differs, not a behavioral bug
- Scope: Only for SIGTERM handling in safe-run ABORTED logs

---

## Drift Detection Strategy

### Phase 1: Basic Output Comparison (Current)
- Compare exit codes across implementations
- Compare presence/absence of artifacts
- Compare log file patterns
- Fail on any unexpected divergence

### Phase 2: Semantic Comparison (Future, if needed)
- Normalize timestamps (keep format, ignore value)
- Normalize PIDs (keep pattern, ignore value)
- Normalize paths (handle platform separators)
- Only if Phase 1 produces false positives

**Default to Phase 1 until proven insufficient.**

---

## CI Gate Design Principles

1. **Fail closed:** Drift is always an error until proven acceptable
2. **Explicit allowances:** No implicit tolerance
3. **Minimal scope:** Exceptions narrowly target specific cases
4. **Documented:** Every allowance has a justification
5. **Incremental:** Add exceptions only when real drift surfaces

---

## Metrics

**Track over time:**
- Number of drift failures per month
- Number of allowed exceptions
- Ratio of bugs vs acceptable differences

**Goal:** Low drift rate, minimal exceptions, high confidence in parity.

---

## Example Workflow Output

**When implementations match (success):**
```
✅ Bash:       safe-run-001 → exit 0, no artifacts
✅ Python 3:   safe-run-001 → exit 0, no artifacts
✅ Perl:       safe-run-001 → exit 0, no artifacts
✅ PowerShell: safe-run-001 → exit 0, no artifacts

✅ All implementations match. Parity validated.
```

**When drift detected (failure):**
```
❌ DRIFT DETECTED: safe-run-002

Bash:       exit 7, log format: 20251226T051234Z-pid1234-FAIL.log
Python 3:   exit 7, log format: 20251226T051234Z-pid1234-FAIL.log
Perl:       exit 7, log format: 20251226-051234-pid1234-FAIL.log ⚠️
PowerShell: exit 7, log format: 20251226T051234Z-pid1234-FAIL.log

❌ Perl output diverges from expected format.
   Expected: YYYYMMDDTHHMMSSZ-pidPID-STATUS.log
   Actual:   YYYYMMDD-HHMMSS-pidPID-STATUS.log (missing 'T' and 'Z')

FAIL: Behavioral divergence detected. Fix Perl implementation or justify exception.
```

---

## Responsibilities

### Implementers
- Ensure implementations match M0 contract exactly
- Run drift detection locally before submitting PR
- Fix divergence or justify exception

### Maintainers
- Review drift failures
- Approve/reject exception requests
- Keep allowed differences minimal

### CI
- Enforce strict parity by default
- Block merges on drift
- Provide actionable failure messages

---

## Success Criteria

M2-P2-I1 is successful when:

- [x] CI drift gate is operational
- [x] Gate runs on every relevant PR
- [ ] Gate has caught at least 1 real drift (validates effectiveness)
- [ ] Exception policy is documented
- [ ] Allowed differences list exists (even if empty)

---

## References

- **Epic Tracker:** Issue #3, M2-P2-I1
- **Conformance Vectors:** `conformance/vectors.json`
- **M0 Contract:** `M0-DECISIONS.md`
- **Decision Prompt:** @m1ndn1nj4 2025-12-26

---

**Version:** 1.0  
**Last Updated:** 2025-12-26  
**Refs:** #3, M2-P2-I1
