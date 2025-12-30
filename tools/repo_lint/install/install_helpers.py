"""Installation helpers for repo_lint tools.

:Purpose:
    Provides safe, deterministic installation of linting tools with support for
    repo-local installations. Follows Phase 4 constraints:
    - Only auto-install what is safe/deterministic
    - Print manual steps for anything not auto-installable
    - Support repo-local tool directories (.venv-lint/, .tools/)
    - Never uninstall system packages

:Functions:
    - install_python_tools: Install Python tools in repo-local venv
    - print_bash_tool_instructions: Print instructions for Bash tools
    - print_powershell_tool_instructions: Print instructions for PowerShell tools
    - print_perl_tool_instructions: Print instructions for Perl tools
    - cleanup_repo_local: Remove repo-local tool installations

:Environment Variables:
    None

:Examples:
    Install Python tools::

        from tools.repo_lint.install.install_helpers import install_python_tools
        success, msg = install_python_tools(verbose=True)

:Exit Codes:
    N/A - Functions return success/failure tuples
"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from tools.repo_lint.install.version_pins import BASH_TOOLS, PIP_VERSION, POWERSHELL_TOOLS, PYTHON_TOOLS


def get_repo_root() -> Path:
    """Get the repository root directory.

    :returns:
        Path to repository root

    :raises
        RuntimeError: If repository root cannot be determined
    """
    # Start from current file's directory
    current = Path(__file__).resolve().parent

    # Walk up until we find .git directory
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    raise RuntimeError("Could not find repository root (no .git directory)")


def get_venv_path() -> Path:
    """Get the path to the repo-local Python virtual environment.

    :returns:
        Path to .venv-lint directory
    """
    return get_repo_root() / ".venv-lint"


def get_tools_path() -> Path:
    """Get the path to the repo-local tools directory.

    :returns:
        Path to .tools directory
    """
    return get_repo_root() / ".tools"


def venv_exists() -> bool:
    """Check if repo-local venv exists.

    :returns:
        True if .venv-lint exists and appears valid
    """
    venv_path = get_venv_path()
    if not venv_path.exists():
        return False

    # Check for basic venv structure
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"

    return python_path.exists()


def create_venv(verbose: bool = False) -> Tuple[bool, Optional[str]]:
    """Create repo-local virtual environment.

    :param
        verbose: If True, print detailed output

    :returns:
        Tuple of (success, error_message)
    """
    venv_path = get_venv_path()

    if venv_exists():
        if verbose:
            print(f"✓ Virtual environment already exists at {venv_path}")
        return True, None

    if verbose:
        print(f"Creating virtual environment at {venv_path}...")

    try:
        # Create venv without pip (we'll upgrade it)
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True, capture_output=not verbose)

        # Get venv python path
        if sys.platform == "win32":
            venv_python = venv_path / "Scripts" / "python.exe"
        else:
            venv_python = venv_path / "bin" / "python"

        # Upgrade pip to pinned version for deterministic installs
        if verbose:
            print(f"Upgrading pip to version {PIP_VERSION}...")
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", f"pip=={PIP_VERSION}"], check=True, capture_output=not verbose
        )

        if verbose:
            print("✓ Virtual environment created successfully")
        return True, None

    except subprocess.CalledProcessError as e:
        return False, f"Failed to create virtual environment: {e}"
    except Exception as e:
        return False, f"Unexpected error creating virtual environment: {e}"


def install_python_tools(verbose: bool = False) -> Tuple[bool, List[str]]:
    """Install Python linting tools in repo-local venv.

    :param
        verbose: If True, print detailed output

    :returns:
        Tuple of (success, list of error messages)
    """
    errors = []

    # Create venv if needed
    success, error = create_venv(verbose=verbose)
    if not success:
        return False, [error]

    venv_path = get_venv_path()
    if sys.platform == "win32":
        venv_pip = venv_path / "Scripts" / "pip.exe"
    else:
        venv_pip = venv_path / "bin" / "pip"

    # Install each tool with pinned version
    for tool, version in PYTHON_TOOLS.items():
        tool_spec = f"{tool}=={version}"
        if verbose:
            print(f"Installing {tool_spec}...")

        try:
            subprocess.run([str(venv_pip), "install", tool_spec], check=True, capture_output=not verbose)
            if verbose:
                print(f"✓ {tool} installed successfully")
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install {tool}: {e}"
            errors.append(error_msg)
            if verbose:
                print(f"✗ {error_msg}")

    return len(errors) == 0, errors


def print_bash_tool_instructions():
    """Print manual installation instructions for Bash tools.

    :returns:
        None
    """
    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Bash Tools - Manual Installation Required")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    print("shellcheck:")
    print("  Ubuntu/Debian:  sudo apt-get install shellcheck")
    print("  macOS:          brew install shellcheck")
    print("  Other:          https://github.com/koalaman/shellcheck#installing")
    print("")
    print(f"shfmt (version {BASH_TOOLS['shfmt']}):")
    print(f"  go install mvdan.cc/sh/v3/cmd/shfmt@{BASH_TOOLS['shfmt']}")
    print("  Note: Requires Go to be installed")
    print("")


def print_powershell_tool_instructions():
    """Print manual installation instructions for PowerShell tools.

    :returns:
        None
    """
    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  PowerShell Tools - Manual Installation Required")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    print("PSScriptAnalyzer:")
    print("  PowerShell:     Install-Module -Name PSScriptAnalyzer -RequiredVersion")
    print(f"                  {POWERSHELL_TOOLS['PSScriptAnalyzer']} -Scope CurrentUser")
    print("  Note: Requires PowerShell 5.0+ or PowerShell Core")
    print("")


def print_perl_tool_instructions():
    """Print manual installation instructions for Perl tools.

    :returns:
        None
    """
    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Perl Tools - Manual Installation Required")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    print("Perl::Critic:")
    print("  CPAN:           cpan Perl::Critic")
    print("  cpanminus:      cpanm Perl::Critic")
    print("  Ubuntu/Debian:  sudo apt-get install libperl-critic-perl")
    print("")


def cleanup_repo_local(verbose: bool = False) -> Tuple[bool, List[str]]:
    """Remove repo-local tool installations.

    :param
        verbose: If True, print detailed output

    :returns:
        Tuple of (success, list of messages)

    :Notes:
        Only removes directories created by repo-lint install.
        Never removes system packages.
    """
    messages = []
    success = True

    # Directories to clean up
    cleanup_dirs = [
        (".venv-lint", "Python lint tools virtual environment"),
        (".tools", "Standalone tool binaries"),
        (".psmodules", "PowerShell modules"),
        (".cpan-local", "Perl CPAN local install"),
    ]

    repo_root = get_repo_root()

    for dir_name, description in cleanup_dirs:
        dir_path = repo_root / dir_name

        if not dir_path.exists():
            if verbose:
                messages.append(f"  {dir_name}/ does not exist, skipping")
            continue

        try:
            if verbose:
                print(f"Removing {dir_name}/ ({description})...")

            shutil.rmtree(dir_path, ignore_errors=False)
            messages.append(f"✓ Removed {dir_name}/ ({description})")

        except Exception as e:
            success = False
            messages.append(f"✗ Failed to remove {dir_name}/: {e}")

    if not messages:
        messages.append("No repo-local installations found to clean up")

    return success, messages
