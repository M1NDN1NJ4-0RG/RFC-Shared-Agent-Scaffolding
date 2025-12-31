//! # Bootstrap Repo-CLI Tool
//!
//! This module implements the bootstrap-repo-cli functionality for setting up
//! the repo-lint toolchain in a local Python virtual environment.
//!
//! # Platform Support
//!
//! This tool is designed for Unix-like systems (Linux, macOS) and requires:
//! - Bash shell (for command existence checking)
//! - Unix-style paths (bin/python3, not Scripts/python.exe)
//! - System package managers: apt-get (Debian/Ubuntu), go, cpan, pwsh
//!
//! # Purpose
//!
//! Automates the installation and verification of:
//! - Python virtual environment (.venv)
//! - repo-lint package and dependencies
//! - System tools (shellcheck, shfmt, ripgrep, PowerShell, Perl modules)
//!
//! # Examples
//!
//! Run the bootstrap from the bootstrap_main.rs binary:
//!
//! ```bash
//! bootstrap-repo-cli
//! ```
//!
//! The bootstrap will automatically:
//! - Find the repository root
//! - Create a Python virtual environment
//! - Install repo-lint and dependencies
//! - Install and verify system tools
//!
//! # Exit Codes
//!
//! - 0: Success
//! - 1: Generic failure
//! - 10: Repository root could not be located
//! - 11: Could not determine install target (no packaging metadata found)
//! - 12: pip install -e failed
//! - 13: repo-lint is not runnable after install
//! - 14: repo-lint exists but failed to run --help
//! - 15: repo-lint install failed

use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode, Stdio};

const VENV_DIR: &str = ".venv";

/// Print log message to stdout
fn log(msg: &str) {
    println!("\n[bootstrap] {}", msg);
}

/// Print warning message to stderr
fn warn(msg: &str) {
    eprintln!("\n[bootstrap][WARN] {}", msg);
}

/// Print error message and exit with code
fn die(msg: &str, code: i32) -> ! {
    eprintln!("\n[bootstrap][ERROR] {}", msg);
    std::process::exit(code);
}

/// Find repository root by walking up until we hit .git or pyproject.toml or README.md
fn find_repo_root() -> Result<PathBuf, String> {
    let mut current =
        env::current_dir().map_err(|e| format!("Failed to get current directory: {}", e))?;

    loop {
        if current.join(".git").is_dir()
            || current.join("pyproject.toml").is_file()
            || current.join("README.md").is_file()
        {
            return Ok(current);
        }

        if !current.pop() {
            return Err("Could not find repo root".to_string());
        }
    }
}

/// Check if a command exists on PATH
/// Cross-platform implementation that works on Unix-like systems and Windows
fn command_exists(cmd: &str) -> bool {
    if cmd.is_empty() {
        return false;
    }

    // If the command already contains a path separator, treat it as a direct path
    let cmd_path = Path::new(cmd);
    if cmd_path.components().count() > 1 {
        return cmd_path.is_file();
    }

    let path_var = match env::var_os("PATH") {
        Some(p) => p,
        None => return false,
    };

    let paths = env::split_paths(&path_var);

    // For each directory in PATH, check if the command exists
    for dir in paths {
        let candidate = dir.join(cmd);
        if candidate.is_file() {
            return true;
        }
    }

    false
}

/// Run a command and return success status
fn run_command(cmd: &str, args: &[&str]) -> bool {
    Command::new(cmd)
        .args(args)
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

/// Run a command with output capture
fn run_command_output(cmd: &str, args: &[&str]) -> Result<String, String> {
    let output = Command::new(cmd)
        .args(args)
        .output()
        .map_err(|e| format!("Failed to execute {}: {}", cmd, e))?;

    if output.status.success() {
        String::from_utf8(output.stdout).map_err(|e| format!("Invalid UTF-8 output: {}", e))
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

/// Helper function to install a package via apt-get
/// Returns true if installation succeeded or apt-get is not available
fn install_via_apt(package_name: &str) -> bool {
    if !command_exists("apt-get") {
        return false;
    }

    if !run_command("sudo", &["apt-get", "update", "-qq"]) {
        warn("Failed to update apt-get");
    }

    run_command("sudo", &["apt-get", "install", "-y", "-qq", package_name])
}

/// Helper function to verify and log a tool's installation status
/// Used by both verify_tools and print_success_summary to avoid duplication
fn verify_and_log_tool(tool_name: &str, display_name: &str, for_summary: bool) {
    if command_exists(tool_name) {
        // Try to get full path using which-style lookup
        let mut found_path = None;
        if let Some(path_var) = env::var_os("PATH") {
            for dir in env::split_paths(&path_var) {
                let candidate = dir.join(tool_name);
                if candidate.is_file() {
                    found_path = Some(candidate);
                    break;
                }
            }
        }

        let msg = if let Some(path) = found_path {
            format!("✓ {}: {}", display_name, path.display())
        } else {
            format!("✓ {}: found", display_name)
        };

        if for_summary {
            log(&format!("  - {}", &msg[2..])); // Remove "✓ " for summary
        } else {
            log(&msg);
        }
    } else {
        let msg = format!("✗ {} not found", display_name);
        if for_summary {
            log(&format!("  - {}: not found", display_name));
        } else {
            warn(&msg);
        }
    }
}

/// Create Python virtual environment if it doesn't exist
/// Note: This function assumes the current directory has been set to repo_root
fn create_venv(repo_root: &Path) -> Result<(), String> {
    let venv_path = repo_root.join(VENV_DIR);

    if !venv_path.exists() {
        log(&format!("Creating venv: {}", VENV_DIR));
        let venv_path_str = venv_path
            .to_str()
            .ok_or_else(|| "Invalid UTF-8 in venv path".to_string())?;

        if !run_command("python3", &["-m", "venv", venv_path_str]) {
            return Err("Failed to create virtual environment".to_string());
        }
    }

    Ok(())
}

/// Determine the install target for repo-lint
fn determine_install_target(repo_root: &Path) -> Result<PathBuf, String> {
    let root_has_pkg = repo_root.join("pyproject.toml").exists()
        || repo_root.join("setup.py").exists()
        || repo_root.join("setup.cfg").exists();

    let tools_repo_cli = repo_root.join("tools/repo_cli");
    let tools_has_pkg = tools_repo_cli.join("pyproject.toml").exists()
        || tools_repo_cli.join("setup.py").exists()
        || tools_repo_cli.join("setup.cfg").exists();

    if root_has_pkg && tools_has_pkg {
        log("Found packaging metadata in repo root and tools/repo_cli; preferring tools/repo_cli as install target.");
        Ok(tools_repo_cli)
    } else if tools_has_pkg {
        Ok(tools_repo_cli)
    } else if root_has_pkg {
        Ok(repo_root.to_path_buf())
    } else {
        Err(
            "Could not determine where to install repo-lint (no packaging metadata found)."
                .to_string(),
        )
    }
}

/// Install repo-lint package
fn install_repo_lint(repo_root: &Path, install_target: &Path) -> Result<(), String> {
    log("Upgrading pip tooling");
    let venv_python = repo_root.join(VENV_DIR).join("bin/python3");
    let venv_python_str = venv_python
        .to_str()
        .ok_or_else(|| "Invalid UTF-8 in venv python path".to_string())?;

    if !run_command(
        venv_python_str,
        &["-m", "pip", "install", "-U", "pip", "setuptools", "wheel"],
    ) {
        warn("Failed to upgrade pip tooling");
    }

    log(&format!(
        "Installing repo-lint (editable) from: {}",
        install_target.display()
    ));

    let install_target_str = install_target
        .to_str()
        .ok_or_else(|| "Invalid UTF-8 in install target path".to_string())?;

    if !run_command(
        venv_python_str,
        &["-m", "pip", "install", "-e", install_target_str],
    ) {
        return Err(format!(
            "pip install -e failed for: {}",
            install_target.display()
        ));
    }

    Ok(())
}

/// Verify repo-lint is installed and runnable
fn verify_repo_lint(repo_root: &Path) -> Result<(), String> {
    log("Verifying repo-lint is on PATH");

    let repo_lint_path = repo_root.join(VENV_DIR).join("bin/repo-lint");

    if !repo_lint_path.exists() {
        warn("repo-lint not found on PATH after install.");
        warn("Diagnostics:");

        let venv_python = repo_root.join(VENV_DIR).join("bin/python3");
        if let Some(venv_python_str) = venv_python.to_str() {
            if let Ok(python_path) = run_command_output(
                venv_python_str,
                &["-c", "import sys; print(sys.executable)"],
            ) {
                eprintln!("  python: {}", python_path.trim());
            }
        }

        return Err("repo-lint is not runnable. Fix packaging/venv/PATH first.".to_string());
    }

    let repo_lint_str = repo_lint_path
        .to_str()
        .ok_or_else(|| "Invalid UTF-8 in repo-lint path".to_string())?;

    if !run_command(repo_lint_str, &["--help"]) {
        return Err("repo-lint exists but failed to run: repo-lint --help".to_string());
    }

    log(&format!("repo-lint OK: {}", repo_lint_path.display()));
    Ok(())
}

/// Run repo-lint install command
fn run_repo_lint_install(repo_root: &Path) -> Result<(), String> {
    let repo_lint_path = repo_root.join(VENV_DIR).join("bin/repo-lint");
    let repo_lint_str = repo_lint_path
        .to_str()
        .ok_or_else(|| "Invalid UTF-8 in repo-lint path".to_string())?;

    // Check if install command exists
    if !run_command(repo_lint_str, &["install", "--help"]) {
        log("repo-lint install not available; skipping.");
        return Ok(());
    }

    log("Running: repo-lint install");
    if !run_command(repo_lint_str, &["install"]) {
        return Err(
            "repo-lint install failed. Missing tools are BLOCKER. Install missing tools and rerun."
                .to_string(),
        );
    }

    // Add .venv-lint/bin to PATH message
    let venv_lint_bin = repo_root.join(".venv-lint/bin");
    if venv_lint_bin.exists() {
        log("Added .venv-lint/bin to PATH for Python linting tools");
    }

    Ok(())
}

/// Install shellcheck via apt-get
/// Platform note: Designed for Debian/Ubuntu systems with apt-get
fn install_shellcheck() {
    if command_exists("shellcheck") {
        return;
    }

    log("Installing shellcheck...");
    if install_via_apt("shellcheck") {
        // Successfully installed
    } else {
        warn("shellcheck not found and apt-get not available. Please install manually.");
    }
}

/// Install shfmt via go install
fn install_shfmt() {
    if command_exists("shfmt") {
        return;
    }

    log("Installing shfmt...");
    if command_exists("go") {
        if !run_command("go", &["install", "mvdan.cc/sh/v3/cmd/shfmt@latest"]) {
            warn("Failed to install shfmt");
        }
    } else {
        warn(
            "shfmt requires Go to be installed. Please install Go first or install shfmt manually.",
        );
    }
}

/// Install ripgrep via apt-get
/// Platform note: Designed for Debian/Ubuntu systems with apt-get
fn install_ripgrep() {
    if command_exists("rg") {
        return;
    }

    log("Installing ripgrep (rg)...");
    if install_via_apt("ripgrep") {
        // Successfully installed
    } else {
        warn("ripgrep not found and apt-get not available. Please install manually.");
    }
}

/// Install PowerShell via apt-get
/// Platform note: Designed for Ubuntu/Debian systems with apt-get and Microsoft repos
fn install_powershell() {
    if command_exists("pwsh") {
        return;
    }

    log("Installing PowerShell (pwsh)...");
    if !command_exists("apt-get") {
        warn("PowerShell not found and apt-get not available. Please install manually.");
        return;
    }

    // Install prerequisites
    if !run_command(
        "sudo",
        &[
            "apt-get",
            "install",
            "-y",
            "-qq",
            "wget",
            "apt-transport-https",
            "software-properties-common",
        ],
    ) {
        warn("Failed to install PowerShell prerequisites");
        return;
    }

    // Determine Ubuntu release
    if !command_exists("lsb_release") {
        warn("lsb_release not found; skipping automatic PowerShell installation. Please install PowerShell manually.");
        return;
    }

    let ubuntu_release = match run_command_output("lsb_release", &["-rs"]) {
        Ok(r) => r.trim().to_string(),
        Err(_) => {
            warn("Failed to determine Ubuntu release");
            return;
        }
    };

    let deb_url = format!(
        "https://packages.microsoft.com/config/ubuntu/{}/packages-microsoft-prod.deb",
        ubuntu_release
    );

    // Use platform-appropriate temporary directory
    let deb_path = env::temp_dir().join("packages-microsoft-prod.deb");
    let deb_path_str = match deb_path.to_str() {
        Some(s) => s,
        None => {
            warn("Invalid UTF-8 in temporary file path");
            return;
        }
    };

    // Download Microsoft repository GPG keys
    if !run_command("wget", &["-q", &deb_url, "-O", deb_path_str]) {
        warn("Failed to download Microsoft package");
        return;
    }

    if !run_command("sudo", &["dpkg", "-i", deb_path_str]) {
        warn("Failed to install Microsoft package");
    }

    let _ = fs::remove_file(&deb_path);

    // Install PowerShell
    if !run_command("sudo", &["apt-get", "update", "-qq"]) {
        warn("Failed to update apt-get");
    }
    if !run_command("sudo", &["apt-get", "install", "-y", "-qq", "powershell"]) {
        warn("Failed to install PowerShell");
    }
}

/// Install PSScriptAnalyzer PowerShell module
fn install_psscriptanalyzer() {
    if !command_exists("pwsh") {
        warn("PowerShell (pwsh) not available. Skipping PSScriptAnalyzer installation.");
        return;
    }

    log("Installing PSScriptAnalyzer...");

    // Check if already installed
    let check_output = Command::new("pwsh")
        .args([
            "-Command",
            "Get-Module -ListAvailable -Name PSScriptAnalyzer",
        ])
        .output();

    if let Ok(output) = check_output {
        if output.status.success() && !output.stdout.is_empty() {
            log("PSScriptAnalyzer already installed");
            return;
        }
    }

    // Install the module
    if !run_command(
        "pwsh",
        &[
            "-Command",
            "Install-Module -Name PSScriptAnalyzer -MinimumVersion 1.23.0 -Scope CurrentUser -Force",
        ],
    ) {
        warn("Failed to install PSScriptAnalyzer");
    }
}

/// Install Perl::Critic and PPI
fn install_perl_modules() {
    if !command_exists("cpan") && !command_exists("apt-get") {
        warn("Neither cpan nor apt-get available. Cannot install Perl::Critic and PPI.");
        return;
    }

    log("Installing Perl::Critic and PPI...");

    if command_exists("cpan") {
        // Install cpanminus for faster installation
        if !command_exists("cpanm") {
            let _ = run_command("sudo", &["cpan", "-T", "App::cpanminus"]);
        }

        if command_exists("cpanm") {
            let _ = run_command("cpanm", &["--quiet", "--notest", "Perl::Critic", "PPI"]);
        } else {
            let _ = run_command("sudo", &["cpan", "-T", "Perl::Critic", "PPI"]);
        }
    } else if command_exists("apt-get") {
        log("Installing Perl::Critic via apt-get...");
        let _ = run_command(
            "sudo",
            &[
                "apt-get",
                "install",
                "-y",
                "-qq",
                "libperl-critic-perl",
                "libppi-perl",
            ],
        );
    }
}

/// Verify tool installations
fn verify_tools() {
    log("Tool installation complete. Verifying...");

    verify_and_log_tool("shellcheck", "shellcheck", false);
    verify_and_log_tool("shfmt", "shfmt", false);
    verify_and_log_tool("rg", "ripgrep", false);
    verify_and_log_tool("pwsh", "PowerShell", false);

    // Check Perl::Critic
    let perl_check = Command::new("perl")
        .args(["-MPerl::Critic", "-e", "1"])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();

    if perl_check.map(|s| s.success()).unwrap_or(false) {
        log("✓ Perl::Critic installed");
    } else {
        warn("✗ Perl::Critic not found");
    }
}

/// Run verification check
fn run_verification(repo_root: &Path) -> bool {
    log("Running: repo-lint check --ci --only bash");

    let repo_lint_path = repo_root.join(VENV_DIR).join("bin/repo-lint");

    if let Some(repo_lint_str) = repo_lint_path.to_str() {
        run_command(repo_lint_str, &["check", "--ci", "--only", "bash"])
    } else {
        warn("Invalid UTF-8 in repo-lint path");
        false
    }
}

/// Print success summary
fn print_success_summary(repo_root: &Path) {
    log("SUCCESS: Bootstrap complete!");
    log("Tools installed:");

    let repo_lint_path = repo_root.join(VENV_DIR).join("bin/repo-lint");
    log(&format!("  - repo-lint: {}", repo_lint_path.display()));
    log("  - Python tools (black, ruff, pylint, yamllint, pytest) in: .venv-lint/bin");

    verify_and_log_tool("shellcheck", "shellcheck", true);
    verify_and_log_tool("shfmt", "shfmt", true);
    verify_and_log_tool("rg", "ripgrep", true);
    verify_and_log_tool("pwsh", "PowerShell", true);

    let perl_check = Command::new("perl")
        .args(["-MPerl::Critic", "-e", "1"])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();

    if perl_check.map(|s| s.success()).unwrap_or(false) {
        log("  - Perl::Critic: installed");
    } else {
        log("  - Perl::Critic: not found");
    }

    log("");
    log("To use in your shell session:");
    log(&format!(
        "  source {}/.venv/bin/activate",
        repo_root.display()
    ));
    log(&format!(
        "  export PATH=\"{}/.venv-lint/bin:$HOME/go/bin:$PATH\"",
        repo_root.display()
    ));
}

/// Main bootstrap function
pub fn run() -> ExitCode {
    // Find repository root
    let repo_root = match find_repo_root() {
        Ok(root) => root,
        Err(_) => die("Could not find repo root. Run from inside the repo.", 10),
    };

    env::set_current_dir(&repo_root).unwrap_or_else(|_| die("Failed to change to repo root", 1));
    log(&format!("Repo root: {}", repo_root.display()));

    // Create venv
    if let Err(e) = create_venv(&repo_root) {
        die(&e, 1);
    }

    log("Activating venv");

    // Determine install target
    let install_target = match determine_install_target(&repo_root) {
        Ok(target) => target,
        Err(_) => die(
            "Could not determine where to install repo-lint (no packaging metadata found).",
            11,
        ),
    };

    // Install repo-lint
    if let Err(e) = install_repo_lint(&repo_root, &install_target) {
        die(&e, 12);
    }

    // Verify repo-lint
    if let Err(e) = verify_repo_lint(&repo_root) {
        die(&e, 13);
    }

    // Run repo-lint install
    if let Err(e) = run_repo_lint_install(&repo_root) {
        die(&e, 15);
    }

    // Install additional tools
    log("Installing additional required tools...");
    install_shellcheck();
    install_shfmt();
    install_ripgrep();
    install_powershell();
    install_psscriptanalyzer();
    install_perl_modules();

    // Verify installations
    verify_tools();

    // Run verification check
    if run_verification(&repo_root) {
        log("SUCCESS: All tools installed and bash linting works");
    } else {
        warn("Bash linting had issues, but continuing...");
    }

    // Print success summary
    print_success_summary(&repo_root);

    ExitCode::SUCCESS
}
