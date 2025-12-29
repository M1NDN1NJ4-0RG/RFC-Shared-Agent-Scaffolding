# Sharded Agent Instructions + Journaled Tracker

This scaffold converts a monolithic `CLAUDE.md` into:
- a small **bootstrap** (`CLAUDE.md`)
- a set of **sharded rules** under `.docs/agent/`
- a **journaled tracker** under `.docs/journal/`

## Typical start / resume sequence
1) Read `CLAUDE.md`
2) Read `.docs/journal/CURRENT.md`
3) Read `.docs/agent/00_INDEX.md`
4) Load only the shard(s) needed for the active chunk

## After each PR
- Append a new entry to `.docs/journal/PR-LOG/` using `TEMPLATE.md`
- Update `.docs/journal/CURRENT.md` to reflect the next chunk

