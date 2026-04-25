"""
install_tmodloader.py  -  Downloads the latest stable tModLoader dedicated server from GitHub.

The server files are extracted to server/tmodloader/.

Run standalone:
  python scripts/install_tmodloader.py
  python scripts/install_tmodloader.py --force    # re-download even if already installed
"""

import os
import sys
import json
import shutil
import stat
import platform
import urllib.request
import urllib.error
import zipfile
import tarfile
import re
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SERVER_DIR = os.path.join(BASE_DIR, "server")
TMOD_DIR   = os.path.join(SERVER_DIR, "tmodloader")

GITHUB_API  = "https://api.github.com/repos/tModLoader/tModLoader/releases/latest"
GITHUB_TAGS = "https://api.github.com/repos/tModLoader/tModLoader/releases"

# Expected name of the server start scripts inside the extracted archive
SERVER_SCRIPT_WIN = "start-tModLoaderServer.bat"
SERVER_SCRIPT_NIX = "start-tModLoaderServer.sh"


# ─────────────────────────────────────────────────────────────────────────────
#  HTTP helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_json(url):
    """GETs a URL and returns the parsed JSON. Exits on error."""
    headers = {"User-Agent": "terraria-tmod-server-kit/1.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        print(f"\n  ERROR: Could not reach GitHub API: {exc}")
        print("         Check your internet connection and try again.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("\n  ERROR: Unexpected response from GitHub (not valid JSON).")
        sys.exit(1)


def _download(url, dest_path):
    """Download a file to dest_path with a simple progress bar."""
    tmp = dest_path + ".tmp"
    headers = {"User-Agent": "terraria-tmod-server-kit/1.0"}
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            total   = int(resp.headers.get("Content-Length", 0))
            written = 0
            block   = 65536
            with open(tmp, "wb") as fh:
                while True:
                    chunk = resp.read(block)
                    if not chunk:
                        break
                    fh.write(chunk)
                    written += len(chunk)
                    if total > 0:
                        pct = min(100, written * 100 // total)
                        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                        print(f"\r  [{bar}] {pct:3d}%", end="", flush=True)
        print()
    except urllib.error.URLError as exc:
        print(f"\n  ERROR: Download failed: {exc}")
        if os.path.exists(tmp):
            os.remove(tmp)
        sys.exit(1)

    os.replace(tmp, dest_path)


# ─────────────────────────────────────────────────────────────────────────────
#  Release selection
# ─────────────────────────────────────────────────────────────────────────────

def _is_stable_tag(tag):
    """Return True for version tags like v2024.6.4 or v1.4.4.9 (no alpha/beta/rc)."""
    lower = tag.lower()
    return not any(s in lower for s in ("alpha", "beta", "preview", "rc", "dev"))


def get_latest_stable_release():
    """
    Returns (version_tag, assets_list) for the latest stable tModLoader release.
    Falls back to iterating recent releases if the 'latest' tag is a pre-release.
    """
    print("  Fetching tModLoader release info from GitHub…")
    data = _fetch_json(GITHUB_API)

    tag    = data.get("tag_name", "")
    assets = data.get("assets", [])

    if not data.get("prerelease", False) and _is_stable_tag(tag):
        print(f"  Latest stable: {tag}")
        return tag, assets

    # /releases/latest pointed to a pre-release — scan recent releases
    print(f"  {tag} is a pre-release. Looking for latest stable…")
    releases = _fetch_json(GITHUB_TAGS + "?per_page=20")
    for rel in releases:
        t = rel.get("tag_name", "")
        if not rel.get("prerelease", False) and _is_stable_tag(t):
            print(f"  Latest stable: {t}")
            return t, rel.get("assets", [])

    # Nothing found — use whatever latest has
    print(f"  WARNING: Could not find a stable release. Using {tag}.")
    return tag, assets


def _pick_asset(assets):
    """
    Choose the right download asset for the current OS.

    tModLoader releases use naming conventions like:
      tModLoader.zip                  — Windows (and cross-platform)
      tModLoader-linux-{ver}.zip
      tModLoader-osx-{ver}.zip
    Earlier releases may differ; we try several heuristics.
    """
    os_name = platform.system()

    def _score(asset):
        name  = asset["name"].lower()
        score = 0

        # Must be an archive
        if not (name.endswith(".zip") or name.endswith(".tar.gz")):
            return -1
        # Skip source code archives
        if "source" in name:
            return -1

        # Platform preference
        if os_name == "Windows":
            if "linux" in name or "osx" in name or "mac" in name:
                score -= 10
            if name.endswith(".zip"):
                score += 5
        elif os_name == "Darwin":
            if "osx" in name or "mac" in name:
                score += 10
            if "linux" in name or ("win" in name and "darwin" not in name):
                score -= 10
        else:  # Linux
            if "linux" in name:
                score += 10
            if "osx" in name or "mac" in name or "win" in name:
                score -= 10

        # Prefer assets with "tmodloader" in the name
        if "tmodloader" in name:
            score += 3

        return score

    ranked = sorted(assets, key=_score, reverse=True)
    best   = ranked[0] if ranked else None

    if best is None or _score(best) < 0:
        return None
    return best


# ─────────────────────────────────────────────────────────────────────────────
#  Extraction
# ─────────────────────────────────────────────────────────────────────────────

def _extract(archive_path, dest_dir):
    """Extract a .zip or .tar.gz archive into dest_dir."""
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)

    name = archive_path.lower()
    print(f"  Extracting {os.path.basename(archive_path)}…")

    if name.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            # Check for a single top-level directory (common in GitHub zips)
            names   = zf.namelist()
            roots   = {n.split("/")[0] for n in names if n}
            if len(roots) == 1:
                # Strip the top-level directory when extracting
                top = next(iter(roots)) + "/"
                for member in zf.infolist():
                    if member.filename.startswith(top) and member.filename != top:
                        member.filename = member.filename[len(top):]
                        zf.extract(member, dest_dir)
            else:
                zf.extractall(dest_dir)

    elif name.endswith(".tar.gz") or name.endswith(".tgz"):
        with tarfile.open(archive_path, "r:gz") as tf:
            tf.extractall(dest_dir)
    else:
        print(f"  ERROR: Unknown archive format: {archive_path}")
        sys.exit(1)

    # Make .sh files executable on Unix
    if platform.system() != "Windows":
        for root, _, files in os.walk(dest_dir):
            for f in files:
                if f.endswith(".sh"):
                    fp = os.path.join(root, f)
                    try:
                        st = os.stat(fp)
                        os.chmod(fp, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    except OSError:
                        pass


# ─────────────────────────────────────────────────────────────────────────────
#  Post-install verification
# ─────────────────────────────────────────────────────────────────────────────

def find_server_script(base=None):
    """
    Walk base (default TMOD_DIR) and return the path to the tModLoader server
    start script for the current OS, or None if not found.
    """
    base = base or TMOD_DIR
    if not os.path.isdir(base):
        return None

    target = SERVER_SCRIPT_WIN if platform.system() == "Windows" else SERVER_SCRIPT_NIX

    for root, _, files in os.walk(base):
        if target in files:
            return os.path.join(root, target)

    # Also accept the other platform's script as a fallback
    alt = SERVER_SCRIPT_NIX if platform.system() == "Windows" else SERVER_SCRIPT_WIN
    for root, _, files in os.walk(base):
        if alt in files:
            return os.path.join(root, alt)

    return None


def is_installed():
    """Return True if tModLoader server files look intact."""
    return bool(find_server_script())


# ─────────────────────────────────────────────────────────────────────────────
#  Main install function
# ─────────────────────────────────────────────────────────────────────────────

def install_tmodloader(force=False):
    """
    Download and extract the latest stable tModLoader dedicated server.
    Returns the path to the server start script.

    If already installed and force=False, skips the download.
    """
    os.makedirs(SERVER_DIR, exist_ok=True)

    if is_installed() and not force:
        script = find_server_script()
        print(f"  tModLoader already installed.")
        print(f"  Script: {os.path.relpath(script, BASE_DIR)}")
        return script

    version, assets = get_latest_stable_release()
    asset = _pick_asset(assets)

    if asset is None:
        print()
        print("  ERROR: Could not find a suitable tModLoader download for your OS.")
        print("         Please download manually from:")
        print("         https://github.com/tModLoader/tModLoader/releases/latest")
        print()
        print("         Then extract the archive to:  server/tmodloader/")
        print("         Make sure  start-tModLoaderServer.bat  (or .sh) is in that folder.")
        sys.exit(1)

    archive_name = asset["name"]
    archive_url  = asset["browser_download_url"]
    archive_path = os.path.join(SERVER_DIR, archive_name)

    print(f"  Downloading {archive_name} ({asset.get('size', 0) // (1024*1024)} MB)…")
    _download(archive_url, archive_path)

    _extract(archive_path, TMOD_DIR)

    # Clean up the downloaded archive
    try:
        os.remove(archive_path)
    except OSError:
        pass

    script = find_server_script()
    if script is None:
        print()
        print("  WARNING: Could not locate the server start script after extraction.")
        print(f"           Check the contents of:  {os.path.relpath(TMOD_DIR, BASE_DIR)}")
        print(f"           You should see  {SERVER_SCRIPT_WIN}  or  {SERVER_SCRIPT_NIX}  there.")
    else:
        print(f"  tModLoader {version} ready.")
        print(f"  Script: {os.path.relpath(script, BASE_DIR)}")

    return script


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and install the tModLoader dedicated server."
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-download even if tModLoader is already installed."
    )
    args = parser.parse_args()
    install_tmodloader(force=args.force)
