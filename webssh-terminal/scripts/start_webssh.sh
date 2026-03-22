#!/usr/bin/env bash
# start_webssh.sh — Start a webssh server and optionally push a Wee Canvas iframe
#
# Usage:
#   start_webssh.sh [--port PORT] [--host HOST] [--canvas] [--canvas-session SESSION_ID]
#
# Defaults:
#   PORT=8022
#   HOST=0.0.0.0
#
# Environment:
#   CANVAS_HOST  — Hostname/IP for browser-accessible URL (default: 100.124.186.75)
#   CANVAS_PORT  — Wee Orchestrator port (default: 8000)

set -euo pipefail

PORT="${WEBSSH_PORT:-8022}"
BIND_HOST="${WEBSSH_BIND:-0.0.0.0}"
CANVAS_HOST="${CANVAS_HOST:-100.124.186.75}"
CANVAS_PORT="${CANVAS_PORT:-8000}"
DO_CANVAS=false
CANVAS_SESSION=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --port) PORT="$2"; shift 2 ;;
    --host) BIND_HOST="$2"; shift 2 ;;
    --canvas) DO_CANVAS=true; shift ;;
    --canvas-session) CANVAS_SESSION="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

WSSH_BIN="$(which wssh 2>/dev/null || echo "$HOME/.local/bin/wssh")"

if [[ ! -x "$WSSH_BIN" ]]; then
  echo "webssh not found. Installing..."
  pip3 install webssh
  WSSH_BIN="$(which wssh)"
fi

# Kill any existing wssh on this port
if lsof -ti ":$PORT" &>/dev/null; then
  echo "Stopping existing wssh on port $PORT..."
  kill "$(lsof -ti ":$PORT")" 2>/dev/null || true
  sleep 1
fi

echo "Starting webssh on ${BIND_HOST}:${PORT}..."
nohup "$WSSH_BIN" \
  --address="$BIND_HOST" \
  --port="$PORT" \
  --xsrf=false \
  --origin='*' \
  >> /tmp/webssh.log 2>&1 &

WSSH_PID=$!
echo "webssh started (PID $WSSH_PID)"
echo "Access: http://${CANVAS_HOST}:${PORT}"

# Wait for it to be ready
for i in {1..10}; do
  if curl -sf "http://127.0.0.1:${PORT}" &>/dev/null; then
    echo "webssh is ready."
    break
  fi
  sleep 1
done

if [[ "$DO_CANVAS" == "true" && -n "$CANVAS_SESSION" ]]; then
  CANVAS_PY="/opt/n8n-copilot-shim/canvas.py"
  if [[ ! -f "$CANVAS_PY" ]]; then
    echo "Warning: canvas.py not found at $CANVAS_PY — skipping canvas push"
    exit 0
  fi

  WEBSSH_URL="http://${CANVAS_HOST}:${PORT}"

  python3 - <<PYEOF
import sys
sys.path.insert(0, '/opt/n8n-copilot-shim')
from canvas import Canvas

c = Canvas(session_id="${CANVAS_SESSION}")
html = """
<div style="display:flex;flex-direction:column;height:100vh;background:#0d1117;font-family:monospace;">
  <div style="padding:10px 16px;background:#161b22;border-bottom:1px solid #30363d;display:flex;align-items:center;gap:12px;">
    <span style="color:#58a6ff;font-size:14px;font-weight:600;">&#9889; WebSSH Terminal</span>
    <span style="color:#8b949e;font-size:12px;">&#8594; ${CANVAS_HOST}</span>
  </div>
  <iframe
    src="${WEBSSH_URL}"
    style="flex:1;border:none;width:100%;height:100%;"
    allow="clipboard-read; clipboard-write"
  ></iframe>
</div>
"""
c.push_html(html, height=800)
print("Canvas pushed. URL: https://${CANVAS_HOST}:${CANVAS_PORT}/ui/?canvas=${CANVAS_SESSION}")
PYEOF
fi
