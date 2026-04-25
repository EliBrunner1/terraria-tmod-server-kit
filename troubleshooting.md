# Troubleshooting

Common problems and fixes for the tModLoader dedicated server.

---

## Server Won't Start / Closes Immediately

### tModLoader files not found

```
ERROR: tModLoader server files not found
```

**Fix:** Run setup again — it will download tModLoader.
```
python scripts\setup.py
```

If the download failed, check your internet connection.  
You can also download manually from:  
https://github.com/tModLoader/tModLoader/releases/latest  
Then extract the zip to `server/tmodloader/`.

---

### serverconfig.txt missing

```
ERROR: serverconfig.txt is missing
```

**Fix:** Regenerate it:
```
python scripts\setup.py
```
or just:
```
python scripts\generate_serverconfig.py
```

---

### World file not found

```
Failed to find world file: worlds/MyWorld.wld
```
or the server creates a world in an unexpected location.

**Fix:**
- If `auto_create` is `true` in `server-config.json`, the server creates a
  world on first run. Check `worlds/` after starting.
- If `auto_create` is `false`, copy your `.wld` file into `worlds/` and make
  sure `world_name` in `server-config.json` matches the file name
  (without the `.wld` extension).
- After any change, regenerate the config:
  ```
  python scripts\generate_serverconfig.py
  ```

---

### .NET runtime error

```
A fatal error occurred. The required library hostfxr.dll could not be found.
```
or
```
dotnet: command not found
```

**Fix:** Install the .NET 6+ (or .NET 8) runtime.

- Windows: https://dotnet.microsoft.com/en-us/download/dotnet/8.0
- Linux: `sudo apt install dotnet-runtime-8.0`
- macOS: `brew install --cask dotnet-sdk`

After installing, close any open terminals/Command Prompts, open a new one,
and run `dotnet --version` to verify.

---

### Server closes the instant it starts (no error shown)

Possible causes:

1. **EULA or first-run interactive prompt** — tModLoader may be waiting for
   input and the window closes.  
   **Fix:** Try running the server manually to see any interactive prompts:
   ```
   cd server\tmodloader
   start-tModLoaderServer.bat -config "..\serverconfig.txt"
   ```

2. **Port conflict** — something is already using port 7777.  
   **Fix:** See "Port already in use" section below.

3. **Corrupted download** — the tModLoader files are incomplete.  
   **Fix:** Re-run setup with `--force` to re-download:
   ```
   python scripts\install_tmodloader.py --force
   ```

4. **Wrong .NET version** — tModLoader needs .NET 6 or newer.  
   **Fix:** See `.NET runtime error` section above.

---

## Port Already in Use

```
WARNING: Port 7777 may already be in use
```

**Fix:**

1. Make sure you do not already have a Terraria server running.
2. Check what is using the port:
   - Windows: `netstat -ano | findstr :7777`
   - Linux/macOS: `ss -ltnp | grep :7777`
3. Change the port in `config/server-config.json` to something else (e.g. 7778)
   and re-run `python scripts\setup.py`.

---

## Friends Can't Connect

### On the same network (LAN)

- Make sure your **firewall** is not blocking port 7777 (TCP).  
  Windows: Search "Windows Defender Firewall" → Advanced Settings →
  Inbound Rules → New Rule → Port → TCP → 7777.
- Give friends your **local IP**, not `127.0.0.1`.  
  Find it: open Command Prompt → `ipconfig` → look for "IPv4 Address".

### Over the internet (without port forwarding)

Direct connections require port forwarding on your router, OR a tunnel.

**Easiest fix:** Use Playit.gg — see `playit_setup.md`.  

If using port forwarding:
1. Forward TCP port 7777 on your router to your PC's local IP.
2. Share your **public** IP (https://whatismyip.com) with friends.

### Firewall blocking the server

Windows may pop up a firewall dialog when the server first starts. Click
**Allow** for both public and private networks.

If you missed it, go to:  
Windows Defender Firewall → Advanced Settings → Inbound Rules → New Rule  
→ Port → TCP → 7777 → Allow → name it "tModLoader Server".

---

## Mod Problems

### Players get "Mod mismatch" or can't join

Terraria/tModLoader requires every player to have **exactly the same mods**
installed and enabled as the server.

**Fix:**
1. Tell each player to open tModLoader → Workshop → Manage Mods.
2. They must enable the same mods that the server has loaded.
3. Restart both the server and the client after enabling/disabling mods.

### Mods not loading / mod not found

```
tModLoader could not find mod: ExampleMod
```

**Fix:**
1. Make sure the `.tmod` file is in `mods/`.
2. Re-run `python scripts\setup.py` to sync it to the tModLoader Mods folder.
3. Check the path printed in setup output ("tModLoader Mods directory: …").
4. Verify the `.tmod` file is there.

### How to get mod files

1. In your **Terraria client**, open Workshop → search for the mod → Download.
2. After downloading, copy the `.tmod` file from your client Mods folder:
   - Windows: `%USERPROFILE%\Documents\My Games\Terraria\tModLoader\Mods\`
   - Linux:   `~/.local/share/Terraria/tModLoader/Mods/`
   - macOS:   `~/Library/Application Support/Terraria/tModLoader/Mods/`
3. Paste the `.tmod` file into `mods/` in this project.
4. Run `python scripts\setup.py` to sync and enable it on the server.

### Outdated mod / outdated tModLoader

If a mod requires a newer tModLoader version:
1. Re-download tModLoader: `python scripts\install_tmodloader.py --force`
2. Tell all players to update their tModLoader client as well.

---

## Performance / Lag

### High CPU usage

- Lower `view_distance` in `config/server-config.json` (try 6–8) and
  regenerate serverconfig.txt.
- Remove resource-heavy mods (large content mods like Calamity on a weak PC).

### High ping for online friends

- Friends connecting through Playit.gg will have some added latency — this is
  normal; Playit routes traffic through its servers.
- Friends on the same LAN should have minimal latency.

---

## Playit.gg Issues

See `playit_setup.md → Troubleshooting` for Playit-specific problems.

Key rule: **always start the Terraria server BEFORE starting Playit.**

---

## Still Stuck?

1. Check the server log in `server/tmodloader/` (look for `.log` files).
2. Run the server manually in a terminal to see full error output:
   ```
   cd server\tmodloader
   start-tModLoaderServer.bat -config "..\serverconfig.txt"
   ```
3. Check the tModLoader GitHub issues:  
   https://github.com/tModLoader/tModLoader/issues
