# 278-docstring-style-conversion-strategy.md

## Purpose

Design and implement a **bidirectional, multi-style Python docstring converter** inside `repo-lint`, with:

- A **stable, deterministic formatter** for each supported docstring style
- A **safe “infer + convert” autofix** mode powered by Python **AST** (Abstract Syntax Tree) metadata
- Clear safety controls so conversions are **trustworthy, reviewable, and reversible**

This document is meant to be a durable strategy/plan that Copilot can compare against (and align implementation with).

---

## Goals

1. **Support multiple docstring styles** and convert between them reliably.
2. **Avoid direct style→style conversion spaghetti** by using an intermediate representation (IR).
3. **Use AST to enrich docstrings** (types, ordering, yields/returns) without guessing intent beyond reason.
4. Provide a **safe-by-default autofix** with explicit “unsafe” modes.
5. Ensure conversions are **stable** (format doesn’t churn on repeated runs).
6. Provide an extensible architecture that can add new styles or features without rewriting everything.

---

## Non-goals

- Perfect semantic recovery from poorly written docstrings (not possible).
- Full type inference beyond explicit annotations (no mypy/pyright-level inference here).
- Reformatting / wrapping of code examples (examples must be preserved verbatim).
- General-purpose Markdown parsing (docstrings are not full Markdown documents).

---

## Supported docstring styles (six-style target set)

Recommended canonical set:

1. **Google**
2. **NumPy**
3. **reST/Sphinx** (`:param x:`, `:returns:`)
4. **EpyDoc** (`@param x`, `@return`)
5. **Javadoc-ish** (tag-based; similar to EpyDoc but commonly used in polyglot repos)
6. **Plain** (summary + optional extended description, no structured sections)

> Note: Style #5 and #6 can be swapped for “Markdown-ish” docstrings if the repo actually uses them—but Markdown docstrings are difficult to parse reliably.

---

## Core architecture: Parse → IR → Render

### Why

Six styles *bidirectionally* implies up to 30 conversion paths if implemented directly (6×5).  
Instead:

- Style-specific **Parser**: `docstring(text) → IR`
- Style-specific **Renderer**: `IR → docstring(text)`

This reduces complexity, centralizes logic, and enables better testing.

---

## Intermediate Representation (IR)

Define a structured IR that captures docstring intent consistently.

### Suggested IR fields

- `summary: str`
- `extended: str | None` (freeform long description)
- `params: list[Param]`
  - `name: str`
  - `type: str | None` (opaque string by default)
  - `default: str | None`
  - `desc: str | None`
  - `kind: positional | kwonly | varargs | varkw`
- `returns: Return | None` (`type`, `desc`)
- `yields: Yield | None` (`type`, `desc`) — for generators
- `raises: list[Raise]` (`exc_type`, `desc`)
- `attributes: list[Attr]` (`name`, `type`, `desc`) — primarily for classes
- `examples: list[Block]` (`text`, `verbatim=True`)
- `notes/warnings/see_also/references: list[Block]`
- `metadata: dict[str, Any]`
  - original detected style
  - detection confidence
  - formatting hints / raw blocks if needed

### Fidelity + loss tracking

Some styles encode richer structure than others.  
IR should allow “raw/verbatim blocks” so fidelity isn’t destroyed when converting.

---

## Style detection

Implement a lightweight detector that returns:

- `style: DocstringStyle`
- `confidence: float`
- `reasons: list[str]` (useful for logging and tests)

### Example heuristics (scoring)

- Google: `Args:`, `Returns:`, `Raises:` headings
- NumPy: `Parameters\n----------`, `Returns\n-------`, etc.
- reST/Sphinx: `:param`, `:type`, `:return`, `:raises`
- EpyDoc/Javadoc-ish: `@param`, `@return`, `@raises`, etc.
- Plain: fallback if none match

**Confidence gating** is critical for autofix:

- High confidence → eligible for autofix
- Low confidence → report-only (unless `--unsafe`)

---

## Parsing (style → IR)

### Preferred approach

Use a real docstring parser where possible (to avoid regex chaos).  
Candidates:

- A dedicated docstring parsing library for Google/NumPy/reST, plus:
- Thin adapter layers + fallback parsing for the styles the library doesn’t fully support

### Parser requirements

- Preserve **examples** blocks verbatim (do not wrap or normalize them).
- Preserve **multi-line descriptions** without collapsing structure.
- Normalize whitespace minimally, but maintain stable output.

### Failure behavior

- If parsing fails: emit a checker warning and skip conversion (safe default).
- If `--unsafe` is enabled: allow “best-effort” parsing and attach a warning tag in metadata.

---

## AST enrichment (IR + AST → enriched IR)

AST is used to fill gaps and align the docstring with code truth.

### What AST can reliably provide

- Function signature:
  - parameter names/order
  - `*args`, `**kwargs`, kw-only params
  - defaults
- Annotations:
  - parameter annotations
  - return annotation
- Generator detection:
  - presence of `yield` / `yield from`
- Context:
  - module docstring vs class docstring vs function/method docstring
  - async function vs normal function

### Enrichment rules (safe-by-default)

1. **Parameter ordering**
   - Reorder IR params to match signature order.
2. **Missing params**
   - If docstring missing an arg present in signature:
     - add it with empty description (or a placeholder) and annotate if available
3. **Types**
   - If docstring missing types but annotations exist:
     - copy annotation string into IR type field
   - If docstring type conflicts with annotation:
     - do not “auto-correct” silently by default; report a mismatch
     - optional mode: `--docstrings=types=prefer-annotations`
4. **Returns vs Yields**
   - If generator detected, use `yields` section; otherwise use `returns`
5. **Defaults**
   - Populate default values from signature if docstring omitted them

### Guardrails

- Do not invent types beyond annotations.
- Do not rewrite examples.
- Do not merge or split semantic blocks unless required by the target renderer format.

---

## Rendering (IR → style)

### Renderer requirements

- Deterministic output:
  - stable ordering
  - stable whitespace
  - stable wrapping rules
- Respect maximum line length (repo policy) with style-appropriate wrapping
- Preserve raw/verbatim blocks without reflow

### Wrapping and formatting rules

- Wrap prose to configured width (e.g., 88/100/120) **but**:
  - never wrap inside code blocks
  - never wrap inside doctest examples
  - avoid breaking URLs
- Treat types as opaque strings (unless separate “type normalization” is explicitly enabled).

---

## Applying fixes: editing files safely

### Locating docstrings

Use AST to locate docstring nodes:

- module docstring
- class docstring
- function/method docstring

### Writing changes without mangling formatting

Prefer token- or slice-based replacement:

- Replace only the docstring literal content range
- Preserve:
  - original quote style (`'''` vs `"""`)
  - indentation
  - raw string prefixes when present

### Output stability

Repeated runs should yield **no diff** once already formatted in the target style.

---

## CLI / UX design (repo-lint)

Add explicit commands/modes (names can be adjusted to repo conventions):

### Suggested flags/modes

- `--docstrings check`
  - report style, detect issues, no changes
- `--docstrings convert --from <style> --to <style>`
  - explicit conversion
- `--docstrings normalize --style <style>`
  - detect current style → convert to canonical style
- `--docstrings autofix`
  - auto-detect style and convert when confidence threshold is met
- `--docstrings autofix --unsafe`
  - allow best-effort on low-confidence parses

### Safety controls

- `--min-confidence 0.85` (default)
- `--types prefer-annotations | prefer-docstring | report-only` (default: report-only)
- `--scope function|class|module|all`
- `--exclude tests/fixtures/...` as needed

---

## Logging + reporting

Reports should be clear and actionable:

- file path
- object name (module/class/function)
- detected style + confidence
- actions taken (check/convert/skipped)
- warnings:
  - parse failures
  - low confidence skips
  - type mismatches
  - missing params

---

## Test strategy

### 1) Fixture-driven tests

Maintain “torture garden” docstring fixtures per style:

- “Bad examples” (violations / missing sections / mismatches)
- “Good examples” (canonical patterns that must remain stable)

### 2) Round-trip stability tests

- `parse → render(style X) → parse` must preserve IR (as much as the style permits)
- `render(render(parse(x))) == render(parse(x))` for each style (idempotence)

### 3) Bidirectional semantic tests

- `X → Y → X` should preserve IR semantics (not necessarily exact original text)
- Validate:
  - params preserved
  - types preserved (or expected loss documented)
  - returns/yields correctly chosen

### 4) AST enrichment tests

- Missing doc params are added
- Ordering matches signature
- yields vs returns chosen correctly
- default values copied when enabled
- mismatch detection works (and is configurable)

### 5) Safety gating tests

- low-confidence detection causes skip in safe mode
- `--unsafe` allows conversion but records warnings

---

## Edge cases to explicitly cover

- Multi-line param descriptions
- `*args` / `**kwargs`
- kw-only params and `/` positional-only params (Py3.8+)
- Generators and async generators
- Properties and descriptors (docstring context)
- Exceptions lists (multiple Raises entries)
- Example blocks with doctest prompts
- Non-ASCII text (UTF-8)
- Mixed-style docstrings (should be detected as low confidence)

---

## “Safe enough to scale” rollout plan

1. Implement and validate parsing/rendering for the canonical style(s) first (e.g., Google + NumPy).
2. Add AST enrichment with conservative defaults (report-only on conflicts).
3. Require fixture coverage before enabling autofix on repo-wide runs.
4. Enable batch conversion gradually:
   - run on a small subset of files
   - require clean CI and stable diffs
   - expand batch size (1 → 2 → 4 → 8 …) after each validated run
5. Only then enforce style normalization in CI.

---

## Acceptance criteria

A feature set is “done” when:

- All supported styles:
  - can be detected with confidence scoring
  - can be parsed to IR (or fail safely)
  - can be rendered deterministically
- Autofix mode:
  - only acts above confidence threshold
  - is idempotent
  - preserves examples verbatim
  - never corrupts code formatting
- Tests:
  - include torture fixtures
  - include round-trip and enrichment validations
  - cover the edge-case list above
- `repo-lint` output:
  - provides clear reporting
  - produces durable failure reports consistent with repo contract

---

## Implementation notes (recommended file/module layout)

Example layout (adjust to repo conventions):

- `tools/repo_lint/docstrings/`
  - `ir.py` (IR dataclasses)
  - `detect.py` (style detection)
  - `parse/`
    - `google.py`, `numpy.py`, `rest.py`, `epydoc.py`, `javadoc.py`, `plain.py`
  - `render/`
    - same structure
  - `ast_enrich.py`
  - `rewrite.py` (safe editing)
  - `exceptions.py`
  - `tests/` (fixtures + unit tests)

---

## Notes on type-string normalization (optional future)

Docstring type strings vary (`Optional[int]` vs `int | None`).  
Keep types as opaque strings by default. If normalization is desired later, implement it as a separate, explicit feature with its own tests and safety flags.
