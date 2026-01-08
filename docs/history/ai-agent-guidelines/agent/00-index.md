# Agent Shard Routing Index

**Purpose:** Navigation map for loading the right shards at the right time.
**Rule:** Load only what the active chunk needs. Avoid ingesting everything at once.

---

## Quick Reference

| Shard | When to Load | Size |
|-------|-------------|------|
| `10_CORE_RULES.md` | **Always** (first read after bootstrap) | Small |
| `20_GIT_WORKFLOW.md` | When working with git/PRs | Medium |
| `21_AUTO_MERGE_WAITING.md` | When using auto-merge workflow | Small |
| `22_AUTOMERGE_PREFLIGHT.md` | Before enabling auto-merge on a PR | Medium |
| `30_TESTING_STANDARDS.md` | When writing/running tests | Medium |
| `40_BUILD_AND_VERIFICATION.md` | When building or verifying changes | Medium |
| `50_DEPENDENCIES.md` | When adding/updating dependencies | Medium |

---

## Loading Strategy by Task Type

### New Feature Implementation

1. `10_CORE_RULES.md` (core principles)
2. `30_TESTING_STANDARDS.md` (test-first approach)
3. `40_BUILD_AND_VERIFICATION.md` (verification steps)

### Bug Fix

1. `10_CORE_RULES.md` (core principles)
2. `30_TESTING_STANDARDS.md` (regression test requirements)
3. `40_BUILD_AND_VERIFICATION.md` (verification steps)

### PR Workflow (Manual)

1. `10_CORE_RULES.md` (core principles)
2. `20_GIT_WORKFLOW.md` (PR creation and management)

### PR Workflow (Auto-merge)

1. `10_CORE_RULES.md` (core principles)
2. `20_GIT_WORKFLOW.md` (git workflow)
3. `21_AUTO_MERGE_WAITING.md` (timing constants)
4. `22_AUTOMERGE_PREFLIGHT.md` (preflight validation)

### Dependency Update

1. `10_CORE_RULES.md` (core principles)
2. `50_DEPENDENCIES.md` (dependency policies)
3. `40_BUILD_AND_VERIFICATION.md` (verification steps)

---

## Shard Descriptions

### `10_CORE_RULES.md`

**Required reading for all tasks.**
Contains non-negotiable rules that apply universally:

- No destructive operations without approval
- Small, verifiable chunks
- Resume protocol
- Failure handling

### `20_GIT_WORKFLOW.md`

**Load when:** Creating PRs, managing branches, working with git.
Contains:

- Branch naming conventions
- PR creation workflow
- Commit message standards
- Mode detection (safe mode vs auto-merge mode)

### `21_AUTO_MERGE_WAITING.md`

**Load when:** Using auto-merge workflow.
Contains:

- `AUTO_MERGE_MAX_WAIT_SECONDS = 600` (single source of truth)
- Polling interval recommendations
- Timeout handling

### `22_AUTOMERGE_PREFLIGHT.md`

**Load when:** Before enabling auto-merge on a PR.
Contains:

- Preflight validation checklist
- Ruleset verification requirements
- Safety checks before auto-merge

### `30_TESTING_STANDARDS.md`

**Load when:** Writing or running tests.
Contains:

- Test coverage expectations
- Test naming conventions
- Test-first workflow
- Conformance testing requirements

### `40_BUILD_AND_VERIFICATION.md`

**Load when:** Building code or verifying changes.
Contains:

- Build commands per language
- Verification checklist
- Approval gates for tooling changes
- CI/CD expectations

### `50_DEPENDENCIES.md`

**Load when:** Adding or updating dependencies.
Contains:

- Dependency approval requirements
- Security scanning expectations
- Version pinning policies
- Lock file management

---

## Anti-patterns (What NOT to do)

❌ **Don't:** Load all shards at session start "just in case"
✅ **Do:** Load the bootstrap + index, then load specific shards per task

❌ **Don't:** Skip the index and load shards randomly
✅ **Do:** Use this index to decide which shards are relevant

❌ **Don't:** Load outdated or stale shards from memory
✅ **Do:** Re-read from disk when resuming after context loss

---

## Update Protocol

When adding new shards:

1. Create the shard file in `.docs/agent/`
2. Add entry to the Quick Reference table
3. Add loading scenarios to the "Loading Strategy" section
4. Add shard description to the "Shard Descriptions" section
5. Update `.docs/journal/CURRENT.md` if adding mid-project

---

**Version:** 1.0
**Last Updated:** 2025-12-26
**Refs:** RFC v0.1.0 sections 4-6
