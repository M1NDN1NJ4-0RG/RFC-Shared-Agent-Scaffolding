//! # Integration Tests for Bootstrap v2
//!
//! End-to-end tests for the complete bootstrap flow.
//!
//! # Purpose
//!
//! Tests the full install/verify/doctor command flows with realistic scenarios.
//! Validates checkpoint save/load/resume functionality.
//!
//! # Examples
//!
//! ```no_run
//! // Run with: cargo test --test integration_tests
//! ```

use safe_run::bootstrap_v2::checkpoint::Checkpoint;
use safe_run::bootstrap_v2::config::Config;
use safe_run::bootstrap_v2::context::{Context, OsType, PackageManager, Verbosity};
use safe_run::bootstrap_v2::doctor::{doctor, CheckStatus};
use safe_run::bootstrap_v2::installers::InstallerRegistry;
use safe_run::bootstrap_v2::plan::ExecutionPlan;
use std::sync::Arc;
use tempfile::TempDir;

/// Helper to create a test context
fn create_test_context(temp_dir: &TempDir, dry_run: bool) -> Context {
    let config = Arc::new(Config::default());
    Context::with_config(
        temp_dir.path().to_path_buf(),
        OsType::detect(),
        PackageManager::detect(OsType::detect()),
        dry_run,
        Verbosity::Normal,
        None, // no progress reporter in tests
        config,
        true,    // ci_mode
        Some(2), // jobs
        false,   // offline
        false,   // allow_downgrade
    )
}

#[tokio::test]
async fn test_full_install_flow_dry_run() {
    let temp_dir = TempDir::new().unwrap();
    let ctx = create_test_context(&temp_dir, true);

    // Create registry
    let registry = InstallerRegistry::new();

    // Compute plan for a minimal set of tools
    let plan = ExecutionPlan::compute(
        &registry,
        &ctx.config,
        &ctx,
        "dev", // profile
    )
    .await;

    assert!(plan.is_ok(), "Plan computation should succeed");
    let plan = plan.unwrap();

    assert!(!plan.phases.is_empty(), "Plan should have phases");
    assert_eq!(
        plan.phases[0].name, "Detection",
        "First phase should be detection"
    );

    // In dry-run mode, we can't execute the full plan because
    // verification will fail for tools that aren't actually installed.
    // Instead, test individual installer dry-run mode
    let ripgrep = registry.get("ripgrep").unwrap();
    let result = ripgrep.install(&ctx).await;
    assert!(result.is_ok(), "Dry-run install should succeed");
}

#[tokio::test]
async fn test_checkpoint_save_load_resume() {
    let temp_dir = TempDir::new().unwrap();
    let ctx = create_test_context(&temp_dir, true);

    // Compute a plan
    let plan = ExecutionPlan::compute(&InstallerRegistry::new(), &ctx.config, &ctx, "dev")
        .await
        .unwrap();

    // Create a checkpoint
    let mut checkpoint = Checkpoint::new(&plan);
    checkpoint.mark_completed("detect-ripgrep".to_string());
    checkpoint.mark_completed("detect-python-black".to_string());
    checkpoint.mark_failed("install-actionlint".to_string());

    // Save checkpoint
    let save_result = checkpoint.save(temp_dir.path());
    assert!(save_result.is_ok(), "Checkpoint save should succeed");

    // Load checkpoint
    let loaded = Checkpoint::load(temp_dir.path());
    assert!(loaded.is_ok(), "Checkpoint load should succeed");

    let loaded_checkpoint = loaded.unwrap().unwrap();
    assert!(
        loaded_checkpoint.is_completed("detect-ripgrep"),
        "Loaded checkpoint should preserve completed steps"
    );
    assert!(
        !loaded_checkpoint.is_completed("detect-python-ruff"),
        "Loaded checkpoint should not mark uncompleted steps"
    );

    // Validate plan hash
    assert!(
        loaded_checkpoint.is_valid(&plan),
        "Checkpoint should be valid for same plan"
    );
}

#[tokio::test]
async fn test_doctor_command_execution() {
    let temp_dir = TempDir::new().unwrap();
    let ctx = create_test_context(&temp_dir, false);

    // Run doctor diagnostics
    let report = doctor(&ctx).await;
    assert!(report.is_ok(), "Doctor command should succeed");

    let diagnostic_report = report.unwrap();

    // Verify checks were performed
    assert!(
        !diagnostic_report.checks.is_empty(),
        "Doctor should perform checks"
    );

    // Check for expected diagnostic categories
    let check_names: Vec<_> = diagnostic_report
        .checks
        .iter()
        .map(|c| c.name.as_str())
        .collect();

    assert!(
        check_names.contains(&"Repository"),
        "Should check repository"
    );
    assert!(check_names.contains(&"Python"), "Should check Python");

    // Verify exit code logic (non-strict mode)
    let exit_code = diagnostic_report.exit_code();
    let has_failures = diagnostic_report
        .checks
        .iter()
        .any(|c| matches!(c.status, CheckStatus::Fail));
    // In non-strict mode, only FAIL status causes non-zero exit
    assert!(
        exit_code.as_i32() == 0 || has_failures,
        "Exit code should be 0 unless there are failures"
    );
}

#[tokio::test]
async fn test_verify_only_mode() {
    let temp_dir = TempDir::new().unwrap();
    let ctx = create_test_context(&temp_dir, true);

    let registry = InstallerRegistry::new();

    // Test verify on a known tool (ripgrep)
    let installer = registry.get("ripgrep");
    assert!(installer.is_some(), "Registry should have ripgrep");

    let verify_result = installer.unwrap().verify(&ctx).await;
    assert!(verify_result.is_ok(), "Verify should execute without error");

    // In dry-run or when tool may not be installed, we just verify the method runs
    let result = verify_result.unwrap();
    assert!(
        result.version.is_some() || !result.success,
        "Verify should report version or failure state"
    );
}

#[tokio::test]
async fn test_plan_phases_structure() {
    let temp_dir = TempDir::new().unwrap();
    let ctx = create_test_context(&temp_dir, true);

    let plan = ExecutionPlan::compute(&InstallerRegistry::new(), &ctx.config, &ctx, "dev")
        .await
        .unwrap();

    // Verify 3-phase structure: Detection → Installation → Verification
    assert_eq!(plan.phases.len(), 3, "Plan should have 3 phases");
    assert_eq!(plan.phases[0].name, "Detection");
    assert_eq!(plan.phases[1].name, "Installation");
    assert_eq!(plan.phases[2].name, "Verification");

    // Detection should be parallel-safe
    assert!(
        plan.phases[0].can_parallelize,
        "Detection phase should allow parallelism"
    );

    // Installation should be sequential
    assert!(
        !plan.phases[1].can_parallelize,
        "Installation phase should be sequential"
    );

    // Verification should be parallel-safe
    assert!(
        plan.phases[2].can_parallelize,
        "Verification phase should allow parallelism"
    );
}

#[tokio::test]
async fn test_registry_has_all_installers() {
    let registry = InstallerRegistry::new();

    // Verify all expected tools are registered
    let expected_tools = vec![
        "ripgrep",
        "python-black",
        "python-ruff",
        "python-pylint",
        "yamllint",
        "pytest",
        "actionlint",
        "shellcheck",
        "shfmt",
        "perlcritic",
        "ppi",
        "pwsh",
        "psscriptanalyzer",
    ];

    for tool in expected_tools {
        assert!(
            registry.get(tool).is_some(),
            "Registry should have installer for {}",
            tool
        );
    }
}

#[tokio::test]
async fn test_dependency_resolution() {
    let registry = InstallerRegistry::new();

    // PSScriptAnalyzer depends on pwsh
    let resolved = registry.resolve_dependencies(&["psscriptanalyzer"]);
    assert!(resolved.is_ok(), "Dependency resolution should succeed");

    let installers = resolved.unwrap();
    let ids: Vec<_> = installers.iter().map(|i| i.id()).collect();

    assert!(ids.contains(&"pwsh"), "Should include pwsh dependency");
    assert!(
        ids.contains(&"psscriptanalyzer"),
        "Should include requested tool"
    );

    // pwsh should come before psscriptanalyzer (dependency order)
    let pwsh_idx = ids.iter().position(|&id| id == "pwsh");
    let pssa_idx = ids.iter().position(|&id| id == "psscriptanalyzer");

    assert!(
        pwsh_idx < pssa_idx,
        "Dependencies should come before dependents"
    );
}

#[tokio::test]
async fn test_plan_to_json() {
    let temp_dir = TempDir::new().unwrap();
    let ctx = create_test_context(&temp_dir, true);

    let plan = ExecutionPlan::compute(&InstallerRegistry::new(), &ctx.config, &ctx, "dev")
        .await
        .unwrap();

    let json = plan.to_json();

    // Verify JSON structure
    assert!(json.is_object(), "JSON should be an object");
    assert!(json.get("phases").is_some(), "JSON should have phases");
    assert!(
        json.get("total_steps").is_some(),
        "JSON should have total_steps"
    );
}
