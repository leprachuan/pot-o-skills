# Component Library Reference

Full specification for all Live Canvas components.

## Component Structure

Every component is a JSON object with a `type` field. Optional `id` field enables partial updates via `canvas.update(node_id, changes)`.

---

## Layout Components

### `board`
Kanban-style column board.

```json
{
  "type": "board",
  "id": "my-board",
  "columns": [
    {
      "id": "col-done",
      "title": "✅ Done",
      "items": [
        {"type": "card", "id": "item-1", "title": "Pull repo", "status": "done"}
      ]
    },
    {
      "id": "col-running",
      "title": "🔄 Running",
      "items": []
    },
    {
      "id": "col-pending",
      "title": "⏳ Pending",
      "items": [
        {"type": "card", "id": "item-2", "title": "Deploy", "status": "pending"}
      ]
    }
  ]
}
```

**Board item status colors:** `done` = emerald, `running` = gold, `pending` = dim, `error` = red.

---

### `card`
Bordered glass panel with optional title and children.

```json
{
  "type": "card",
  "id": "my-card",
  "title": "Card Title",
  "children": [
    {"type": "text", "text": "Card content here"}
  ],
  "content": "Or plain text content"
}
```

---

### `grid`
N-column grid layout.

```json
{
  "type": "grid",
  "cols": 3,
  "children": [...]
}
```

---

### `row`
Flex row container (horizontal layout, wraps).

```json
{
  "type": "row",
  "children": [
    {"type": "metric", "label": "CPU", "value": "42%"},
    {"type": "metric", "label": "RAM", "value": "8 GB"}
  ]
}
```

---

### `col`
Flex column container (vertical stack with gap).

```json
{
  "type": "col",
  "children": [...]
}
```

---

## Data Display Components

### `table`
Sortable table.

```json
{
  "type": "table",
  "id": "results-table",
  "label": "Top Processes",
  "headers": ["Process", "CPU %", "Memory"],
  "rows": [
    ["nginx", "2%", "64 MB"],
    ["node",  "12%", "400 MB"]
  ]
}
```

Rows can also be objects: `{"Process": "nginx", "CPU %": "2%", "Memory": "64 MB"}`.

---

### `chart_bar`
Bar chart using Chart.js.

```json
{
  "type": "chart_bar",
  "id": "my-bar",
  "label": "Requests per Hour",
  "labels": ["10am", "11am", "12pm", "1pm"],
  "datasets": [
    {"label": "Requests", "data": [120, 240, 180, 310], "color": "#3ecf8e"}
  ]
}
```

---

### `chart_line`
Line chart using Chart.js.

```json
{
  "type": "chart_line",
  "id": "cpu-chart",
  "label": "CPU Over Time",
  "labels": ["0s", "10s", "20s", "30s"],
  "datasets": [
    {"label": "CPU %", "data": [30, 45, 38, 52], "fill": true},
    {"label": "Target", "data": [80, 80, 80, 80], "color": "#ff5f6d"}
  ]
}
```

---

### `metric`
Big number with label and optional trend.

```json
{
  "type": "metric",
  "id": "cpu-metric",
  "label": "CPU",
  "value": "42%",
  "trend": "up",
  "sub": "vs 38% yesterday"
}
```

`trend`: `"up"` (emerald ↑) or `"down"` (red ↓).

---

### `progress`
Progress bar.

```json
{
  "type": "progress",
  "id": "job-progress",
  "label": "Building — step 3 of 8",
  "pct": 37
}
```

`pct`: 0–100.

---

### `badge`
Status chip.

```json
{
  "type": "badge",
  "text": "Deployed",
  "variant": "success"
}
```

`variant`: `success`, `warning`, `danger`, `info`, `neutral`.

---

### `log`
Scrolling log output in monospace.

```json
{
  "type": "log",
  "id": "build-log",
  "label": "Build Output",
  "lines": "npm install\nfound 0 vulnerabilities\nnpm run build…"
}
```

`lines` can be a string or an array of strings.

---

## Interactive Components

### `button`
Clickable button that fires an action back to the agent.

```json
{
  "type": "button",
  "label": "Deploy Now",
  "action_id": "deploy",
  "variant": "primary"
}
```

`variant`: `primary` (emerald), `ghost` (transparent), `danger` (red), `gold`.

When clicked, sends: `{"type": "action", "action_id": "deploy", "data": {}, ...}`.

---

### `form`
Auto-rendered form from field schema. Submit fires action with all field values.

```json
{
  "type": "form",
  "id": "settings-form",
  "fields": [
    {"name": "env",      "label": "Environment", "type": "select",   "options": ["staging", "prod"]},
    {"name": "tag",      "label": "Docker tag",  "type": "text",     "placeholder": "v1.2.3"},
    {"name": "notify",   "label": "Notify on complete", "type": "checkbox", "default": true}
  ],
  "actions": [
    {"label": "Cancel", "action_id": "cancel", "variant": "ghost"},
    {"label": "Deploy",  "action_id": "submit", "variant": "primary"}
  ]
}
```

Field `type` values: `text`, `number`, `select`, `checkbox`.

---

### `input`
Standalone input field (for use inside row/col layouts).

```json
{
  "type": "input",
  "id": "search-box",
  "label": "Search",
  "input_type": "text",
  "placeholder": "Type to search…",
  "default": ""
}
```

---

### `confirm`
Inline confirmation with message and two buttons.

```json
{
  "type": "confirm",
  "message": "This will delete all data. Continue?",
  "confirm_label": "Delete",
  "cancel_label": "Keep it",
  "confirm_id": "confirm-delete",
  "cancel_id": "cancel-delete"
}
```

---

## Content Components

### `heading`
h1–h4 headings.

```json
{"type": "heading", "level": 2, "text": "My Title"}
```

---

### `text`
Paragraph text.

```json
{"type": "text", "text": "Some descriptive text here.", "muted": false}
```

`muted: true` renders in a dimmer color.

---

### `list`
Bulleted or numbered list.

```json
{
  "type": "list",
  "ordered": false,
  "items": ["First item", "Second item", "Third item"]
}
```

---

### `divider`
Horizontal rule.

```json
{"type": "divider"}
```

---

### `flowchart`
Mermaid.js diagram.

```json
{
  "type": "flowchart",
  "id": "deploy-flow",
  "content": "flowchart TD\n  A[Start] --> B{Check}\n  B -->|OK| C[Deploy]\n  B -->|Fail| D[Abort]"
}
```

---

### `code`
Syntax-highlighted code block.

```json
{
  "type": "code",
  "language": "python",
  "label": "canvas_example.py",
  "content": "from canvas import Canvas\nc = Canvas()\nc.open()"
}
```
