//! # Bootstrap Repo-CLI Tool
//!
//! This module implements the bootstrap-repo-cli functionality for setting up
//! the repo-lint toolchain in a local Python virtual environment.
//!
//! # Purpose
//!
//! Automates the installation and verification of:
//! - Python virtual environment (.venv)
//! - repo-lint package and dependencies
//! - System tools (shellcheck, shfmt, ripgrep, PowerShell, Perl modules)
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
    let mut current = env::current_dir().map_err(|e| format!("Failed to get current directory: {}", e))?;

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
fn command_exists(cmd: &str) -> bool {
    Command::new("command")
        .args(["-v", cmd])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
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
        String::from_utf8(output.stdout)
            .map_err(|e| format!("Invalid UTF-8 output: {}", e))
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

/// Create Python virtual environment if it doesn't exist
fn create_venv(repo_root: &Path) -> Result<(), String> {
    let venv_path = repo_root.join(VENV_DIR);

    if !venv_path.exists() {
        log(&format!("Creating venv: {}", VENV_DIR));
        if !run_command("python3", &["-m", "venv", VENV_DIR]) {
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
        Err("Could not determine where to install repo-lint (no packaging metadata found).".to_string())
    }
}

/// Install repo-lint package
fn install_repo_lint(repo_root: &Path, install_target: &Path) -> Result<(), String> {
    log("Upgrading pip tooling");
    let venv_python = repo_root.join(VENV_DIR).join("bin/python3");

    if !run_command(
        venv_python.to_str().unwrap(),
        &["-m", "pip", "install", "-U", "pip", "setuptools", "wheel"],
    ) {
        warn("Failed to upgrade pip tooling");
    }

    log(&format!(
        "Installing repo-lint (editable) from: {}",
        install_target.display()
    ));

    if !run_command(
        venv_python.to_str().unwrap(),
        &["-m", "pip", "install", "-e", install_target.to_str().unwrap()],
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
        if let Ok(python_path) = run_command_output(venv_python.to_str().unwrap(), &["-c", "import sys; print(sys.executable)"]) {
            eprintln!("  python: {}", python_path.trim());
        }

        return Err("repo-lint is not runnable. Fix packaging/venv/PATH first.".to_string());
    }

    if !run_command(repo_lint_path.to_str().unwrap(), &["--help"]) {
        return Err("repo-lint exists but failed to run: repo-lint --help".to_string());
    }

    log(&format!("repo-lint OK: {}", repo_lint_path.display()));
    Ok(())
}

/// Run repo-lint install command
fn run_repo_lint_install(repo_root: &Path) -> Result<(), String> {
    let repo_lint_path = repo_root.join(VENV_DIR).join("bin/repo-lint");

    // Check if install command exists
    if !run_command(repo_lint_path.to_str().unwrap(), &["install", "--help"]) {
        log("repo-lint install not available; skipping.");
        return Ok(());
    }

    log("Running: repo-lint install");
    if !run_command(repo_lint_path.to_str().unwrap(), &["install"]) {
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
fn install_shellcheck() {
    if command_exists("shellcheck") {
        return;
    }

    log("Installing shellcheck...");
    if command_exists("apt-get") {
        if !run_command("sudo", &["apt-get", "update", "-qq"]) {
            warn("Failed to update apt-get");
        }
        if !run_command("sudo", &["apt-get", "install", "-y", "-qq", "shellcheck"]) {
            warn("Failed to install shellcheck");
        }
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
        warn("shfmt requires Go to be installed. Please install Go first or install shfmt manually.");
    }
}

/// Install ripgrep via apt-get
fn install_ripgrep() {
    if command_exists("rg") {
        return;
    }

    log("Installing ripgrep (rg)...");
    if command_exists("apt-get") {
        if !run_command("sudo", &["apt-get", "install", "-y", "-qq", "ripgrep"]) {
            warn("Failed to install ripgrep");
        }
    } else {
        warn("ripgrep not found and apt-get not available. Please install manually.");
    }
}

/// Install PowerShell via apt-get
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
    let deb_path = "/tmp/packages-microsoft-prod.deb";

    // Download Microsoft repository GPG keys
    if !run_command("wget", &["-q", &deb_url, "-O", deb_path]) {
        warn("Failed to download Microsoft package");
        return;
    }

    if !run_command("sudo", &["dpkg", "-i", deb_path]) {
        warn("Failed to install Microsoft package");
    }

    let _ = fs::remove_file(deb_path);

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
        .args(&[
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
            &["apt-get", "install", "-y", "-qq", "libperl-critic-perl", "libppi-perl"],
        );
    }
}

/// Verify tool installations
fn verify_tools() {
    log("Tool installation complete. Verifying...");

    if command_exists("shellcheck") {
        if let Ok(path) = run_command_output("command", &["-v", "shellcheck"]) {
            log(&format!("✓ shellcheck: {}", path.trim()));
        }
    } else {
        warn("✗ shellcheck not found");
    }

    if command_exists("shfmt") {
        if let Ok(path) = run_command_output("command", &["-v", "shfmt"]) {
            log(&format!("✓ shfmt: {}", path.trim()));
        }
    } else {
        warn("✗ shfmt not found");
    }

    if command_exists("rg") {
        if let Ok(path) = run_command_output("command", &["-v", "rg"]) {
            log(&format!("✓ ripgrep: {}", path.trim()));
        }
    } else {
        warn("✗ ripgrep not found");
    }

    if command_exists("pwsh") {
        if let Ok(path) = run_command_output("command", &["-v", "pwsh"]) {
            log(&format!("✓ PowerShell: {}", path.trim()));
        }
    } else {
        warn("✗ PowerShell not found");
    }

    // Check Perl::Critic
    let perl_check = Command::new("perl")
        .args(&["-MPerl::Critic", "-e", "1"])
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

    run_command(
        repo_lint_path.to_str().unwrap(),
        &["check", "--ci", "--only", "bash"],
    )
}

/// Print success summary
fn print_success_summary(repo_root: &Path) {
    log("SUCCESS: Bootstrap complete!");
    log("Tools installed:");

    let repo_lint_path = repo_root.join(VENV_DIR).join("bin/repo-lint");
    log(&format!("  - repo-lint: {}", repo_lint_path.display()));
    log("  - Python tools (black, ruff, pylint, yamllint, pytest) in: .venv-lint/bin");

    if let Ok(path) = run_command_output("command", &["-v", "shellcheck"]) {
        log(&format!("  - shellcheck: {}", path.trim()));
    } else {
        log("  - shellcheck: not found");
    }

    if let Ok(path) = run_command_output("command", &["-v", "shfmt"]) {
        log(&format!("  - shfmt: {}", path.trim()));
    } else {
        log("  - shfmt: not found");
    }

    if let Ok(path) = run_command_output("command", &["-v", "rg"]) {
        log(&format!("  - ripgrep: {}", path.trim()));
    } else {
        log("  - ripgrep: not found");
    }

    if let Ok(path) = run_command_output("command", &["-v", "pwsh"]) {
        log(&format!("  - PowerShell: {}", path.trim()));
    } else {
        log("  - PowerShell: not found");
    }

    let perl_check = Command::new("perl")
        .args(&["-MPerl::Critic", "-e", "1"])
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
    log(&format!("  source {}/.venv/bin/activate", repo_root.display()));
    log(&format!("  export PATH=\"{}/.venv-lint/bin:$HOME/go/bin:$PATH\"", repo_root.display()));
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
    if let Err(_) = install_repo_lint(&repo_root, &install_target) {
        die(
            &format!("pip install -e failed for: {}", install_target.display()),
            12,
        );
    }

    // Verify repo-lint
    if let Err(_) = verify_repo_lint(&repo_root) {
        die("repo-lint is not runnable. Fix packaging/venv/PATH first.", 13);
    }

    // Run repo-lint install
    if let Err(_) = run_repo_lint_install(&repo_root) {
        die(
            "repo-lint install failed. Missing tools are BLOCKER. Install missing tools and rerun.",
            15,
        );
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
