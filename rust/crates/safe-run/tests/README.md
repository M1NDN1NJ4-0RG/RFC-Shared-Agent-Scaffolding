# Rust Conformance Tests

## Overview

This directory contains integration tests that validate the Rust canonical tool against the contract defined in `conformance/vectors.json`.

## Structure

```
tests/
├── README.md              # This file
├── common/
│   └── mod.rs            # Shared test utilities and vector loading
├── conformance.rs        # Main conformance test suite
├── fixtures/             # Test data and helper scripts
└── snapshots/            # Golden outputs for snapshot testing
```

## Running Tests

### All tests (excluding ignored)
```bash
cargo test
```

### All tests including ignored (will fail until implementation)
```bash
cargo test -- --include-ignored
```

### Specific test file
```bash
cargo test --test conformance
```

### Specific test
```bash
cargo test --test conformance test_safe_run_001
```

## Test Status

**Current Status:** Tests are written test-first and marked with `#[ignore]`.

Tests are currently **ignored** because the implementation does not exist yet (PR3). Once implementation is added, remove the `#[ignore]` attributes and tests should pass.

## Test Coverage

### safe-run (5 vectors)
- `test_safe_run_001_success_no_artifacts` - Vector safe-run-001
- `test_safe_run_002_failure_creates_log` - Vector safe-run-002  
- `test_safe_run_003_sigterm_aborted` - Vector safe-run-003 (Unix only)
- `test_safe_run_004_custom_log_dir` - Vector safe-run-004
- `test_safe_run_005_snippet_output` - Vector safe-run-005

### safe-archive (4 vectors)
- `test_safe_archive_001_basic` - Vector safe-archive-001
- `test_safe_archive_002_compression_formats` - Vector safe-archive-002
- `test_safe_archive_003_no_clobber_auto_suffix` - Vector safe-archive-003
- `test_safe_archive_004_no_clobber_strict` - Vector safe-archive-004

### preflight-automerge-ruleset (4 vectors)
- `test_preflight_001_success` - Vector preflight-001
- `test_preflight_002_auth_failure` - Vector preflight-002
- `test_preflight_003_ruleset_not_found` - Vector preflight-003
- Note: Vector preflight-004 not yet implemented

## Meta-Tests

- `test_all_vectors_have_tests` - Verifies test coverage for all vectors
- `test_load_vectors` - Validates vector loading from JSON
- `test_safe_run_vector_structure` - Validates vector structure

## Test Utilities

The `common` module provides:

- **`load_vectors()`** - Loads conformance vectors from `conformance/vectors.json`
- **`get_safe_run_binary()`** - Locates the safe-run binary (debug or release)
- Vector type definitions matching the JSON schema

## Writing New Tests

When adding a new conformance test:

1. Add the vector to `conformance/vectors.json`
2. Create a test function in `conformance.rs` in the appropriate module
3. Use `#[ignore]` if implementation doesn't exist yet
4. Load the vector using `load_vectors()`
5. Use `assert_cmd::Command` to execute the binary
6. Validate all expected outcomes from the vector

Example:
```rust
#[test]
#[ignore] // Remove when implementation exists
fn test_my_new_vector() {
    let vectors = load_vectors().expect("Failed to load vectors");
    let vector = vectors.vectors.safe_run
        .iter()
        .find(|v| v.id == "safe-run-XXX")
        .expect("Vector not found");

    let temp = TempDir::new().expect("Failed to create temp dir");
    
    let mut cmd = Command::new(get_safe_run_binary());
    cmd.current_dir(temp.path());
    cmd.arg("run");
    cmd.args(&vector.command.args);

    let mut assert = cmd.assert();
    
    if let Some(exit_code) = vector.expected.exit_code {
        assert = assert.code(exit_code);
    }

    // Add more assertions based on expected outcomes
}
```

## CI Integration

These tests will run in CI once:
1. Implementation exists (PR3+)
2. `#[ignore]` attributes are removed
3. CI workflow is configured to run `cargo test`

## Platform Considerations

- Signal handling tests (`test_safe_run_003_sigterm_aborted`) are Unix-only (`#[cfg(unix)]`)
- Path separators and line endings are normalized per contract
- Test scripts use bash on Unix, will need PowerShell equivalents for Windows

## Next Steps

1. **PR2** (current): Test infrastructure in place, tests written and ignored
2. **PR3**: Implement `safe-run` command, remove `#[ignore]` from safe-run tests
3. **PR4+**: Implement remaining commands, remove remaining `#[ignore]` attributes
