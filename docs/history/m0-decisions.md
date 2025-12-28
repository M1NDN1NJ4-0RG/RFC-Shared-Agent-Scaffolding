# M0 Decisions (Final) — Contract Clarity Foundation

**Status:** DECIDED  
**Date Finalized:** 2025-12-26  
**Source:** Commit c60e5c3, RFC v0.1.0 sections 7.1-7.5

This document records the **final, authoritative decisions** for all M0 (Milestone 0) decision gates.
These decisions establish the foundational behavioral contract for the RFC Shared Agent Scaffolding system.

All implementations MUST align with these decisions.

---

## M0-P1-I1: `safe-run` Logging Semantics

**Decision:** Split stdout and stderr (Option B)

### Requirements

`safe-run` MUST:
- Capture stdout and stderr **separately**
- Include clear section markers in log files:
  - `=== STDOUT ===`
  - `=== STDERR ===`
- Preserve both streams in their entirety in failure logs
- Preserve exit codes regardless of output format

### Rationale

Split streams provide richer debugging information and allow agents to distinguish between
actual program output (stdout) and diagnostic messages (stderr). While combined output
is simpler, the additional plumbing cost is minimal and the diagnostic value is significant.

---

## M0-P1-I2: Failure Log File Naming Scheme

**Decision:** Deterministic, non-overwriting naming with timestamp + PID + status

### Required Format

```
{ISO8601_TIMESTAMP}-pid{PID}-{STATUS}.log
```

### Example

```
20251226T020707Z-pid4821-FAIL.log
```

### Requirements

- **Timestamp:** ISO 8601 format with timezone (UTC recommended)
- **PID:** Process ID included for correlation and debugging
- **Status:** One of: `FAIL`, `ABORTED`, `ERROR`
- **Directory:** `.agent/FAIL-LOGS/`
- **No random suffixes:** Deterministic naming for predictability
- **No overwrites:** Each failure creates a unique file

### Rationale

Deterministic naming enables:
- Predictable log discovery and sorting
- Process correlation via PID
- Chronological ordering via timestamp
- No data loss from overwrites
- Simple glob patterns for cleanup/archival

---

## M0-P1-I3: `safe-archive` No-Clobber Semantics

**Decision:** Hybrid approach with auto-suffix default

### Default Behavior: Auto-suffix

When destination file exists:
- Append numeric suffix (e.g., `.2`, `.3`, `.4`)
- Continue incrementing until unique filename found
- Never overwrite existing files

### Opt-in: Strict No-Clobber (Fail Fast)

Enable via:
- CLI flag: `--no-clobber`
- Environment variable: `SAFE_ARCHIVE_NO_CLOBBER=1`

When enabled:
- Exit with error if destination exists
- Do not create any file
- Provide clear error message

### Rationale

Hybrid approach balances safety and convenience:
- Default auto-suffix prevents data loss while allowing automated workflows
- Opt-in strict mode enables workflows that require explicit collision handling
- Both modes guarantee no silent overwrites

---

## M0-P2-I1: Auth Method & Header Semantics

**Decision:** Precedence A with Bearer token format

### Auth Precedence (Highest to Lowest)

1. **Explicit CLI arguments** (e.g., `--token <value>`)
2. **Environment variables** (`GITHUB_TOKEN`, `TOKEN`)
3. **Configuration files** (e.g., `.env`, config files)
4. **`gh auth` token** (via `gh auth token` command)

### Header Format

```
Authorization: Bearer <token>
```

### Security Requirements

- Token values MUST **never** be logged
- Tokens MUST NOT appear in error messages
- Tokens MUST NOT be included in debug output

### Failure Behavior

If no auth available:
- Exit with code **2** (auth/permission error)
- Provide clear error message indicating auth is required
- Suggest resolution steps (set GITHUB_TOKEN, run `gh auth login`, etc.)

### Rationale

- Bearer token format is GitHub API standard
- Precedence order allows environment-specific overrides while respecting explicit user input
- Never logging tokens prevents accidental credential exposure
- Exit code 2 enables scripts to distinguish auth failures from other errors

---

## M0-P2-I2: Exit Code Taxonomy

**Decision:** Stable exit code ranges for deterministic automation

### Exit Code Table

| Code   | Meaning                          | Examples                                    |
|--------|----------------------------------|---------------------------------------------|
| 0      | Success                          | Operation completed successfully            |
| 1      | General failure                  | Unclassified error                          |
| 2      | Auth/permission error            | Missing token, 401, 403                     |
| 3      | Usage/validation error           | Missing required args, invalid input        |
| 10-19  | Dependency errors                | Missing `jq`, `gh`, `pwsh`, `curl`          |
| 20-29  | Network errors                   | Timeout, connection refused, DNS failure    |
| 30-39  | Parse errors                     | Malformed JSON, invalid response format     |
| 40-49  | File system errors               | Permission denied, disk full, path not found|
| 50-59  | Ruleset/policy errors            | Ruleset not found, ruleset mismatch         |

### Implementation Requirements

- Implementations MUST use these codes consistently
- Error messages SHOULD be informative but not brittle
- Tests MUST assert exact exit codes for failure classes
- Exit codes MUST be stable across versions

### Rationale

Deterministic exit codes enable:
- Agent scripts to make informed decisions based on failure type
- Automated retry logic (e.g., retry network errors, fail fast on auth errors)
- Better error reporting and debugging
- Conformance testing across language implementations

---

## Implementation Status

### Completed
- [x] M0-P1-I1: RFC updated (section 7.1)
- [x] M0-P1-I2: RFC updated (section 7.2)
- [x] M0-P1-I3: RFC updated (section 7.3)
- [x] M0-P2-I1: RFC updated (section 7.4)
- [x] M0-P2-I2: RFC updated (section 7.5)

### Remaining Work (M1+)
- [ ] Align all language implementations to M0 contract
- [ ] Update all tests to assert M0 behaviors
- [ ] Create conformance test vectors
- [ ] Enable CI enforcement

---

## References

- **RFC v0.1.0:** `rfc-shared-agent-scaffolding-v0.1.0.md` sections 7.1-7.5
- **Epic Tracker:** Issue #3
- **Decision Commit:** c60e5c38d87d5855fe4d024a7129f9456d194c17
