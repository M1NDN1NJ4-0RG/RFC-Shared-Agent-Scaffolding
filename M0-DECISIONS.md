# M0 Decision Gates — FINAL DECISIONS (Authoritative)

**Status:** DECIDED (as of 2025-12-26)  
**References:** Epic #3 (Refs #3)

This document records the final, authoritative decisions for all M0 (Contract Clarity) decision gates from the canonical epic tracker.

---

## M0-P1 — Safe Wrapper Contract Finalization

### M0-P1-I1 — safe-run Logging Semantics

**Decision:** **Split stdout and stderr**

**Rationale:** Provides richer debugging information and allows distinguishing between normal output and error messages.

**Implementation Requirements:**
- `safe-run` MUST capture stdout and stderr separately
- Log files MUST include clear section markers (e.g., `=== STDOUT ===`, `=== STDERR ===`)
- Both streams MUST be preserved in their entirety in failure logs
- Exit codes MUST be preserved regardless of output format

---

### M0-P1-I2 — Failure Log File Naming Scheme

**Decision:** **Deterministic, non-overwriting naming (no randomness)**

**Format:** `{ISO8601_TIMESTAMP}-pid{PID}-{STATUS}.log`

**Examples:**
- `20251226T020707Z-pid4821-FAIL.log`
- `20251226T020830Z-pid5142-ABORTED.log`

**Requirements:**
- Timestamp MUST be ISO 8601 format with timezone (UTC recommended)
- PID MUST be included for correlation
- Status MUST be one of: `FAIL`, `ABORTED`, `ERROR`
- Extension MUST be `.log`
- Directory MUST be `.agent/FAIL-LOGS/`
- No random suffixes or sequences permitted
- Uniqueness guaranteed by timestamp + PID combination

---

### M0-P1-I3 — safe-archive No-Clobber Semantics

**Decision:** **Hybrid approach**

**Default Behavior (Option B):** Auto-suffix for archive outputs
- If `archive.tar.gz` exists, create `archive.2.tar.gz`
- If `archive.2.tar.gz` exists, create `archive.3.tar.gz`
- Continue incrementing until unique filename found

**Opt-in Flag (Option A):** Strict no-clobber (fail fast)
- Flag: `--no-clobber` or `SAFE_ARCHIVE_NO_CLOBBER=1`
- Behavior: Exit with error if destination exists
- Exit code: 1 (failure due to existing file)
- Error message MUST clearly indicate collision

**Implementation Requirements:**
- Default MUST be auto-suffix behavior
- Strict mode MUST be opt-in via explicit flag or environment variable
- Both modes MUST preserve existing files (never overwrite)
- Log messages MUST indicate which mode is active and what action was taken

---

## M0-P2 — Preflight Automerge Ruleset Contract

### M0-P2-I1 — Auth Method & Header Semantics

**Decision:** **Precedence A with GitHub-compatible headers**

**Authentication Precedence (highest to lowest):**
1. Explicit CLI arguments (`--token`, `--auth`)
2. Environment variables (`GITHUB_TOKEN`, `TOKEN`)
3. Configuration files (if applicable)
4. `gh auth` token (via `gh` CLI)

**Authorization Header Format:**
- MUST use: `Authorization: Bearer <token>`
- This is GitHub API v3/v4 compatible format

**Implementation Requirements:**
- Token resolution MUST follow precedence order strictly
- Token values MUST never be logged or printed
- If no auth is available, exit with code 2 (auth error)
- Error messages MUST guide users to auth setup without exposing tokens

**GitHub Compatibility Notes:**
- Some older GitHub API endpoints may accept `Authorization: token <token>`
- Implementations SHOULD prefer `Bearer` format for forward compatibility
- Document any endpoint-specific variations if encountered

---

### M0-P2-I2 — Exit Code Taxonomy

**Decision:** **Option B — Stable exit code ranges per subsystem**

**Exit Code Ranges:**

| Range | Category | Description |
|-------|----------|-------------|
| 0 | Success | Operation completed successfully |
| 1 | General failure | Command/operation failed (unspecified) |
| 2 | Auth/permission error | Missing credentials, forbidden, unauthorized |
| 3 | Usage/validation error | Invalid arguments, missing required params |
| 4-9 | Reserved | For future subsystem-specific errors |
| 10-19 | Dependency errors | Missing tools (`jq`, `gh`, `curl`, etc.) |
| 20-29 | Network errors | Timeouts, connection failures, DNS issues |
| 30-39 | Parse errors | Malformed JSON, invalid responses |
| 40-49 | File system errors | File not found, permission denied, disk full |
| 50-59 | Ruleset/policy errors | Ruleset not found, validation failed |
| 100+ | Reserved | For implementation-specific extensions |

**Specific Exit Codes:**
- `0` - Success
- `1` - General failure (default for unexpected errors)
- `2` - Authentication or permission error
- `3` - Usage error (invalid arguments)
- `10` - Missing dependency tool
- `20` - Network failure
- `30` - JSON parse failure
- `40` - File system error
- `50` - Ruleset validation failure

**Implementation Requirements:**
- All scripts MUST use these exit codes consistently
- Error messages SHOULD indicate the exit code category
- Callers MAY use exit code ranges to determine retry strategy
- Exit code 0 MUST only be used for successful operations

---

## Implementation Status

These decisions are now canonical and non-negotiable. Implementation work is tracked separately:

- M1-P1-I1: jq Error Noise Suppression (COMPLETED)
- M1-P2-I1: Python 3 implementation alignment (PENDING M0 completion)
- M1-P4-I1: Perl test discovery (COMPLETED)
- M2+: Conformance infrastructure (BLOCKED on M0 documentation completion)

---

## Version History

- 2025-12-26: Initial M0 decisions finalized and documented
