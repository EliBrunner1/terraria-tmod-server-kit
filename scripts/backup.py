"""
backup.py  -  Creates a zip backup of your Terraria world files.

Usage:
  Manual backup:
    python scripts/backup.py

  Auto-backup (runs every N minutes):
    python scripts/backup.py --auto
    python scripts/backup.py --auto --interval 60

  List available backups:
    python scripts/backup.py --list

Backups are saved to:
  backups/world-YYYY-MM-DD_HH-MM-SS.zip

The oldest backups are deleted automatically once you exceed MAX_BACKUPS.
"""

import os
import sys
import zipfile
import datetime
import time
import argparse

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
BASE_DIR         = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
WORLDS_DIR       = os.path.join(BASE_DIR, "worlds")
BACKUP_DIR       = os.path.join(BASE_DIR, "backups")

# File extensions that belong to a Terraria world
WORLD_EXTENSIONS = (".wld", ".wld.bak", ".twld")

# How many backup zips to keep before deleting the oldest
MAX_BACKUPS      = 10

# Default auto-backup interval (minutes)
DEFAULT_INTERVAL = 30


# ─────────────────────────────────────────────────────────────────────────────
#  Core backup logic
# ─────────────────────────────────────────────────────────────────────────────

def _collect_world_files():
    """
    Returns a list of (abs_path, arcname) tuples for every world file found.
    arcname is the path as stored inside the zip (relative to BASE_DIR).
    """
    found = []
    if not os.path.isdir(WORLDS_DIR):
        return found

    for fname in os.listdir(WORLDS_DIR):
        # Match any of the world file extensions
        if any(fname.endswith(ext) for ext in WORLD_EXTENSIONS):
            abs_path = os.path.join(WORLDS_DIR, fname)
            arcname  = os.path.relpath(abs_path, BASE_DIR)
            found.append((abs_path, arcname))
    return found


def create_backup():
    """
    Zip all world files and save the archive to backups/.
    Returns the path to the new zip, or None if no worlds were found.
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)

    world_files = _collect_world_files()
    if not world_files:
        print("No world files found in worlds/")
        print("Has the server created a world yet? Check worlds/ after the first run.")
        return None

    timestamp   = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"world-{timestamp}.zip"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    print(f"Creating backup: {backup_name}")

    total   = 0
    skipped = 0

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for abs_path, arcname in world_files:
            try:
                zf.write(abs_path, arcname)
                total += 1
                print(f"  Added: {arcname}")
            except (PermissionError, OSError) as exc:
                print(f"  WARNING: skipped {os.path.basename(abs_path)}: {exc}")
                skipped += 1

    size_mb = os.path.getsize(backup_path) / (1024 * 1024)
    print(f"  {total} file(s) → {size_mb:.1f} MB"
          + (f"  ({skipped} skipped)" if skipped else ""))
    print(f"  Saved: {backup_path}")

    _rotate_backups()
    return backup_path


def _rotate_backups():
    """Delete the oldest backups when there are more than MAX_BACKUPS."""
    try:
        zips = sorted(
            f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")
        )
        while len(zips) > MAX_BACKUPS:
            oldest = zips.pop(0)
            os.remove(os.path.join(BACKUP_DIR, oldest))
            print(f"  Removed old backup: {oldest}")
    except OSError:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  Auto-backup loop
# ─────────────────────────────────────────────────────────────────────────────

def auto_backup(interval_minutes):
    """Run backups on a recurring schedule until Ctrl+C."""
    print(f"Auto-backup active — every {interval_minutes} minute(s).")
    print("Press Ctrl+C to stop.\n")

    while True:
        create_backup()
        print(f"\nNext backup in {interval_minutes} minute(s)…\n")
        try:
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\nAuto-backup stopped.")
            break


# ─────────────────────────────────────────────────────────────────────────────
#  List helper
# ─────────────────────────────────────────────────────────────────────────────

def list_backups():
    """Print all available backup zips with their sizes."""
    if not os.path.isdir(BACKUP_DIR):
        print("backups/ folder does not exist yet.")
        return

    zips = sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip"))
    if not zips:
        print("No backups found in backups/")
        return

    print(f"Available backups ({len(zips)}):")
    for name in zips:
        path    = os.path.join(BACKUP_DIR, name)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"  {name}  ({size_mb:.1f} MB)")

    print()
    print("To restore a backup:")
    print("  1. Stop the server.")
    print("  2. Delete (or rename) the .wld files in worlds/")
    print("  3. Extract the zip file — it contains a worlds/ subfolder.")
    print("  4. Start the server.")


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Back up Terraria world files from the worlds/ folder."
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Run automatically on a repeating interval (default: 30 min)."
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL, metavar="MINUTES",
        help=f"Minutes between auto-backups (default: {DEFAULT_INTERVAL})."
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available backups."
    )
    args = parser.parse_args()

    if args.list:
        list_backups()
    elif args.auto:
        auto_backup(args.interval)
    else:
        result = create_backup()
        sys.exit(0 if result else 1)
