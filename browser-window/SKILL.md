---
name: browser-window
description: "Launch a live interactive browser window inside Wee Canvas via noVNC. Runs Chrome/Chromium in a virtual framebuffer (Xvfb) and streams it over a WebSocket proxy. Use when the user asks for a 'browser window', 'live browser', 'noVNC', 'remote browser', 'browser in canvas', or 'web browser subwindow'."
---

# Browser Window Skill

Run a full interactive browser (Chrome/Chromium) inside a Wee Canvas iframe. Users can
click, type, and scroll — all within the WebUI canvas panel.

## Architecture

```
Xvfb (:99) → Chrome/Chromium → x11vnc → websockify/noVNC → Wee Canvas iframe
```

| Component | Role |
|-----------|------|
| **Xvfb** | Virtual X11 framebuffer (headless display) |
| **Chrome/Chromium** | Full browser running in the virtual display |
| **x11vnc** | Bridges X11 display to VNC protocol |
| **websockify / noVNC** | Proxies VNC over WebSocket with HTTPS for the browser |
| **Wee Canvas** | Embeds the noVNC page in an iframe pushed to the user |

## Requirements

| Dependency | Install |
|------------|---------|
| `Xvfb` | `sudo apt-get install -y xvfb` |
| `x11vnc` | `sudo apt-get install -y x11vnc` |
| `websockify` | `pip3 install websockify` |
| `noVNC` | Clone to `/opt/noVNC`: `git clone https://github.com/novnc/noVNC /opt/noVNC` |
| Browser | `google-chrome`, `chromium-browser`, or `chromium` (auto-detected) |

> **Note:** The script will attempt to install missing dependencies automatically.

## Quick Start

```bash
# Open a URL in the browser window and push to canvas
bash /opt/pot-o-skills/browser-window/scripts/start_browser_window.sh \
  --canvas-session SESSION_ID --url https://example.com

# Default URL (Google) with custom ports
bash /opt/pot-o-skills/browser-window/scripts/start_browser_window.sh \
  --canvas-session SESSION_ID \
  --vnc-port 5950 --novnc-port 6090 --display :50
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--canvas-session ID` | **Yes** | Wee Canvas session to push the iframe to |
| `--url URL` | No | URL to open (default: `https://www.google.com`) |
| `--display :N` | No | Xvfb display number (default: `:99`) |
| `--vnc-port PORT` | No | x11vnc listen port (default: `5999`) |
| `--novnc-port PORT` | No | noVNC WebSocket proxy port (default: `6080`) |
| `--stop` | No | Kill all running browser-window components |
| `-h`, `--help` | No | Show usage |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CANVAS_HOST` | `localhost` | Hostname/IP the user's browser can reach |
| `CANVAS_PORT` | `8000` | Wee Orchestrator API port |
| `NOVNC_PORT` | `6080` | noVNC WebSocket proxy port |
| `VNC_PORT` | `5999` | x11vnc listen port |
| `DISPLAY_NUM` | `99` | Xvfb display number |
| `NOVNC_DIR` | `/opt/noVNC` | noVNC installation directory |
| `RESOLUTION` | `1280x900x24` | Virtual display resolution (WxHxDepth) |
| `BROWSER_BIN` | *(auto-detect)* | Browser binary path override |

## Port Allocation

| Port | Service |
|------|---------|
| 6080 | noVNC WebSocket proxy (user-facing) |
| 5999 | x11vnc (internal VNC) |

## Manage

```bash
# View logs
tail -f /tmp/browser-window.log   # noVNC / startup logs
tail -f /tmp/x11vnc.log           # x11vnc logs

# Stop all components
bash /opt/pot-o-skills/browser-window/scripts/start_browser_window.sh --stop
```

## Workflow: Agent Launches a Browser Window

1. **Resolve canvas session** — open a new Wee Canvas or reuse the user's active session
2. **Set `CANVAS_HOST`** to the host's IP/hostname accessible from the user's browser
3. **Run the script** with `--canvas-session SESSION_ID --url URL`
4. **Report the canvas URL**: `https://CANVAS_HOST:CANVAS_PORT/ui/?canvas=SESSION_ID`

## Security Notes

- HTTPS with **self-signed certs** generated at runtime in `${XDG_RUNTIME_DIR:-/tmp}/browser-window-certs/`
- TLS certs are **never committed** to the repository
- noVNC has no built-in authentication — rely on network-level access control (VPN, firewall)
- Only expose on trusted networks
- Do **NOT** commit IPs, passwords, API keys, or credentials to this skill
