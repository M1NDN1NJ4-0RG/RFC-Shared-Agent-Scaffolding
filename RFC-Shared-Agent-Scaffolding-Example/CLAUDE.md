# CLAUDE.md — Bootstrap (Read First)

This repository uses *sharded* agent instructions plus a *journaled* work tracker.  
Your job is to **load only the shards you need**, and to **resume deterministically** after any interruption.

---

## 0) Non‑negotiables (Always apply)

1) **No destructive commands** (no deletes/resets/overwrites) unless the user explicitly approves.  
2) **Follow the repo’s PR workflow** (including auto-merge rules when applicable).
   - If using auto-merge, you MUST run the auto-merge preflight (see `.docs/agent/22_AUTOMERGE_PREFLIGHT.md`).  
3) **Work in small, verifiable chunks**; record progress in the journal.  
4) **When context is lost:** resume using the journal + routing index (below).  
5) **If anything conflicts:** this `CLAUDE.md` wins; then `.docs/agent/00_INDEX.md`.

---

## 1) Where the rules live (Routing)

Read `.docs/agent/00_INDEX.md` to decide which shard(s) to load for the current task.

**Do not ingest every file by default.** Load only what the current chunk needs.

---

## 2) Resume protocol (Mandatory)

Whenever you start, restart, or regain context:

1) Read `.docs/journal/CURRENT.md`
2) Identify the **Active Chunk ID**
3) Load the minimum relevant shard(s) from `.docs/agent/` using the routing table
4) Validate reality (git status / PR state / last verification notes)
5) Continue at the next unchecked item in the active chunk

If the journal appears stale, update it immediately before proceeding.

---

## 3) Work tracking (Journaled)

- **Hot state:** `.docs/journal/CURRENT.md` (small; always readable)
- **Append-only history:** `.docs/journal/PR-LOG/*` (one entry per PR or milestone)

Never allow a single tracker file to grow without bound. Keep CURRENT small and authoritative.

---

## 4) Key improvements baked into this setup

- Mandatory **Mode Detection** preflight in `20_GIT_WORKFLOW.md`
- A single constant **AUTO_MERGE_MAX_WAIT_SECONDS = 600** in `21_AUTO_MERGE_WAITING.md`
- Tracker rewritten as **CURRENT.md + PR-LOG** (journaled), not a monolithic document
- Approval-gated dependency/tooling actions preserved in `40_BUILD_AND_VERIFICATION.md`

---

## 5) If you need “the old monolith”

The previous monolithic rules have been redistributed into `.docs/agent/*` shards and journal templates.  
Follow the routing index rather than searching ad-hoc.

