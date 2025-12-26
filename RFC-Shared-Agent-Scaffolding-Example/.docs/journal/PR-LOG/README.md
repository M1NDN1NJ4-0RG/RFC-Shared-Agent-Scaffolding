# PR Log Directory

**Purpose:** Append-only archive of completed work.

---

## Structure

Each completed PR gets its own markdown file in this directory.

**Filename format:** `YYYY-MM-DD-PR-<number>-<slug>.md`

**Examples:**
- `2025-12-26-PR-001-bootstrap-scaffolding.md`
- `2025-12-27-PR-002-add-logging-semantics.md`
- `2026-01-15-PR-042-conformance-vectors.md`

---

## What Goes Here

**Archive entries when:**
- PR is merged
- Chunk is complete
- Work transitions to next chunk

**Each entry should:**
- Use the `TEMPLATE.md` format
- Summarize what was accomplished
- List verification steps
- Document lessons learned
- Reference related issues/epic

---

## What Stays in CURRENT.md

Only **active, in-progress work** belongs in `CURRENT.md`.

**Move to PR-LOG when:**
- PR is merged
- Chunk is complete
- Work is no longer active

---

## Benefits of Append-Only Log

**Advantages:**
- Never loses historical context
- Searchable archive of decisions
- Tracks progress over time
- Enables pattern recognition (what works, what doesn't)

**Prevents:**
- Monolithic tracker growth
- Context loss from overwriting
- Confusion about what's active vs historical

---

## Example Entry

See `../TEMPLATE.md` for the full template.

Quick example:
```markdown
# PR #8: M1-P2-I1 Python 3 Bundle Alignment

**Date:** 2025-12-26
**Status:** Merged
**Chunk ID:** CHUNK-008-python3-m0-align

## Summary
Aligned Python 3 implementation with M0 contract decisions.

## Changes Made
- [x] Updated safe_run.py for split stdout/stderr
- [x] Updated logging format per M0-P1-I2
- [x] All tests pass

## Verification
```bash
cd scripts/python3 && python3 -m unittest discover -v
```
✅ All tests passed

Refs: #3
```

---

## Searching the Log

**To find entries about a specific topic:**
```bash
# Search all PR logs for keyword
grep -r "logging" .docs/journal/PR-LOG/

# Find all entries for a specific epic item
grep -r "M0-P1-I1" .docs/journal/PR-LOG/

# List entries by date
ls -lt .docs/journal/PR-LOG/
```

---

**Note:** This directory is initially empty. It will be populated as PRs are completed.
