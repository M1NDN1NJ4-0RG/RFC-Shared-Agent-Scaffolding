# Conformance Contract

## Overview

This document defines the **output format contract** that the Rust canonical tool implements and that all wrappers must produce. Conformance tests validate that tool outputs match these specifications exactly (or within explicitly-allowed equivalences).

## Contract Version

- **Contract Version:** M0-v0.1.0
- **Defined in:** [rfc-shared-agent-scaffolding-v0.1.0.md](../rfc-shared-agent-scaffolding-v0.1.0.md)
- **Test Vectors:** [conformance/vectors.json](../conformance/vectors.json)

## Output Modes

The canonical tool supports two output modes, controlled by the `SAFE_RUN_VIEW` environment variable:

### 1. Event Ledger Mode (Default)

**Trigger:** `SAFE_RUN_VIEW` not set, or `SAFE_RUN_VIEW=ledger`

**Format:**

The log file contains both split sections and an event ledger, as defined in RFC section 7.1.1:

```
=== STDOUT ===
Hello, world!

=== STDERR ===
Warning: deprecated API

--- BEGIN EVENTS ---
[SEQ=1][META] safe-run start: cmd="echo 'Hello, world!' >&2 echo 'Warning: deprecated API'"
[SEQ=2][STDOUT] Hello, world!
[SEQ=3][STDERR] Warning: deprecated API
[SEQ=4][META] safe-run exit: code=0
--- END EVENTS ---
```

**Requirements:**

1. **Split Sections** (M0 backward compatibility):
   - `=== STDOUT ===` section with stdout content
   - `=== STDERR ===` section with stderr content
   - Per-stream ordering preserved

2. **Event Ledger Section:**
   - Enclosed in `--- BEGIN EVENTS ---` and `--- END EVENTS ---` markers
   - Event format: `[SEQ=<seq>][<stream>] <text>`
   - `<seq>`: Monotonically increasing integer starting at 1
   - `<stream>`: One of `STDOUT`, `STDERR`, `META`
   - `<text>`: Exact text payload for that event

3. **Event Types:**
   - `META` with `safe-run start: cmd="<command>"` - marks command start (seq=1)
   - `STDOUT` - child process stdout line
   - `STDERR` - child process stderr line
   - `META` with `safe-run exit: code=<N>` - final event with exit code

4. **Per-Line Emission:** Each output line is a separate STDOUT/STDERR event

**Edge Cases:**

- Empty output: Only META events (start, exit)
- No stdout: STDOUT section empty, only STDERR events
- No stderr: STDERR section empty, only STDOUT events
- Non-zero exit: EXIT meta event includes non-zero code
- Signal termination: EXIT code reflects signal (128 + signal number)

### 2. Merged View Mode

**Trigger:** `SAFE_RUN_VIEW=merged`

**Format:**

```
Hello, world!
Warning: deprecated API
```

**Requirements:**

1. **Temporal Ordering:** Output preserves the order in which stdout/stderr were written
2. **No Prefixes:** Raw output without stream tags or sequence numbers
3. **No META Events:** START/END/EXIT metadata is suppressed
4. **Interleaved Streams:** stdout and stderr are merged as they occur

**Use Case:** Human-readable output for local development/debugging

## Exit Code Behavior

The canonical tool MUST forward the child process exit code according to these rules:

### Normal Exit

- Child exits with code N → tool exits with code N
- Range: 0-255

### Signal Termination (Unix-like)

- Child terminated by signal S → tool exits with code (128 + S)
- Examples:
  - SIGTERM (15) → exit code 143
  - SIGINT (2) → exit code 130
  - SIGKILL (9) → exit code 137

### Windows Termination

- Windows exit codes are preserved as-is
- Special codes (e.g., 0xC0000005 = access violation) are preserved

## Artifact Generation

The canonical tool MUST create log artifacts with the following behavior:

### Filename Pattern

```
safe-run-YYYYMMDD-HHMMSS-<random>.log
```

Example: `safe-run-20240115-103000-a3f9b2.log`

### No-Clobber Semantics

- If a log file already exists with the same timestamp, append random suffix
- Never overwrite existing logs
- Fail with error if unable to create unique filename after N attempts

### Custom Log Directory

- Default: `.agent/FAIL-LOGS/` (for failures)
- Override via `SAFE_LOG_DIR` environment variable
- Tool MUST create directory if it doesn't exist

### Log Content

Event ledger mode (default):
- Log file contains split sections (`=== STDOUT ===`, `=== STDERR ===`)
- Log file contains event ledger between `--- BEGIN EVENTS ---` and `--- END EVENTS ---` markers
- Event format: `[SEQ=N][STREAM] text`

Merged view mode:
- Log file contains merged stdout/stderr output
- Optional: Include metadata header/footer

## Conformance Testing Strategy

### Test Fixtures

Test vectors are defined in `conformance/vectors.json` using the established M0 format:

```json
{
  "version": "1.0",
  "m0_contract_version": "v0.1.0",
  "vectors": {
    "safe_run": [
      {
        "id": "safe-run-001",
        "name": "Success produces no artifacts",
        "m0_spec": [],
        "command": {
          "args": ["echo", "ok"],
          "env": {}
        },
        "expected": {
          "exit_code": 0,
          "stdout_contains": ["ok"],
          "artifacts_created": false
        }
      }
    ]
  }
}
```

See `conformance/vectors.json` for the complete set of test vectors covering M0 spec items.

### Conformance Harness

The harness:

1. Loads test vectors from `conformance/vectors.json`
2. Executes the Rust canonical tool with specified args/env
3. Captures stdout, stderr, exit code, and artifacts
4. Validates against expected values
5. Reports pass/fail for each vector

### Wrapper Conformance

Wrapper conformance tests:

1. Execute each language wrapper with the same test vectors
2. Compare wrapper output to Rust canonical output
3. Validate byte-for-byte equivalence (or allowed equivalences)

**Allowed Equivalences:**

- Timestamp values may differ (within reason)
- Random filename suffixes may differ
- Whitespace normalization (CRLF vs LF) if explicitly allowed by contract

**Prohibited Drift:**

- Sequence numbers MUST match exactly
- Event types MUST match exactly
- Exit codes MUST match exactly
- Data content MUST match exactly (after normalization)

## CI Enforcement

### Required CI Jobs

1. **Rust Conformance:** Run conformance harness against Rust tool
2. **Wrapper Conformance:** Run wrapper tests for each language
3. **Cross-Platform Matrix:** Test on Linux, macOS, Windows

### Failure Conditions

CI MUST fail if:

- Any conformance vector fails
- Any wrapper output differs from Rust canonical output
- Exit codes don't match
- Artifacts are missing or malformed

### Golden Outputs

Expected outputs are stored in:

```
conformance/
├── expected/
│   ├── safe_run_basic_stdout.json
│   ├── safe_run_stderr_only.json
│   └── ...
└── vectors.json
```

## Normalization Rules

### Line Endings

- Unix/Linux: LF (`\n`)
- Windows: CRLF (`\r\n`)
- Contract allows either, tools normalize internally to LF for text processing

### Encoding

- UTF-8 required for all text
- Binary output: Base64-encoded if needed in event ledger text field

### Whitespace

- Trailing whitespace on data lines is preserved
- Empty lines produce STDOUT/STDERR events with empty text field

## Versioning & Compatibility

### Contract Versioning

Contract changes are versioned:

- **Patch:** Bug fixes, clarifications (backward compatible)
- **Minor:** New optional features (backward compatible)
- **Major:** Breaking changes (e.g., new event types, format changes)

### Tool Versioning

The Rust tool reports its version via `--version`:

```
safe-run 0.1.0 (contract: M0-v0.1.0)
```

### Wrapper Compatibility

Wrappers MUST declare the contract version they target in their help text or header.

## References

- [rfc-shared-agent-scaffolding-v0.1.0.md](../rfc-shared-agent-scaffolding-v0.1.0.md)
- [Rust Canonical Tool](../architecture/rust-canonical-tool.md)
- [Wrapper Discovery](../architecture/wrapper-discovery.md)
- [Test Vectors](../conformance/vectors.json)
- [EPIC #33: Rust Canonical Tool](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues/33)
