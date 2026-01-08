# Documentation Index

This directory contains all documentation for the RFC-Shared-Agent-Scaffolding repository.

## Start Here

Choose your path based on your role:

### 👤 Users (Running the Tools)

**You want to:** Use safe-run, safe-check, or safe-archive in your projects

**Start with:**

1. 1. [RFC v0.1.0](../rfc-shared-agent-scaffolding-v0.1.0.md) - What the contract does 2. [Usage Guide](./usage/) - How
   to use the tools 3. [Wrapper Discovery](./architecture/wrapper-discovery.md) - How wrappers find the Rust binary

**Quick example:**

```bash
# Build the Rust tool
cd rust/ && cargo build --release

# Run via wrapper
wrappers/bash/scripts/safe-run.sh echo "Hello World"
```

### 🔧 Contributors (Adding Features or Fixing Bugs)

**You want to:** Contribute code, documentation, or tests

**Start with:**

1. 1. **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Quick start guide (GitHub surfaces this) 2. [Contributing
   Guide](./contributing/contributing-guide.md) - Detailed workflow, naming conventions, PR process 3. [Docstring
   Contracts](./contributing/docstring-contracts/README.md) - Required documentation standards for all languages 4.
   [Testing Documentation](./testing/conformance-tests.md) - How to run and write tests

**Before your first PR:**

- - Review [Naming and Style](./contributing/naming-and-style.md) - File naming and symbol conventions
- Run `python3 -m tools.repo_lint check` - Validate your changes
- - Ensure all tests pass (Rust + wrappers + conformance)

### 🏗️ Maintainers (Architecture and Design)

**You want to:** Understand design decisions, architectural constraints, and long-term structure

**Start with:**

1. 1. [Canonical Structure](./architecture/canonical-structure.md) - Repository directory layout 2. [Contract
   Extraction](./architecture/contract-extraction.md) - Contract definitions and specifications 3. [Risk Vector
   Enumeration](./architecture/risk-vector-enumeration.md) - Risk analysis and mitigation 4. [Rust Canonical
   Tool](./architecture/rust-canonical-tool.md) - Implementation details

**Decision logs:**

- - [History Index](./history/README.md) - Complete index of epics, milestones, and decisions - [Allowed
  Drift](./contributing/allowed-drift.md) - Behavioral difference policy

---

## Documentation Structure

### Overview

High-level summaries and project documentation:

- - [Final Summary](./overview/final-summary.md) - Complete project overview - [Chat
  Summary](./overview/chat-summary.md) - Development conversation summary

### Architecture

Design documents, specifications, and structural decisions:

- - [Canonical Structure](./architecture/canonical-structure.md) - Repository directory layout - [Contract
  Extraction](./architecture/contract-extraction.md) - Contract definitions and specifications - [Risk Vector
  Enumeration](./architecture/risk-vector-enumeration.md) - Risk analysis and mitigation strategies

### Usage

How to use the tools and scripts in this repository:

- - [Conformance Contract](./usage/conformance-contract.md) - Contract specification - [Rust Canonical
  Tool](./architecture/rust-canonical-tool.md) - Rust implementation guide - [Safe Archive
  Guide](./usage/safe-archive.md) - Archive utility documentation - [Wrapper
  Discovery](./architecture/wrapper-discovery.md) - How wrappers find the Rust binary

### Testing

Test plans, evidence, and validation procedures:

- - [Conformance Tests](./testing/conformance-tests.md) - Test specifications - [Instrumentation
  Evidence](./testing/instrumentation-evidence.md) - Test execution evidence - [CI Validation
  Checklist](./testing/ci-validation-checklist.md) - CI requirements and validation

### Contributing

Guidelines for contributing to the project:

- - **[Root CONTRIBUTING.md](../CONTRIBUTING.md)** - Quick start guide for contributors (GitHub surfaces this
  automatically) - [Contributing Guide](./contributing/contributing-guide.md) - Detailed contributing workflow (naming
  conventions, required checks, PR process) - [Allowed Drift](./contributing/allowed-drift.md) - Behavioral difference
  policy - [Docstring Contracts](./contributing/docstring-contracts/README.md) - Documentation standards for all
  languages

### History

Historical documents, decision logs, and progress tracking:

- - **[History Index](./history/README.md)** - Complete index of historical documentation - Major epics (EPIC #3, EPIC
  #33, EPIC #59) - Milestone summaries (M0, M1, M2-M4, M5) - PR completion reports - Verification evidence and decision
  records - Legacy AI agent guidelines

## Additional Resources

- - [RFC v0.1.0](../rfc-shared-agent-scaffolding-v0.1.0.md) - Contract specification - [Main README](../README.md) -
  Repository overview - [License](../LICENSE) - Unlicense
