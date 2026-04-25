"""
check_dependencies.py  -  Verifies that required software is installed.

Checks:
  1. Python version (3.8+)
  2. .NET runtime (6.0+)  — required to run tModLoader
  3. Internet connectivity — needed to download tModLoader from GitHub

Run standalone:
  python scripts/check_dependencies.py
"""

import sys
import subprocess
import platform
import socket
import re

REQUIRED_PYTHON  = (3, 8)
REQUIRED_DOTNET  = 6          # major version


# ─────────────────────────────────────────────────────────────────────────────
#  Python check
# ─────────────────────────────────────────────────────────────────────────────

def check_python():
    ver = sys.version_info
    if ver < REQUIRED_PYTHON:
        print(f"  ERROR: Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ is required.")
        print(f"         You have Python {ver.major}.{ver.minor}.")
        print(f"         Download from: https://www.python.org/downloads/")
        return False
    print(f"  Python {ver.major}.{ver.minor}.{ver.micro} — OK")
    return True


# ─────────────────────────────────────────────────────────────────────────────
#  .NET check
# ─────────────────────────────────────────────────────────────────────────────

def check_dotnet():
    """Check for .NET 6+ runtime (required by tModLoader)."""
    try:
        result = subprocess.run(
            ["dotnet", "--list-runtimes"],
            capture_output=True, text=True, timeout=10
        )
        output = (result.stdout or "") + (result.stderr or "")

        # Look for any Microsoft.NETCore.App runtime >= 6
        found_versions = []
        for line in output.splitlines():
            m = re.search(r"Microsoft\.NETCore\.App\s+(\d+)\.", line)
            if m:
                found_versions.append(int(m.group(1)))

        if any(v >= REQUIRED_DOTNET for v in found_versions):
            best = max(v for v in found_versions if v >= REQUIRED_DOTNET)
            print(f"  .NET {best}.x runtime — OK")
            return True

        # Fall back: try dotnet --version
        result2 = subprocess.run(
            ["dotnet", "--version"],
            capture_output=True, text=True, timeout=10
        )
        ver_str = (result2.stdout or "").strip()
        m2 = re.match(r"(\d+)\.", ver_str)
        if m2 and int(m2.group(1)) >= REQUIRED_DOTNET:
            print(f"  .NET {ver_str} — OK")
            return True

        print(f"  ERROR: .NET {REQUIRED_DOTNET}+ is required but was not found.")
        _print_dotnet_instructions()
        return False

    except FileNotFoundError:
        print("  ERROR: .NET is not installed (dotnet command not found).")
        _print_dotnet_instructions()
        return False
    except subprocess.TimeoutExpired:
        print("  ERROR: dotnet command timed out — cannot verify .NET.")
        return False


def _print_dotnet_instructions():
    os_name = platform.system()
    print()
    print("  ┌─────────────────────────────────────────────────────────┐")
    print("  │  How to install .NET 6+ (required by tModLoader)        │")
    print("  └─────────────────────────────────────────────────────────┘")

    if os_name == "Windows":
        print("""
  1. Go to: https://dotnet.microsoft.com/en-us/download/dotnet/8.0
  2. Under "Run apps — .NET Runtime", click the Windows x64 download.
  3. Run the installer.
  4. Close this window, open a NEW Command Prompt, then run:
       dotnet --version
     You should see 8.x.x (or any version >= 6).
  5. Run setup again:
       python scripts\\setup.py
""")
    elif os_name == "Darwin":
        print("""
  Option 1 — Installer:
    https://dotnet.microsoft.com/en-us/download/dotnet/8.0
    Download the macOS .pkg and run it.

  Option 2 — Homebrew:
    brew install --cask dotnet-sdk

  After installing, open a new Terminal and run:
    dotnet --version
""")
    else:  # Linux
        print("""
  Ubuntu / Debian:
    sudo apt update && sudo apt install dotnet-runtime-8.0

  Fedora / RHEL:
    sudo dnf install dotnet-runtime-8.0

  Arch Linux:
    sudo pacman -S dotnet-runtime

  Or download from: https://dotnet.microsoft.com/en-us/download/dotnet/8.0

  After installing, run:  dotnet --version
""")


# ─────────────────────────────────────────────────────────────────────────────
#  Internet check
# ─────────────────────────────────────────────────────────────────────────────

def check_internet():
    """Warn (not fail) if GitHub is unreachable."""
    try:
        socket.create_connection(("github.com", 443), timeout=5)
        print("  Internet (github.com) — OK")
        return True
    except OSError:
        print("  WARNING: Cannot reach github.com.")
        print("           You will need internet to download tModLoader.")
        print("           If you already extracted tModLoader to server/tmodloader/,")
        print("           you can skip this warning.")
        return False   # Not a hard failure


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def check_all():
    """Run all checks. Returns True only if every required check passes."""
    ok = True
    ok = check_python() and ok
    ok = check_dotnet()  and ok
    check_internet()            # advisory — doesn't affect return value
    return ok


if __name__ == "__main__":
    print("Checking dependencies…\n")
    if check_all():
        print("\nAll required checks passed.")
        sys.exit(0)
    else:
        print("\nOne or more required checks failed.")
        print("Fix the issues above, then run setup again:")
        print("  python scripts/setup.py")
        sys.exit(1)
