#!/usr/bin/env bash
# start_local_terminal.sh — Launch a local terminal (ttyd) and embed in Wee Canvas
#
# Usage:
#   start_local_terminal.sh --canvas-session SESSION_ID [--cwd PATH] [--port PORT]
#
# Unlike the WebSSH terminal (which SSHes to a remote host), this opens a local
# bash shell directly on the host machine, starting in the specified directory.
#
# Environment:
#   CANVAS_HOST       — Hostname/IP for browser-accessible URLs (default: localhost)
#   CANVAS_PORT       — Wee Orchestrator API port (default: 8000)
#   LOCAL_TERM_PORT   — ttyd listen port (default: 8023)
#   SESSIONS_FILE     — Path to sessions.json for auto-detecting agent cwd

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────
CANVAS_HOST="${CANVAS_HOST:-localhost}"
CANVAS_PORT="${CANVAS_PORT:-8000}"
PORT="${LOCAL_TERM_PORT:-8023}"
CWD=""
CANVAS_SESSION=""
SESSIONS_FILE="${SESSIONS_FILE:-/opt/n8n-copilot-shim/.task-scheduler/sessions.json}"
DEFAULT_CWD="/opt"

# ── Parse args ────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --canvas-session) CANVAS_SESSION="$2"; shift 2 ;;
    --cwd)            CWD="$2"; shift 2 ;;
    --port)           PORT="$2"; shift 2 ;;
    --stop)
      echo "Stopping local terminal..."
      pids=$(lsof -ti ":${LOCAL_TERM_PORT:-8023}" 2>/dev/null || true)
      if [[ -n "$pids" ]]; then
        echo "$pids" | xargs kill 2>/dev/null || true
        echo "Stopped."
      else
        echo "No terminal running on port ${LOCAL_TERM_PORT:-8023}."
      fi
      exit 0
      ;;
    -h|--help)
      head -8 "$0" | tail -6
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$CANVAS_SESSION" ]]; then
  echo "Error: --canvas-session SESSION_ID is required"
  exit 1
fi

# ── Resolve working directory ─────────────────────────────────────
if [[ -z "$CWD" ]]; then
  # Try to detect from active session
  if [[ -f "$SESSIONS_FILE" ]]; then
    DETECTED_CWD=$(python3 -c "
import json, sys
try:
    with open('$SESSIONS_FILE') as f:
        sessions = json.load(f)
    active = [s for s in sessions.values() if isinstance(s, dict) and s.get('identity')]
    if active:
        latest = max(active, key=lambda s: s.get('created_at', 0))
        cwd = latest.get('cwd', latest.get('working_directory', ''))
        if cwd:
            print(cwd)
            sys.exit()
except Exception:
    pass
" 2>/dev/null || true)

    if [[ -n "$DETECTED_CWD" && -d "$DETECTED_CWD" ]]; then
      CWD="$DETECTED_CWD"
      echo "Auto-detected agent working directory: $CWD"
    fi
  fi

  # Fallback to default
  if [[ -z "$CWD" ]]; then
    CWD="$DEFAULT_CWD"
    echo "Using default working directory: $CWD"
  fi
fi

if [[ ! -d "$CWD" ]]; then
  echo "Warning: Directory $CWD does not exist, falling back to $DEFAULT_CWD"
  CWD="$DEFAULT_CWD"
fi

# ── Verify ttyd is available ──────────────────────────────────────
if ! command -v ttyd &>/dev/null; then
  echo "Error: ttyd not found. Install it: sudo apt-get install -y ttyd"
  exit 1
fi

# ── TLS certificates (reuse webssh certs) ─────────────────────────
CERT_DIR="${XDG_RUNTIME_DIR:-/tmp}/webssh-certs"
CERT_FILE="$CERT_DIR/cert.pem"
KEY_FILE="$CERT_DIR/key.pem"

if [[ ! -f "$CERT_FILE" || ! -f "$KEY_FILE" ]]; then
  mkdir -p "$CERT_DIR"
  chmod 700 "$CERT_DIR"
  openssl req -x509 -newkey rsa:2048 -keyout "$KEY_FILE" -out "$CERT_FILE" \
    -days 3650 -nodes -subj "/CN=${CANVAS_HOST}" \
    -addext "subjectAltName=IP:127.0.0.1" 2>/dev/null
  echo "TLS cert generated at $CERT_DIR"
fi

# ── Kill any existing ttyd on this port ───────────────────────────
pids=$(lsof -ti ":$PORT" 2>/dev/null || true)
if [[ -n "$pids" ]]; then
  echo "Stopping existing process on port $PORT..."
  echo "$pids" | xargs kill 2>/dev/null || true
  sleep 1
fi

# ── Start ttyd ────────────────────────────────────────────────────
echo "Starting ttyd on port ${PORT} (HTTPS), cwd: ${CWD}..."
nohup ttyd \
  --port "$PORT" \
  --writable \
  --cwd "$CWD" \
  --ssl \
  --ssl-cert "$CERT_FILE" \
  --ssl-key "$KEY_FILE" \
  -t titleFixed="Local Terminal — ${CWD}" \
  -t fontSize=14 \
  -t theme='{"background":"#0d1117","foreground":"#c9d1d9","cursor":"#58a6ff"}' \
  bash \
  > /tmp/ttyd-local.log 2>&1 &

TTYD_PID=$!
echo "ttyd started (PID $TTYD_PID)"

# ── Wait for ttyd to be ready ─────────────────────────────────────
echo "Waiting for ttyd to be ready..."
for i in {1..10}; do
  if curl -sfk "https://127.0.0.1:${PORT}" &>/dev/null; then
    echo "  ttyd is ready."
    break
  fi
  sleep 1
done

# ── Push Wee Canvas iframe ────────────────────────────────────────
CANVAS_PY="/opt/n8n-copilot-shim/canvas.py"
if [[ ! -f "$CANVAS_PY" ]]; then
  echo "Warning: canvas.py not found — skipping canvas push"
  echo ""
  echo "Terminal URL: https://${CANVAS_HOST}:${PORT}"
  exit 0
fi

TTYD_URL="https://${CANVAS_HOST}:${PORT}"

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
  .toolbar .path {
    color:#8b949e; font-size:12px; background:#0d1117; padding:2px 10px;
    border-radius:4px; border:1px solid #30363d; flex:1;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  }
  .toolbar .badge {
    background:#238636; color:white; font-size:10px; padding:2px 8px;
    border-radius:10px; font-weight:600;
  }
  iframe { flex:1; border:none; width:100%; }
</style></head><body>
  <div class="toolbar">
    <span class="title">&#9889; Local Terminal</span>
    <span class="path">${CWD}</span>
    <span class="badge">LOCAL</span>
  </div>
  <iframe src="${TTYD_URL}" allow="clipboard-read; clipboard-write"></iframe>
</body></html>"""

c.push_html(html, height=600)
print("Canvas pushed for session ${CANVAS_SESSION}")
PYEOF

echo ""
echo "✅ Local terminal ready!"
echo "   URL: https://${CANVAS_HOST}:${PORT}"
echo "   Canvas: https://${CANVAS_HOST}:${CANVAS_PORT}/ui/?canvas=${CANVAS_SESSION}"
echo "   Working dir: ${CWD}"
echo ""
echo "To stop: $0 --stop"
