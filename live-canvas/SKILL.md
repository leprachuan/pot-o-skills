---
name: live-canvas
description: >
  Live visual canvas for agents. Use when running multi-step tasks (deploys, installs, batch jobs),
  gathering config from the user (forms), showing plan approval (flowchart + buttons), or displaying
  live dashboards (metrics, charts, tables). The canvas opens a browser panel that updates in real
  time as the agent pushes components over WebSocket. Users can click buttons or submit forms and
  the agent receives the action. Server auto-starts on first use.
metadata:
  keywords: [canvas, visual, ui, dashboard, progress, form, plan, chart, board, task, deploy, config, interactive]
  port: 18793
  templates: [progress_board, data_dashboard, config_form, plan_view]
---

# Live Canvas Skill 🍀

Give any agent a live visual workspace. Instead of walls of markdown, push rich interactive panels—progress boards, dashboards, forms, and plan diagrams—that update in real time as work progresses. Users can click buttons and submit forms; the agent receives those actions as structured responses.

## When to Use

| Trigger | Use This Template |
|---|---|
| Running a multi-step task (deploy, install, build) | `progress_board` |
| Displaying metrics, charts, or table data | `data_dashboard` |
| Collecting config/settings from the user | `config_form` |
| Showing a plan and asking for approval | `plan_view` |

## Quick Start

```python
import sys
sys.path.insert(0, '/opt/skills/live-canvas/claude/implementation')
from canvas import Canvas

c = Canvas()     # auto-generates session ID; auto-starts server
c.open()         # opens http://localhost:18793?session=<id> in browser
```

## API Reference

```python
c.render(components: list)                # full re-render
c.render_template(name, data)             # render a built-in template
c.update(node_id, changes)               # partial update (live, no flicker)
c.clear()                                # wipe canvas
c.open()                                 # open browser tab
action = c.wait_for_action(timeout=60)   # block until user clicks
```

`wait_for_action` returns a dict:
```python
{"type": "action", "action_id": "approve", "data": {...}, "session_id": "...", "timestamp": "..."}
# or on timeout:
{"type": "timeout"}
```

---

## Template 1: `progress_board`

Kanban board showing Todo / Running / Done columns with an overall progress bar.

**Use for:** deployments, installs, batch jobs, any multi-step workflow.

```python
c.render_template("progress_board", {
    "title": "Deploy v2.1",
    "elapsed": "3m 12s",         # optional
    "steps": [
        {"name": "Pull repo",      "status": "done"},
        {"name": "npm build",      "status": "running"},
        {"name": "Restart svc",    "status": "pending"},
        {"name": "Health check",   "status": "pending"},
    ]
})

# Live update a step without full re-render:
c.update("step-1", {"status": "done"})    # index-based id
c.update("overall-progress", {"pct": 75})
```

Status values: `done`, `running`, `pending`, `error`, `skip`

---

## Template 2: `data_dashboard`

Metrics row + optional line chart + optional table.

**Use for:** server status, Home Assistant devices, GitHub stats, monitoring.

```python
c.render_template("data_dashboard", {
    "title": "Server Status",
    "metrics": [
        {"label": "CPU",  "value": "42%",  "trend": "up"},
        {"label": "RAM",  "value": "6.1 GB"},
        {"label": "Disk", "value": "78%",  "trend": "down"},
        {"label": "Svcs", "value": "4/4"},
    ],
    "chart": {                             # optional
        "label": "CPU last 1h",
        "labels": ["10m", "20m", "30m", "40m", "50m", "60m"],
        "datasets": [{"label": "CPU %", "data": [30, 45, 42, 55, 48, 42]}],
    },
    "table": {                             # optional
        "headers": ["Process", "CPU", "MEM"],
        "rows": [["node", "12%", "400 MB"], ["python", "5%", "120 MB"]],
    },
})
```

---

## Template 3: `config_form`

Dynamic form rendered from a field schema. Returns submitted values.

**Use for:** collecting settings, rules, credentials, preferences from the user.

```python
c.render_template("config_form", {
    "title": "Email Triage Rules",
    "description": "Configure how incoming emails are processed.",
    "fields": [
        {"name": "sender_filter", "label": "Sender filter", "type": "text",     "placeholder": "e.g. @spam.com"},
        {"name": "action",        "label": "Action",         "type": "select",   "options": ["Move", "Delete", "Flag"]},
        {"name": "notify",        "label": "Notify me",      "type": "checkbox", "default": True},
    ],
    "submit_label": "Apply Rules",
    "cancel_label": "Cancel",
})

action = c.wait_for_action(timeout=120)
if action["action_id"] == "submit":
    values = action["data"]   # {"sender_filter": "...", "action": "...", "notify": True}
```

---

## Template 4: `plan_view`

Mermaid.js flowchart + Approve / Cancel buttons.

**Use for:** showing a plan before executing, getting explicit user approval.

```python
c.render_template("plan_view", {
    "title": "Rotate SSL Certificates",
    "description": "This will renew and deploy 3 certificates.",
    "mermaid": """flowchart TD
  A[Check expiry] --> B{Expired?}
  B -->|Yes| C[Generate new cert]
  B -->|No| D[Skip]
  C --> E[Deploy to nginx]
  E --> F[Restart service]""",
    "approve_label": "Execute Plan",
    "cancel_label": "Cancel",
})

action = c.wait_for_action(timeout=300)
if action.get("action_id") == "approve":
    # proceed with execution
    pass
```

---

## Building Custom Component Trees

For full control, pass a component tree to `render()`:

```python
c.render([
    {"type": "heading", "level": 2, "text": "My Dashboard"},
    {"type": "row", "children": [
        {"type": "metric", "id": "cpu-metric", "label": "CPU", "value": "42%"},
        {"type": "metric", "id": "ram-metric", "label": "RAM", "value": "8 GB"},
    ]},
    {"type": "progress", "id": "job-progress", "label": "Indexing…", "pct": 35},
    {"type": "button", "label": "Cancel Job", "action_id": "cancel", "variant": "danger"},
])
```

### Component Quick Reference

| Type | Key Props |
|---|---|
| `heading` | `level` (1–4), `text` |
| `text` | `text`, `muted` (bool) |
| `card` | `title`, `children`, `content` |
| `row` | `children` |
| `col` | `children` |
| `grid` | `cols` (int), `children` |
| `board` | `columns: [{id, title, items}]` |
| `progress` | `id`, `label`, `pct` (0–100) |
| `metric` | `id`, `label`, `value`, `trend` (up/down) |
| `badge` | `text`, `variant` (success/warning/danger/info/neutral) |
| `table` | `headers`, `rows` |
| `chart_bar` | `label`, `labels`, `datasets` |
| `chart_line` | `label`, `labels`, `datasets` |
| `log` | `label`, `lines` (str or list) |
| `button` | `label`, `action_id`, `variant` (primary/ghost/danger/gold) |
| `form` | `fields`, `actions` |
| `confirm` | `message`, `confirm_id`, `cancel_id` |
| `flowchart` | `content` (Mermaid source) |
| `code` | `content`, `language`, `label` |
| `list` | `items`, `ordered` (bool) |
| `divider` | (no props) |

---

## Mobile Channel Behavior

When Foster is on **Telegram or WebEx** (mobile channels), canvas URLs must be optimized for phone viewports (375–430px wide).

### Rules for mobile channels

- Append `?mobile=1` to every canvas URL sent via Telegram or WebEx
- The canvas HTML includes a CSS media query (`@media (max-width: 480px)`) AND a `body.mobile-mode` class applied when `?mobile=1` is set — both paths produce the same mobile-friendly layout
- Mobile layout: stacked cards (flex-column), 14px base font, 100% widths, min 44px tap targets
- All content fits within viewport — no horizontal scroll

### Mobile CSS behaviour (auto-applied)

| Element | Desktop | Mobile |
|---|---|---|
| `body` | 16px font | 14px font, 8px padding |
| `.c-row` | `flex-wrap: wrap` (side-by-side) | `flex-direction: column` (stacked) |
| `.c-grid` | multi-column grid | `grid-template-columns: 1fr` |
| `.board-wrap` | `repeat(auto-fit, ...)` columns | single column |
| `.btn`, inputs | natural size | `min-height: 44px` for tap targets |
| `.c-h1/.c-h2` | 28px / 22px | 18px / 16px |
| `.metric-value` | 28px | 20px |

### Channel detection in agent code

```python
import os
channel = os.environ.get('WEE_CHANNEL', 'webui').lower()
mobile = channel in ('telegram', 'webex')

url = canvas.viewer_url()
if mobile:
    url += ('&' if '?' in url else '?') + 'mobile=1'

# Send url to user
```

---

## Server Details

- **Port:** 18793 (override: `CANVAS_PORT` env var)
- **Host:** `localhost` by default (override: `CANVAS_HOST` env var — set to Tailscale IP for remote access)
- **Bind:** Server always binds to `0.0.0.0`, so it accepts connections on all interfaces including Tailscale
- **Auto-start:** `Canvas()` starts `canvas_server.py` if not already running
- **Auto-stop:** Server stops after 30 minutes with no active WebSocket connections
- **Session isolation:** Each `session_id` has its own state; multiple agents can use the same server
- **State persistence:** Last rendered state restores on page refresh
- **Install dependency:** `pip install websockets`

### Tailscale Access

To open the canvas on a remote device (phone, MacBook) via Tailscale:

```bash
export CANVAS_HOST=100.124.186.75   # lepbuntu Tailscale IP
python3 canvas.py
# Opens: http://100.124.186.75:18793/?session=...
```

Or set permanently in the agent's environment/`.env`.

> The WebSocket in `index.html` also reads the host from the URL, so remote browsers
> connect to the correct Tailscale IP automatically.
