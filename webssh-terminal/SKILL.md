---
name: webssh-terminal
description: "Web-based terminal and browser tools for Wee Canvas: remote SSH terminal (WebSSH), local bash terminal (ttyd), and live browser window (noVNC). Embeds interactive panels in Wee Canvas iframes. Use when the user asks for a 'web terminal', 'browser window', 'local terminal', 'browser SSH', 'webssh', or wants to interact with a host through the WebUI canvas."
---

# WebSSH Terminal Skill

Three web-based tools embedded in Wee Canvas iframes:

| Tool | Script | Port | Purpose |
|------|--------|------|---------|
| **WebSSH** (Remote SSH) | `start_webssh.sh` | 8022 | SSH into remote hosts via browser |
| **Local Terminal** | `start_local_terminal.sh` | 8023 | Local bash shell on the host |
| **Browser Window** | `start_browser_window.sh` | 6080 | Live browser via noVNC |

All three use HTTPS with self-signed certs (auto-generated at runtime, never committed).

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

## 3. Browser Window (noVNC)

Runs a full browser (Chromium) in a virtual framebuffer and streams it to the canvas
via noVNC. Users can interact with the browser — click, type, scroll — all within
the Wee Canvas iframe.

### Architecture

```
Xvfb (:99) → Chromium → x11vnc → websockify/noVNC → Canvas iframe
```

### Requirements

- `Xvfb`: virtual framebuffer (`sudo apt-get install -y xvfb`)
- `x11vnc`: X11 to VNC bridge (`sudo apt-get install -y x11vnc`)
- `chromium-browser` or `google-chrome`
- noVNC + websockify (noVNC at `/opt/noVNC/`, websockify via pip)

### Quick Start

```bash
# Open Google in a browser window on canvas
bash /opt/pot-o-skills/webssh-terminal/scripts/start_browser_window.sh \
  --canvas-session SESSION_ID --url https://www.google.com

# Open a specific URL
bash /opt/pot-o-skills/webssh-terminal/scripts/start_browser_window.sh \
  --canvas-session SESSION_ID --url https://github.com

# Custom ports
bash /opt/pot-o-skills/webssh-terminal/scripts/start_browser_window.sh \
  --canvas-session SESSION_ID --url https://example.com \
  --vnc-port 5950 --novnc-port 6090 --display :50
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NOVNC_PORT` | `6080` | noVNC WebSocket proxy port |
| `VNC_PORT` | `5999` | x11vnc listen port |
| `DISPLAY_NUM` | `99` | Xvfb display number |
| `NOVNC_DIR` | `/opt/noVNC` | noVNC installation directory |
| `RESOLUTION` | `1280x900x24` | Virtual display resolution |
| `BROWSER_BIN` | *(auto-detect)* | Browser binary path |
| `CANVAS_HOST` | `localhost` | Public IP for browser URLs |
| `CANVAS_PORT` | `8000` | Wee Orchestrator API port |

### Manage

```bash
tail -f /tmp/novnc-browser.log   # noVNC logs
tail -f /tmp/x11vnc-browser.log  # x11vnc logs

# Stop all components
bash start_browser_window.sh --stop
```

---

## Workflow: Agent Launches a Terminal/Browser

1. **Resolve canvas session** — open a new Wee Canvas or reuse the user's active session
2. **Set CANVAS_HOST** to the host's IP/hostname accessible from the user's browser
3. **Run the appropriate script** with `--canvas-session SESSION_ID`
4. **Report the canvas URL**: `https://CANVAS_HOST:CANVAS_PORT/ui/?canvas=SESSION_ID`

## Port Allocation

| Port | Service | Script |
|------|---------|--------|
| 8022 | WebSSH (remote SSH) | `start_webssh.sh` |
| 8023 | ttyd (local terminal) | `start_local_terminal.sh` |
| 6080 | noVNC (browser window) | `start_browser_window.sh` |
| 5999 | x11vnc (internal, VNC) | `start_browser_window.sh` |

## Security Notes

- All services use HTTPS with self-signed certs (generated at runtime in `/tmp/webssh-certs/`)
- TLS certs are **never committed** to the repository
- `--xsrf=false` and `--origin='*'` are set for iframe embedding — only expose on trusted/VPN networks
- webssh does NOT persist SSH keys — users supply them per session in the browser
- ttyd runs as the user who started the script — restrict access to trusted networks
- noVNC has no built-in auth — rely on network-level access control
- Do NOT commit SSH keys, passwords, host IPs, or credentials to this skill

