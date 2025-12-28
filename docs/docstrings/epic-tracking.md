# [Epic] Strengthen and Harmonize Docstring Contracts Across All Languages

**Issue:** TBD (GitHub issue number will be assigned)  
**Status:** Complete  
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
- [x] Update `docs/docstrings/README.md`
  - [x] Add mapping table: Required Semantic Section → Language-Specific Keywords
  - [x] Add "How to Extend Contracts" section
  - [x] Add "Prompting Tips for AI Tools" section
  - [x] Fix references to use full paths
  - [x] Add link to validator script's docstring
- [x] Enhance `scripts/validate-docstrings.py`
  - [x] Add optional pragma support (e.g., `# noqa: EXITCODES`)
  - [x] Add basic content checks for EXIT CODES
  - [x] Add single-file mode flag
- [x] Create `docs/docstrings/exit-codes-contract.md`

### Phase 2: Language-Specific Harmonization & Completion
- [x] `bash.md`
  - [x] Review and verify template completeness
  - [x] Standardize section order to match README
  - [x] Ensure EXIT CODES is prominently featured in OUTPUTS
  - [x] Verify "Common Mistakes" section exists and is comprehensive
  - [x] Verify line length limit and shebang requirements are documented
- [x] `perl.md`
  - [x] Review and verify template completeness
  - [x] Review BINARY DISCOVERY + ENVIRONMENT VARIABLES organization
  - [x] Verify "NOTES" is used consistently over "CAVEATS"
  - [x] Add/verify guidance on intra-doc links (L<>)
- [x] `powershell.md`
  - [x] Introduce dedicated `.EXITCODES` keyword recommendation
  - [x] Document when `.INPUTS`/`.OUTPUTS` should be required
  - [x] Expand validation notes
  - [x] Standardize example prompts (remove inconsistent paths)
- [x] `python.md`
  - [x] Review and verify template completeness
  - [x] Unify section naming: "CLI Interface"/"Usage" → "Usage"
  - [x] Ensure "Exit Codes" is a top-level section
  - [x] Add docstring placement rule (after shebang, before imports)
  - [x] Add PEP 8 width guidance (72 chars)
- [x] `rust.md`
  - [x] Review and verify template completeness
  - [x] Standardize on "# Exit Codes" instead of "# Exit Behavior"
  - [x] Add clear templates distinguishing `lib.rs` vs `main.rs`
  - [x] Emphasize `cargo doc --open` for local preview
- [x] `yaml.md`
  - [x] Review and verify template completeness
  - [x] Clarify "Triggers:" and "Usage:" guidance
  - [x] Make "Permissions:" required for GitHub Actions workflow YAMLs
  - [x] Add "Environment:" section guidance (matrix, jobs, runners)
  - [x] Standardize header names consistency

### Phase 3: Optional Enhancements & Future-Proofing
- [x] Add "Platform Compatibility" as an optional but encouraged section across all contracts
- [x] Version the contract suite (e.g., introduce `CONTRACT_VERSION: 1.1` in README)
- [x] Add unit tests for the validator script covering each language
- [x] Optional: Begin planning for deeper semantic validation (e.g., param name matching, type hint checks)
- [x] Optional: Add preliminary contracts for potential future languages (e.g., JavaScript/Node, Go)

## Acceptance Criteria
- [x] Tracking document created and maintained
- [x] Shared exit codes reference doc exists
- [x] All language contract templates are complete and consistent
- [x] README is updated with mappings, extension guide, and AI prompting tips
- [x] Validator supports pragma ignores and basic content checks
- [x] Documentation is clear and actionable for both humans and AI agents
- [x] Contract suite is versioned (v1.1)
- [x] Platform compatibility is optional but recommended across all contracts
- [x] Unit tests added for validator
- [x] Future validation plans documented
- [x] Preliminary contract for future language (JavaScript) created

## Notes
- This epic was completed across multiple commits
- All phases (1, 2, and 3) are now complete
- The docstring contract system is now at version 1.1
- Future enhancements documented in FUTURE_VALIDATION.md
- Preliminary JavaScript contract available for future adoption

## Completion Summary

**Date Completed:** 2025-12-28

### Key Deliverables
1. **exit-codes-contract.md** - Comprehensive exit code reference for all languages
2. **Enhanced Validator** - Pragma support, content checks, single-file mode
3. **Semantic Mapping Table** - Maps required sections to language-specific keywords
4. **Extension Guide** - Step-by-step guide for adding new languages
5. **AI Prompting Guide** - Best practices for using GitHub Copilot with contracts
6. **Harmonized Contracts** - All 6 language contracts (bash, perl, powershell, python, rust, yaml) updated
7. **Unit Tests** - test-validate-docstrings.py with coverage for each language
8. **Version History** - Contract suite now versioned (v1.1)
9. **Platform Compatibility** - Recommended as optional section across all contracts
10. **Future Planning** - FUTURE_VALIDATION.md outlines next-generation validation
11. **JavaScript Contract (DRAFT)** - Preliminary contract for potential future use

### Impact
- **52 files** validated across repository
- **All validations passing**
- **Consistent documentation** across 6 programming languages
- **AI-agent friendly** with prompting tips and clear templates
- **Extensible** with guide for adding new languages
- **Future-proof** with planning doc and preliminary contracts

### References
- Commits: 0511095, 5e5c878, 9f756e1, 7384cea, 62a4624, and final Phase 3 commit
- Main epic issue: TBD
- Related documentation: All files in docs/docstrings/
- This epic focuses on making minimal, surgical improvements to existing contracts
- Each phase can be completed incrementally with separate PRs
- Focus on consistency and completeness over adding new features
- All changes should maintain backward compatibility where possible

## References
- Original contracts: `docs/docstrings/`
- Validator: `scripts/validate-docstrings.py`
- Repository instructions: `.github/copilot-instructions.md`
