# Historical Documentation

This directory contains historical documents, decision logs, and progress summaries from the development of the
RFC-Shared-Agent-Scaffolding repository.

## Purpose

The history directory serves as an archive of:

- **Milestone summaries** - Completion reports for major development milestones
- **Epic tracking** - Progress and completion of epics
- **PR summaries** - Notable pull request completion reports
- **Decision records** - Technical decisions and their rationale
- **Verification reports** - Testing and validation evidence
- **Legacy documentation** - Archived guidelines and instructions

## Navigation

### Major Epics

- **[EPIC #3 Completion](./epic-3-final-summary.md)** - Initial epic completion
  - [M0 Summary](./epic-3-m0-summary.md) - Milestone 0 summary
  - [Update](./epic-3-update.md) - Epic 3 progress update

- **[EPIC #33 Rust Canonical Tool](./epic-33-rust-canonical-tool-completion.md)** - Complete Rust implementation
  - [Final Completion](./epic-33-final-completion-summary.md) - Final summary
  - [Verification Summary](./epic-33-verification-summary.md) - Verification results
  - [Completion Summary](./epic-completion-summary.md) - Overall completion

- **[EPIC #59 Next Steps](./epic-59-next-steps.md)** - Future work planning

### Milestone Summaries

#### M0 (Milestone 0)

- [M0 Decisions](./m0-decisions.md) - Initial decisions and baseline

#### M1 (Documentation Consolidation)

- [M1 Documentation Consolidation](./m1-documentation-consolidation-summary.md) - docs/ structure creation
- [M1-P2-I1 Status](./m1-p2-i1-status.md) - Phase 2, Item 1 status
- [M1-P3-I1 Decision](./m1-p3-i1-decision.md) - Phase 3, Item 1 decision
- [M1-P5-I1 Status](./m1-p5-i1-status.md) - Phase 5, Item 1 status

#### M2-M4 (Wrappers and Drift Detection)

- [M2-M3-M4 Completion](./m2-m3-m4-completion-summary.md) - Combined milestone summary
- [M2-P2-I1 Drift Detection](./m2-p2-i1-drift-detection.md) - Cross-language drift detection strategy

#### M5 (Final Verification)

- [M5 Final Verification](./m5-final-verification-summary.md) - Final verification summary

### Pull Request Summaries

Notable PRs that introduced significant functionality:

- **[PR0: Preflight Complete](./pr0-preflight-complete.md)** - Initial baseline and conformance
- **[PR1: Rust Scaffolding](./pr1-rust-scaffolding-complete.md)** - Rust project scaffolding
- **[PR2: Conformance Harness](./pr2-conformance-harness-complete.md)** - Conformance testing framework
- **[PR3: Safe-Run Implementation](./pr3-safe-run-implementation-complete.md)** - safe-run command implementation
- **[PR62: CI Failure Prompt](./pr-62-ci-failure-prompt.md)** - CI failure handling

### Verification and Testing

- [P0-P3.5 Verification Report](./p0-p3.5-verification-report.md) - Comprehensive verification report
- [P4 Bash Wrapper Conversion](./p4-bash-wrapper-conversion-complete.md) - Bash wrapper conversion to invoker pattern
- [Phase 3 Windows Ctrl+C Probe](./phase3-windows-ctrlc-probe.md) - Windows signal handling investigation
- [Future Work Verification Report](./future-work-verification-report.md) - Future enhancements

### Legacy AI Agent Guidelines

Archived guidelines for AI agents working on this repository:

- [AI Agent Guidelines](./ai-agent-guidelines/) - Sharded agent instructions and journal
  - `agent/` - Sharded rule files (core rules, git workflow, testing standards, etc.)
  - `journal/` - PR log templates and tracking
  - [Wrappers README (Legacy)](./ai-agent-guidelines/wrappers-readme-legacy.md) - Original wrappers README (moved from
    wrappers/)

## How to Use This Directory

### For Understanding Project History

Read documents in chronological order by milestone (M0 → M1 → M2-M4 → M5) or by epic (EPIC #3 → EPIC #33 → EPIC #59).

### For Decision Context

When wondering "why was this done this way?", search for decision documents (e.g., `m1-p3-i1-decision.md`) or PR summaries.

### For Verification Evidence

Verification reports contain test results, conformance data, and validation evidence from specific development phases.

### For Legacy Guidelines

The `ai-agent-guidelines/` directory contains archived agent instructions. These are historical - current guidelines are in `.github/copilot-instructions.md` and docs/contributing/.

## Updating This Index

When adding new historical documents:

1. Add the file to the appropriate section above (Epics, Milestones, PRs, Verification)
2. Use descriptive titles and links
3. Include a brief description of what the document covers
4. Maintain chronological or logical grouping

## Related Documentation

- [Main Documentation Index](../README.md) - Current documentation
- [Contributing Guide](../contributing/contributing-guide.md) - How to contribute
- [Architecture Documentation](../architecture/) - Current system design
