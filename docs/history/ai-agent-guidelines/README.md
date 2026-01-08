# AI Agent Guidelines (Archived)

**Status:** Historical / Archived

## Purpose

This directory contains historical AI agent guidelines and workflow templates that were originally embedded within the
wrapper scripts directory structure. These files have been archived here to separate documentation from code structure.

## Contents

### Agent Shards (`agent/`)

Modular documentation files that provided guidance for GitHub Copilot agents during the wrapper implementation phase:

- `00_INDEX.md` - Index and overview of agent guidelines
- `10_CORE_RULES.md` - Core development rules and principles
- `20_GIT_WORKFLOW.md` - Git workflow and commit conventions
- `21_AUTO_MERGE_WAITING.md` - Auto-merge waiting procedures
- `22_AUTOMERGE_PREFLIGHT.md` - Pre-merge validation checklist
- `30_TESTING_STANDARDS.md` - Testing requirements and standards
- `40_BUILD_AND_VERIFICATION.md` - Build and verification procedures
- `50_DEPENDENCIES.md` - Dependency management guidelines

### Journal Templates (`journal/`)

Work tracking templates used during wrapper development:

- `CURRENT.md` - Current work status template
- `TEMPLATE.md` - Generic journal entry template
- `PR-LOG/README.md` - Pull request log template

### Claude Documentation

- `claude.md` - Original Claude AI agent guidelines for wrapper development

## Why Archived

These files served their purpose during the wrapper implementation phase (Epic #33) and provided valuable structure for
AI-assisted development. They have been archived to:

1. **Separate concerns**: Code structure should not contain agent-specific documentation
2. **Preserve history**: These files document the development methodology used
3. **Maintain clarity**: Future contributors can focus on canonical documentation in `docs/`

## Current Agent Guidelines

For current repository-wide agent guidelines, see:

- [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md) - Repository-level Copilot instructions
- [`docs/contributing/`](../../contributing/) - Contributing guidelines and standards

## Historical Context

These files were created during:

- **Epic #33**: Rust Canonical Tool Implementation
- **Date Range**: 2024 (estimated based on wrapper development timeline)
- **Purpose**: Guide AI coding agents through wrapper script creation and validation

The methodology proved effective and some concepts have been integrated into the repository-wide agent instructions.
