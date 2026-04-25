# Playit.gg Setup — Let Friends Join Without Port Forwarding

Playit.gg is a free tunnelling service. It creates a public address that routes
traffic to your local Terraria server. No router changes, no static IP needed.

---

## What Playit.gg Can and Cannot Do

| It CAN | It CANNOT |
|--------|-----------|
| Let friends join without port forwarding | Remove the need to run the server on your PC |
| Give you a stable, shareable address | Work if your server is not running |
| Keep your home IP private | Fix in-game lag caused by a slow PC |

---

## Quick Start

### 1. Download Playit

Go to **https://playit.gg/download** and download the version for your OS.

| OS      | What to download                |
|---------|---------------------------------|
| Windows | `playit-windows-x86_64.exe`     |
| macOS   | `playit-darwin-x86_64`          |
| Linux   | `playit-linux-x86_64`           |

### 2. Run Playit for the first time

**Windows:** Double-click the `.exe` file.  
**macOS / Linux:** Open a terminal and run:

```
chmod +x playit-darwin-x86_64
./playit-darwin-x86_64
```

Playit prints a claim URL in the terminal. Open it in your browser to create a
free account and get a permanent address (optional — it works without an
account but the address may change each session).

### 3. Add a Terraria tunnel

In the Playit web dashboard (or follow the terminal prompts):

1. Click **Add Tunnel**
2. Protocol: **TCP** (Terraria uses TCP — choose "Minecraft Java" only if there
   is no plain TCP option; it works the same for our purposes)
3. **Local Port:** match your `port` setting in `config/server-config.json`
   (default: `7777`)
4. Save — Playit will give you a public address and port, e.g.:
   `abc123.joinmc.link:7777`  or  `95.211.x.x:12345`

### 4. Start order (important!)

Always start in this order:

1. **Start your Terraria server first** — double-click `server\start-tmod.bat`
   and wait for `Server started`.
2. **Then start Playit** — run the Playit agent/desktop app.

If you start Playit before the server, the tunnel may fail to connect.

### 5. Share the address

Give friends the full address Playit assigned, including the port:
```
abc123.joinmc.link:7777
```

In Terraria:  
**Multiplayer → Join via IP → enter address → enter port**

---

## Keeping Playit Running

Playit must stay running while friends are playing. If you close the Playit
window, the tunnel goes down and connected players will disconnect.

**Windows tip:** Minimize the Playit window to the system tray.

---

## Free Account vs No Account

| Without account | With free account |
|-----------------|-------------------|
| Works immediately | Requires a quick sign-up |
| Address may change each session | Permanent, stable address |
| | Custom subdomain (e.g. `myserver.joinmc.link`) |

Sign up at **https://playit.gg** — it's free and takes under a minute.

---

## Privacy Notes

- Playit **does not** expose your home IP to players. They connect to Playit's
  infrastructure, which forwards traffic to your PC.
- **Do not commit `playit.toml`** to git — it contains your tunnel secret.
  It is already listed in `.gitignore`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Players get "Connection refused" | Make sure the **server** is running before Playit |
| Playit says "No agent connected" | The Playit desktop/CLI must be running on your PC |
| Address keeps changing | Create a free Playit account for a fixed address |
| Wrong port | Check the tunnel Local Port matches `port` in `server-config.json` |
| High ping for friends | Expected — traffic routes through Playit's servers |

See `troubleshooting.md` for more server-side problems.
