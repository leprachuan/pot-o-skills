#!/usr/bin/env bash
# start_browser_window.sh — Launch a browser in a virtual display and expose via noVNC
#
# Usage:
#   start_browser_window.sh --canvas-session SESSION_ID --url URL [--display :99] [--vnc-port 5999] [--novnc-port 6080]
#
# Stack: Xvfb → Chrome/Chromium → x11vnc → websockify (noVNC) → Canvas iframe
#
# Environment:
#   CANVAS_HOST   — Hostname/IP for browser-accessible URLs (default: localhost)
#   CANVAS_PORT   — Wee Orchestrator API port (default: 8000)
#   NOVNC_PORT    — noVNC WebSocket proxy port (default: 6080)
#   VNC_PORT      — x11vnc listen port (default: 5999)
#   DISPLAY_NUM   — Xvfb display number (default: 99)
#   BROWSER_BIN   — Browser binary (default: auto-detect)
#   NOVNC_DIR     — noVNC installation directory (default: /opt/noVNC)
#   RESOLUTION    — Virtual display resolution (default: 1280x900x24)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/browser-window.log"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# ── Defaults ──────────────────────────────────────────────────────
CANVAS_HOST="${CANVAS_HOST:-localhost}"
CANVAS_PORT="${CANVAS_PORT:-8000}"
NOVNC_PORT="${NOVNC_PORT:-6080}"
VNC_PORT="${VNC_PORT:-5999}"
DISPLAY_NUM="${DISPLAY_NUM:-99}"
NOVNC_DIR="${NOVNC_DIR:-/opt/noVNC}"
RESOLUTION="${RESOLUTION:-1280x900x24}"
BROWSER_BIN="${BROWSER_BIN:-}"
URL=""
CANVAS_SESSION=""
PIDFILE="/tmp/browser-window-pids"

# ── Parse args ────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --canvas-session) CANVAS_SESSION="$2"; shift 2 ;;
    --url)            URL="$2"; shift 2 ;;
    --display)        DISPLAY_NUM="${2#:}"; shift 2 ;;
    --vnc-port)       VNC_PORT="$2"; shift 2 ;;
    --novnc-port)     NOVNC_PORT="$2"; shift 2 ;;
    --stop)
      log "Stopping browser window..."
      if [[ -f "$PIDFILE" ]]; then
        while read -r pid; do
          kill "$pid" 2>/dev/null || true
        done < "$PIDFILE"
        rm -f "$PIDFILE"
      fi
      log "Stopped."
      exit 0
      ;;
    -h|--help)
      head -10 "$0" | tail -8
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$CANVAS_SESSION" ]]; then
  echo "Error: --canvas-session SESSION_ID is required"
  exit 1
fi

if [[ -z "$URL" ]]; then
  URL="https://www.google.com"
fi

# ── Auto-detect browser ──────────────────────────────────────────
if [[ -z "$BROWSER_BIN" ]]; then
  for candidate in google-chrome chromium-browser chromium; do
    if command -v "$candidate" &>/dev/null; then
      BROWSER_BIN="$candidate"
      break
    fi
  done
fi

if [[ -z "$BROWSER_BIN" ]]; then
  echo "Error: No browser found. Install google-chrome or chromium-browser."
  exit 1
fi

# ── Install missing dependencies ──────────────────────────────────
install_if_missing() {
  local cmd="$1" pkg="$2"
  if ! command -v "$cmd" &>/dev/null; then
    log "Installing $pkg..."
    sudo apt-get install -y "$pkg" >/dev/null 2>&1
  fi
}

install_if_missing Xvfb xvfb
install_if_missing x11vnc x11vnc

if ! command -v websockify &>/dev/null; then
  log "Installing websockify..."
  pip3 install websockify >/dev/null 2>&1
fi

if [[ ! -d "$NOVNC_DIR" ]]; then
  log "Cloning noVNC to $NOVNC_DIR..."
  git clone --depth 1 https://github.com/novnc/noVNC "$NOVNC_DIR" >/dev/null 2>&1
fi

# ── Verify dependencies ──────────────────────────────────────────
for cmd in Xvfb x11vnc websockify; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: $cmd not found after install attempt."
    exit 1
  fi
done

if [[ ! -d "$NOVNC_DIR" ]]; then
  echo "Error: noVNC directory not found at $NOVNC_DIR"
  exit 1
fi

# ── TLS certificates (runtime-only, never committed) ─────────────
CERT_DIR="${XDG_RUNTIME_DIR:-/tmp}/browser-window-certs"
CERT_FILE="$CERT_DIR/cert.pem"
KEY_FILE="$CERT_DIR/key.pem"
COMBINED_PEM="$CERT_DIR/combined.pem"

if [[ ! -f "$CERT_FILE" || ! -f "$KEY_FILE" ]]; then
  mkdir -p "$CERT_DIR"
  chmod 700 "$CERT_DIR"
  openssl req -x509 -newkey rsa:2048 -keyout "$KEY_FILE" -out "$CERT_FILE" \
    -days 3650 -nodes -subj "/CN=${CANVAS_HOST}" \
    -addext "subjectAltName=IP:127.0.0.1" 2>/dev/null
  log "TLS cert generated at $CERT_DIR"
fi

# websockify --cert expects a combined PEM (cert + key)
if [[ ! -f "$COMBINED_PEM" ]] || [[ "$CERT_FILE" -nt "$COMBINED_PEM" ]]; then
  cat "$CERT_FILE" "$KEY_FILE" > "$COMBINED_PEM"
fi

# ── Clean up any previous instances on these ports ────────────────
cleanup_port() {
  local port=$1
  local pids
  pids=$(lsof -ti ":$port" 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    log "Cleaning up existing process on port $port..."
    echo "$pids" | xargs kill 2>/dev/null || true
    sleep 1
  fi
}

cleanup_port "$VNC_PORT"
cleanup_port "$NOVNC_PORT"

# Kill any existing Xvfb on this display
if [[ -f "/tmp/.X${DISPLAY_NUM}-lock" ]]; then
  log "Cleaning up existing Xvfb on :${DISPLAY_NUM}..."
  kill "$(cat /tmp/.X${DISPLAY_NUM}-lock 2>/dev/null | tr -d ' ')" 2>/dev/null || true
  rm -f "/tmp/.X${DISPLAY_NUM}-lock" "/tmp/.X11-unix/X${DISPLAY_NUM}" 2>/dev/null || true
  sleep 1
fi

# Track PIDs for cleanup
> "$PIDFILE"

# ── Step 1: Start Xvfb ───────────────────────────────────────────
log "Starting Xvfb on :${DISPLAY_NUM} (${RESOLUTION})..."
Xvfb ":${DISPLAY_NUM}" -screen 0 "${RESOLUTION}" -ac +extension GLX +render -noreset &
XVFB_PID=$!
echo "$XVFB_PID" >> "$PIDFILE"
sleep 1

if ! kill -0 "$XVFB_PID" 2>/dev/null; then
  echo "Error: Xvfb failed to start"
  exit 1
fi
log "  Xvfb started (PID $XVFB_PID)"

export DISPLAY=":${DISPLAY_NUM}"

# ── Step 2: Start browser ────────────────────────────────────────
log "Starting ${BROWSER_BIN} on :${DISPLAY_NUM} → ${URL}..."
"$BROWSER_BIN" \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --no-first-run \
  --disable-default-apps \
  --disable-extensions \
  --start-maximized \
  --window-size=1280,900 \
  "$URL" &>/dev/null &
BROWSER_PID=$!
echo "$BROWSER_PID" >> "$PIDFILE"
sleep 2

log "  Browser started (PID $BROWSER_PID)"

# ── Step 3: Start x11vnc ─────────────────────────────────────────
log "Starting x11vnc on :${DISPLAY_NUM} → port ${VNC_PORT}..."
x11vnc \
  -display ":${DISPLAY_NUM}" \
  -rfbport "$VNC_PORT" \
  -shared \
  -forever \
  -nopw \
  -noxdamage \
  -cursor arrow \
  -bg \
  -o /tmp/x11vnc.log

log "  x11vnc started on port $VNC_PORT"

# ── Step 4: Start noVNC (websockify) ─────────────────────────────
log "Starting noVNC websocket proxy on port ${NOVNC_PORT} → VNC ${VNC_PORT}..."
nohup "$NOVNC_DIR/utils/novnc_proxy" \
  --listen "${NOVNC_PORT}" \
  --vnc "localhost:${VNC_PORT}" \
  --cert "$CERT_FILE" \
  --key "$KEY_FILE" \
  --ssl-only \
  --web "$NOVNC_DIR" \
  > /tmp/browser-window.log 2>&1 &
NOVNC_PID=$!
echo "$NOVNC_PID" >> "$PIDFILE"
sleep 2

log "  noVNC proxy started (PID $NOVNC_PID)"

# ── Wait for noVNC to be ready ────────────────────────────────────
log "Waiting for noVNC to be ready..."
for i in {1..15}; do
  if curl -sfk "https://127.0.0.1:${NOVNC_PORT}" &>/dev/null; then
    log "  noVNC is ready."
    break
  fi
  sleep 1
done

# ── Step 5: Push Wee Canvas iframe ───────────────────────────────
CANVAS_PY="/opt/n8n-copilot-shim/canvas.py"
if [[ ! -f "$CANVAS_PY" ]]; then
  log "Warning: canvas.py not found — skipping canvas push"
  echo ""
  echo "noVNC URL: https://${CANVAS_HOST}:${NOVNC_PORT}/vnc.html?autoconnect=true&resize=remote"
  exit 0
fi

NOVNC_URL="https://${CANVAS_HOST}:${NOVNC_PORT}/vnc.html?autoconnect=true&resize=remote&reconnect=true&reconnect_delay=2000"

python3 - <<PYEOF
import sys
sys.path.insert(0, '/opt/n8n-copilot-shim')
from canvas import Canvas

c = Canvas(session_id="${CANVAS_SESSION}")
html = """<!DOCTYPE html>
<html><head><style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#0d1117; font-family:monospace; height:100vh; display:flex; flex-direction:column; }
  .toolbar {
    padding:8px 16px; background:#161b22; border-bottom:1px solid #30363d;
    display:flex; align-items:center; gap:12px;
  }
  .toolbar .title { color:#58a6ff; font-size:14px; font-weight:600; }
  .toolbar .url { color:#8b949e; font-size:12px; flex:1; overflow:hidden; text-overflow:ellipsis; }
  .toolbar .badge {
    background:#238636; color:white; font-size:10px; padding:2px 8px;
    border-radius:10px; font-weight:600;
  }
  iframe { flex:1; border:none; width:100%; }
</style></head><body>
  <div class="toolbar">
    <span class="title">&#127760; Browser Window</span>
    <span class="url">${URL}</span>
    <span class="badge">LIVE</span>
  </div>
  <iframe src="${NOVNC_URL}" allow="clipboard-read; clipboard-write"></iframe>
</body></html>"""

c.push_html(html, height=700)
print("Canvas pushed for session ${CANVAS_SESSION}")
print("Direct noVNC: ${NOVNC_URL}")
PYEOF

echo ""
log "✅ Browser window ready!"
echo "   noVNC: https://${CANVAS_HOST}:${NOVNC_PORT}/vnc.html?autoconnect=true&resize=remote"
echo "   Canvas: https://${CANVAS_HOST}:${CANVAS_PORT}/ui/?canvas=${CANVAS_SESSION}"
echo ""
echo "To stop: $0 --stop"
echo "PIDs saved to: $PIDFILE"
