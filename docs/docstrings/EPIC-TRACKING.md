# [Epic] Strengthen and Harmonize Docstring Contracts Across All Languages

**Issue:** TBD (GitHub issue number will be assigned)  
**Status:** In Progress  
**Last Updated:** 2025-12-28

## Why
The current docstring contracts in `/docs/docstrings/` are a powerful mechanism for enforcing consistency, discoverability, and AI-agent compliance (especially Copilot). However, there are inconsistencies in section naming, required vs. optional elements, template completeness, and validation depth. Harmonizing and tightening these contracts will:
- Reduce friction when writing new scripts
- Improve validator accuracy and usefulness
- Make AI-generated code even more reliably compliant
- Future-proof the system for new languages and deeper checks

## Phased Approach

### Phase 1: Cross-Cutting Foundations & Consistency
- [x] Create tracking document `docs/docstrings/EPIC-TRACKING.md`
- [ ] Update `docs/docstrings/README.md`
  - [ ] Add mapping table: Required Semantic Section → Language-Specific Keywords
  - [ ] Add "How to Extend Contracts" section
  - [ ] Add "Prompting Tips for AI Tools" section
  - [ ] Fix references to use full paths
  - [ ] Add link to validator script's docstring
- [ ] Enhance `scripts/validate-docstrings.py`
  - [ ] Add optional pragma support (e.g., `# noqa: EXITCODES`)
  - [ ] Add basic content checks for EXIT CODES
  - [ ] Add single-file mode flag
- [x] Create `docs/docstrings/EXIT_CODES_CONTRACT.md`

### Phase 2: Language-Specific Harmonization & Completion
- [ ] `bash.md`
  - [ ] Review and verify template completeness
  - [ ] Standardize section order to match README
  - [ ] Ensure EXIT CODES is prominently featured in OUTPUTS
  - [ ] Verify "Common Mistakes" section exists and is comprehensive
  - [ ] Verify line length limit and shebang requirements are documented
- [ ] `perl.md`
  - [ ] Review and verify template completeness
  - [ ] Review BINARY DISCOVERY + ENVIRONMENT VARIABLES organization
  - [ ] Verify "NOTES" is used consistently over "CAVEATS"
  - [ ] Add/verify guidance on intra-doc links (L<>)
- [ ] `powershell.md`
  - [ ] Introduce dedicated `.EXITCODES` keyword recommendation
  - [ ] Document when `.INPUTS`/`.OUTPUTS` should be required
  - [ ] Expand validation notes
  - [ ] Standardize example prompts (remove inconsistent paths)
- [ ] `python.md`
  - [ ] Review and verify template completeness
  - [ ] Unify section naming: "CLI Interface"/"Usage" → "Usage"
  - [ ] Ensure "Exit Codes" is a top-level section
  - [ ] Add docstring placement rule (after shebang, before imports)
  - [ ] Add PEP 8 width guidance (72 chars)
- [ ] `rust.md`
  - [ ] Review and verify template completeness
  - [ ] Standardize on "# Exit Codes" instead of "# Exit Behavior"
  - [ ] Add clear templates distinguishing `lib.rs` vs `main.rs`
  - [ ] Emphasize `cargo doc --open` for local preview
- [ ] `yaml.md`
  - [ ] Review and verify template completeness
  - [ ] Clarify "Triggers:" and "Usage:" guidance
  - [ ] Make "Permissions:" required for GitHub Actions workflow YAMLs
  - [ ] Add "Environment:" section guidance (matrix, jobs, runners)
  - [ ] Standardize header names consistency

### Phase 3: Optional Enhancements & Future-Proofing
- [ ] Add "Platform Compatibility" as an optional but encouraged section across all contracts
- [ ] Version the contract suite (e.g., introduce `CONTRACT_VERSION: 1.1` in README)
- [ ] Add unit tests for the validator script covering each language
- [ ] Optional: Begin planning for deeper semantic validation (e.g., param name matching, type hint checks)
- [ ] Optional: Add preliminary contracts for potential future languages (e.g., JavaScript/Node, Go)

## Acceptance Criteria
- [x] Tracking document created and maintained
- [x] Shared exit codes reference doc exists
- [ ] All language contract templates are complete and consistent
- [ ] README is updated with mappings, extension guide, and AI prompting tips
- [ ] Validator supports pragma ignores and basic content checks
- [ ] Documentation is clear and actionable for both humans and AI agents

## Notes
- This epic focuses on making minimal, surgical improvements to existing contracts
- Each phase can be completed incrementally with separate PRs
- Focus on consistency and completeness over adding new features
- All changes should maintain backward compatibility where possible

## References
- Original contracts: `docs/docstrings/`
- Validator: `scripts/validate-docstrings.py`
- Repository instructions: `.github/copilot-instructions.md`
