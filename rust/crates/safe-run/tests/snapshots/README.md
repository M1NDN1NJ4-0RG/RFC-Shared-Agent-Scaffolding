# Snapshots Directory

This directory contains **golden outputs** (expected outputs) for snapshot testing.

## Purpose

Snapshot files capture the expected behavior of the canonical Rust tool. Tests compare actual outputs against these snapshots to detect unintended changes.

## Format

Snapshots are stored as `.txt` files with normalized content:
- Line endings normalized to LF
- PIDs replaced with `{PID}` placeholder
- Timestamps replaced with `{TIMESTAMP}` placeholder
- Trailing whitespace removed

## Naming Convention

Snapshot files are named after the test vector ID:
- `safe-run-001.txt` - Expected output for vector safe-run-001
- `safe-run-002-log.txt` - Expected log file content for vector safe-run-002
- etc.

## Generating Snapshots

Snapshots will be generated once the implementation exists (PR3+).

To update snapshots after implementation changes:
1. Run tests to see actual output
2. Review changes carefully
3. If changes are intentional, update snapshots
4. Commit updated snapshots with clear explanation

## Status

**Current Status:** Directory is empty. Snapshots will be added in PR3 after implementation.

## Platform Considerations

Snapshots should be platform-agnostic where possible:
- Use normalized paths
- Use normalized line endings
- Use placeholder values for dynamic content (PIDs, timestamps)

Platform-specific behavior differences that are allowed by the contract should be documented in the test code, not hidden in snapshots.
