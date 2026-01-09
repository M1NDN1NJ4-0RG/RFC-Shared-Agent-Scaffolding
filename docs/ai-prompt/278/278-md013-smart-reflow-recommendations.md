# MD013 Smart Reflow Fixer Recommendations & Tracker

**File**: `docs/ai-prompt/278/278-md013-smart-reflow-recommendations.md` (suggested location)  
**Purpose**: Track evolution of `scripts/fix_md013_line_length_option_b.py` into a battle-hardened, torture-garden-proof Markdown line-length enforcer.  
**Status**: [ ] Draft → [ ] Implemented Basics → [ ] Passes Torture Garden → [ ] Integrated into repo_lint → [ ] Repo-wide Cleanup Complete

## Current State (as of 2026-01-08)

- Basic `textwrap.fill()` with some skip logic (tables, code fences, backticks, URLs, etc.).
- Handles simple paragraphs and basic lists.
- **Major known failures**:
  - Loses blockquote `>` prefixes on wrapped lines.
  - Breaks lazy paragraph continuations in lists.
  - Mis-indents deep nests and mixed-marker lists.
  - Can mangle checkbox nesting.
  - Doesn't preserve continuation paragraphs attached to list items.

Tested against `markdown-md013-torture-garden-bad-good.md` → fails ~60% of cursed sections.

## Priority Recommendations (Chaos-Approved Roadmap)

### Phase 1: Add Proper Context Tracking (Critical for Lists & Blockquotes)

- [ ] Implement a **state machine** while processing lines:
  - Track current list depth stack (list of (indent_level, marker_type, marker_text)).
  - Track blockquote depth (number of `>` prefixes).
  - Track if current paragraph is a "continuation" (no blank line since last item).
- [ ] When wrapping a line:
  - First line keeps original prefix/marker.
  - Continuation lines get appropriate indent + repeated prefixes (`>` for each blockquote level).
  - No marker repeated on continuations.

### Phase 2: Smart Paragraph & Continuation Handling

- [ ] Detect lazy continuations:
  - If line indent ≥ current list item's content indent and not a new list marker → treat as continuation.
  - Wrap with hanging indent (usually +2 or +4 spaces).
- [ ] Preserve multi-paragraph blocks inside list items (blank lines allowed, but stay nested).

### Phase 3: Checkbox & Mixed Marker Protection

- [ ] Special handling for `- [ ]` / `- [x]` markers:
  - Never duplicate checkbox on wrapped lines.
  - Treat checkbox as part of marker detection.
- [ ] Support mixed bullet types (`*`, `-`, `+`) and ordered (`.`, `)`) without losing context.

### Phase 4: Admonition & Cursed Edge Cases

- [ ] Preserve `> [!NOTE]` / `> [!WARNING]` lines exactly (or re-prefix properly).
- [ ] Ensure HTML comments stay untouched and don't break context.
- [ ] Handle frontmatter, footnotes, reference defs, images, autolinks (already mostly skipped — verify).

### Phase 5: Tooling & Safety

- [ ] Add CLI flags:
  - `--max-line-length` (default 120)
  - `--dry-run` / `--diff` (show git-style diff instead of overwriting)
  - `--in-place` (default) vs `--output -` for stdout
- [ ] Add `--check` mode: exit non-zero if any fixes would be needed (for CI).
- [ ] Unit tests using the torture garden fixture (split bad → apply fixer → compare to good).

### Phase 6: Integration & Mass Deployment

- [ ] Hook into `repo_lint`:
  - New rule: `md013-smart`
  - Optional `--auto-fix-md013=smart` flag that calls this script.
- [ ] Run repo-wide (exclude `repo-lint-failure-reports/` obviously).
- [ ] Commit the glorious cleanup and watch ~10,000 violations vanish.

## Bonus Chaos Ideas

- [ ] Configurable hanging indent amount per list depth.
- [ ] `--aggressive` mode that also reflows table cells (optional, dangerous).
- [ ] Generate a "before/after" HTML preview for review on big runs.

## Progress Tracker

- [ ] Phase 1 complete
- [ ] Phase 2 complete
- [ ] Phase 3 complete
- [ ] Phase 4 complete
- [ ] Phase 5 complete
- [ ] Phase 6 complete → Repo achieves Markdown Nirvana

Drop this file into `docs/`, commit it, and let the self-dogfooding begin.  
Next step: reply with which phase you want pseudocode/refactor help on first, and we'll start carving this beast into perfection. 🔥🐍
