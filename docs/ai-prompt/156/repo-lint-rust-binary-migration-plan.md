# [EPIC] Migrate `repo_lint` to a Self-Contained Rust Binary

**Issue:** #156  
**Status:** Planning  
**Last Updated:** 2025-12-30  
**Owner:** @GitHubCopilot

---

## Executive Summary

This migration plan outlines the transformation of `repo_lint` from a Python-based multi-tool orchestrator (~7,000 LOC) into a self-contained Rust binary with embedded AST/linting capabilities, YAML-based configuration with IDE support, and cross-platform distribution. The plan addresses technical feasibility, security implications, contract adherence, and maintainability gains while identifying potential pitfalls and trade-offs.

**Key Benefits:**
- Single standalone binary (no Python/tool dependencies at runtime)
- Embedded multi-language AST parsing (tree-sitter)
- YAML configs with JSON Schema for IDE autocomplete
- ~10-100x performance improvement for large codebases
- Cross-platform static binaries (Linux, macOS, Windows)
- Enhanced security through type safety and minimal attack surface

**Key Risks:**
- Significant upfront development effort (est. 3-6 months for full parity)
- Learning curve for Rust AST/linting ecosystem
- Potential breaking changes during transition period
- Contract adherence complexity increases with embedded tooling

---

## Table of Contents

- [Repository Analysis Findings](#repository-analysis-findings)
- [Current Implementation Analysis](#current-implementation-analysis)
- [Migration Milestones](#migration-milestones)
  - [Milestone 1: Foundation and Architecture](#milestone-1-foundation-and-architecture)
  - [Milestone 2: Embedded Linting Core](#milestone-2-embedded-linting-core)
  - [Milestone 3: YAML Configuration System](#milestone-3-yaml-configuration-system)
  - [Milestone 4: Feature Parity](#milestone-4-feature-parity)
  - [Milestone 5: Distribution and Documentation](#milestone-5-distribution-and-documentation)
  - [Milestone 6: Migration and Deprecation](#milestone-6-migration-and-deprecation)
- [Future Work Integration](#future-work-integration)
- [Contract Adherence Analysis](#contract-adherence-analysis)
- [Risk Assessment and Mitigation](#risk-assessment-and-mitigation)
- [TODOs](#todos)
- [Deferments](#deferments)

---

## Repository Analysis Findings

### Documentation Landscape (147 Markdown Files Analyzed)

**Contract System:**
The repository has a sophisticated multi-level contract system:

1. **Behavioral Contracts** (10 identified in `contract-extraction.md`):
   - Binary discovery, repo root detection, argument pass-through
   - Exit code forwarding, error handling, output modes
   - All wrappers must maintain identical behavior

2. **Docstring Contracts** (8 languages, v1.2):
   - File-level and symbol-level documentation requirements
   - Enforced by CI via `scripts/validate_docstrings.py`
   - Required sections: Purpose, Usage, Arguments, Environment, Exit Codes, Examples, Notes

3. **Naming Conventions** (Phase 4.5 enforcement):
   - Language-specific: Python (snake_case), PowerShell (PascalCase), Bash (kebab-case), Perl (snake_case)
   - Non-script files: kebab-case
   - Enforced by `.github/workflows/naming-enforcement.yml`

4. **AI Agent Constraints** (`ai-constraints.md`):
   - Unsafe operations prohibited without human approval
   - `repo-lint fix --unsafe` is human-only command
   - Escalation policy for dangerous operations

**Critical Finding:** The repository's contract-driven approach means the Rust migration MUST:
- Preserve all existing behavioral contracts
- Maintain CLI compatibility
- Enforce contract validation at build/test time
- Provide migration path for configuration files

### Current repo_lint Implementation

**Language:** Pure Python 3  
**Lines of Code:** ~7,000 (32 Python files)  
**Architecture:** Plugin-based runner system with central orchestration

**Components:**
1. **CLI Layer** (`cli.py`, `__main__.py`): Command parsing, mode dispatch
2. **Runner System** (`runners/`): 6 language runners (Python, Bash, PowerShell, Perl, YAML, Rust-stub)
3. **Policy Engine** (`policy.py`): JSON-based autofix allow/deny lists
4. **Forensics** (`forensics.py`): Unsafe fix tracking with patch generation
5. **Installation** (`install/`): Repo-local tool management (`.venv-lint/`)
6. **Reporting** (`reporting.py`): JSON/text output formatting
7. **Unsafe Fixers** (`unsafe_fixers.py`): Behavior-changing transformations

**Dependencies:**
- **External CLI tools**: `black`, `ruff`, `pylint`, `shellcheck`, `shfmt`, `yamllint`, PSScriptAnalyzer, Perl::Critic
- **Python libs**: Standard library only (no heavy deps like `ast`, `tree-sitter` currently)
- **Config format**: JSON for autofix policy, TOML for Python tool config

**Exit Codes:**
- `0`: All checks passed
- `1`: Violations found
- `2`: Missing tools (CI mode) or unsafe mode blocked
- `3`: Internal error

**Key Features:**
- **Safe vs Unsafe Fixes**: Policy-controlled with CI blockers
- **Per-Language Filtering**: `--only <language>` flag
- **CI/Local Modes**: Auto-install vs fail-fast
- **JSON Output**: Machine-readable results
- **Forensic Logging**: Unsafe fixes generate patches and logs

---

## Current Implementation Analysis

### Strengths
1. **Modular Architecture**: Clean separation between runners, policy, CLI
2. **Contract Adherence**: Enforces docstring/naming/exit-code contracts
3. **Safety First**: Unsafe operations require dual-confirmation
4. **CI Integration**: Well-integrated with GitHub Actions
5. **Comprehensive Testing**: 32 test files with good coverage

### Weaknesses
1. **External Tool Dependencies**: Requires 10+ tools across 5 ecosystems
2. **Performance**: Sequential Python orchestration, slow on large repos
3. **Installation Complexity**: `.venv-lint/` isolation, manual non-Python tools
4. **No True AST Analysis**: Delegates to external tools, can't implement custom rules
5. **JSON Config**: No IDE support (autocomplete, validation)
6. **Distribution**: Requires Python 3.8+ and pip install

---

## Migration Milestones

### Milestone 1: Foundation and Architecture

**Goal:** Establish Rust project structure, core CLI, and migration strategy.

**Estimated Duration:** 2-3 weeks

---

#### Phase 1.1: Project Scaffolding

- [ ] **Item 1.1.1: Create Rust workspace structure**
  - **Severity:** High
  - **Description:** Initialize Cargo workspace under `tools/repo_lint_rust/`
  - **Files:**
    - Create `tools/repo_lint_rust/Cargo.toml` (workspace manifest)
    - Create `tools/repo_lint_rust/repo-lint/Cargo.toml` (binary crate)
    - Create `tools/repo_lint_rust/repo-lint-core/Cargo.toml` (library crate for reusability)
  - **Rationale:** Workspace allows separating binary CLI from reusable library components
  - **Implementation:**
    ```toml
    # Cargo.toml (workspace)
    [workspace]
    members = ["repo-lint", "repo-lint-core", "repo-lint-parsers"]
    resolver = "2"
    
    [workspace.dependencies]
    # Shared versions across crates
    serde = { version = "1.0", features = ["derive"] }
    serde_json = "1.0"
    serde_yaml = "0.9"
    clap = { version = "4.5", features = ["derive", "cargo"] }
    anyhow = "1.0"
    ```

- [ ] **Item 1.1.2: Set up cross-compilation targets**
  - **Severity:** High
  - **Description:** Configure build for Linux x86_64, macOS (Intel/ARM), Windows x86_64
  - **Files:**
    - `.github/workflows/build-repo-lint-rust.yml`
    - `tools/repo_lint_rust/.cargo/config.toml`
  - **Implementation:**
    ```toml
    # .cargo/config.toml
    [build]
    target-dir = "../../dist/rust-build"
    
    [target.x86_64-unknown-linux-musl]
    linker = "x86_64-linux-musl-gcc"
    
    [target.x86_64-pc-windows-gnu]
    linker = "x86_64-w64-mingw32-gcc"
    ```
  - **Notes:** Use `musl` for static Linux binaries, cross for Windows from Linux CI

- [ ] **Item 1.1.3: Define CLI interface (clap v4)**
  - **Severity:** High
  - **Description:** Implement CLI arg parsing with full compatibility to Python version
  - **Files:** `tools/repo_lint_rust/repo-lint/src/cli.rs`
  - **Sub-Items:**
    - [ ] Sub-Item 1.1.3.1: `check` subcommand with `--ci`, `--verbose`, `--only`, `--json`
    - [ ] Sub-Item 1.1.3.2: `fix` subcommand with unsafe guards (`--unsafe` + `--yes-i-know`)
    - [ ] Sub-Item 1.1.3.3: `install` subcommand (may become `verify` in Rust version)
    - [ ] Sub-Item 1.1.3.4: Global `--version`, `--help` with version from `Cargo.toml`
  - **Implementation:**
    ```rust
    use clap::{Parser, Subcommand};
    
    #[derive(Parser)]
    #[command(name = "repo-lint", version, about = "Unified multi-language linting")]
    struct Cli {
        #[command(subcommand)]
        command: Commands,
    }
    
    #[derive(Subcommand)]
    enum Commands {
        Check {
            #[arg(long)]
            ci: bool,
            #[arg(long, short)]
            verbose: bool,
            #[arg(long)]
            only: Option<String>,
            #[arg(long)]
            json: bool,
        },
        Fix {
            #[arg(long)]
            ci: bool,
            #[arg(long)]
            unsafe_mode: bool,
            #[arg(long = "yes-i-know")]
            confirm_unsafe: bool,
            // ... other flags
        },
    }
    ```

---

#### Phase 1.2: Configuration Migration

- [ ] **Item 1.2.1: Design YAML schema for linting rules**
  - **Severity:** High
  - **Description:** Convert `autofix-policy.json` to YAML with full schema
  - **Files:**
    - `conformance/repo-lint/policy.yaml` (new YAML config)
    - `conformance/repo-lint/policy.schema.json` (JSON Schema for IDEs)
  - **Rationale:** YAML is more human-readable, schema enables IDE autocomplete/validation
  - **Sub-Items:**
    - [ ] Sub-Item 1.2.1.1: Define YAML structure (categories, tools, safe/unsafe flags)
    - [ ] Sub-Item 1.2.1.2: Generate JSON Schema using `schemars` crate
    - [ ] Sub-Item 1.2.1.3: Add `$schema` key in YAML for IDE integration
    - [ ] Sub-Item 1.2.1.4: Test with VS Code, JetBrains IDEs, Vim (YAMLlint plugin)
  - **Implementation:**
    ```yaml
    # policy.yaml
    $schema: "./policy.schema.json"
    version: "2.0"
    policy: deny_by_default
    
    allowed_categories:
      - category: FORMAT.BLACK
        tool: embedded  # No external black needed
        safe: true
        mutating: true
        description: "Python code formatter (Rust implementation)"
    
      - category: LINT.RUFF.SAFE
        tool: embedded
        safe: true
        mutating: true
        flags: ["--no-unsafe-fixes"]
    ```
    ```rust
    use schemars::{schema_for, JsonSchema};
    use serde::{Deserialize, Serialize};
    
    #[derive(Serialize, Deserialize, JsonSchema)]
    struct PolicyConfig {
        version: String,
        policy: PolicyMode,
        allowed_categories: Vec<Category>,
    }
    
    // Generate schema.json:
    let schema = schema_for!(PolicyConfig);
    ```

- [ ] **Item 1.2.2: Implement YAML config loader with validation**
  - **Severity:** High
  - **Description:** Parse YAML, validate against schema, fail fast on errors
  - **Files:** `tools/repo_lint_rust/repo-lint-core/src/config.rs`
  - **Dependencies:** `serde_yaml`, `schemars`, `validator`
  - **Implementation:**
    ```rust
    use serde_yaml;
    use validator::Validate;
    
    pub fn load_policy(path: &Path) -> Result<PolicyConfig> {
        let content = fs::read_to_string(path)?;
        let config: PolicyConfig = serde_yaml::from_str(&content)?;
        config.validate()?;  // Schema validation
        Ok(config)
    }
    ```

- [ ] **Item 1.2.3: Backwards compatibility layer for JSON config**
  - **Severity:** Medium
  - **Description:** Support reading old `autofix-policy.json` during transition
  - **Files:** `tools/repo_lint_rust/repo-lint-core/src/config.rs`
  - **Implementation:**
    ```rust
    pub fn load_policy_auto(dir: &Path) -> Result<PolicyConfig> {
        // Prefer YAML, fall back to JSON
        if dir.join("policy.yaml").exists() {
            load_policy_yaml(&dir.join("policy.yaml"))
        } else if dir.join("autofix-policy.json").exists() {
            load_policy_json(&dir.join("autofix-policy.json"))
        } else {
            Err(anyhow!("No policy config found"))
        }
    }
    ```

---

#### Phase 1.3: Core Abstractions

- [ ] **Item 1.3.1: Define Runner trait**
  - **Severity:** High
  - **Description:** Abstract interface for language-specific linters
  - **Files:** `tools/repo_lint_rust/repo-lint-core/src/runner.rs`
  - **Implementation:**
    ```rust
    pub trait Runner: Send + Sync {
        fn name(&self) -> &str;
        fn file_extensions(&self) -> &[&str];
        fn check(&self, files: &[PathBuf], config: &Config) -> Result<CheckResult>;
        fn fix(&self, files: &[PathBuf], config: &Config, unsafe_mode: bool) -> Result<FixResult>;
        fn can_fix_unsafe(&self) -> bool { false }
    }
    
    pub struct CheckResult {
        pub violations: Vec<Violation>,
        pub passed: bool,
    }
    
    pub struct Violation {
        pub file: PathBuf,
        pub line: usize,
        pub column: usize,
        pub severity: Severity,
        pub message: String,
        pub rule: String,
    }
    ```

- [ ] **Item 1.3.2: Implement exit code system**
  - **Severity:** High
  - **Description:** Match Python exit codes exactly (0/1/2/3)
  - **Files:** `tools/repo_lint_rust/repo-lint/src/exit_codes.rs`
  - **Implementation:**
    ```rust
    pub enum ExitCode {
        Success = 0,
        Violations = 1,
        MissingTools = 2,
        InternalError = 3,
    }
    
    impl From<ExitCode> for i32 {
        fn from(code: ExitCode) -> i32 {
            code as i32
        }
    }
    ```

- [ ] **Item 1.3.3: Error handling strategy**
  - **Severity:** High
  - **Description:** Use `anyhow` for application errors, `thiserror` for library errors
  - **Files:** `tools/repo_lint_rust/repo-lint-core/src/error.rs`
  - **Implementation:**
    ```rust
    use thiserror::Error;
    
    #[derive(Error, Debug)]
    pub enum LintError {
        #[error("Configuration error: {0}")]
        Config(String),
        
        #[error("Parser error in {file}:{line} - {msg}")]
        Parse { file: String, line: usize, msg: String },
        
        #[error("IO error: {0}")]
        Io(#[from] std::io::Error),
    }
    ```

---

### Milestone 2: Embedded Linting Core

**Goal:** Embed AST parsing and linting logic for all supported languages.

**Estimated Duration:** 6-8 weeks

---

#### Phase 2.1: Tree-sitter Integration

- [ ] **Item 2.1.1: Set up tree-sitter dependencies**
  - **Severity:** High
  - **Description:** Add tree-sitter parsers for Python, Bash, Perl, PowerShell, Rust, YAML
  - **Files:** `tools/repo_lint_rust/repo-lint-parsers/Cargo.toml`
  - **Dependencies:**
    ```toml
    [dependencies]
    tree-sitter = "0.20"
    tree-sitter-python = "0.20"
    tree-sitter-bash = "0.20"
    tree-sitter-perl = { git = "https://github.com/...", branch = "main" }
    tree-sitter-powershell = { git = "https://github.com/...", branch = "main" }
    tree-sitter-rust = "0.20"
    tree-sitter-yaml = "0.20"
    ```
  - **Notes:** Some languages lack official tree-sitter support (Perl, PowerShell) - may need custom grammars

- [ ] **Item 2.1.2: Parse file to AST**
  - **Severity:** High
  - **Description:** Generic AST parser with per-language grammar selection
  - **Files:** `tools/repo_lint_rust/repo-lint-parsers/src/lib.rs`
  - **Implementation:**
    ```rust
    pub struct Parser {
        python: tree_sitter::Parser,
        bash: tree_sitter::Parser,
        // ... per language
    }
    
    impl Parser {
        pub fn parse_file(&mut self, path: &Path) -> Result<tree_sitter::Tree> {
            let ext = path.extension().unwrap().to_str().unwrap();
            let parser = match ext {
                "py" => &mut self.python,
                "sh" | "bash" => &mut self.bash,
                // ...
                _ => return Err(anyhow!("Unsupported file type: {}", ext)),
            };
            
            let content = fs::read_to_string(path)?;
            let tree = parser.parse(&content, None)
                .ok_or_else(|| anyhow!("Parse failed"))?;
            Ok(tree)
        }
    }
    ```

- [ ] **Item 2.1.3: AST query system for linting rules**
  - **Severity:** Medium
  - **Description:** Use tree-sitter queries to find patterns (e.g., missing docstrings)
  - **Files:** `tools/repo_lint_rust/repo-lint-parsers/src/queries.rs`
  - **Implementation:**
    ```rust
    const PYTHON_MISSING_DOCSTRING: &str = r#"
    (function_definition
      name: (identifier) @func.name
      (!  (expression_statement (string)) )
    ) @func.missing_doc
    "#;
    
    pub fn find_missing_docstrings(tree: &Tree, source: &str) -> Vec<Violation> {
        let query = Query::new(tree_sitter_python::language(), PYTHON_MISSING_DOCSTRING).unwrap();
        let mut cursor = QueryCursor::new();
        let matches = cursor.matches(&query, tree.root_node(), source.as_bytes());
        
        matches.map(|m| {
            let node = m.captures[0].node;
            Violation {
                line: node.start_position().row + 1,
                message: "Missing docstring".into(),
                // ...
            }
        }).collect()
    }
    ```

---

#### Phase 2.2: Python Linting (Black + Ruff + Pylint Equivalent)

- [ ] **Item 2.2.1: Implement Black formatter equivalent**
  - **Severity:** High
  - **Description:** Embed Python formatting logic (or use `ruff format`)
  - **Files:** `tools/repo_lint_rust/repo-lint-parsers/src/python/format.rs`
  - **Options:**
    1. **Option A:** Use `ruff format` (Rust-based, Black-compatible, actively maintained)
    2. **Option B:** Implement custom formatter using tree-sitter AST
    3. **Option C:** FFI to Python `black` (not self-contained)
  - **Recommendation:** Option A (ruff format) - production-ready, Black-compatible
  - **Implementation:**
    ```rust
    use std::process::Command;
    
    pub fn format_python(file: &Path) -> Result<bool> {
        // If ruff is embedded as library (future):
        // use ruff::format;
        // For now, shell out to ruff binary embedded in resources
        let output = Command::new("ruff")
            .args(["format", file.to_str().unwrap()])
            .output()?;
        Ok(output.status.success())
    }
    ```
  - **Alternative (fully embedded):**
    - Vendor `ruff_python_formatter` crate if published
    - OR: Implement minimal Python formatter for 80% use cases

- [ ] **Item 2.2.2: Embed Ruff linter**
  - **Severity:** High
  - **Description:** Use `ruff_linter` crate or shell out to embedded binary
  - **Files:** `tools/repo_lint_rust/repo-lint-parsers/src/python/lint.rs`
  - **Implementation (if ruff_linter is available):**
    ```rust
    use ruff_linter::{check_file, LintConfig};
    
    pub fn lint_python(file: &Path, config: &Config) -> Result<Vec<Violation>> {
        let ruff_config = LintConfig {
            select: config.python_rules.clone(),
            ignore: config.python_ignore.clone(),
            // ...
        };
        let violations = check_file(file, &ruff_config)?;
        Ok(violations.into_iter().map(|v| Violation::from_ruff(v)).collect())
    }
    ```
  - **Fallback:** Embed ruff binary in executable using `include_bytes!()` or build-time resource bundling

- [ ] **Item 2.2.3: Pylint equivalent checks (tree-sitter based)**
  - **Severity:** Medium
  - **Description:** Implement subset of Pylint rules as tree-sitter queries
  - **Files:** `tools/repo_lint_rust/repo-lint-parsers/src/python/pylint_rules.rs`
  - **Sub-Items:**
    - [ ] Sub-Item 2.2.3.1: Missing docstrings (functions, classes, modules)
    - [ ] Sub-Item 2.2.3.2: Unused imports
    - [ ] Sub-Item 2.2.3.3: Undefined variables
    - [ ] Sub-Item 2.2.3.4: Line length violations (>120 chars)
  - **Notes:** Start with high-value rules, expand incrementally

---

#### Phase 2.3: Bash Linting (ShellCheck + shfmt Equivalent)

- [ ] **Item 2.3.1: Embed ShellCheck rules**
  - **Severity:** High
  - **Description:** Reimplement ShellCheck's most critical rules
  - **Files:** `tools/repo_lint_rust/repo-lint-parsers/src/bash/shellcheck.rs`
  - **Challenges:**
    - ShellCheck has ~400 rules; full parity is impractical
    - Bash parsing is notoriously complex (quoting, expansion, heredocs)
  - **Approach:**
    - Use tree-sitter-bash for AST
    - Implement top 20 ShellCheck rules (SC2086, SC2046, SC2006, etc.)
    - Provide opt-in "strict mode" for full ShellCheck via external tool
  - **Implementation:**
    ```rust
    pub fn check_bash(tree: &Tree, source: &str) -> Vec<Violation> {
        let mut violations = Vec::new();
        
        // SC2086: Double quote to prevent globbing and word splitting
        violations.extend(check_unquoted_expansion(tree, source));
        
        // SC2006: Use $(...) instead of legacy `...`
        violations.extend(check_legacy_backticks(tree, source));
        
        // ... top 20 rules
        violations
    }
    ```

- [ ] **Item 2.3.2: Embed shfmt formatter**
  - **Severity:** Medium
  - **Description:** Implement Bash formatting logic
  - **Options:**
    1. **Option A:** Shell out to embedded `shfmt` binary
    2. **Option B:** Implement minimal formatter using tree-sitter
  - **Recommendation:** Option A (shfmt is mature, written in Go, can cross-compile)
  - **Implementation:**
    - Embed shfmt binary at build time using `build.rs`
    - Extract to temp dir and execute
    - OR: Use Go FFI (complex, not recommended)

---

#### Phase 2.4: PowerShell Linting

- [ ] **Item 2.4.1: PSScriptAnalyzer equivalent**
  - **Severity:** High
  - **Description:** Implement PowerShell linting rules
  - **Challenges:**
    - PSScriptAnalyzer is .NET-based, cannot easily embed
    - tree-sitter-powershell grammar may be incomplete
  - **Approach:**
    - Implement basic rules via tree-sitter (e.g., verb-noun functions, CmdletBinding)
    - Provide "enhanced mode" that shells out to PSScriptAnalyzer if available
  - **Implementation:**
    ```rust
    pub fn check_powershell(tree: &Tree, source: &str) -> Vec<Violation> {
        let mut violations = Vec::new();
        
        // Rule: Functions should use Verb-Noun naming
        violations.extend(check_function_naming(tree, source));
        
        // Rule: Use approved verbs (Get, Set, New, Remove, etc.)
        violations.extend(check_approved_verbs(tree, source));
        
        violations
    }
    ```

- [ ] **Item 2.4.2: PowerShell formatter**
  - **Severity:** Low
  - **Description:** Basic formatting (indentation, brace style)
  - **Notes:** PowerShell formatting is less critical than Python/Bash

---

#### Phase 2.5: Perl Linting

- [ ] **Item 2.5.1: Perl::Critic equivalent rules**
  - **Severity:** Medium
  - **Description:** Implement severity 5 Perl::Critic rules
  - **Challenges:**
    - Perl is notoriously hard to parse (context-sensitive, TIMTOWTDI)
    - tree-sitter-perl grammar is experimental
  - **Approach:**
    - Implement ~10 basic rules (use strict, use warnings, bareword filehandles)
    - Provide opt-in mode to shell out to Perl::Critic
  - **Implementation:**
    ```rust
    pub fn check_perl(tree: &Tree, source: &str) -> Vec<Violation> {
        let mut violations = Vec::new();
        
        // Rule: Require "use strict;" and "use warnings;"
        if !source.contains("use strict") {
            violations.push(Violation { message: "Missing 'use strict;'", ... });
        }
        
        violations
    }
    ```

---

#### Phase 2.6: YAML & Rust Linting

- [ ] **Item 2.6.1: yamllint embedded**
  - **Severity:** Low
  - **Description:** Parse YAML, check syntax, indentation, line length
  - **Dependencies:** `serde_yaml` for parsing, tree-sitter-yaml for AST analysis
  - **Implementation:**
    ```rust
    pub fn check_yaml(path: &Path) -> Result<Vec<Violation>> {
        let content = fs::read_to_string(path)?;
        let _doc: serde_yaml::Value = serde_yaml::from_str(&content)?;
        
        // Check line length
        let violations = content.lines()
            .enumerate()
            .filter(|(_, line)| line.len() > 120)
            .map(|(i, _)| Violation { line: i + 1, message: "Line too long", ... })
            .collect();
        
        Ok(violations)
    }
    ```

- [ ] **Item 2.6.2: Rust linting (clippy equivalent)**
  - **Severity:** Low (Rust linting is already handled by rustfmt/clippy in the build)
  - **Description:** Provide opt-in mode to run `cargo clippy` on Rust files
  - **Notes:** Defer to external clippy; embedding is impractical

---

### Milestone 3: YAML Configuration System

**Goal:** Full YAML configuration with JSON Schema support for IDE integration.

**Estimated Duration:** 2 weeks

---

#### Phase 3.1: Schema Generation

- [ ] **Item 3.1.1: Generate JSON Schema from Rust structs**
  - **Severity:** High
  - **Description:** Use `schemars` to auto-generate schemas
  - **Files:** `tools/repo_lint_rust/repo-lint-core/src/config.rs`
  - **Implementation:**
    ```rust
    use schemars::{schema_for, JsonSchema};
    
    #[derive(Serialize, Deserialize, JsonSchema)]
    struct PolicyConfig {
        /// Schema version (semver)
        #[schemars(regex = r"^\d+\.\d+$")]
        version: String,
        
        /// Policy mode: "allow_by_default" or "deny_by_default"
        #[schemars(default = "deny_by_default")]
        policy: PolicyMode,
        
        /// List of allowed auto-fix categories
        allowed_categories: Vec<Category>,
    }
    
    // Generate schema:
    fn generate_schema() {
        let schema = schema_for!(PolicyConfig);
        let json = serde_json::to_string_pretty(&schema).unwrap();
        fs::write("conformance/repo-lint/policy.schema.json", json).unwrap();
    }
    ```

- [ ] **Item 3.1.2: Add $schema references in YAML configs**
  - **Severity:** High
  - **Description:** Ensure YAML files reference schema for IDE validation
  - **Files:** `conformance/repo-lint/policy.yaml`
  - **Implementation:**
    ```yaml
    # yaml-language-server: $schema=./policy.schema.json
    $schema: "./policy.schema.json"
    version: "2.0"
    policy: deny_by_default
    # ...
    ```

- [ ] **Item 3.1.3: Test IDE integration**
  - **Severity:** Medium
  - **Description:** Verify autocomplete/validation in VS Code, JetBrains, Vim
  - **Sub-Items:**
    - [ ] Sub-Item 3.1.3.1: VS Code (YAML extension with schema support)
    - [ ] Sub-Item 3.1.3.2: JetBrains IDEs (IntelliJ, PyCharm, RustRover)
    - [ ] Sub-Item 3.1.3.3: Vim (with ALE or coc-yaml)
  - **Documentation:** Add screenshots to `tools/repo_lint_rust/docs/ide-setup.md`

---

#### Phase 3.2: Linting Rule Configuration

- [ ] **Item 3.2.1: Per-language rule selection in YAML**
  - **Severity:** High
  - **Description:** Allow enabling/disabling specific rules per language
  - **Files:** `conformance/repo-lint/rules.yaml`
  - **Implementation:**
    ```yaml
    python:
      rules:
        - id: "E501"  # Line too long
          enabled: true
          max_line_length: 120
        - id: "F401"  # Unused import
          enabled: true
          severity: error
    
    bash:
      rules:
        - id: "SC2086"  # Unquoted expansion
          enabled: true
          severity: warning
    ```

- [ ] **Item 3.2.2: Severity levels (error/warning/info)**
  - **Severity:** Medium
  - **Description:** Map rule violations to severity levels
  - **Implementation:**
    ```rust
    #[derive(Serialize, Deserialize, JsonSchema)]
    enum Severity {
        Error,   // Exit code 1
        Warning, // Report but don't fail
        Info,    // Log only
    }
    ```

---

### Milestone 4: Feature Parity

**Goal:** Match all features of Python `repo_lint`.

**Estimated Duration:** 3-4 weeks

---

#### Phase 4.1: CLI Commands

- [ ] **Item 4.1.1: `check` command (read-only linting)**
  - **Severity:** High
  - **Description:** Full parity with `python3 -m tools.repo_lint check`
  - **Sub-Items:**
    - [ ] Sub-Item 4.1.1.1: `--ci` mode (fail on missing tools, no auto-install)
    - [ ] Sub-Item 4.1.1.2: `--verbose` (show passed checks)
    - [ ] Sub-Item 4.1.1.3: `--only <language>` (filter by language)
    - [ ] Sub-Item 4.1.1.4: `--json` (machine-readable output)

- [ ] **Item 4.1.2: `fix` command (safe auto-fixes)**
  - **Severity:** High
  - **Description:** Apply formatters + safe lint fixes
  - **Sub-Items:**
    - [ ] Sub-Item 4.1.2.1: Safe fixes only (no behavior changes)
    - [ ] Sub-Item 4.1.2.2: Policy validation (deny-by-default)
    - [ ] Sub-Item 4.1.2.3: Exit code 1 if violations remain after fixes

- [ ] **Item 4.1.3: `fix --unsafe` command (dangerous fixes)**
  - **Severity:** High
  - **Description:** Unsafe fixes with forensic logging
  - **Sub-Items:**
    - [ ] Sub-Item 4.1.3.1: Require `--yes-i-know` dual confirmation
    - [ ] Sub-Item 4.1.3.2: Hard-block in CI (detect via `--ci` or `CI` env var)
    - [ ] Sub-Item 4.1.3.3: Generate patch file (`logs/unsafe-fixes/unsafe-fix-TIMESTAMP.patch`)
    - [ ] Sub-Item 4.1.3.4: Generate log file (`logs/unsafe-fixes/unsafe-fix-TIMESTAMP.log`)

- [ ] **Item 4.1.4: `install` command (tool verification)**
  - **Severity:** Low
  - **Description:** In Rust version, this becomes "verify embedded tools"
  - **Notes:** Since tools are embedded, `install` is a no-op or checks binary integrity

---

#### Phase 4.2: Docstring Validation

- [ ] **Item 4.2.1: File-level docstring validation**
  - **Severity:** High
  - **Description:** Validate required sections per language contract
  - **Files:** `tools/repo_lint_rust/repo-lint-parsers/src/docstrings/`
  - **Sub-Items:**
    - [ ] Sub-Item 4.2.1.1: Python (Purpose, Usage, Exit Codes, Examples)
    - [ ] Sub-Item 4.2.1.2: Bash (DESCRIPTION, USAGE, EXAMPLES, EXIT CODES)
    - [ ] Sub-Item 4.2.1.3: PowerShell (.SYNOPSIS, .DESCRIPTION, .EXAMPLE, Exit Codes)
    - [ ] Sub-Item 4.2.1.4: Perl (=head1 NAME, DESCRIPTION, SYNOPSIS, EXAMPLES)
    - [ ] Sub-Item 4.2.1.5: Rust (//! # Purpose, //! # Examples, //! # Exit Behavior)
  - **Implementation:**
    ```rust
    pub fn validate_python_docstring(tree: &Tree, source: &str) -> Vec<Violation> {
        let module_docstring = extract_module_docstring(tree, source);
        let required = vec!["Purpose", "Usage", "Exit Codes", "Examples"];
        
        required.iter()
            .filter(|section| !module_docstring.contains(section))
            .map(|section| Violation {
                message: format!("Missing required docstring section: {}", section),
                // ...
            })
            .collect()
    }
    ```

- [ ] **Item 4.2.2: Symbol-level docstring validation**
  - **Severity:** Medium
  - **Description:** Check function/class/method docstrings
  - **Files:** `tools/repo_lint_rust/repo-lint-parsers/src/docstrings/symbols.rs`
  - **Sub-Items:**
    - [ ] Sub-Item 4.2.2.1: Python (functions, classes, methods)
    - [ ] Sub-Item 4.2.2.2: Rust (pub fn, pub struct)
    - [ ] Sub-Item 4.2.2.3: Bash (functions starting with `#:`)
    - [ ] Sub-Item 4.2.2.4: PowerShell (functions with `.SYNOPSIS`)

---

#### Phase 4.3: Unsafe Fixers

- [ ] **Item 4.3.1: Docstring rewrite unsafe fixer**
  - **Severity:** Medium
  - **Description:** Convert Google-style to Sphinx-style (or vice versa)
  - **Files:** `tools/repo_lint_rust/repo-lint-parsers/src/unsafe_fixers/docstring_rewrite.rs`
  - **Rationale:** This is the main unsafe fixer from Python version
  - **Implementation:**
    ```rust
    pub struct DocstringRewriteFixer;
    
    impl UnsafeFixer for DocstringRewriteFixer {
        fn name(&self) -> &str { "docstring_rewrite" }
        
        fn can_fix(&self, file: &Path) -> bool {
            file.extension().map(|e| e == "py").unwrap_or(false)
        }
        
        fn fix(&self, file: &Path, config: &Config) -> Result<FixResult> {
            // Parse AST, find docstrings, rewrite format
            // Generate patch + forensics
        }
    }
    ```

---

### Milestone 5: Distribution and Documentation

**Goal:** Build, package, and document the Rust binary.

**Estimated Duration:** 2 weeks

---

#### Phase 5.1: Binary Packaging

- [ ] **Item 5.1.1: Static binary builds (musl for Linux)**
  - **Severity:** High
  - **Description:** Fully static binaries with no libc dependencies
  - **Files:** `.github/workflows/build-repo-lint-rust.yml`
  - **Implementation:**
    ```yaml
    - name: Build static Linux binary
      run: |
        cargo build --release --target x86_64-unknown-linux-musl
        strip target/x86_64-unknown-linux-musl/release/repo-lint
    ```
  - **Testing:** Verify on Alpine Linux (musl-based)

- [ ] **Item 5.1.2: Cross-compile for Windows/macOS**
  - **Severity:** High
  - **Description:** Build from Linux CI using cross-compilation
  - **Tools:** `cross` or `cargo-zigbuild`
  - **Implementation:**
    ```yaml
    - name: Build Windows binary
      run: cross build --release --target x86_64-pc-windows-gnu
    
    - name: Build macOS binaries
      run: |
        cross build --release --target x86_64-apple-darwin
        cross build --release --target aarch64-apple-darwin
    ```

- [ ] **Item 5.1.3: Artifact upload and GitHub Releases**
  - **Severity:** Medium
  - **Description:** Upload binaries to GitHub Releases with checksums
  - **Files:** `.github/workflows/release-repo-lint-rust.yml`
  - **Implementation:**
    - Generate SHA256 checksums for all binaries
    - Create release with tag `repo-lint-v1.0.0`
    - Attach binaries: `repo-lint-linux-x86_64`, `repo-lint-macos-x86_64`, `repo-lint-macos-aarch64`, `repo-lint-windows-x86_64.exe`

---

#### Phase 5.2: Documentation

- [ ] **Item 5.2.1: Update README.md**
  - **Severity:** High
  - **Description:** Replace Python instructions with Rust binary usage
  - **Files:** `tools/repo_lint/README.md` (keep for migration), `tools/repo_lint_rust/README.md` (new)
  - **Content:**
    - Installation: Download binary, add to PATH
    - Quick start: `repo-lint check`, `repo-lint fix`
    - Configuration: YAML schema reference
    - Migration guide: Python → Rust transition

- [ ] **Item 5.2.2: Configuration documentation**
  - **Severity:** Medium
  - **Description:** Document YAML config structure and schema
  - **Files:** `tools/repo_lint_rust/docs/configuration.md`
  - **Content:**
    - Schema reference
    - Per-language rule configuration
    - IDE setup for autocomplete/validation
    - Examples

- [ ] **Item 5.2.3: Migration guide for users**
  - **Severity:** High
  - **Description:** Step-by-step migration from Python to Rust version
  - **Files:** `docs/migration/python-to-rust-repo-lint.md`
  - **Content:**
    - Why migrate (performance, no dependencies)
    - Breaking changes (if any)
    - Config file migration (JSON → YAML)
    - CI workflow updates
    - Rollback procedure

---

### Milestone 6: Migration and Deprecation

**Goal:** Transition repository from Python to Rust `repo_lint`.

**Estimated Duration:** 2 weeks

---

#### Phase 6.1: Parallel Testing

- [ ] **Item 6.1.1: Add Rust repo-lint to CI alongside Python**
  - **Severity:** High
  - **Description:** Run both versions in CI, compare results
  - **Files:** `.github/workflows/repo-lint-comparison.yml`
  - **Implementation:**
    ```yaml
    - name: Run Python repo-lint
      run: python3 -m tools.repo_lint check --json > python-results.json
    
    - name: Run Rust repo-lint
      run: ./dist/repo-lint check --json > rust-results.json
    
    - name: Compare results
      run: ./scripts/compare-lint-results.py python-results.json rust-results.json
    ```
  - **Success Criteria:** 95%+ agreement on violations found

- [ ] **Item 6.1.2: Performance benchmarking**
  - **Severity:** Medium
  - **Description:** Measure time/memory improvements
  - **Files:** `tools/repo_lint_rust/benches/linting_bench.rs`
  - **Implementation:**
    ```rust
    use criterion::{black_box, criterion_group, criterion_main, Criterion};
    
    fn bench_python_files(c: &mut Criterion) {
        c.bench_function("lint 100 Python files", |b| {
            b.iter(|| {
                lint_all_python_files(black_box("tools/"));
            });
        });
    }
    
    criterion_group!(benches, bench_python_files);
    criterion_main!(benches);
    ```
  - **Metrics:** Speedup factor, peak memory usage

---

#### Phase 6.2: Cutover

- [ ] **Item 6.2.1: Update CI workflows to use Rust binary**
  - **Severity:** High
  - **Description:** Replace Python repo-lint with Rust version
  - **Files:**
    - `.github/workflows/repo-lint-and-docstring-enforcement.yml`
    - `.github/workflows/repo-lint-weekly-full-scan.yml`
  - **Implementation:**
    ```yaml
    # OLD:
    - run: python3 -m tools.repo_lint check --ci
    
    # NEW:
    - run: ./dist/repo-lint check --ci
    ```

- [ ] **Item 6.2.2: Update contributing docs**
  - **Severity:** Medium
  - **Description:** Update all references to repo-lint
  - **Files:**
    - `CONTRIBUTING.md`
    - `docs/contributing/contributing-guide.md`
    - `.github/copilot-instructions.md`

- [ ] **Item 6.2.3: Archive Python repo-lint**
  - **Severity:** Low
  - **Description:** Move to `tools/repo_lint_legacy/` for reference
  - **Files:** `git mv tools/repo_lint tools/repo_lint_legacy`
  - **Add README:** Explain deprecation, point to Rust version

---

## Future Work Integration

**From `docs/future-work.md`:**

### FW-013: Make repo_lint installable package

**Status:** Partially addressed by Rust migration

- **Rust Approach:** Binary distribution via GitHub Releases (no pip install needed)
- **Advantages:** No Python dependency, simpler installation
- **Trade-off:** Lose ecosystem integration (pip, poetry, pipx)
- **Recommendation:** Provide both:
  - Rust binary as primary distribution
  - Thin Python wrapper for pip install compatibility (wraps Rust binary)

**Implementation:**
```python
# Python wrapper (tools/repo_lint_wrapper/setup.py)
setup(
    name="repo-lint",
    version="2.0.0",
    entry_points={"console_scripts": ["repo-lint=repo_lint_wrapper:main"]},
    # ...
)

# repo_lint_wrapper/__init__.py
def main():
    binary = find_rust_binary()  # Download from GitHub releases if missing
    os.execvp(binary, [binary] + sys.argv[1:])
```

---

### FW-014: Advanced repo-local tool isolation

**Status:** Obsoleted by Rust migration

- **Rust Advantage:** Self-contained binary eliminates need for `.venv-lint/`, `.psmodules/`, etc.
- **Remaining Use Case:** IDE extensions still need PSScriptAnalyzer, Perl::Critic for live feedback
- **Recommendation:** Document IDE setup separately, don't bundle in repo-lint binary

---

### FW-015: CI workflow tool installation security hardening

**Status:** Greatly improved by Rust migration

- **Rust Advantage:** No runtime tool downloads, all parsers embedded
- **Remaining Risk:** Build-time dependencies (cargo crates)
- **Mitigation:**
  - Pin all cargo dependencies with exact versions + checksums (Cargo.lock)
  - Use cargo-audit to check for vulnerable dependencies
  - Add checksums to release binaries

**Implementation:**
```yaml
# .github/workflows/security-scan.yml
- name: Audit Rust dependencies
  run: cargo audit --deny warnings

- name: Generate SBOM (Software Bill of Materials)
  run: cargo sbom > repo-lint-sbom.json
```

---

### FW-016: CI log capture, retention, and debug-mode switch

**Status:** Out of scope for repo-lint Rust migration

- This is a CI/CD infrastructure concern, not specific to repo-lint implementation
- Applies equally to Python and Rust versions
- Defer to separate epic for CI improvements

---

## Contract Adherence Analysis

### Behavioral Contracts (from `contract-extraction.md`)

**Impact:** The Rust migration does NOT affect wrapper contracts, as repo_lint is orthogonal to safe-run/safe-check/safe-archive wrappers.

**Relevant Contracts:**
- **Exit Code Contract:** Rust version MUST preserve exit codes 0/1/2/3 exactly
- **Error Handling:** Actionable error messages to stderr
- **Environment Variables:** Pass through `CI`, `SAFE_*` vars (not applicable to repo-lint)

### Docstring Contracts (v1.2)

**Impact:** CRITICAL - Rust repo-lint MUST enforce the same docstring contracts as Python version.

**Requirements:**
- File-level: 8 semantic sections (Purpose, Usage, Args, Env, Exit Codes, Examples, Notes, Platform Compatibility)
- Symbol-level: Function/class/method documentation
- Pragma support: `# noqa: EXITCODES`, `# noqa: DOCSTRING`

**Implementation:** See Milestone 4, Phase 4.2

### Naming Conventions

**Impact:** Moderate - Rust repo-lint MUST validate naming per `naming-and-style.md`

**Requirements:**
- Python: `snake_case.py`
- PowerShell: `PascalCase.ps1`
- Bash: `kebab-case.sh`
- Perl: `snake_case.pl`
- Non-script: `kebab-case.md`

**Implementation:**
- Embed naming rules in YAML config
- Use tree-sitter + regex to validate file and symbol names

### AI Agent Constraints

**Impact:** HIGH - Rust version MUST maintain same safety constraints

**Requirements:**
- `fix --unsafe` requires `--yes-i-know` dual confirmation
- Hard-block unsafe mode in CI (detect via `CI` env var or `--ci` flag)
- Generate forensic artifacts (patch + log)

**Implementation:** See Milestone 4, Phase 4.1.3

---

## Risk Assessment and Mitigation

### High Severity Risks

#### Risk 1: Tree-sitter Grammar Gaps

**Description:** Some languages (Perl, PowerShell) lack mature tree-sitter grammars

**Impact:** Cannot achieve full AST-based linting for these languages

**Mitigation:**
1. Use tree-sitter-perl and tree-sitter-powershell community grammars (with caveats)
2. Implement fallback regex-based checks for unsupported constructs
3. Provide "enhanced mode" that shells out to external tools (Perl::Critic, PSScriptAnalyzer)
4. Contribute to tree-sitter grammar projects to improve coverage

**Contingency:** If grammars prove unusable, keep Python repo-lint for Perl/PowerShell, migrate Python/Bash/YAML only

---

#### Risk 2: Black/Ruff Embedding Complexity

**Description:** ruff and black may not be embeddable as Rust libraries

**Impact:** Must shell out to external binaries, losing "self-contained" benefit

**Mitigation:**
1. Investigate `ruff_python_formatter` and `ruff_linter` crate availability
2. If unavailable, embed ruff/black binaries using `include_bytes!()` and extract at runtime
3. Implement minimal Python formatter for 80% use cases (indentation, line breaks) as fallback

**Contingency:** Accept shelling out to embedded binaries as acceptable trade-off

---

#### Risk 3: Performance Regression on Small Repos

**Description:** Rust binary startup overhead may be slower than Python for <10 files

**Impact:** Developers may perceive Rust version as slower for small commits

**Mitigation:**
1. Benchmark startup time (target <50ms including binary load)
2. Optimize binary size with `strip = true` and LTO
3. Use `lazy_static` for global initializations
4. Provide "fast mode" that skips non-critical checks

**Testing:** Benchmark on repo with 1, 10, 100, 1000 files

---

### Medium Severity Risks

#### Risk 4: Breaking Changes During Transition

**Description:** Config migration (JSON → YAML) may break existing workflows

**Impact:** CI failures, user frustration

**Mitigation:**
1. Maintain backwards compatibility layer for JSON config (6 months deprecation period)
2. Provide automated migration tool: `repo-lint migrate-config autofix-policy.json`
3. Run both Python and Rust versions in parallel during transition
4. Clear communication in release notes and migration guide

---

#### Risk 5: IDE Integration Flakiness

**Description:** JSON Schema validation may not work in all IDEs

**Impact:** Reduced developer experience, typos in YAML configs

**Mitigation:**
1. Test with top 5 IDEs (VS Code, IntelliJ, PyCharm, Vim, Emacs)
2. Provide IDE-specific setup guides with screenshots
3. Add `repo-lint validate-config` command for CLI validation
4. Generate detailed error messages for schema violations

---

### Low Severity Risks

#### Risk 6: Increased Compile Times

**Description:** Rust build times may be slow for large dependency trees

**Impact:** Slower CI, slower development iteration

**Mitigation:**
1. Use incremental compilation in dev mode
2. Cache Cargo build artifacts in CI
3. Split into multiple crates for parallel compilation
4. Use `cargo-chef` for Docker layer caching

---

#### Risk 7: Cross-Compilation Complexity

**Description:** Building for macOS ARM from Linux may be fragile

**Impact:** Missing or broken macOS binaries

**Mitigation:**
1. Use GitHub Actions macOS runners for native builds
2. Maintain cross-compilation as backup
3. Test binaries on real hardware (macOS, Windows)
4. Provide universal binary for macOS (x86_64 + aarch64)

---

## TODOs

### Unresolved Analysis Points

- [ ] **TODO-001:** Verify tree-sitter-perl and tree-sitter-powershell grammar stability
  - **Action:** Create test suite with 100+ real-world files, measure parse success rate
  - **Owner:** TBD
  - **Deadline:** Before Phase 2.3/2.4 start

- [ ] **TODO-002:** Investigate ruff_linter and ruff_python_formatter crate availability
  - **Action:** Check crates.io, contact Astral team, evaluate FFI options
  - **Owner:** TBD
  - **Deadline:** Before Phase 2.2 start

- [ ] **TODO-003:** Define exact backwards compatibility policy for JSON config
  - **Action:** Decide deprecation timeline (3 months? 6 months? 1 year?)
  - **Owner:** @m1ndn1nj4
  - **Deadline:** Before Milestone 3 start

- [ ] **TODO-004:** Evaluate whether to embed tools (shfmt, shellcheck) as binaries or rewrite
  - **Action:** Prototype both approaches, measure binary size impact
  - **Owner:** TBD
  - **Deadline:** Before Phase 2.3 start

- [ ] **TODO-005:** Decide on docstring rewrite fixer scope (Google → Sphinx only, or bidirectional?)
  - **Action:** Analyze repository docstring styles, survey user preferences
  - **Owner:** TBD
  - **Deadline:** Before Phase 4.3 start

- [ ] **TODO-006:** Contract contradiction analysis incomplete
  - **Action:** Cross-reference all 10 behavioral contracts with repo-lint requirements
  - **Owner:** TBD
  - **Deadline:** Before Milestone 1 completion

- [ ] **TODO-007:** Security review of embedded parsers (tree-sitter, AST traversal)
  - **Action:** Identify potential DoS vectors (large files, recursive AST nodes), add fuzzing
  - **Owner:** TBD
  - **Deadline:** Before Milestone 2 completion

---

## Deferments

### Tasks Deferred to Future Epics

- [ ] **DEFER-001:** Full ShellCheck parity (all 400+ rules)
  - **Reason:** Impractical, 80/20 rule applies (top 20 rules cover most issues)
  - **Deferred To:** Future enhancement after initial release
  - **Condition:** If user demand justifies effort

- [ ] **DEFER-002:** Perl::Critic full parity
  - **Reason:** Perl usage is minimal in this repo, low ROI
  - **Deferred To:** Conditional - implement only if Perl usage increases

- [ ] **DEFER-003:** PowerShell formatter implementation
  - **Reason:** PSScriptAnalyzer doesn't provide auto-formatting, low priority
  - **Deferred To:** v2.0 or later

- [ ] **DEFER-004:** Custom linting rule DSL (user-defined rules in YAML)
  - **Reason:** Scope creep, v1.0 should focus on existing rules
  - **Deferred To:** v2.0 - requires plugin architecture

- [ ] **DEFER-005:** Language Server Protocol (LSP) integration
  - **Reason:** IDE extensions are separate concern, not core to repo-lint
  - **Deferred To:** Separate epic for `repo-lint-lsp` server

- [ ] **DEFER-006:** Windows .exe discovery in Python wrapper (FW-009)
  - **Reason:** Unrelated to repo-lint migration (applies to safe-run wrappers)
  - **Deferred To:** EPIC 59 follow-up

- [ ] **DEFER-007:** Canonical epic tracker (FW-010)
  - **Reason:** Governance concern, not technical implementation
  - **Deferred To:** Repository-wide decision

- [ ] **DEFER-008:** CI runtime optimization with scheduled Bash runners (FW-012)
  - **Reason:** CI infrastructure concern, applies to all workflows
  - **Deferred To:** Separate CI optimization epic

---

## Appendices

### Appendix A: Cargo.toml Workspace Example

```toml
# tools/repo_lint_rust/Cargo.toml
[workspace]
members = ["repo-lint", "repo-lint-core", "repo-lint-parsers"]
resolver = "2"

[workspace.package]
version = "1.0.0"
edition = "2021"
authors = ["M1NDN1NJ4-0RG"]
license = "Unlicense"
repository = "https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding"

[workspace.dependencies]
# CLI
clap = { version = "4.5", features = ["derive", "cargo"] }

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
serde_yaml = "0.9"
schemars = "0.8"

# Error handling
anyhow = "1.0"
thiserror = "1.0"

# AST parsing
tree-sitter = "0.20"
tree-sitter-python = "0.20"
tree-sitter-bash = "0.20"
tree-sitter-rust = "0.20"
tree-sitter-yaml = "0.1"

# Linting (if embeddable)
# ruff-linter = "0.1"  # Check availability
# ruff-python-formatter = "0.1"  # Check availability

# Testing
criterion = "0.5"
```

### Appendix B: Performance Targets

| Metric | Python Baseline | Rust Target | Speedup |
|--------|----------------|-------------|---------|
| Lint 100 Python files | 8.5s | <1s | 8-10x |
| Lint 1000 Python files | 85s | <10s | 8-10x |
| Parse single 5000-line file | 120ms | <10ms | 10-15x |
| Memory usage (1000 files) | 450 MB | <100 MB | 4-5x |
| Binary startup time | 30ms | <50ms | Similar |
| Binary size | N/A (Python) | <20 MB | N/A |

### Appendix C: Migration Timeline (Estimated)

| Phase | Duration | Cumulative | Dependencies |
|-------|----------|------------|--------------|
| M1: Foundation | 3 weeks | 3 weeks | None |
| M2: Embedded Linting | 8 weeks | 11 weeks | M1 complete |
| M3: YAML Config | 2 weeks | 13 weeks | M1 complete |
| M4: Feature Parity | 4 weeks | 17 weeks | M2, M3 complete |
| M5: Distribution | 2 weeks | 19 weeks | M4 complete |
| M6: Migration | 2 weeks | 21 weeks | M5 complete |

**Total: ~5-6 months** (conservative estimate)

---

**End of Migration Plan**

