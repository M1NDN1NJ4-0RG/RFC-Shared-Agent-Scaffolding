# RFC: Sharded Agent Scaffolding & Journaling for Long-Running AI Coding Workflows (v0.1.0)

**Status:** Implemented (iterated)  
**Audience:** Humans collaborating with LLM-based coding agents (Claude Code, Codex, etc.)  
**Primary Environment:** GitHub repositories with PR-based workflows, CI gating, and auto-merge  
**Motivation:** Reliability, continuity, safety, and human-error resistance in long-running agent sessions

---

## 0. Executive Summary

This RFC defines a restartable, failure-resilient operating model for AI coding agents.

Version 8 adds an important lens: the system is not “bureaucratic rigor” for its own sake. It is **operational scar tissue** from running constrained agents (small context, rigid output limits, cheaper/free tiers) alongside more capable agents. In practice, the scaffolding acts as a **compatibility layer** (a “hypervisor”) that allows:

- **Constrained agents** (e.g., small context windows, strict output limits) to function safely via sharding, journaling, stop conditions, and serialized handoff files.
- **More capable agents** to unlock “higher gears” (e.g., CI-gated auto-merge) because safety proofs are explicit and persistent on disk.

v8 also introduces:
- an explicit **Token Budget / Runway Check** before starting large work items,
- and a diagnostic loop for the **“npm ci --ignore-scripts” trap**.

---

## 1. Problem Statement

LLM-based coding agents can perform multi-day refactors and CI-gated workflows, but without an operational model, their work is fragile:

- Sessions are volatile.
- Context is finite.
- Humans misconfigure repositories.
- Instruction files and trackers grow without bound.
- Smaller agents can truncate outputs or silently “finish” partial edits.

Reliability requires treating agents like fallible workers with volatile memory and bounded output.

---

## 2. Observational Trigger (Empirical Epiphany)

Testing on a large refactor (~9,200 LOC monolithic JS → modular TS) showed recovery depends on **externalized state discipline**, not model intelligence.

Large context windows delay—but do not eliminate—the need to chunk. When trackers exceed a single message, chunking becomes inevitable.

---

## 3. Core Design Principles

1. **Shard instructions** to prevent monolithic growth.
2. **Journal state to disk**; treat memory as volatile.
3. **Fail closed**; prove safety before acting.
4. **Checkpoint failures**; errors become resumable state.
5. **Avoid destructive operations**; preserve auditability.
6. **Serialize progress explicitly** to survive truncation and context loss.

---

## 4. The “Universal Agent OS” Lens (New)

This framework behaves like a minimal “operating system” for agents—supplying executive function that many models lack:

- planning and chunking,
- durable state,
- “safe mode” vs “fast mode” gates,
- and explicit feature flags persisted on disk.

### 4.1 Codex Scars: Managing the Token Economy

Constrained agents can:
- cut off mid-task,
- hallucinate file endings,
- or drop existing code when context falls out.

**Mitigation pattern:** explicit stop conditions and serialized continuation.

- Work is broken into bounded items.
- The agent is required to stop at a boundary and provide a deterministic continuation prompt (or journal state) before output truncation becomes fatal.

### 4.2 Bootloader / Feature Flag Logic

A robust “boot chain” allows graceful downgrade:

- No `.git` → safe mode (snapshot/patch only).
- Git present but policy unproven → manual PR flow.
- Policy proven (preflight pass) + feature flag present → auto-merge flow permitted.

Feature flags implemented as files (e.g., `.agent/auto-merge.enabled`) persist across context resets and agent swaps.

### 4.3 Anti-Hallucination File System

Snapshot/patch patterns (e.g., patch files, version logs) reduce blast radius when an agent forgets which file it’s editing or truncates content.

Hard safety defaults:
- keep default branch untouchable,
- prefer throwaway branches for changes,
- record diffs and checkpoints.

### 4.4 Interchangeable Agents via Handoff Files

A standardized serialized memory format (handoff files and journals) allows:
- starting work with a cheaper/constrained agent,
- pausing at a safe boundary,
- resuming with a more capable agent without re-reading long chat history.

---

## 5. Implementation Pattern (Recap)

### 5.1 Reference Layout

```
CLAUDE.md
.docs/agent/
  10_SAFETY_COMMANDS.md
  20_GIT_WORKFLOW.md
  21_AUTO_MERGE_WAITING.md
  22_AUTOMERGE_PREFLIGHT.md
  30_JOURNALING.md
  40_HANDOFF_PROTOCOL.md
.agent/
  CURRENT.md
  REMAINING_WORK.md
  PR_LOG.md
  FAIL-LOGS/
  FAIL-ARCHIVE/
scripts/
  safe-run.sh
  safe-archive.sh
  safe-check.sh
  preflight_automerge_ruleset.sh
```

---

## 6. Failure Pause Ritual (Normative)

On any non-zero exit from build/test/verify commands, the agent MUST:
1. Write a FAILURE PAUSE block into `CURRENT.md`.
2. Persist stdout/stderr to `.agent/FAIL-LOGS/`.
3. Stop unless explicitly instructed to continue.

Logging is fail-only.

---

## 7. Safe Wrapper Execution Contract (Recap)

Wrappers SHOULD be used for critical commands. They must:
- run commands verbatim,
- preserve exit codes,
- produce artifacts on failure,
- and have no success-path side effects.

Wrapper failure fallback remains mandatory.

---

## 8. New: Token Budget / Runway Check (Normative for Constrained Agents)

Constrained agents often cannot reliably introspect their remaining context. To prevent starting work that will likely truncate mid-edit, agents MUST perform a **runway check** before beginning large refactor items.

### 8.1 Rule

Before starting a work item that involves editing a file or diff larger than a threshold (default: 300 lines), the agent MUST:

- estimate whether it can complete the item *and* produce a complete patch/output within its remaining budget,
- and if uncertain, STOP and request a fresh session or narrower scope.

### 8.2 Practical heuristic

If:
- file is > 300 lines **and**
- the agent’s remaining message budget is plausibly < ~4k tokens (or unknown),
then:

- DO NOT start the edit.
- Instead, propose:
  - splitting into smaller chunks,
  - or extracting only the relevant function/region,
  - or switching to patch-based/snapshot mode.

This prevents “half-edits” and hallucinated endings.

---

## 9. New: Diagnostic Loop for `npm ci --ignore-scripts`

Using `npm ci --ignore-scripts` can be a safe default, but it can also cause confusing downstream failures if dependencies rely on postinstall scripts (native modules, generated files, etc.).

### 9.1 Rule

If:
- `npm ci --ignore-scripts` succeeds,
- but builds/tests fail with missing modules, missing generated artifacts, or “module not found” errors,

then the agent MUST perform a diagnostic loop:

1. Identify the missing artifact/module.
2. Check whether it is typically produced by:
   - `postinstall`,
   - `prepare`,
   - `install`,
   - native build steps.
3. If evidence indicates postinstall is required:
   - STOP and ask the user whether scripts may be enabled for install in this repository context,
   - or propose a safer alternative (e.g., allowlist scripts, run install in a sandbox, or CI-only execution).

This prevents circular “build failed” loops that constrained agents misinterpret.

---

## 10. Metrics (Recap + Optional Expansion)

Suggested metrics now explicitly include:
- wrapper-invoked vs raw command ratio,
- number of restarts that avoided recomputation due to archived logs,
- time-to-resume after failure,
- and failure artifact completeness.

---

## 11. TL;DR

This framework is a “prosthetic frontal cortex” for agents.

It provides:
- executive function (chunking, stop conditions),
- durable state (journals),
- safety inhibition (fail closed),
- and compatibility across constrained and capable models.

Reliability comes from explicit state, not from hope, memory, or “bigger context windows.”

This is not overengineering.

This is survival engineering.
