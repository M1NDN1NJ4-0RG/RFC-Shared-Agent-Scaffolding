# CLAUDE.md — Bootstrap (Read First)

This repository uses *sharded* agent instructions plus a *journaled* work tracker.  
Your job is to **load only the shards you need**, and to **resume deterministically** after any interruption.

---

## 0) Non-negotiables (Always apply)

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

1) Re-establish the current task from the user request, issue, or PR description.
2) Load the minimum relevant shard(s) from `.docs/agent/` using the routing table in `00_INDEX.md`.
3) Validate reality (e.g., `git status`, PR state, and any verification notes available in the repo or PR).
4) Continue at the next clearly defined, unchecked item for the active task.

> Note: A previous journal system based on `.docs/journal/CURRENT.md` and `.docs/journal/PR-LOG/*` was archived and is **not** currently used by this repository. Do not attempt to read or write those paths.

---

## 3) Work tracking (Journaled)

The earlier, journaled work-tracking system has been archived under:

- `docs/history/ai-agent-guidelines/journal/`

You may consult this history for background, but you **must not** assume any `.docs/journal/*` files exist or are authoritative in the current repository state.

---

## 4) Key improvements baked into this setup

- Mandatory **Mode Detection** preflight in `20_GIT_WORKFLOW.md`
- A single constant **AUTO_MERGE_MAX_WAIT_SECONDS = 600** in `21_AUTO_MERGE_WAITING.md`
- Legacy tracker design (CURRENT.md + PR-LOG, journaled) is preserved only as historical reference under `docs/history/ai-agent-guidelines/journal/`, not as an active monolithic document.
- Approval-gated dependency/tooling actions preserved in `40_BUILD_AND_VERIFICATION.md`

---

## 5) If you need “the old monolith”

The previous monolithic rules and their journal templates have been archived under `docs/history/ai-agent-guidelines/journal/` and redistributed into `.docs/agent/*` shards.  
Follow the routing index rather than searching ad-hoc or relying on `.docs/journal/*` paths.

