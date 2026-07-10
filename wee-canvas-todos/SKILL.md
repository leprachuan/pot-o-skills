---
name: wee-canvas-todos
description: >
  Interactive TODO board for Wee Canvas. Displays TODOs from both GitHub Issues
  (leprachuan/fosterbot-home) and flat files in two views: list and kanban.
  Features filtering, drag-and-drop status changes, quick-add, and auto-refresh
  every 30 seconds. Use when Foster asks to "show TODOs", "open TODO board",
  "view my tasks", or "TODO kanban".
---

# Wee Canvas TODOs Skill

An interactive, real-time TODO board rendered on **Wee Canvas** — the WebUI slide-out panel.

## When to Use

- Foster asks to "show my TODOs", "open the TODO board", "view my tasks on canvas"
- After adding/completing TODOs via todo-tracker, wants a visual overview
- Managing tasks in kanban style with drag-and-drop status changes
- Embedding a live TODO widget in another canvas workflow

## Quick Start

```python
import subprocess, sys
result = subprocess.run(
    [sys.executable, "/opt/skills/wee-canvas-todos/copilot/canvas_todos.py",
     "--once"],
    capture_output=True, text=True
)
print(result.stdout)
```

Or as a long-running live board:
```bash
python3 /opt/skills/wee-canvas-todos/copilot/canvas_todos.py --refresh 30
```

## Views

| View | Description |
|------|-------------|
| **List** | Table with status badge, description, labels, due date, source icon |
| **Kanban** | 3 columns (Pending, In Progress, Completed) with drag-and-drop cards |

## Features

- 🔄 **Dual source** — GitHub Issues + flat files, deduplicated
- 🎯 **Filters** — by status, source, label, free-text search
- ➕ **Quick-add** — create TODOs directly from the canvas
- ✅ **Toggle complete** — click checkboxes in list view
- 🃏 **Drag-and-drop** — move cards between kanban columns
- 🔴 **Due date warnings** — overdue (red), due soon (yellow)
- 📱 **Mobile-friendly** — responsive layout for Telegram canvas links
- ♻️ **Auto-refresh** — every 30 seconds (configurable)

## CLI Options

```
--session-id  STR   Canvas session ID (auto-generated if omitted)
--height      INT   iframe height in pixels (default: 700)
--once              Render once and exit (for embedding)
--refresh     INT   Refresh interval in seconds (default: 30)
```

## Embedding in Other Workflows

```python
import sys; sys.path.insert(0, '/opt/n8n-copilot-shim')
sys.path.insert(0, '/opt/skills/wee-canvas-todos/copilot')
from canvas import Canvas
from canvas_todos import load_todos, render_todos

c = Canvas()
c.open()
todos = load_todos()
render_todos(c, todos, height=600)
print(c.viewer_url())
```

## Data Sources

| Source | Description |
|--------|-------------|
| GitHub Issues | `leprachuan/fosterbot-home` issues with label `todo` |
| Flat files | `/opt/fosterbot-home/TODOs/ACTIVE/` and `COMPLETED/` |

GitHub wins on title deduplication. Falls back to flat files if GitHub is unavailable.
