//! # Bootstrap V2 Binary Entry Point
//!
//! # Purpose
//!
//! Main entry point for the bootstrap-repo-cli v2 binary, implementing Issue #235.
//! This binary provides modular toolchain bootstrapping with parallel execution,
//! rich progress UI, and structured error handling.
//!
//! # Examples
//!
//! Install all tools for development:
//! ```bash
//! bootstrap-repo-cli install --profile dev
//! ```
//!
//! Run diagnostics:
//! ```bash
//! bootstrap-repo-cli doctor
//! ```
//!
//! Verify installations:
//! ```bash
//! bootstrap-repo-cli verify
//! ```

use clap::Parser;
use safe_run::bootstrap_v2::{
    cli::{Cli, Commands},
    config::Config,
    context::{Context, OsType, PackageManager, Verbosity},
    doctor,
    errors::BootstrapError,
    executor::Executor,
    exit_codes::ExitCode,
    installers::{repo_lint::REPO_LINT_INSTALLER_ID, InstallerRegistry},
    lock::LockManager,
    plan::ExecutionPlan,
    platform,
    progress::{ProgressMode, ProgressReporter},
};
use std::path::PathBuf;
use std::sync::Arc;

#[tokio::main]
async fn main() {
    let exit_code = run().await;
    std::process::exit(exit_code.as_i32());
}

async fn run() -> ExitCode {
    // Parse CLI arguments
    let cli = Cli::parse();

    // Execute the appropriate command
    match handle_command(cli).await {
        Ok(code) => code,
        Err(e) => {
            eprintln!("Error: {:#}", e);
            if let Some(bootstrap_err) = e.downcast_ref::<BootstrapError>() {
                bootstrap_err.exit_code()
            } else {
                ExitCode::UsageError
            }
        }
    }
}

async fn handle_command(cli: Cli) -> anyhow::Result<ExitCode> {
    match cli.command {
        Commands::Install { profile } => {
            handle_install(
                Some(profile),
                cli.jobs,
                cli.dry_run,
                cli.ci,
                cli.offline,
                cli.allow_downgrade,
                cli.json,
                cli.verbose,
            )
            .await
        }
        Commands::Doctor { strict } => handle_doctor(strict, cli.ci, cli.json).await,
        Commands::Verify { profile } => handle_verify(profile, cli.ci, cli.verbose).await,
    }
}

#[allow(clippy::too_many_arguments)]
async fn handle_install(
    profile: Option<String>,
    jobs: Option<usize>,
    dry_run: bool,
    ci_mode: bool,
    offline: bool,
    allow_downgrade: bool,
    json: bool,
    verbose_count: u8,
) -> anyhow::Result<ExitCode> {
    // 1. Find repository root
    let repo_root = find_repo_root().await?;

    // 2. Detect OS and package manager
    let os = OsType::detect();
    let package_manager = PackageManager::detect(os);

    // 3. Load configuration
    let config = Arc::new(Config::load(&repo_root, ci_mode)?);

    // 4. Create virtual environment if it doesn't exist
    let venv_path = repo_root.join(".venv");
    if !venv_path.exists() || dry_run {
        if !dry_run {
            println!("🔧 Creating Python virtual environment...");
        }
        let _ = platform::create_venv(&venv_path, dry_run).await?;
        if !dry_run {
            println!("  ✓ Virtual environment created");
        }
    }

    // 5. Setup progress reporter
    let progress_mode = if json {
        ProgressMode::Json
    } else if ci_mode {
        ProgressMode::Ci
    } else {
        // Default to Interactive when not in CI or JSON mode
        ProgressMode::Interactive
    };
    let progress = Arc::new(ProgressReporter::new(progress_mode));

    // 5. Setup progress reporter
    let progress_mode = if json {
        ProgressMode::Json
    } else if ci_mode {
        ProgressMode::Ci
    } else {
        // Default to Interactive when not in CI or JSON mode
        ProgressMode::Interactive
    };
    let progress = Arc::new(ProgressReporter::new(progress_mode));

    // 6. Create execution context
    let verbosity = Verbosity::from_count(verbose_count);
    let ctx = Arc::new(Context::with_config(
        repo_root.clone(),
        os,
        package_manager,
        dry_run,
        verbosity,
        Some(progress.clone()),
        config.clone(),
        ci_mode,
        jobs,
        offline,
        allow_downgrade,
    ));

    // 7. Initialize installer registry
    let registry = InstallerRegistry::new();

    // 8. Compute execution plan
    let profile_name = profile.as_deref().unwrap_or("dev");
    let plan =
        ExecutionPlan::compute(&registry, config.as_ref(), ctx.as_ref(), profile_name).await?;
    progress.emit_event_plan_computed();

    // Print plan in appropriate format
    if json {
        println!("{}", plan.to_json());
    } else if !ci_mode {
        plan.print_human();
    }

    // 9. Create executor and lock manager
    let lock_manager = Arc::new(LockManager::new());
    let executor = Executor::new(ctx.clone(), lock_manager);

    // 10. Execute the plan (detect → install → verify)
    let results = executor.execute_plan(&plan).await?;

    // 11. Check for failures
    let failed = results.iter().any(|r| !r.success);
    if failed {
        eprintln!("\n❌ Installation failed - see errors above");
        return Ok(ExitCode::VerificationFailed);
    }

    // 12. Run automatic verification gate (repo-lint check --ci)
    // This runs if repo-lint was in the plan (profile includes it)
    let repo_lint_in_plan = plan.phases.iter().any(|phase| {
        phase
            .steps
            .iter()
            .any(|step| step.installer == REPO_LINT_INSTALLER_ID)
    });

    if repo_lint_in_plan && !dry_run {
        println!("\n🔍 Running verification gate (repo-lint check --ci)...");

        let repo_lint_bin = ctx.repo_lint_bin();
        let gate_result = tokio::process::Command::new(&repo_lint_bin)
            .args(["check", "--ci"])
            .status()
            .await;

        match gate_result {
            Ok(status) => {
                let exit_code = status.code().unwrap_or(-1);
                match exit_code {
                    0 => {
                        println!("  ✓ Verification gate passed (no violations)");
                    }
                    1 => {
                        println!(
                            "  ✓ Verification gate passed (tools functional, violations found)"
                        );
                        println!(
                            "  Note: Repository has lint violations but all tools are working"
                        );
                    }
                    2 => {
                        eprintln!("  ✗ Verification gate failed: Missing tools");
                        eprintln!("Some required tools are not installed or not on PATH");
                        return Ok(ExitCode::VerificationFailed);
                    }
                    _ => {
                        eprintln!("  ✗ Verification gate failed with exit code {}", exit_code);
                        return Ok(ExitCode::VerificationFailed);
                    }
                }
            }
            Err(e) => {
                eprintln!("  ✗ Failed to run verification gate: {}", e);
                return Ok(ExitCode::VerificationFailed);
            }
        }
    }

    println!("\n✅ Bootstrap completed successfully");
    Ok(ExitCode::Success)
}

async fn handle_doctor(strict: bool, ci_mode: bool, json: bool) -> anyhow::Result<ExitCode> {
    // 1. Find repository root
    let repo_root = find_repo_root().await?;

    // 2. Detect OS and package manager
    let os = OsType::detect();
    let package_manager = PackageManager::detect(os);

    // 3. Create minimal context for doctor
    let config = Arc::new(Config::default());
    let ctx = Context::with_config(
        repo_root,
        os,
        package_manager,
        false, // not dry-run
        Verbosity::Normal,
        None, // no progress reporter needed
        config,
        ci_mode,
        None,
        false,
        false,
    );

    // 4. Run doctor diagnostics
    let report = doctor::doctor(&ctx).await?;

    // 5. Print report
    if json {
        println!("{}", report.to_json());
    } else {
        report.print();
    }

    // 6. Determine exit code
    let exit_code = if strict {
        report.exit_code_strict()
    } else {
        report.exit_code()
    };

    Ok(exit_code)
}

async fn handle_verify(
    profile: String,
    ci_mode: bool,
    verbose_count: u8,
) -> anyhow::Result<ExitCode> {
    // 1. Find repository root
    let repo_root = find_repo_root().await?;

    // 2. Detect OS and package manager
    let os = OsType::detect();
    let package_manager = PackageManager::detect(os);

    // 3. Load configuration
    let config = Arc::new(Config::load(&repo_root, ci_mode)?);

    // 4. Create minimal execution context (no progress reporter needed for verify)
    let verbosity = Verbosity::from_count(verbose_count);
    let ctx = Arc::new(Context::with_config(
        repo_root.clone(),
        os,
        package_manager,
        false, // verify is never dry-run
        verbosity,
        None, // No progress reporter - verify prints directly
        config.clone(),
        ci_mode,
        None,
        false,
        false,
    ));

    // 5. Initialize installer registry
    let registry = InstallerRegistry::new();

    // 6. Run verify-only (no installs, no downloads)
    println!("🔍 Verifying installed tools...\n");

    // Use CLI profile argument (with env var fallback for backwards compatibility)
    let profile_to_use = if profile != "dev" {
        profile
    } else {
        std::env::var("BOOTSTRAP_REPO_PROFILE").unwrap_or(profile)
    };
    let tools = config.get_tools_for_profile(&profile_to_use);
    let installers = registry.resolve_dependencies(&tools)?;

    let mut failed = false;
    for installer in installers {
        let result = installer.verify(ctx.as_ref()).await?;
        if result.success {
            println!(
                "✅ {}: {}",
                installer.name(),
                result
                    .version
                    .map(|v| v.to_string())
                    .unwrap_or_else(|| "OK".to_string())
            );
        } else {
            println!("❌ {}: FAILED", installer.name());
            for issue in &result.issues {
                println!("   - {}", issue);
            }
            failed = true;
        }
    }

    if failed {
        println!("\n❌ Verification failed");
        Ok(ExitCode::VerificationFailed)
    } else {
        println!("\n✅ All tools verified successfully");
        Ok(ExitCode::Success)
    }
}

async fn find_repo_root() -> anyhow::Result<PathBuf> {
    let current_dir = std::env::current_dir()?;
    let mut dir = current_dir.as_path();

    loop {
        let git_path = dir.join(".git");
        if git_path.is_dir() || git_path.is_file() {
            return Ok(dir.to_path_buf());
        }

        dir = dir.parent().ok_or_else(|| BootstrapError::NotInRepo)?;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_find_repo_root_from_subdir() {
        // This test assumes it's running inside a git repo
        let result = find_repo_root().await;
        // Should either succeed or fail with NotInRepo
        match result {
            Ok(root) => {
                assert!(root.join(".git").exists());
            }
            Err(e) => {
                if let Some(bootstrap_err) = e.downcast_ref::<BootstrapError>() {
                    assert!(matches!(bootstrap_err, BootstrapError::NotInRepo));
                }
            }
        }
    }
}
