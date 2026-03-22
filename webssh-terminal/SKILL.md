---
name: webssh-terminal
description: Launch a WebSSH terminal server and embed it in a Wee Canvas iframe so the user gets an in-browser SSH terminal. Uses SSH key authentication — no passwords or credentials stored. Use when the user asks for a "web terminal", "browser SSH", "webssh", or wants to SSH into a host through the WebUI canvas.
---

# WebSSH Terminal

Starts a `webssh` server (Python, MIT license) and optionally pushes an iframe canvas to the Wee Orchestrator WebUI so the user gets an interactive SSH terminal in their browser.

## Requirements

- `webssh` package: `pip3 install webssh` (binary: `wssh`)
- SSH key already configured on the target host for the connecting user
- Port 8022 open on the host running webssh (or choose another port)

## Quick Start

```bash
# Start webssh on default port 8022
bash /opt/pot-o-skills/webssh-terminal/scripts/start_webssh.sh

# Start and push a Wee Canvas iframe
bash /opt/pot-o-skills/webssh-terminal/scripts/start_webssh.sh \
  --canvas \
  --canvas-session SESSION_ID

# Custom port
bash /opt/pot-o-skills/webssh-terminal/scripts/start_webssh.sh --port 8033 --canvas --canvas-session SESSION_ID
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBSSH_PORT` | `8022` | Port to bind webssh on |
| `WEBSSH_BIND` | `0.0.0.0` | Bind address |
| `CANVAS_HOST` | *(required)* | Public/Tailscale IP of the host for browser-accessible URLs |
| `CANVAS_PORT` | `8000` | Wee Orchestrator API port |

## Workflow When User Asks for a WebSSH Terminal

1. **Resolve canvas session** — open a new Wee Canvas or reuse the user's active session
2. **Run the script** with `--canvas --canvas-session SESSION_ID`
3. **Report the canvas URL** to the user: `https://CANVAS_HOST:CANVAS_PORT/ui/?canvas=SESSION_ID`
4. The user connects in the iframe: enters hostname, username, and uses their SSH key

## Connecting to a Host

In the webssh browser UI the user fills in:
- **Hostname**: target host IP or FQDN
- **Port**: 22 (default SSH)
- **Username**: the SSH user on the target host
- **Auth**: select **Private Key** and paste the relevant private key

No passwords or keys are stored. The key is used per-session in the browser only.

## Managing the Server

```bash
# Check if running
lsof -ti :8022

# View logs
tail -f /tmp/webssh.log

# Stop
kill $(lsof -ti :8022)
```

## Security Notes

- `--xsrf=false` and `--origin='*'` are set for iframe embedding — only expose on trusted/VPN networks
- webssh does NOT persist SSH keys — users supply them per session in the browser
- For production use, put webssh behind an authenticated reverse proxy
- Do NOT commit SSH keys, passwords, or host credentials to this skill

