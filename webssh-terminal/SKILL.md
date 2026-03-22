---
name: webssh-terminal
description: "Web-based terminal tools for Wee Canvas: remote SSH terminal (WebSSH) and local bash terminal (ttyd). Embeds interactive terminal panels in Wee Canvas iframes. Use when the user asks for a 'web terminal', 'local terminal', 'browser SSH', 'webssh', or wants to interact with a host through the WebUI canvas. For browser windows, see the browser-window skill."
---

# WebSSH Terminal Skill

Two web-based terminal tools embedded in Wee Canvas iframes:

| Tool | Script | Port | Purpose |
|------|--------|------|---------|
| **WebSSH** (Remote SSH) | `start_webssh.sh` | 8022 | SSH into remote hosts via browser |
| **Local Terminal** | `start_local_terminal.sh` | 8023 | Local bash shell on the host |

Both use HTTPS with self-signed certs (auto-generated at runtime, never committed).

> **Note:** The browser window feature (noVNC) has been moved to the standalone **browser-window** skill.

---

## 1. Remote SSH Terminal (WebSSH)

Starts a `webssh` server (Python, MIT license) for interactive SSH sessions in the browser.

### Requirements

- `webssh` package: `pip3 install webssh` (binary: `wssh`)
- SSH key configured on the target host
- Port 8022 open (or custom via `--port`)

### Quick Start

```bash
# Start webssh and push to canvas
bash /opt/pot-o-skills/webssh-terminal/scripts/start_webssh.sh \
  --canvas --canvas-session SESSION_ID

# Custom port
bash /opt/pot-o-skills/webssh-terminal/scripts/start_webssh.sh \
  --port 8033 --canvas --canvas-session SESSION_ID
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBSSH_PORT` | `8022` | Port to bind webssh on |
| `WEBSSH_BIND` | `0.0.0.0` | Bind address |
| `CANVAS_HOST` | `localhost` | Public/Tailscale IP for browser-accessible URLs |
| `CANVAS_PORT` | `8000` | Wee Orchestrator API port |

### Connecting

In the webssh browser UI:
- **Hostname**: target host IP or FQDN
- **Port**: 22 (default SSH)
- **Username**: SSH user on target
- **Auth**: select **Private Key** and paste key (per-session only, never stored)

### Manage

```bash
lsof -ti :8022            # check if running
tail -f /tmp/webssh.log   # view logs
kill $(lsof -ti :8022)    # stop
```

---

## 2. Local Terminal (ttyd)

Opens a local bash shell directly on the host, starting in the specified working directory. Unlike WebSSH, this does **not** SSH anywhere — it runs a shell directly.

### Requirements

- `ttyd` package: `sudo apt-get install -y ttyd`
- Port 8023 open (or custom via `--port`)

### Quick Start

```bash
# Start in default directory and push to canvas
bash /opt/pot-o-skills/webssh-terminal/scripts/start_local_terminal.sh \
  --canvas-session SESSION_ID

# Start in a specific directory
bash /opt/pot-o-skills/webssh-terminal/scripts/start_local_terminal.sh \
  --canvas-session SESSION_ID --cwd /opt/n8n-copilot-shim

# Custom port
bash /opt/pot-o-skills/webssh-terminal/scripts/start_local_terminal.sh \
  --canvas-session SESSION_ID --port 9090
```

### Auto-Detect Working Directory

If `--cwd` is not specified, the script attempts to read the active agent session
from `sessions.json` and use that session's working directory. Falls back to `/opt`.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_TERM_PORT` | `8023` | Port for ttyd |
| `CANVAS_HOST` | `localhost` | Public IP for browser URLs |
| `CANVAS_PORT` | `8000` | Wee Orchestrator API port |
| `SESSIONS_FILE` | `/opt/n8n-copilot-shim/.task-scheduler/sessions.json` | Sessions file for auto-detecting cwd |

### Manage

```bash
lsof -ti :8023              # check if running
tail -f /tmp/ttyd-local.log # view logs
kill $(lsof -ti :8023)      # stop
# or:
bash start_local_terminal.sh --stop
```

---

## Workflow: Agent Launches a Terminal

1. **Resolve canvas session** — open a new Wee Canvas or reuse the user's active session
2. **Set CANVAS_HOST** to the host's IP/hostname accessible from the user's browser
3. **Run the appropriate script** with `--canvas-session SESSION_ID`
4. **Report the canvas URL**: `https://CANVAS_HOST:CANVAS_PORT/ui/?canvas=SESSION_ID`

## Port Allocation

| Port | Service | Script |
|------|---------|--------|
| 8022 | WebSSH (remote SSH) | `start_webssh.sh` |
| 8023 | ttyd (local terminal) | `start_local_terminal.sh` |

## Security Notes

- All services use HTTPS with self-signed certs (generated at runtime in `/tmp/webssh-certs/`)
- TLS certs are **never committed** to the repository
- `--xsrf=false` and `--origin='*'` are set for iframe embedding — only expose on trusted/VPN networks
- webssh does NOT persist SSH keys — users supply them per session in the browser
- ttyd runs as the user who started the script — restrict access to trusted networks
- Do NOT commit SSH keys, passwords, host IPs, or credentials to this skill

