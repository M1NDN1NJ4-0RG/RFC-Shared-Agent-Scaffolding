# Comprehensive Autofix Strategy Plan (Issue #278)

## Human Decision (MANDATORY Order)

Per human instruction comment #3726894000:
1. **FIRST**: Implement autofixers (Option A: PEP 526 + docstring `:rtype:`)
2. **SECOND**: Build style converter (Option B: bidirectional reST ↔ Google ↔ NumPy)
3. **THIRD**: Proceed to Phases 5-6 (CI enforcement + documentation)

---

## Part 1: Python Type Annotation Autofixers (PRIORITY 1)

### Phase 4.3: PEP 526 Autofix Tool (8-10 hours)

**Design**: `docs/ai-prompt/278/278-phase-4-pep526-docstring-autofix.md` (already created)

**Implementation tasks:**
- [ ] 4.3.1: Create `tools/repo_lint/fixers/pep526_fixer.py`
  - AST-based analyzer for module-level and class attribute assignments
  - Literal inference: `TIMEOUT = 30` → `TIMEOUT: int = 30`
  - Typed constructors: `ROOT = Path(".")` → `ROOT: Path = Path(".")`
  - Function return types: `CONFIG = get_config()` → infer from annotation
  - Skip already annotated variables
  - Skip empty collections (ambiguous: `[]`, `{}`, `set()`)
  
- [ ] 4.3.2: Add CLI integration
  - `repo-lint fix --pep526` flag
  - `--dry-run` mode to preview changes
  - `--diff` mode to show git-style diffs
  
- [ ] 4.3.3: Comprehensive unit tests
  - Test literal inference (int, str, bool, float)
  - Test Path constructor detection
  - Test function return type lookup
  - Test edge cases (unpacking, comprehensions, etc.)
  - Test that already-annotated code is skipped
  - Golden fixtures for before/after validation
  
- [ ] 4.3.4: Run on codebase
  - Apply to all Python files
  - Estimated ~60-90 fixes (40-65% of 152 PEP 526 violations)
  - Verify with `repo-lint check --ci`

**Coverage estimate**: 40-65% of PEP 526 violations auto-fixable

---

### Phase 4.4: Docstring `:rtype:` Autofix Tool (6-8 hours)

**Design**: `docs/ai-prompt/278/278-phase-4-pep526-docstring-autofix.md` (already created)

**Implementation tasks:**
- [ ] 4.4.1: Create `tools/repo_lint/fixers/docstring_rtype_fixer.py`
  - AST-based analyzer for functions with return annotations
  - Parse reST docstrings
  - Check if `:rtype:` field exists
  - If missing and function has `-> T` (not `-> None`): add `:rtype: T`
  - Preserve exact type annotation syntax (use `ast.unparse()`)
  - Insert `:rtype:` after `:returns:` or other fields
  
- [ ] 4.4.2: Add CLI integration
  - `repo-lint fix --docstring-rtype` flag
  - `--dry-run` and `--diff` modes
  
- [ ] 4.4.3: Comprehensive unit tests
  - Test adding `:rtype:` to functions with various return types
  - Test skipping `-> None` functions
  - Test preserving existing `:rtype:` fields
  - Test complex types (generics, unions, optionals)
  - Test docstring structure preservation
  
- [ ] 4.4.4: Run on codebase
  - Apply to all Python files
  - Estimated ~370 fixes (functions with annotations but missing `:rtype:`)
  - Verify with docstring validator

**Coverage estimate**: ~370 docstrings fixed

---

## Part 2: Docstring Style Converter (PRIORITY 2)

### Phase 4.5: Bidirectional Docstring Converter (10-15 hours)

**Design**: `docs/ai-prompt/278/278-docstring-style-converter-design.md` (already created)

**Implementation tasks:**
- [ ] 4.5.1: Install and evaluate `docstring_parser` library
  - Test parsing capabilities for reST, Google, NumPy styles
  - Verify semantic model extraction
  - Confirm it meets our needs
  
- [ ] 4.5.2: Build formatters
  - [ ] Create `tools/repo_lint/docstrings/formatters/rest_formatter.py`
  - [ ] Create `tools/repo_lint/docstrings/formatters/google_formatter.py`
  - [ ] Create `tools/repo_lint/docstrings/formatters/numpy_formatter.py`
  - Each formatter converts semantic model → target style
  
- [ ] 4.5.3: Build converter orchestrator
  - [ ] Create `tools/repo_lint/docstrings/converter.py`
  - Auto-detect source style (heuristics: `:param:` = reST, `Args:` = Google, `Parameters\n---` = NumPy)
  - Chain: parse → enhance with AST → format
  - Support all 6 conversion pairs
  
- [ ] 4.5.4: AST integration
  - Enhance DocstringModel with function signature type hints
  - Merge parameter/return types from annotations into docstring
  - This enables auto-adding `:rtype:` via reST→reST conversion trick!
  
- [ ] 4.5.5: CLI integration
  - `repo-lint convert-docstrings --from-style <style> --to-style <style> [files]`
  - `--in-place` to modify files
  - `--diff` to preview changes
  - `--from-style auto` for auto-detection
  
- [ ] 4.5.6: Comprehensive tests
  - Test all 6 conversion pairs (reST↔Google, reST↔NumPy, Google↔NumPy)
  - Test auto-detection
  - Test AST enrichment (adding types from annotations)
  - Test edge cases (generators, complex generics, missing descriptions)
  
- [ ] 4.5.7: Optional: Run on codebase
  - Convert any Google/NumPy docstrings to reST (repo standard)
  - Or leave as future enhancement tool

**Benefit**: Universal docstring style converter + bonus `:rtype:` autofix via conversion

---

## Part 3: MD013 Smart Reflow Fixer (NEW REQUIREMENT - PRIORITY 3)

### Phase 4.6: MD013 Markdown Line Length Smart Fixer (15-20 hours)

**Design**: `docs/ai-prompt/278/278-md013-smart-reflow-recommendations.md` (already exists)

**Current state**: Basic `textwrap.fill()` implementation in `scripts/fix_md013_line_length_option_b.py`
- Handles simple paragraphs
- Fails on blockquotes, nested lists, checkboxes, lazy continuations

**Implementation roadmap (from design doc):**

- [ ] 4.6.1: Phase 1 - Add proper context tracking
  - State machine for list depth stack (indent_level, marker_type, marker_text)
  - Track blockquote depth (number of `>` prefixes)
  - Track continuation paragraphs (no blank line since last item)
  - When wrapping: first line keeps marker, continuation lines get indent + prefixes
  
- [ ] 4.6.2: Phase 2 - Smart paragraph & continuation handling
  - Detect lazy continuations (indent ≥ content indent, not new marker)
  - Wrap with hanging indent (+2 or +4 spaces)
  - Preserve multi-paragraph blocks inside list items
  
- [ ] 4.6.3: Phase 3 - Checkbox & mixed marker protection
  - Special handling for `- [ ]` / `- [x]` markers (never duplicate)
  - Support mixed bullet types (`*`, `-`, `+`) and ordered (`.`, `)`)
  
- [ ] 4.6.4: Phase 4 - Admonition & edge cases
  - Preserve `> [!NOTE]` / `> [!WARNING]` exactly
  - Handle HTML comments without breaking context
  - Verify frontmatter, footnotes, reference defs, images, autolinks are skipped
  
- [ ] 4.6.5: Phase 5 - Tooling & safety
  - Add CLI flags: `--max-line-length`, `--dry-run`, `--diff`, `--in-place`, `--check`
  - `--check` mode: exit non-zero if fixes needed (for CI)
  - Unit tests using torture garden fixture (bad → apply fixer → compare to good)
  
- [ ] 4.6.6: Phase 6 - Integration & mass deployment
  - Hook into `repo_lint`: new rule `md013-smart`
  - Optional `--auto-fix-md013=smart` flag
  - Run repo-wide (exclude `repo-lint-failure-reports/`)
  - Watch ~1,800+ MD013 violations vanish

**Coverage estimate**: ~1,800 MD013 line-length violations (currently 1,888 remain after basic auto-fix)

---

## Part 4: Examine Existing Tools for Autofix Potential (NEW REQUIREMENT)

### Tool-by-Tool Analysis

#### Python Tools (fix-capable ✅):
1. **black**: Already auto-formats Python code ✅
   - No additional work needed
   
2. **ruff**: Already supports `--fix` and `--unsafe-fixes` ✅
   - We used this for Phase 4.2 Stage 1 (586 return type fixes)
   - No additional work needed
   
3. **pylint**: NO autofix capability ❌
   - Diagnostic only
   - No action needed

#### Bash Tools:
4. **shfmt**: Already auto-formats shell scripts ✅
   - Currently integrated as fix-capable
   - No additional work needed
   
5. **shellcheck**: NO built-in autofix ❌
   - Diagnostic only
   - Could build wrapper for some fixes (e.g., quote variables)
   - **Recommendation**: LOW PRIORITY - manual fixes preferred for shell safety

#### Rust Tools:
6. **rustfmt**: Already auto-formats Rust code ✅
   - Currently integrated as fix-capable
   - No additional work needed
   
7. **clippy**: Some fixes available via `--fix` flag ⚠️
   - **ACTION**: Investigate if `cargo clippy --fix` is safe to integrate
   - Could auto-fix some lints
   - **Recommendation**: MEDIUM PRIORITY

#### YAML, TOML, JSON, Markdown Tools:
8. **yamllint**: NO autofix capability ❌
   - Diagnostic only
   - No action needed

9. **Taplo** (TOML): Already auto-formats ✅
   - Currently integrated as fix-capable
   - No additional work needed

10. **Prettier** (JSON/JSONC): Already auto-formats ✅
    - Currently integrated as fix-capable
    - No additional work needed

11. **markdownlint-cli2** (Markdown): Has `--fix` flag ✅
    - Currently integrated as fix-capable
    - Basic fixes work, but MD013 needs smart fixer (Phase 4.6)

#### Perl and PowerShell Tools:
12. **perlcritic** (Perl): NO autofix capability ❌
    - Diagnostic only
    - No action needed

13. **PSScriptAnalyzer** (PowerShell): Some fixes via `-Fix` flag ⚠️
    - **ACTION**: Investigate if safe to integrate
    - **Recommendation**: LOW PRIORITY (PowerShell usage is minimal)

### Summary: Additional Autofix Opportunities

**High Priority (Implement):**
- ✅ Python: PEP 526 fixer (Phase 4.3)
- ✅ Python: Docstring `:rtype:` fixer (Phase 4.4)
- ✅ Markdown: MD013 smart reflow fixer (Phase 4.6)

**Medium Priority (Investigate):**
- ⚠️ Rust: `cargo clippy --fix` integration
- ⚠️ PowerShell: `PSScriptAnalyzer -Fix` integration

**Already Working (No Action):**
- ✅ Python: black, ruff
- ✅ Bash: shfmt
- ✅ Rust: rustfmt
- ✅ TOML: Taplo
- ✅ JSON: Prettier
- ✅ Markdown: markdownlint-cli2 (basic fixes)

**Not Applicable (Diagnostic Only):**
- ❌ Python: pylint
- ❌ Bash: shellcheck
- ❌ YAML: yamllint
- ❌ Perl: perlcritic

---

## Execution Plan (MANDATORY Order from Human)

### FIRST: Implement Python Autofixers (Option A)

1. **Phase 4.3**: PEP 526 autofix tool (8-10 hours)
2. **Phase 4.4**: Docstring `:rtype:` autofix tool (6-8 hours)
3. **Apply both**: Run on codebase, commit, verify

**Total time**: 14-18 hours  
**Expected fixes**: ~60-90 PEP 526 + ~370 docstring `:rtype:` = **~430-460 violations resolved**

### SECOND: Build Style Converter (Option B)

4. **Phase 4.5**: Bidirectional docstring converter (10-15 hours)

**Total time**: 10-15 hours  
**Benefit**: Universal converter + bonus tool for future migrations

### THIRD: MD013 Smart Fixer (NEW - High Impact)

5. **Phase 4.6**: MD013 smart reflow fixer (15-20 hours)

**Total time**: 15-20 hours  
**Expected fixes**: ~1,800 MD013 violations resolved

### FOURTH: Investigate Medium Priority Tools (Optional)

6. Research `cargo clippy --fix` safety
7. Research `PSScriptAnalyzer -Fix` safety

**Total time**: 2-4 hours

### FIFTH: Proceed to Phases 5-6 (Option C - MANDATORY)

8. **Phase 5**: CI enforcement rollout
9. **Phase 6**: Documentation updates

---

## Total Estimated Timeline

- **Python autofixers (FIRST)**: 14-18 hours → ~430-460 fixes
- **Style converter (SECOND)**: 10-15 hours → Universal tool
- **MD013 fixer (THIRD)**: 15-20 hours → ~1,800 fixes
- **Tool investigation (OPTIONAL)**: 2-4 hours
- **Phases 5-6 (MANDATORY)**: 8-12 hours

**Grand total**: 49-69 hours for complete autofix infrastructure + enforcement

**Total violations resolvable**: ~2,800+ violations auto-fixed (Python + Markdown combined)

---

## Success Metrics

After all autofixers implemented:
- **PEP 526**: ~90 remaining manual fixes (60% auto-fixed)
- **Docstring `:rtype:`**: ~0 remaining (100% auto-fixed where annotations exist)
- **MD013**: ~88 remaining manual fixes (95% auto-fixed)
- **Function annotations**: ~200-300 remaining manual (parameters only)

**Overall**: ~75-85% of all type annotation and formatting violations auto-fixed

---

## Next Steps

**IMMEDIATE**: Begin Phase 4.3 (PEP 526 autofix tool) per human decision Option A.

Update `278-next-steps.md` and `278-overview.md` to reflect this comprehensive plan.
