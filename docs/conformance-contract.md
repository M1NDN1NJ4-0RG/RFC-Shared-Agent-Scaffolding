# Conformance Contract

## Overview

This document defines the **output format contract** that the Rust canonical tool implements and that all wrappers must produce. Conformance tests validate that tool outputs match these specifications exactly (or within explicitly-allowed equivalences).

## Contract Version

- **Contract Version:** M0-v0.1.0
- **Defined in:** [RFC-Shared-Agent-Scaffolding-v0.1.0.md](../RFC-Shared-Agent-Scaffolding-v0.1.0.md)
- **Test Vectors:** [conformance/vectors.json](../conformance/vectors.json)

## Output Modes

The canonical tool supports two output modes, controlled by the `SAFE_RUN_VIEW` environment variable:

### 1. Event Ledger Mode (Default)

**Trigger:** `SAFE_RUN_VIEW` not set, or `SAFE_RUN_VIEW=ledger`

**Format:**

```
{"seq":1,"event":"META","data":"START","timestamp":"2024-01-15T10:30:00.123Z"}
{"seq":2,"event":"STDOUT","data":"Hello, world!"}
{"seq":3,"event":"STDERR","data":"Warning: deprecated API"}
{"seq":4,"event":"META","data":"END","timestamp":"2024-01-15T10:30:00.456Z"}
{"seq":5,"event":"META","data":"EXIT","exit_code":0}
```

**Requirements:**

1. **Monotonic Sequence Numbers:** `seq` starts at 1 and increments by 1 for each event
2. **Event Types:**
   - `META` with `data="START"` - marks command start
   - `STDOUT` - child process stdout line
   - `STDERR` - child process stderr line
   - `META` with `data="END"` - marks command end
   - `META` with `data="EXIT"` - final event with exit code
3. **Timestamps:** ISO 8601 format with millisecond precision for META events
4. **Per-Line Emission:** Each output line is a separate event
5. **JSON Format:** Each event is a single-line JSON object

**Edge Cases:**

- Empty output: Only META events (START, END, EXIT)
- No stdout: Only STDERR and META events
- No stderr: Only STDOUT and META events
- Non-zero exit: EXIT event includes `exit_code` field
- Signal termination: EXIT event includes `signal` field and translated exit code

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

- Default: Current working directory
- Override via `SAFE_RUN_LOG_DIR` environment variable
- Tool MUST create directory if it doesn't exist

### Log Content

Event ledger mode:
- Log file contains JSON event stream (same format as stdout)

Merged view mode:
- Log file contains merged stdout/stderr output
- Optional: Include metadata header/footer

## Conformance Testing Strategy

### Test Fixtures

Test vectors are defined in `conformance/vectors.json`:

```json
{
  "version": "1.0",
  "contract_version": "M0-v0.1.0",
  "vectors": [
    {
      "id": "safe_run_basic_stdout",
      "command": "safe-run",
      "args": ["echo", "hello"],
      "env": {},
      "expected": {
        "exit_code": 0,
        "stdout_pattern": ".*STDOUT.*hello.*",
        "events": [
          {"event": "META", "data": "START"},
          {"event": "STDOUT", "data": "hello"},
          {"event": "META", "data": "END"},
          {"event": "META", "data": "EXIT", "exit_code": 0}
        ]
      }
    }
  ]
}
```

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
- Contract allows either, tools normalize internally to LF for JSON

### Encoding

- UTF-8 required for all text
- Binary output: Base64-encoded in JSON

### Whitespace

- Trailing whitespace on data lines is preserved
- Empty lines produce events with `data=""`

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

- [RFC-Shared-Agent-Scaffolding-v0.1.0.md](../RFC-Shared-Agent-Scaffolding-v0.1.0.md)
- [Rust Canonical Tool](./rust-canonical-tool.md)
- [Wrapper Discovery](./wrapper-discovery.md)
- [Test Vectors](../conformance/vectors.json)
- [EPIC #33: Rust Canonical Tool](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues/33)
