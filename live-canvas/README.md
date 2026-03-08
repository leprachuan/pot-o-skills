# Live Canvas Skill

A real-time interactive visualization framework for agents. Render dashboards, charts, forms, and flowcharts in a live-updating browser canvas.

**Status**: ✅ HTTP (port 18793) | Auto-starts on first use | Persistent across sessions

---

## Quick Start

### 1. Open a Canvas
```python
from canvas import Canvas

c = Canvas()  # Auto-generates session ID
c.open()      # Opens browser window
```

### 2. Render Components
```python
components = [
    {
        "type": "heading",
        "level": 1,
        "text": "My Dashboard"
    },
    {
        "type": "text",
        "text": "Hello, world!"
    }
]

c.render(components)
```

### 3. Access via Browser
- **Local**: `http://localhost:18793?session=<SESSION_ID>`
- **Tailscale**: `http://lepbuntu.taildbe64.ts.net:18793?session=<SESSION_ID>`

---

## Component Types

### Text/Content
- `heading` — Headings (level 1-6)
- `text` — Paragraphs and multi-line text
- `list` — Bulleted/ordered lists
- `code` — Code blocks with syntax highlighting
- `divider` — Horizontal separator

### Charts (Data Visualization)
- **`chart_line`** — Line charts
- **`chart_bar`** — Bar charts

### Interactive
- `button` — Clickable buttons with callbacks
- `form` — Forms with inputs
- `input` — Text/select inputs
- `confirm` — Confirmation dialogs

### Layout
- `card` — Glass-styled cards with children
- `grid` — Multi-column layouts
- `row` — Horizontal layout
- `col` — Vertical layout
- `board` — Kanban-style board

### Data Display
- `table` — Data tables
- `metric` — Single KPI display with trend
- `progress` — Progress bars
- `badge` — Status badges
- `log` — Log output/console

### Advanced
- `flowchart` — Mermaid flowcharts
- `confirm` — Confirmation dialogs

---

## Chart Components (Important!)

### Correct Format for `chart_line` and `chart_bar`

**✅ CORRECT** — Use `labels` and `datasets`:
```python
{
    "type": "chart_line",
    "title": "Oil Prices",
    "labels": ["Jan", "Feb", "Mar", "Apr"],
    "datasets": [
        {
            "label": "WTI Price",
            "data": [60.0, 62.5, 65.0, 68.0],
            "color": "#ef4444",
            "fill": False
        }
    ]
}
```

**❌ WRONG** — Do NOT use `data.series`:
```python
# This will NOT work - empty chart!
{
    "type": "chart_line",
    "data": {
        "series": [{"name": "Price", "values": [...]}]
    }
}
```

### Dataset Properties
| Property | Type | Default | Notes |
|----------|------|---------|-------|
| `label` | string | `Series 1` | Legend label |
| `data` | number[] | `[]` | **REQUIRED** — actual data points |
| `color` | string | Auto-assigned | Hex color (e.g., `#ef4444`) |
| `fill` | boolean | `false` | Fill area under line (line charts only) |

### Colors (Palette)
Pre-defined colors: `#3ecf8e`, `#f5c542`, `#7fb5ff`, `#ff8888`, `#c084fc`, `#34d399`, `#fb923c`, `#60a5fa`

If no color specified, auto-assigns from palette in order.

---

## Common Patterns

### Example: Oil Price Chart with Annotation
```python
components = [
    {
        "type": "heading",
        "level": 1,
        "text": "📊 WTI Crude Oil Prices"
    },
    {
        "type": "chart_line",
        "title": "6-Month Price Trend",
        "labels": ["Oct 1", "Oct 15", "Nov 1", "Nov 15", "Dec 1", "Dec 15", 
                   "Jan 1", "Jan 15", "Feb 1", "Feb 15", "Mar 1", "Mar 6"],
        "datasets": [
            {
                "label": "WTI Price (USD/barrel)",
                "data": [60.0, 59.5, 59.0, 58.5, 57.5, 57.26, 58.0, 60.0, 62.0, 65.0, 68.0, 91.27],
                "color": "#ef4444"
            }
        ]
    },
    {
        "type": "card",
        "title": "🔴 March 6 - Event Annotation",
        "children": [
            {
                "type": "text",
                "text": "Spike: $68 → $91.27 (+34.2%)\nCause: US-Iran conflict & supply concerns"
            }
        ]
    }
]

c.render(components)
```

### Example: Dashboard with Metrics
```python
components = [
    {
        "type": "metric",
        "value": "$91.27",
        "label": "Current Oil Price",
        "trend": "up"
    },
    {
        "type": "metric",
        "value": "+52.1%",
        "label": "6-Month Change",
        "trend": "up"
    },
    {
        "type": "metric",
        "value": "$57.26",
        "label": "6-Month Low",
        "trend": "down"
    }
]

c.render(components)
```

---

## Server Configuration

### TLS/HTTPS
Live-canvas **defaults to HTTP** on port 18793.

If you need HTTPS, edit `/opt/.claude/skills/live-canvas/claude/implementation/canvas_config.json`:
```json
{
  "bind_hosts": ["127.0.0.1", "100.124.186.75"],
  "tls": {
    "enabled": false
  }
}
```

- Set `"enabled": true` to enable TLS
- Provide valid `certfile` and `keyfile` paths

### Binding Hosts
Default binds to localhost only. To expose via Tailscale:
```json
{
  "bind_hosts": ["127.0.0.1", "100.124.186.75"],
  "tls": { "enabled": false }
}
```

Where `100.124.186.75` is lepbuntu's Tailscale IP.

---

## API Reference

### Canvas Python API

#### Constructor
```python
Canvas(session_id: Optional[str] = None)
```
- Auto-generates session ID if not provided
- Auto-starts server if not running

#### Methods
```python
c.render(components: list)           # Render component tree
c.render_template(name, data)        # Render built-in template
c.update(node_id, changes)           # Update single node
c.clear()                            # Clear canvas
c.open()                             # Open browser
c.viewer_url() -> str                # Get browser URL
c.wait_for_action(timeout=60)        # Block until user action
```

### CLI API

Use the Copilot CLI wrapper:
```bash
python3 /opt/.claude/skills/live-canvas/copilot/implementation/canvas_cli.py \
  render --session <SESSION_ID> --components '<JSON>'

python3 /opt/.claude/skills/live-canvas/copilot/implementation/canvas_cli.py \
  template --session <SESSION_ID> --name dashboard --data '{...}'

python3 /opt/.claude/skills/live-canvas/copilot/implementation/canvas_cli.py \
  update --session <SESSION_ID> --node-id <NODE_ID> --changes '{...}'

python3 /opt/.claude/skills/live-canvas/copilot/implementation/canvas_cli.py \
  clear --session <SESSION_ID>
```

---

## Troubleshooting

### Issue: "Empty reply from server"
**Cause**: TLS/HTTPS protocol mismatch  
**Fix**: Disable TLS in `canvas_config.json`:
```json
{"tls": {"enabled": false}}
```
Then restart the server.

### Issue: Chart line with no data points
**Cause**: Using wrong data format (`data.series` instead of `datasets`)  
**Fix**: Use correct format:
```python
# ✅ CORRECT
"datasets": [{"label": "X", "data": [1, 2, 3]}]

# ❌ WRONG
"data": {"series": [{"name": "X", "values": [1, 2, 3]}]}
```

### Issue: Server not responding
**Cause**: Port 18793 already in use or server crashed  
**Fix**:
```bash
# Check if server running
lsof -i :18793

# Kill old instance
kill <PID>

# Restart
python3 /opt/.claude/skills/live-canvas/claude/implementation/canvas_server.py
```

### Issue: Chart not updating
**Cause**: Browser not connected to WebSocket  
**Fix**:
1. Refresh the page
2. Check browser console for errors (F12)
3. Verify session ID in URL matches

---

## Files Structure

```
/opt/.claude/skills/live-canvas/
├── README.md                           # This file
├── claude/implementation/
│   ├── canvas.py                       # Python API
│   ├── canvas_server.py                # HTTP+WebSocket server
│   ├── canvas_config.json              # Config (TLS, bind hosts)
│   └── certs/                          # TLS certificates
├── copilot/implementation/
│   └── canvas_cli.py                   # CLI wrapper
├── assets/canvas-viewer/
│   ├── index.html                      # UI
│   ├── renderer.js                     # Component rendering
│   └── chart-helpers.js                # Chart.js integration
```

---

## Examples

### Full Working Example
```python
import sys
import json
sys.path.insert(0, '/opt/.claude/skills/live-canvas/claude/implementation')
from canvas import Canvas

# Create canvas
c = Canvas()

# Build components
components = [
    {
        "type": "heading",
        "level": 1,
        "text": "📊 Data Dashboard"
    },
    {
        "type": "chart_line",
        "title": "Sales Trend",
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "datasets": [
            {
                "label": "Revenue",
                "data": [100, 150, 200, 250],
                "color": "#3ecf8e"
            },
            {
                "label": "Expenses", 
                "data": [80, 100, 120, 140],
                "color": "#ff8888"
            }
        ]
    }
]

# Render
c.render(components)

# Show URL
print(f"View at: http://localhost:18793?session={c.session_id}")
```

---

## Best Practices

✅ **DO**:
- Use descriptive labels for chart datasets
- Set explicit colors for consistency
- Use cards to group related content
- Test chart data format in Python first
- Keep component trees under 50 nodes for performance

❌ **DON'T**:
- Mix old `data.series` format with `datasets`
- Use TLS without valid certificates
- Send massive datasets (>1000 points) — consider aggregation
- Leave TLS enabled if causing connection issues
- Rely on implicit session IDs — pass explicit ones

---

## Support

- **Server logs**: Check `/tmp/canvas.log` or systemd journal
- **Browser console**: F12 → Console tab
- **WebSocket status**: Browser DevTools → Network → WS connections
