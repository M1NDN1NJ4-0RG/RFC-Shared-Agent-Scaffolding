# Chat Summary: Sharded Agent Scaffolding, Journaling, and “Universal Agent OS” (RFC Lineage)

> **Purpose:** This document is a **high‑fidelity summary** of the conversation that led to (and iteratively refined) the RFC + scaffolding system for operating LLM coding agents safely across **volatile context**, **rate limits**, **agent capability differences**, and **human toggle mistakes** (e.g., auto‑merge rulesets).  
> It is written to be copy‑pasted into a new chat as canonical background and to serve as a durable reference.

---

## 0) Executive Overview

This chat produced a complete “Agent Operating System” concept and implementation:

- A **sharded instruction architecture** (bootstrap + topic shards) replacing monolithic `CLAUDE.md` / `AGENTS.md` where scale breaks ingestion.
- A **journaled state system** (`CURRENT.md`, PR logs, handoff docs) designed to survive:
  - model context loss
  - terminal/session interruptions
  - rate limit pauses
  - switching between agents (Codex ↔ Claude Code)
- A **fail‑closed Git workflow** with explicit “modes” (no `.git`, manual PR mode, auto‑merge mode).
- A **preflight safety suite** that programmatically verifies “Mode B” (auto‑merge allowed) via GitHub rulesets + required status checks, including **hard rules to avoid leaking `$TOKEN`**.
- A refinement loop that repeatedly incorporated “nips” (iteration suggestions) into successive RFC versions (v2 → v8) and the scaffolding zip.
- A final demonstration of why this matters: insisting on a semantic/behavioral comparison between a legacy monolith and the refactored build caught a subtle, high‑impact behavioral mismatch (focusable selector logic), validating the whole “prove parity” gate.

---

## 1) The Core Problem We Were Solving

### 1.1 The reality of LLM agents in long refactors
LLM agents are powerful but structurally fragile in long projects:

- **Context is finite** and can be lost mid‑task.
- **Rate limits** interrupt active work.
- **Agent sessions** persist only as long as the underlying process survives (terminal not killed; computer not rebooted; etc.).
- **Human toggles** (GitHub settings, auto‑merge rulesets) drift, get disabled for testing, then forgotten.
- Large “one‑file instruction bibles” become **too big to reliably ingest**, even with massive context windows.

### 1.2 Why “manual testing” isn’t a sufficient gate
Manual testing answers: “Does it look okay?”  
But refactors require: **“Is it the same program?”**

Small differences (selectors, edge‑case timings, postinstall behavior, SPA mutation order, etc.) can pass “looks fine” and still ship regressions.

---

## 2) The Observational Trigger and Epiphany

### 2.1 Claude Code session persistence (the “shockingly well” part)
You reported a key operational advantage of **Claude Code**:

- When you hit rate limits, it can **pause/suspend the session**.
- Later—hours later—it can resume **exactly where it left off**.
- It can survive:
  - suspending at home, resuming at work, resuming at another site, resuming back at home
  - *as long as the underlying process doesn’t get killed / stale / terminal closed / system restarted*

This is **session memory**: it’s strong but still **volatile**.

### 2.2 The practical guardrail that made session persistence actually usable
Claude Code’s persistence worked best because you already enforced:

- **Small, explicit work chunks**
- A continuously updated external tracker that the agent can re‑read
- A handoff pattern that re‑anchors the agent

This turned “session memory” (nice) into “recovery memory” (durable).

### 2.3 The “mental click”: distributed systems / journaling analogy
The epiphany: **This is distributed systems thinking.**

You recognized your situation mirrored:
- journaling file systems
- chunked storage constraints (classic 4GB file limits)
- checkpoint/restart models
- distributed job orchestration

**Conclusion:** treat agents like fallible workers with volatile memory—not omniscient processes.  
Therefore: serialize state externally and design for resumption.

---

## 3) The Architecture We Implemented

### 3.1 From monolith to shards (the sharded scaffolding)
You wanted `CLAUDE.md` to become the **bootstrap** doc that routes to smaller shards.

High‑level goals:
- Keep a minimal **bootstrap** that can always be read.
- Move detailed rules into **topic shards** that remain small and swappable.
- Make the system compatible with multiple agents (Claude Code, Codex, etc.) by renaming (`CLAUDE.md` ↔ `AGENTS.md`) and by keeping “state on disk.”

### 3.2 Journaling as durable memory
We standardized external state files so agents can rehydrate:

- `CURRENT.md` — the “now” state: current chunk, what’s done, what’s next, blockers
- `PR_LOG.md` (or equivalent) — what PRs exist, what they contained, verification results
- `AGENT_HANDOFF-YYYYMMDD-HHMM.md` — portable serialized memory for swapping agents or restarting chats
- “Failure logs” directory for failed commands with stdout/stderr capture (added later)

### 3.3 Session memory vs journaled state (diagram concept)
The RFC explicitly distinguishes:

- **Session memory**: process‑tied continuity (great until killed).
- **Journaled state**: durable, disk‑resident truth (survives everything).
- **Rehydration**: agent reads the journal and continues.

The design intent: use session memory when available, but always maintain journaled state so recovery is deterministic.

---

## 4) Git Workflow Modes (Fail‑Closed by Design)

A central design decision: agents must **downgrade gracefully** depending on repo environment:

### Mode 0: No `.git` present
- Work “local only.”
- Snapshot/patch workflow.
- No assumptions about remotes, PRs, or merge safety.

### Git Mode A: Manual PR workflow
- PRs created, but agent does **not** assume auto‑merge exists.
- Safer for constrained/untrusted agents.
- Human approval / manual merge path is always valid.

### Git Mode B: Auto‑merge workflow (high gear)
- Enabled only if:
  - a deliberate **feature flag** file exists (e.g., `.agent/auto-merge.enabled`)
  - **preflight** checks pass (rulesets, required CI contexts)
- This unlocks `gh pr merge --auto --squash` and waiting/polling for completion.

**Key meta‑principle:** Fail closed. If you can’t prove it’s safe, default to Mode A.

---

## 5) Auto‑Merge Safety Suite (Preflight, Rulesets, and Token Safety)

### 5.1 Why we added preflight scripts
You explicitly wanted a mechanism so an agent can detect:
- “Is auto‑merge actually enabled and enforceable on this repo right now?”
- “Are required status checks configured as expected?”
- “Are we about to rely on a ruleset that a human forgot to re‑enable?”

This became a preflight requirement for Mode B.

### 5.2 The GitHub ruleset inspection path
You validated rulesets via GitHub REST API:

- List rulesets:
  - `GET /repos/{owner}/{repo}/rulesets`
- Inspect a specific ruleset:
  - `GET /repos/{owner}/{repo}/rulesets/{id}`
- Extract:
  - `enforcement` (active/disabled)
  - target branch conditions (`~DEFAULT_BRANCH`)
  - `required_status_checks` contexts list

This became the canonical way to verify branch protection *via rulesets*.

### 5.3 The jq pitfall and fix
A jq expression initially failed because it attempted to subtract a boolean from an array:
- error: `array (...) and boolean (true) cannot be subtracted`

This prompted restructuring of jq logic so “array difference” is computed on array operands only, and enforcement checks are separate booleans.

### 5.4 Hard rule: do not leak `$TOKEN`
A non‑negotiable safety addition:
- No commands that print `$TOKEN` or expose it via shell tracing.
- No `set -x` / `xtrace` when tokens might be used.
- Avoid echoing headers.
- Scripts must treat token secrecy as a **hard rule**, not a guideline.

### 5.5 Authentication failure behavior
Another hard workflow rule:
- If authentication errors occur:
  - fall back to Git Mode A
  - stop
  - instruct the human to fix auth
  - proceed only after confirmation, and retry once

---

## 6) “Next Level Paranoia” Additions

Two optional—but implemented—extensions:

### 6.1 Auto‑discover ruleset instead of hardcoding the ruleset ID
Instead of assuming a specific ruleset ID:
- find the default‑branch ruleset by:
  - matching `conditions.ref_name.include` contains `~DEFAULT_BRANCH`
  - and checking for a `required_status_checks` rule

### 6.2 Verify `gh pr merge --auto --squash` is actually usable
Add “prove it first” checks where feasible; otherwise fall back.

---

## 7) The Failure Pause Ritual (A Major RFC Design Upgrade)

### 7.1 The motivation
Interruption during/after a failure can lose:
- what failed
- which command
- stdout/stderr evidence

So we added a mandatory pattern: **pause and journal on failure**.

### 7.2 The ritual itself
On any non‑zero exit:
- Update `CURRENT.md` with a structured “FAILURE PAUSE” block.
- Save stdout/stderr to `.agent/FAIL-LOGS/<timestamp>-<slug>.txt`.

---

## 8) Wrapper Scripts, Archives, and “No Deletion” Policy

### 8.1 Safe wrapper execution
A wrapper script was introduced to:
- run a command
- pass through output on success
- on failure:
  - capture output to FAIL‑LOGS
  - return the original exit code

### 8.2 Wrapper failure fallback
If the wrapper fails:
- do not silently proceed
- require manual Failure Pause Ritual
- journal “wrapper failure” as its own event

### 8.3 Post‑success handling: archive, don’t delete
To preserve the “no destructive commands” posture:
- move FAIL‑LOGS to `FAIL-ARCHIVE/` via safe `mv -n`
- cleanup is human‑approved and risk‑acknowledged

### 8.4 Cleanup queue escalation
At a threshold (default 10):
- stop
- notify human
- request manual intervention

---

## 9) Multi‑Language OS‑Agnostic Implementation

You requested portability and created script sets in:

- Bash
- Perl
- Python 3
- PowerShell

All preserving the same behavioral contract and safety constraints.

---

## 10) The “Universal Agent OS / Hypervisor” Recontextualization (v8)

This reframed the system as a compatibility layer:

- “Codex scars” → explicit serialization (stop conditions + continue prompts)
- Bootloader FSM → Mode detection and feature flags on disk
- Anti‑hallucination filesystem → snapshot/patch/branch containment
- Handoff protocol → agent interchangeability (cheap → smart without losing state)

Two refinements:
- explicit token runway checks for constrained agents
- diagnostic loop for `npm ci --ignore-scripts` vs postinstall expectations

---

## 11) Why the Semantic Comparison Gate Was Vindicated

You insisted on parity proof before manual testing, and it caught a real mismatch:

- focus trap selector logic in `events.ts` was incomplete vs legacy behavior
- parity fix required expanding selector + filtering disabled/hidden elements

**This validated** the entire “prove parity” gate and the journaled OS approach.

---

## 12) Canonical Design Decisions to Preserve

1) Shard anything that grows; bootstrap stays small.  
2) Journal is truth; session memory is acceleration only.  
3) Fail closed; prove safety before auto‑merge.  
4) Feature flags live on disk.  
5) `$TOKEN` is sacred: no printing, no tracing.  
6) Failures become checkpoints via Failure Pause Ritual.  
7) Archive, don’t delete by default.  
8) Refactor “done” requires parity proof, not vibes.

---

## 13) New‑Chat Rehydration Primer

To continue in a new chat:
- provide `CURRENT.md`, latest RFC, and the relevant shards
- state mode rules (A/B), token secrecy, and parity gate
- require failure journaling and archive policy

*End of summary.*
