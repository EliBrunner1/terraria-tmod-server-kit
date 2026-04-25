"""
setup.py  -  One-command setup for terraria-tmod-server-kit.

Run this ONCE before starting your server, and again any time you change
config/server-config.json or add new mods.

  Windows:       python scripts\\setup.py
  macOS / Linux: python3 scripts/setup.py

What this script does:
  1. Checks that .NET 6+ is installed
  2. Validates config/server-config.json
  3. Downloads the latest stable tModLoader dedicated server
  4. Creates the required folders
  5. Helps you pick or create a world
  6. Generates server/serverconfig.txt
  7. Syncs mods from mods/ to the tModLoader Mods folder
  8. Generates server/start-tmod.bat and server/start-tmod.sh
  9. Prints how to start the server and let friends join
"""

import os
import sys
import json
import shutil
import platform
import socket
import stat

# Make sure the other scripts in this directory are importable
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

BASE_DIR    = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SERVER_DIR  = os.path.join(BASE_DIR, "server")
WORLDS_DIR  = os.path.join(BASE_DIR, "worlds")
MODS_DIR    = os.path.join(BASE_DIR, "mods")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "server-config.json")

import check_dependencies
import install_tmodloader
import generate_serverconfig
import validate_config


# ─────────────────────────────────────────────────────────────────────────────
#  UI helpers
# ─────────────────────────────────────────────────────────────────────────────

def _banner(title):
    print()
    print("=" * 64)
    print(f"  {title}")
    print("=" * 64)


def _ask_yes_no(prompt, default="no"):
    """Prompt for yes/no. Returns True for yes, False for no."""
    hint = "[yes/no]" if default is None else ("[YES/no]" if default == "yes" else "[yes/NO]")
    while True:
        raw = input(f"  {prompt} {hint}: ").strip().lower()
        if raw in ("yes", "y"):
            return True
        if raw in ("no", "n"):
            return False
        if raw == "" and default is not None:
            return default == "yes"
        print("  Please type 'yes' or 'no'.")


def _ask(prompt, default=""):
    """Prompt for a string value."""
    if default:
        raw = input(f"  {prompt} [{default}]: ").strip()
        return raw if raw else default
    return input(f"  {prompt}: ").strip()


# ─────────────────────────────────────────────────────────────────────────────
#  Config loading
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULTS = {
    "server_name" : "My tModLoader Server",
    "port"        : 7777,
    "max_players" : 8,
    "password"    : "",
    "motd"        : "Welcome! Type /help for commands.",
    "world_name"  : "MyWorld",
    "world_size"  : 2,
    "difficulty"  : 1,
    "seed"        : "",
    "auto_create" : True,
    "secure"      : True,
    "language"    : "en-US",
    "backup_count": 10,
}

_DIFFICULTY_NAMES = {0: "Classic", 1: "Expert", 2: "Master", 3: "Journey"}
_WORLD_SIZE_NAMES = {1: "Small",   2: "Medium", 3: "Large"}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"  WARNING: config/server-config.json not found — using defaults.")
        return dict(_DEFAULTS)
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        user = json.load(fh)
    user = {k: v for k, v in user.items() if not k.startswith("_")}
    return {**_DEFAULTS, **user}


# ─────────────────────────────────────────────────────────────────────────────
#  Folder creation
# ─────────────────────────────────────────────────────────────────────────────

def create_folders():
    """Create all required directories."""
    for folder in (SERVER_DIR, WORLDS_DIR, MODS_DIR, BACKUPS_DIR):
        os.makedirs(folder, exist_ok=True)
        rel = os.path.relpath(folder, BASE_DIR)
        print(f"  OK: {rel}/")


# ─────────────────────────────────────────────────────────────────────────────
#  World setup
# ─────────────────────────────────────────────────────────────────────────────

def _list_wld_files():
    """Return .wld filenames currently in worlds/."""
    if not os.path.isdir(WORLDS_DIR):
        return []
    return [f for f in os.listdir(WORLDS_DIR) if f.endswith(".wld")]


def setup_world(cfg):
    """
    Interactively decide how the world will be set up.
    Updates cfg in-place and saves changes back to server-config.json.
    """
    existing_worlds = _list_wld_files()

    if existing_worlds:
        print()
        print("  World files found in worlds/:")
        for i, wld in enumerate(existing_worlds, 1):
            print(f"    {i}. {wld}")
        print()

        use_existing = _ask_yes_no("Use one of these existing worlds?", default="yes")

        if use_existing:
            if len(existing_worlds) == 1:
                chosen = existing_worlds[0]
                print(f"  Using: {chosen}")
            else:
                while True:
                    raw = _ask(f"Enter the number (1–{len(existing_worlds)})")
                    try:
                        idx = int(raw) - 1
                        if 0 <= idx < len(existing_worlds):
                            chosen = existing_worlds[idx]
                            break
                    except ValueError:
                        pass
                    print(f"  Please enter a number between 1 and {len(existing_worlds)}.")

            world_name        = chosen.replace(".wld", "")
            cfg["world_name"] = world_name
            cfg["auto_create"]= False
            print(f"  World set to: {world_name} (auto_create disabled)")
            _save_config(cfg)
            return

    # No existing worlds, or user wants a new one
    print()
    if existing_worlds:
        print("  Setting up a new world instead.")
    else:
        print("  No worlds found — a new world will be created on first server start.")

    print()
    print("  World settings (edit config/server-config.json for more options):")
    print()

    # World name
    current_name = cfg.get("world_name", "MyWorld")
    new_name = _ask("  World name", default=current_name)
    if new_name:
        cfg["world_name"] = new_name

    # World size
    size_labels = "1=Small, 2=Medium, 3=Large"
    current_size = cfg.get("world_size", 2)
    while True:
        raw = _ask(f"  World size ({size_labels})", default=str(current_size))
        try:
            size = int(raw)
            if size in (1, 2, 3):
                cfg["world_size"] = size
                break
        except ValueError:
            pass
        print("  Please enter 1, 2, or 3.")

    # Difficulty
    diff_labels = "0=Classic, 1=Expert, 2=Master, 3=Journey"
    current_diff = cfg.get("difficulty", 1)
    while True:
        raw = _ask(f"  Difficulty ({diff_labels})", default=str(current_diff))
        try:
            diff = int(raw)
            if diff in (0, 1, 2, 3):
                cfg["difficulty"] = diff
                break
        except ValueError:
            pass
        print("  Please enter 0, 1, 2, or 3.")

    cfg["auto_create"] = True
    _save_config(cfg)

    world_name = cfg["world_name"]
    size_name  = _WORLD_SIZE_NAMES.get(cfg["world_size"], "Medium")
    diff_name  = _DIFFICULTY_NAMES.get(cfg["difficulty"], "Expert")
    print()
    print(f"  World '{world_name}' will be auto-created on first run.")
    print(f"  Size: {size_name}  |  Difficulty: {diff_name}")
    print()
    print("  TIP: If you want to use an existing world, copy its .wld file")
    print(f"       into the worlds/ folder and re-run setup.py.")


def _save_config(cfg):
    """Write updated config back to config/server-config.json."""
    # Re-load the file to preserve _comment keys and formatting
    existing = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            existing = json.load(fh)

    # Merge updated values (non-comment keys only)
    for k, v in cfg.items():
        if not k.startswith("_"):
            existing[k] = v

    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(existing, fh, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
#  Mod sync
# ─────────────────────────────────────────────────────────────────────────────

def _tmod_mods_dir():
    """
    Return the OS-specific tModLoader Mods directory.
    This is where tModLoader looks for .tmod files when running as a server.
    """
    os_name = platform.system()
    if os_name == "Windows":
        docs = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        return os.path.join(docs, "Documents", "My Games", "Terraria", "tModLoader", "Mods")
    elif os_name == "Darwin":
        return os.path.expanduser(
            "~/Library/Application Support/Terraria/tModLoader/Mods"
        )
    else:  # Linux
        return os.path.expanduser("~/.local/share/Terraria/tModLoader/Mods")


def _update_enabled_json(mods_dir, mod_names):
    """
    Add mod_names to enabled.json in mods_dir (create the file if needed).
    tModLoader reads this to know which mods to activate.
    mod_names should be base names without .tmod extension.
    """
    enabled_path = os.path.join(mods_dir, "enabled.json")
    current = []
    if os.path.exists(enabled_path):
        try:
            with open(enabled_path, "r", encoding="utf-8") as fh:
                current = json.load(fh)
        except (json.JSONDecodeError, OSError):
            current = []

    for name in mod_names:
        if name not in current:
            current.append(name)

    with open(enabled_path, "w", encoding="utf-8") as fh:
        json.dump(current, fh, indent=2)


def sync_mods():
    """
    Copy .tmod files from mods/ into the tModLoader Mods directory,
    then update enabled.json to enable them.
    """
    local_tmods = [
        f for f in os.listdir(MODS_DIR) if f.endswith(".tmod")
    ] if os.path.isdir(MODS_DIR) else []

    if not local_tmods:
        print("  No .tmod files found in mods/ — skipping mod sync.")
        print()
        print("  To add mods:")
        print("    1. Copy .tmod files into the mods/ folder.")
        print("    2. Re-run  python scripts/setup.py  to sync them.")
        return

    dest_dir = _tmod_mods_dir()
    os.makedirs(dest_dir, exist_ok=True)

    copied   = []
    skipped  = []

    for fname in local_tmods:
        src = os.path.join(MODS_DIR, fname)
        dst = os.path.join(dest_dir, fname)
        try:
            shutil.copy2(src, dst)
            copied.append(fname)
            print(f"  Copied: {fname}")
        except (OSError, shutil.Error) as exc:
            skipped.append(fname)
            print(f"  WARNING: Could not copy {fname}: {exc}")

    if copied:
        # Strip .tmod extension to get the mod name for enabled.json
        mod_names = [f[:-5] for f in copied]
        _update_enabled_json(dest_dir, mod_names)
        print(f"  Updated enabled.json: {len(copied)} mod(s) enabled.")

    print()
    print(f"  tModLoader Mods directory: {dest_dir}")
    print()
    print("  IMPORTANT: Every player who joins must have the same mods installed")
    print("  and enabled in their own tModLoader client.")


# ─────────────────────────────────────────────────────────────────────────────
#  Start script generation
# ─────────────────────────────────────────────────────────────────────────────

_BAT_TEMPLATE = """\
@echo off
REM ================================================================
REM  start-tmod.bat  -  Start the tModLoader dedicated server
REM  Generated by setup.py  |  edit config/server-config.json
REM  then re-run:  python scripts\\setup.py
REM ================================================================

title tModLoader Server

REM ── Locate key paths relative to this script ──────────────────
set "SERVER_DIR=%~dp0"
REM Strip trailing backslash
if "%SERVER_DIR:~-1%"=="\\" set "SERVER_DIR=%SERVER_DIR:~0,-1%"
set "TMOD_DIR=%SERVER_DIR%\\tmodloader"
set "TMOD_SCRIPT=%TMOD_DIR%\\start-tModLoaderServer.bat"
set "CONFIG=%SERVER_DIR%\\serverconfig.txt"

REM ── Pre-flight checks ─────────────────────────────────────────
if not exist "%CONFIG%" (
    echo.
    echo  ERROR: serverconfig.txt is missing.
    echo  Fix:   Run  python scripts\\setup.py  from the project root.
    echo.
    pause
    exit /b 1
)

if not exist "%TMOD_SCRIPT%" (
    echo.
    echo  ERROR: tModLoader server files not found at:
    echo         %TMOD_DIR%
    echo  Fix:   Run  python scripts\\setup.py  from the project root.
    echo.
    pause
    exit /b 1
)

REM ── Port conflict check ───────────────────────────────────────
netstat -an | findstr /r ":{port} " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo  WARNING: Port {port} may already be in use.
    echo  Another application or server might be running on this port.
    echo  See troubleshooting.md for help.
    echo.
    pause
)

echo.
echo  ================================================================
echo   tModLoader Dedicated Server
echo   Port    : {port}
echo   Players : up to {max_players}
echo   Config  : server\\serverconfig.txt
echo   Stop    : type  exit  in the server console
echo  ================================================================
echo.
echo  Waiting for server to start — this may take 30-60 seconds...
echo.

REM ── Launch tModLoader ─────────────────────────────────────────
REM  We cd into the tmodloader folder so its internal paths work correctly,
REM  then pass the absolute path to our serverconfig.txt.
cd /d "%TMOD_DIR%"
call start-tModLoaderServer.bat -config "%CONFIG%"

echo.
echo  Server stopped. Press any key to close this window.
pause
"""

_SH_TEMPLATE = """\
#!/usr/bin/env bash
# ================================================================
#  start-tmod.sh  -  Start the tModLoader dedicated server
#  Generated by setup.py  |  edit config/server-config.json
#  then re-run:  python3 scripts/setup.py
# ================================================================

# ── Locate key paths relative to this script ──────────────────
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
TMOD_DIR="$SCRIPT_DIR/tmodloader"
TMOD_SCRIPT="$TMOD_DIR/start-tModLoaderServer.sh"
CONFIG="$SCRIPT_DIR/serverconfig.txt"

# ── Pre-flight checks ─────────────────────────────────────────
if [ ! -f "$CONFIG" ]; then
    echo
    echo " ERROR: serverconfig.txt is missing from server/"
    echo " Fix:   Run  python3 scripts/setup.py  from the project root."
    echo
    exit 1
fi

if [ ! -f "$TMOD_SCRIPT" ]; then
    echo
    echo " ERROR: tModLoader server files not found at:"
    echo "        $TMOD_DIR"
    echo " Fix:   Run  python3 scripts/setup.py  from the project root."
    echo
    exit 1
fi

# ── Port conflict check ───────────────────────────────────────
PORT={port}
if command -v ss &>/dev/null; then
    if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
        echo " WARNING: Port $PORT may already be in use. See troubleshooting.md"
    fi
elif command -v lsof &>/dev/null; then
    if lsof -iTCP:$PORT -sTCP:LISTEN &>/dev/null; then
        echo " WARNING: Port $PORT may already be in use. See troubleshooting.md"
    fi
fi

echo
echo " ================================================================"
echo "  tModLoader Dedicated Server"
echo "  Port    : $PORT"
echo "  Players : up to {max_players}"
echo "  Config  : server/serverconfig.txt"
echo "  Stop    : type  exit  in the server console"
echo " ================================================================"
echo
echo " Waiting for server to start (may take 30-60 seconds)..."
echo

# ── Launch tModLoader ─────────────────────────────────────────
# cd into tmodloader/ so its internal paths work, then pass our config.
cd "$TMOD_DIR" || exit 1
exec ./start-tModLoaderServer.sh -config "$CONFIG"
"""


def generate_start_scripts(cfg):
    """Write server/start-tmod.bat and server/start-tmod.sh."""
    os.makedirs(SERVER_DIR, exist_ok=True)

    params = {
        "port"       : cfg.get("port", 7777),
        "max_players": cfg.get("max_players", 8),
    }

    # Windows batch script
    bat_path = os.path.join(SERVER_DIR, "start-tmod.bat")
    with open(bat_path, "w", newline="\r\n", encoding="utf-8") as fh:
        fh.write(_BAT_TEMPLATE.format(**params))
    print(f"  Written: {os.path.relpath(bat_path, BASE_DIR)}")

    # Unix shell script
    sh_path = os.path.join(SERVER_DIR, "start-tmod.sh")
    with open(sh_path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(_SH_TEMPLATE.format(**params))

    # Make it executable on Unix
    try:
        mode = os.stat(sh_path).st_mode
        os.chmod(sh_path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass

    print(f"  Written: {os.path.relpath(sh_path, BASE_DIR)}")


# ─────────────────────────────────────────────────────────────────────────────
#  Port check
# ─────────────────────────────────────────────────────────────────────────────

def _check_port(port):
    """Print a warning if the chosen port is already in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex(("127.0.0.1", int(port))) == 0:
                print(f"  WARNING: Port {port} is already in use on this machine.")
                print("           Make sure no other server is running.")
                print("           See troubleshooting.md for help.")
    except OSError:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  Final instructions
# ─────────────────────────────────────────────────────────────────────────────

def print_next_steps(cfg):
    port       = cfg.get("port", 7777)
    max_p      = cfg.get("max_players", 8)
    world_name = cfg.get("world_name", "MyWorld")
    has_pw     = bool(cfg.get("password", ""))
    os_name    = platform.system()

    mods_dir   = _tmod_mods_dir()
    local_tmods = [
        f for f in os.listdir(MODS_DIR) if f.endswith(".tmod")
    ] if os.path.isdir(MODS_DIR) else []

    print()
    print("=" * 64)
    print("  Setup complete!")
    print("=" * 64)
    print()

    # ── How to start ──────────────────────────────────────────────────────────
    print("START YOUR SERVER")
    print()
    if os_name == "Windows":
        print("  Double-click:   server\\start-tmod.bat")
        print("  — or from Command Prompt —")
        print("  cd server && start-tmod.bat")
    else:
        print("  cd server && ./start-tmod.sh")
    print()
    print("  Wait for the line:  Server started  (may take 30–60 seconds)")
    print()

    # ── Local join ────────────────────────────────────────────────────────────
    print("JOIN LOCALLY (you, on the same PC as the server):")
    print()
    print("  Terraria → Multiplayer → Join via IP")
    print(f"  Address: 127.0.0.1   Port: {port}")
    if has_pw:
        print("  Password: (the one you set in server-config.json)")
    print()

    # ── LAN join ──────────────────────────────────────────────────────────────
    print("JOIN ON THE SAME NETWORK (same house or Wi-Fi):")
    print()
    if os_name == "Windows":
        print("  Find your local IP:  open Command Prompt → type  ipconfig")
        print("  Look for IPv4 Address (e.g. 192.168.1.42)")
    elif os_name == "Darwin":
        print("  Find your local IP:  System Preferences → Network")
        print("  — or in Terminal:    ifconfig | grep 'inet '")
    else:
        print("  Find your local IP:  ip addr  or  hostname -I")
    print(f"  Give friends your local IP and port {port}.")
    print()

    # ── Online join ───────────────────────────────────────────────────────────
    print("FRIENDS ONLINE (outside your network):")
    print()
    print("  Option 1 — Playit.gg (no router changes needed):")
    print("    1. Download Playit: https://playit.gg/download")
    print("    2. Run Playit and complete the quick setup.")
    print(f"    3. Add a Minecraft/Terraria → TCP tunnel → local port {port}.")
    print("    4. Playit gives you a free address, e.g.  abc123.joinmc.link")
    print("    5. Start your server FIRST, then run Playit.")
    print("    6. Share the Playit address and port with friends.")
    print()
    print("  Full guide: playit_setup.md")
    print()
    print("  Option 2 — Port forwarding on your router:")
    print(f"    Forward TCP port {port} to your PC's local IP.")
    print("    Share your public IP (whatismyip.com) with friends.")
    print()

    # ── Mods reminder ─────────────────────────────────────────────────────────
    if local_tmods:
        print("MODS:")
        print()
        print(f"  {len(local_tmods)} mod(s) synced to: {mods_dir}")
        print()
        print("  IMPORTANT: every player joining must have the SAME mods")
        print("  installed and enabled in their tModLoader client.")
        print()
    else:
        print("MODS (none configured yet):")
        print()
        print("  To add mods:")
        print("    1. Copy .tmod files into the mods/ folder.")
        print("    2. Re-run  python scripts/setup.py  to sync and enable them.")
        print()
        print("  Where to get .tmod files:")
        print("    Open Terraria → Workshop → search for mods → Download.")
        if os_name == "Windows":
            docs = os.environ.get("USERPROFILE", os.path.expanduser("~"))
            client_mods = os.path.join(docs, "Documents", "My Games", "Terraria", "tModLoader", "Mods")
            print(f"    Client mods are at:  {client_mods}")
        print("    Copy the .tmod files from your client Mods folder to mods/")
        print()

    # ── Backups ───────────────────────────────────────────────────────────────
    print("BACKUPS:")
    print()
    print("  Manual:  python scripts/backup.py")
    print("  Auto:    python scripts/backup.py --auto --interval 30")
    print("  List:    python scripts/backup.py --list")
    print()

    # ── Troubleshooting ───────────────────────────────────────────────────────
    print("PROBLEMS?  See troubleshooting.md")
    print()
    print("=" * 64)
    print()


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    _banner("terraria-tmod-server-kit  —  Setup")
    print()
    print("  This will set up a tModLoader dedicated server on your PC.")
    print()

    # ── Step 1: Dependencies ─────────────────────────────────────────────────
    _banner("Step 1 / 7  —  Checking Dependencies")
    if not check_dependencies.check_all():
        print()
        print("  Fix the issues above, then run setup again.")
        sys.exit(1)

    # ── Step 2: Config validation ─────────────────────────────────────────────
    _banner("Step 2 / 7  —  Validating Configuration")
    if not validate_config.validate():
        print()
        print("  Edit config/server-config.json to fix the errors, then run setup again.")
        sys.exit(1)

    cfg = load_config()
    print()
    print(f"  Server name  : {cfg['server_name']}")
    print(f"  Port         : {cfg['port']}")
    print(f"  Max players  : {cfg['max_players']}")
    print(f"  Password     : {'(set)' if cfg.get('password') else '(none)'}")
    print(f"  World name   : {cfg['world_name']}")
    print(f"  Difficulty   : {_DIFFICULTY_NAMES.get(cfg.get('difficulty', 1), '?')}")
    print(f"  World size   : {_WORLD_SIZE_NAMES.get(cfg.get('world_size', 2), '?')}")

    _check_port(cfg["port"])

    # ── Step 3: Install tModLoader ────────────────────────────────────────────
    _banner("Step 3 / 7  —  Installing tModLoader Dedicated Server")

    if install_tmodloader.is_installed():
        if _ask_yes_no("tModLoader is already installed. Re-download latest?", default="no"):
            install_tmodloader.install_tmodloader(force=True)
        else:
            print("  Skipping download.")
            script = install_tmodloader.find_server_script()
            print(f"  Using: {os.path.relpath(script, BASE_DIR)}")
    else:
        install_tmodloader.install_tmodloader()

    # ── Step 4: Folder structure ──────────────────────────────────────────────
    _banner("Step 4 / 7  —  Creating Folders")
    create_folders()

    # ── Step 5: World setup ───────────────────────────────────────────────────
    _banner("Step 5 / 7  —  World Setup")
    setup_world(cfg)

    # Reload config after possible edits in setup_world
    cfg = load_config()

    # ── Step 6: Generate config files + start scripts ─────────────────────────
    _banner("Step 6 / 7  —  Generating Configuration Files")
    generate_serverconfig.generate(cfg)
    generate_start_scripts(cfg)

    # ── Step 7: Mod sync ──────────────────────────────────────────────────────
    _banner("Step 7 / 7  —  Mod Setup")
    sync_mods()

    # ── Done ──────────────────────────────────────────────────────────────────
    print_next_steps(cfg)


if __name__ == "__main__":
    main()
