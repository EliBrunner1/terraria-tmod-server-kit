"""
validate_config.py  -  Validates config/server-config.json before setup runs.

Catches common mistakes (bad port, invalid difficulty, missing world file)
so the user gets a friendly error before anything is installed.

Run standalone:
  python scripts/validate_config.py
"""

import os
import sys
import json

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "server-config.json")
WORLDS_DIR  = os.path.join(BASE_DIR, "worlds")

VALID_DIFFICULTIES = {0: "classic", 1: "expert", 2: "master", 3: "journey"}
VALID_WORLD_SIZES  = {1: "small",   2: "medium", 3: "large"}
VALID_LANGUAGES    = {
    "en-US", "de-DE", "it-IT", "fr-FR", "es-ES",
    "ru-RU", "zh-Hans", "pt-BR", "pl-PL",
}


def validate():
    """
    Validate config/server-config.json.
    Prints warnings and errors, returns True if no hard errors found.
    """
    errors   = []
    warnings = []

    # ── File existence ────────────────────────────────────────────────────────
    if not os.path.exists(CONFIG_PATH):
        print(f"  ERROR: config/server-config.json not found.")
        print(f"         Expected at: {CONFIG_PATH}")
        return False

    # ── JSON parse ────────────────────────────────────────────────────────────
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"  ERROR: server-config.json is not valid JSON: {exc}")
        print(f"         Open the file in a text editor and check for typos.")
        return False

    # ── Port ──────────────────────────────────────────────────────────────────
    port = cfg.get("port", 7777)
    if not isinstance(port, int) or not (1 <= port <= 65535):
        errors.append(
            f"'port' must be an integer between 1 and 65535  (got: {port!r})\n"
            f"         The default Terraria port is 7777."
        )

    # ── Max players ───────────────────────────────────────────────────────────
    mp = cfg.get("max_players", 8)
    if not isinstance(mp, int) or not (1 <= mp <= 255):
        errors.append(f"'max_players' must be an integer between 1 and 255  (got: {mp!r})")

    # ── Difficulty ────────────────────────────────────────────────────────────
    diff = cfg.get("difficulty", 1)
    if diff not in VALID_DIFFICULTIES:
        errors.append(
            f"'difficulty' must be 0 (classic), 1 (expert), 2 (master), or 3 (journey)  "
            f"(got: {diff!r})"
        )

    # ── World size ────────────────────────────────────────────────────────────
    ws = cfg.get("world_size", 2)
    if ws not in VALID_WORLD_SIZES:
        errors.append(
            f"'world_size' must be 1 (small), 2 (medium), or 3 (large)  (got: {ws!r})"
        )

    # ── Language ──────────────────────────────────────────────────────────────
    lang = cfg.get("language", "en-US")
    if lang not in VALID_LANGUAGES:
        warnings.append(
            f"'language' value {lang!r} is not a recognised tModLoader language.\n"
            f"         Valid options: {', '.join(sorted(VALID_LANGUAGES))}"
        )

    # ── World name ────────────────────────────────────────────────────────────
    world_name = cfg.get("world_name", "")
    if not isinstance(world_name, str) or not world_name.strip():
        errors.append("'world_name' cannot be empty — choose a name for your world.")

    # ── Existing world check ──────────────────────────────────────────────────
    auto_create = cfg.get("auto_create", True)
    if not auto_create and world_name:
        expected = os.path.join(WORLDS_DIR, f"{world_name.strip()}.wld")
        if not os.path.exists(expected):
            errors.append(
                f"'auto_create' is false but no world file was found at:\n"
                f"         {expected}\n"
                f"         Copy your .wld file to the worlds/ folder, or set 'auto_create' to true."
            )

    # ── Password warning ──────────────────────────────────────────────────────
    pw = cfg.get("password", "")
    if not pw:
        warnings.append(
            "No password set — anyone with your server address can join.\n"
            "         Add a 'password' to restrict access."
        )

    # ── Report ────────────────────────────────────────────────────────────────
    for w in warnings:
        print(f"  WARNING: {w}")
    for e in errors:
        print(f"  ERROR:   {e}")

    return len(errors) == 0


if __name__ == "__main__":
    print("Validating config/server-config.json…\n")
    if validate():
        print("\nConfig is valid.")
        sys.exit(0)
    else:
        print("\nPlease fix the errors above, then run:")
        print("  python scripts/setup.py")
        sys.exit(1)
