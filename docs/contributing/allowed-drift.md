# Allowed Behavioral Differences

**Status:** Empty (strict parity enforced)  
**Last Updated:** 2025-12-26  
**Decision Authority:** See M2-P2-I1-DRIFT-DETECTION.md

---

## Current Policy

**Default posture:** Strict parity — all implementations must produce identical behavior.

**Allowed differences:** NONE

---

## How to Add an Exception

When drift is detected by the CI gate:

1. **Investigate root cause**
   - Is this a bug in the implementation?
   - Is this an acceptable platform difference?

2. **If bug:** Fix the implementation, do NOT add exception

3. **If acceptable platform difference:**
   - Document justification below
   - Update drift detection workflow to allow this specific case
   - Keep scope minimal (narrowest possible allowance)
   - Get maintainer approval

---

## Exception Template

When adding the first exception, use this format:

```markdown
### Exception #001: <Brief Description>

**Date Added:** YYYY-MM-DD
**Affected Implementations:** <language(s)>
**M0 Contract Reference:** <if applicable>
**Vector:** <conformance vector ID>

**Drift Observed:**
<Exact description of divergent behavior>

**Root Cause:**
<Platform/language difference that causes drift>

**Justification:**
<Why this is acceptable and not a bug>

**Scope:**
<Narrow description of what is allowed to differ>

**Detection Update:**
<What was changed in drift-detection.yml to allow this>

**Approved By:** @username
**References:** <PR, issue, etc.>
```

---

## Examples (Hypothetical — Not Currently Allowed)

**These are examples only. Do NOT treat as allowed until explicitly added above.**

### Hypothetical Example: Signal Exit Codes

**Drift Observed:** SIGTERM produces exit code 143 on Linux, 130 on macOS

**Root Cause:** Platform signal handling differs

**Justification:** Both codes correctly indicate terminated process

**Scope:** Only for SIGTERM/SIGINT handling in safe-run

**This is NOT currently allowed. Listed as example only.**

---

## Statistics

**Total exceptions:** 0  
**Last exception added:** N/A  
**Drift failures this month:** 0 (new gate)

---

## References

- **M2-P2-I1 Implementation:** M2-P2-I1-DRIFT-DETECTION.md
- **Drift Detection Workflow:** .github/workflows/drift-detection.yml
- **Conformance Vectors:** conformance/vectors.json
- **M0 Contract:** M0-DECISIONS.md

---

**Refs:** #3, M2-P2-I1
