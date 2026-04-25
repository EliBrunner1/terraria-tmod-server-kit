# terraria-tmod-server-kit

A plug-and-play tModLoader dedicated server that runs on your PC.  
One setup command → server running in minutes.

**Supports:** Windows · macOS · Linux  
**Server software:** [tModLoader](https://github.com/tModLoader/tModLoader) (latest stable, auto-downloaded)  
**Optional tunnel:** [Playit.gg](https://playit.gg) — friends join without port forwarding

---

## What This Kit Does (and Does Not Do)

| It automates | It does NOT automate |
|---|---|
| Downloading tModLoader | Installing Terraria itself |
| Generating serverconfig.txt | Port forwarding on your router |
| Syncing mods to the right folder | Downloading Workshop mods |
| Creating start scripts | Keeping your IP static |
| World creation on first run | Hiding your IP without a tunnel |

Friends outside your local network need either **port forwarding** on your
router, or a tunnel like **Playit.gg** (see below). This kit cannot bypass
networking by itself.

---

## Requirements

| Requirement | Where to get it |
|---|---|
| **Windows 10/11, macOS 12+, or Linux** | — |
| **.NET 6+ runtime** | https://dotnet.microsoft.com/en-us/download/dotnet/8.0 |
| **Python 3.8+** | https://www.python.org/downloads/ |
| **~500 MB disk space** | For tModLoader + world data |
| **2–6 GB RAM** | Depends on mods |
| **Internet** (first-time setup only) | To download tModLoader |

> **Windows users:** When installing Python, check ✅ **"Add Python to PATH"**
> before clicking Install.

---

## Quick Start — Windows

**Step 1 — Get the files**

Download this repo as a ZIP (green **Code** button → **Download ZIP**) and
extract it anywhere, or clone it:
```
git clone https://github.com/YOUR_USERNAME/terraria-tmod-server-kit.git
cd terraria-tmod-server-kit
```

**Step 2 — (Optional) Customise your server**

Open `config/server-config.json` in Notepad and edit:
```json
{
  "server_name": "My Awesome Server",
  "max_players": 8,
  "difficulty": 1,
  "password": "secretpass"
}
```
See [Configuration](#configuration) below for all options.

**Step 3 — Run setup**

Open Command Prompt in the project folder and run:
```
python scripts\setup.py
```

Setup will:
- Check that .NET 6+ is installed
- Download the latest stable tModLoader dedicated server
- Ask whether to create a new world or use an existing one
- Generate `server/serverconfig.txt`
- Generate `server/start-tmod.bat`

**Step 4 — Start the server**

Double-click `server\start-tmod.bat`

Wait for:
```
Server started
```
(This can take 30–60 seconds on the first run while the world generates.)

**Step 5 — Join**

Open Terraria → **Multiplayer** → **Join via IP**  
Address: `127.0.0.1`  Port: `7777`

---

## Quick Start — macOS / Linux

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/terraria-tmod-server-kit.git
cd terraria-tmod-server-kit

# Run setup
python3 scripts/setup.py

# Start the server
cd server && ./start-tmod.sh
```

Join: `localhost:7777`

---

## How to Use an Existing World

If you already have a Terraria world you want to use:

1. Find your world file — it ends in `.wld`:
   - **Windows:** `%USERPROFILE%\Documents\My Games\Terraria\Worlds\`
   - **Linux:** `~/.local/share/Terraria/Worlds/`
   - **macOS:** `~/Library/Application Support/Terraria/Worlds/`
2. Copy the `.wld` file into the `worlds/` folder in this project.
3. Open `config/server-config.json` and set:
   ```json
   "world_name": "YourWorldFileName",
   "auto_create": false
   ```
   (Use the file name without `.wld`)
4. Run `python scripts\setup.py` — it will detect the file and configure everything.

---

## How to Create a New World

New world creation is the default. In `config/server-config.json`:

```json
"world_name": "MyWorld",
"world_size": 2,
"difficulty": 1,
"seed": "",
"auto_create": true
```

The world is created on the **first server start**, not during setup. Depending
on world size, this can take 1–5 minutes. The `.wld` file is saved in `worlds/`.

| `world_size` | Size |
|---|---|
| `1` | Small |
| `2` | Medium |
| `3` | Large |

| `difficulty` | Mode |
|---|---|
| `0` | Classic |
| `1` | Expert |
| `2` | Master |
| `3` | Journey |

---

## How to Install Mods

tModLoader mods are `.tmod` files. The server and every player must use the
**same mods**.

### Step 1 — Get the .tmod files

Open your **Terraria client** → Workshop → browse and download the mods you
want. After downloading, find the `.tmod` files:

| OS | Path |
|---|---|
| Windows | `%USERPROFILE%\Documents\My Games\Terraria\tModLoader\Mods\` |
| Linux | `~/.local/share/Terraria/tModLoader/Mods/` |
| macOS | `~/Library/Application Support/Terraria/tModLoader/Mods/` |

### Step 2 — Copy mods to this project

Copy the `.tmod` files you want on the server into the `mods/` folder in this
project.

### Step 3 — Sync to the server

```
python scripts\setup.py
```

Setup copies the mods to the correct location and updates `enabled.json` so
the server loads them automatically.

### Step 4 — Tell your players

Every player must:
1. Have the same mods downloaded in their tModLoader client.
2. Enable them in **Workshop → Manage Mods**.
3. Restart Terraria.

> Mod version mismatches will prevent players from joining. Make sure everyone
> updates together.

---

## How to Use Playit.gg (Online Play Without Port Forwarding)

Playit.gg creates a public tunnel address that routes traffic to your server.
Players connect to the Playit address — your home IP stays private.

1. Download Playit: **https://playit.gg/download**
2. Run Playit and complete the quick setup.
3. Add a **TCP tunnel** pointing to local port `7777` (or your configured port).
4. Playit gives you a free address like `abc123.joinmc.link:7777`.
5. Start your server **before** starting Playit.
6. Share the Playit address and port with friends.

Full guide: **[playit_setup.md](playit_setup.md)**

> Without a tunnel or port forwarding, friends outside your network cannot
> connect. This is a limitation of how home internet works, not this kit.

---

## How to Back Up Worlds

**Manual backup** (saves to `backups/world-DATE-TIME.zip`):
```
python scripts\backup.py
```

**Auto-backup** (every 30 minutes while the script is running):
```
python scripts\backup.py --auto --interval 30
```

**List backups:**
```
python scripts\backup.py --list
```

The last 10 backups are kept automatically — older ones are deleted.

**To restore:** Stop the server → extract a backup zip into the project root
(it preserves the `worlds/` folder structure) → restart the server.

---

## Configuration

Edit `config/server-config.json` and re-run `python scripts\setup.py` to apply.

| Key | Default | Description |
|---|---|---|
| `server_name` | `"My tModLoader Server"` | Name shown in Terraria's server list |
| `port` | `7777` | Port the server listens on (Terraria default) |
| `max_players` | `8` | Maximum concurrent players |
| `password` | `""` | Server password (blank = no password) |
| `motd` | `"Welcome!..."` | Message shown when players join |
| `world_name` | `"MyWorld"` | World file name (without `.wld`) |
| `world_size` | `2` | 1=Small, 2=Medium, 3=Large |
| `difficulty` | `1` | 0=Classic, 1=Expert, 2=Master, 3=Journey |
| `seed` | `""` | World seed (blank = random) |
| `auto_create` | `true` | Create a new world if the `.wld` file is missing |
| `secure` | `true` | Kick players using known exploits |
| `language` | `"en-US"` | Server language |
| `backup_count` | `10` | How many backup zips to keep |

After changing any setting, run:
```
python scripts\setup.py
```
or just regenerate the config:
```
python scripts\generate_serverconfig.py
```

---

## File Structure

```
terraria-tmod-server-kit/
├── README.md                     ← You are here
├── troubleshooting.md            ← Common problems and fixes
├── playit_setup.md               ← Playit.gg step-by-step guide
├── .gitignore
│
├── config/
│   ├── server-config.json        ← EDIT THIS — your server settings
│   ├── serverconfig.template.txt ← Reference template (not used directly)
│   └── mods.example.json         ← Mod list reference (not used directly)
│
├── scripts/
│   ├── setup.py                  ← Run this once (and after changes)
│   ├── check_dependencies.py     ← Checks .NET, Python, internet
│   ├── install_tmodloader.py     ← Downloads tModLoader from GitHub
│   ├── generate_serverconfig.py  ← Generates server/serverconfig.txt
│   ├── validate_config.py        ← Validates server-config.json
│   └── backup.py                 ← World backup utility
│
├── server/                       ← Everything the server needs
│   ├── start-tmod.bat            ← Windows launcher (regenerated by setup.py)
│   ├── start-tmod.sh             ← macOS/Linux launcher (regenerated by setup.py)
│   ├── serverconfig.txt          ← Generated by setup.py (not in git)
│   └── tmodloader/               ← Downloaded by setup.py (not in git)
│
├── worlds/                       ← Your world files go here (not in git)
│   └── .gitkeep
│
├── mods/                         ← Drop .tmod files here (not in git)
│   └── .gitkeep
│
└── backups/                      ← Backup zips saved here (not in git)
    └── .gitkeep
```

---

## Updating tModLoader

To download the latest tModLoader version:
```
python scripts\install_tmodloader.py --force
```

Or re-run full setup:
```
python scripts\setup.py
```
(It will ask if you want to re-download.)

---

## Common Problems

See **[troubleshooting.md](troubleshooting.md)** for detailed fixes. Quick list:

| Problem | Fix |
|---|---|
| Server closes immediately | Run setup.py, check .NET is installed |
| "Port already in use" | Close any running server, or change port in config |
| Friends on same network can't join | Check Windows Firewall allows port 7777 |
| Friends online can't join | Use Playit.gg or port forward your router |
| "Mod mismatch" error | All players must enable the same mods |
| World not found | Copy `.wld` to `worlds/`, set `auto_create: false` |
| Slow world generation | Normal on first run — wait 1–5 min |

---

## License

The scripts and configuration in this kit are released under the MIT License.  
Terraria and tModLoader are subject to their own licenses.
