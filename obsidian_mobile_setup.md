# Connecting Obsidian Mobile to Claude Code

You have **paid Obsidian Sync** — your vault is already synced across devices.
This guide explains how to use Claude Code (web/mobile) alongside your Obsidian vault.

---

## How It Works

Claude Code runs in a remote cloud container. It cannot directly read files from your phone.
To get notes or vault content into a Claude Code session you push content to it — there are
three practical ways to do this.

---

## Option 1 — Paste notes directly (quickest, no setup)

Best for: one-off questions, drafting, editing a single note.

1. Open the note in Obsidian on your phone.
2. Copy the text.
3. Paste it into your Claude Code chat and ask your question.

Claude Code can edit it, answer questions about it, or generate new content,
and you paste the result back into Obsidian.

---

## Option 2 — Obsidian Git plugin + Claude Code (recommended for ongoing use)

Best for: keeping a vault in sync with a GitHub repo so Claude Code can read and write files.

### Setup (one time, on desktop)

1. In Obsidian, install the **Obsidian Git** community plugin.
2. Create a private GitHub repo for your vault (or use an existing one).
3. In the Obsidian Git plugin settings, point it at your repo and enable auto-push.
4. On your phone, install **Obsidian Git** via the same vault (Obsidian Sync carries the plugin settings).

### Using it with Claude Code

Claude Code already has GitHub MCP tools. Once your vault is in a GitHub repo:

```
"Read my note Terraria Server Notes from my Obsidian vault repo"
```

Claude Code can fetch, read, edit, and push notes back to the repo.
Obsidian Git then pulls the update onto your phone automatically.

---

## Option 3 — Obsidian Local REST API + a tunnel (advanced)

Best for: real-time two-way access, running Claude Code against a live vault.

This requires a PC or Mac that stays running with Obsidian open.

1. In Obsidian (desktop), install the **Local REST API** community plugin.
2. Note the API key and port shown in the plugin settings (default: `27123`).
3. Install **ngrok** or **Cloudflare Tunnel** on the same machine to expose the port.
4. In Claude Code, configure an MCP server entry pointing at the tunnel URL.

Example `.claude/settings.json` MCP entry:
```json
{
  "mcpServers": {
    "obsidian": {
      "type": "http",
      "url": "https://YOUR_TUNNEL_URL",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

Claude Code can then list vaults, read notes, search, and write — all live.

> This only works while your desktop Obsidian is running. Not suitable for phone-only setups.

---

## Which Option Should You Use?

| Situation | Best option |
|---|---|
| Quick one-off question about a note | Option 1 — paste |
| Regular use, want Claude to read/write vault | Option 2 — Obsidian Git |
| Power user, always have a desktop running | Option 3 — Local REST API |

---

## Obsidian Sync Note

Obsidian Sync keeps your vault content identical across all your devices.
It does **not** expose an API or network endpoint that external tools like Claude Code
can reach — it's device-to-device only. Options 2 and 3 above are the practical
bridges between Sync and Claude Code.
