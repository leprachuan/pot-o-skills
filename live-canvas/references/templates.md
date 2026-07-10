# Template Usage Examples

Complete examples for all four built-in templates.

---

## Template 1: `progress_board`

Use during any multi-step task. Update steps in real time as work progresses.

### Full Example: Deployment Pipeline

```python
import sys, time
sys.path.insert(0, '/opt/skills/live-canvas/claude/implementation')
from canvas import Canvas

c = Canvas()
c.open()

steps = [
    "Pull latest code",
    "Install dependencies",
    "Run tests",
    "Build artifacts",
    "Deploy to staging",
    "Run smoke tests",
    "Deploy to production",
]

# Initial render — all pending
c.render_template("progress_board", {
    "title": "Deploy v2.1 — Production",
    "steps": [{"name": s, "status": "pending"} for s in steps],
})

for i, step in enumerate(steps):
    # Mark step as running
    c.update(f"step-{i}", {"status": "running", "title": f"🔄 {step}"})
    c.update("overall-progress", {"pct": int(i / len(steps) * 100)})

    # ... do the actual work ...
    time.sleep(2)

    # Mark step done
    c.update(f"step-{i}", {"status": "done", "title": f"✅ {step}"})

c.update("overall-progress", {"pct": 100})
c.update("board-title", {"text": "✅ Deploy v2.1 — Complete!"})
```

### Data Schema

```python
{
    "title": str,              # Board heading
    "elapsed": str,            # Optional: "3m 12s"
    "steps": [
        {
            "name": str,       # Step display name
            "status": str,     # "done"|"running"|"pending"|"error"|"skip"
        }
    ]
}
```

---

## Template 2: `data_dashboard`

Use for status snapshots, monitoring, or any data overview.

### Full Example: Home Assistant Status

```python
c.render_template("data_dashboard", {
    "title": "🏠 Home Assistant Status",
    "metrics": [
        {"label": "Temperature", "value": "72°F"},
        {"label": "Humidity",    "value": "45%"},
        {"label": "Lights On",   "value": "3/12"},
        {"label": "Devices",     "value": "24 online"},
    ],
    "chart": {
        "label": "Temperature last 6h",
        "labels": ["6h", "5h", "4h", "3h", "2h", "1h", "now"],
        "datasets": [
            {"label": "°F", "data": [70, 71, 72, 73, 72, 71, 72], "fill": True},
        ],
    },
    "table": {
        "headers": ["Device", "Room", "Status"],
        "rows": [
            ["Thermostat",   "Living Room", "Heating"],
            ["Smart Lock",   "Front Door",  "Locked"],
            ["Motion Sensor","Backyard",    "Clear"],
        ],
    },
})
```

### Data Schema

```python
{
    "title": str,
    "metrics": [
        {"label": str, "value": str, "trend": "up"|"down"|None}
    ],
    "chart": {            # optional
        "label": str,
        "labels": list[str],
        "datasets": [{"label": str, "data": list[number], "color": str, "fill": bool}]
    },
    "table": {            # optional
        "headers": list[str],
        "rows": list[list]
    }
}
```

---

## Template 3: `config_form`

Use whenever you need structured input from the user before proceeding.

### Full Example: Email Triage Config

```python
c.render_template("config_form", {
    "title": "Email Triage Rules",
    "description": "Set up how emails are processed and routed.",
    "fields": [
        {
            "name": "sender_filter",
            "label": "Sender domain filter",
            "type": "text",
            "placeholder": "e.g. @spam.com (leave empty for all)",
        },
        {
            "name": "action",
            "label": "Action",
            "type": "select",
            "options": ["Move to Folder", "Archive", "Delete", "Flag"],
            "default": "Archive",
        },
        {
            "name": "folder",
            "label": "Target folder (if Move)",
            "type": "text",
            "placeholder": "e.g. Newsletters",
        },
        {
            "name": "notify_telegram",
            "label": "Notify via Telegram",
            "type": "checkbox",
            "default": True,
        },
        {
            "name": "confidence",
            "label": "Min confidence threshold (%)",
            "type": "number",
            "default": "80",
        },
    ],
    "submit_label": "Save & Apply",
    "cancel_label": "Cancel",
})

action = c.wait_for_action(timeout=300)
if action.get("action_id") == "submit":
    values = action["data"]
    # values = {"sender_filter": "...", "action": "...", "folder": "...", ...}
    print(f"Config received: {values}")
elif action.get("action_id") == "cancel":
    print("User cancelled")
```

### Data Schema

```python
{
    "title": str,
    "description": str,    # optional
    "fields": [
        {
            "name": str,         # key in returned values dict
            "label": str,        # display label
            "type": str,         # "text"|"number"|"select"|"checkbox"
            "options": list,     # required for "select"
            "default": any,      # pre-filled value
            "placeholder": str,  # hint text for text/number
        }
    ],
    "submit_label": str,   # default "Submit"
    "cancel_label": str,   # default "Cancel"
}
```

---

## Template 4: `plan_view`

Use before executing any irreversible action. Show the plan, wait for approval.

### Full Example: SSL Certificate Rotation

```python
c.render_template("plan_view", {
    "title": "Rotate SSL Certificates",
    "description": "The following actions will be taken on 3 domains. This cannot be undone.",
    "mermaid": """flowchart TD
  A[Start] --> B[Check certificate expiry]
  B --> C{Expired or < 30 days?}
  C -->|Yes| D[Generate new cert via Let's Encrypt]
  C -->|No| E[Skip — cert is valid]
  D --> F[Verify cert is valid]
  F --> G[Deploy to nginx config]
  G --> H[Reload nginx]
  H --> I[Verify HTTPS works]
  I --> J[Done ✅]""",
    "approve_label": "Execute Rotation",
    "cancel_label": "Cancel",
})

print("Waiting for user approval…")
action = c.wait_for_action(timeout=600)

if action.get("action_id") == "approve":
    print("Approved — starting certificate rotation")
elif action.get("action_id") == "cancel":
    print("Cancelled by user")
elif action.get("type") == "timeout":
    print("Timed out waiting for approval")
```

### Data Schema

```python
{
    "title": str,
    "description": str,      # optional context below title
    "mermaid": str,          # Mermaid.js diagram source
    "approve_label": str,    # default "Approve & Execute"
    "cancel_label": str,     # default "Cancel"
}
```

---

## Combining Templates with Updates

Templates can be updated after rendering just like any manual render. The node IDs are predictable:

| Template | Node ID | Updatable Props |
|---|---|---|
| `progress_board` | `board-title` | `text` |
| `progress_board` | `overall-progress` | `pct`, `label` |
| `progress_board` | `step-{index}` | `status`, `title` |
| `data_dashboard` | `metric-{index}` | `value`, `trend`, `sub` |
| `data_dashboard` | `dashboard-chart` | `labels`, `datasets` |
| `data_dashboard` | `dashboard-table` | `headers`, `rows` |
| `plan_view` | `plan-diagram` | `content` |

---

## Pattern: Full Task Lifecycle

```python
c = Canvas()
c.open()

# Phase 1: Show plan, get approval
c.render_template("plan_view", {"title": "Deploy", "mermaid": "…", "approve_label": "Go"})
action = c.wait_for_action(timeout=300)
if action.get("action_id") != "approve":
    c.render([{"type": "heading", "text": "Cancelled"}])
    exit()

# Phase 2: Show progress board
c.render_template("progress_board", {"title": "Deploying…", "steps": steps})

for i, step in enumerate(steps):
    c.update(f"step-{i}", {"status": "running"})
    do_step(step)
    c.update(f"step-{i}", {"status": "done"})
    c.update("overall-progress", {"pct": (i + 1) * 100 // len(steps)})

# Phase 3: Final status
c.render([
    {"type": "heading", "level": 2, "text": "✅ Deploy Complete"},
    {"type": "badge", "text": "Success", "variant": "success"},
])
```
