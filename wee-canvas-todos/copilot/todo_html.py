#!/usr/bin/env python3
"""
Generate self-contained HTML for the TODO canvas component.
Supports list view and kanban view with filtering, drag-and-drop, and quick-add.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional


LABEL_COLORS = {
    "URGENT":    "#ef4444",
    "WORK":      "#3b82f6",
    "FAMILY":    "#8b5cf6",
    "HOME_LAB":  "#06b6d4",
    "SHOPPING":  "#10b981",
    "FINANCE":   "#f59e0b",
    "HEALTH":    "#ec4899",
    "PERSONAL":  "#6366f1",
    "INFRA":     "#14b8a6",
    "DEV":       "#f97316",
}


def _label_color(label: str) -> str:
    return LABEL_COLORS.get(label.upper(), "#6b7280")


def _due_class(due_str: Optional[str]) -> str:
    """Return CSS class based on due date urgency."""
    if not due_str:
        return ""
    try:
        for fmt in ["%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]:
            try:
                due_dt = datetime.strptime(due_str.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return ""
        now = datetime.now()
        if due_dt < now:
            return "overdue"
        if due_dt < now + timedelta(hours=24):
            return "due-soon"
        return ""
    except Exception:
        return ""


def generate_todo_html(todos: List[Dict], last_updated: str = "") -> str:
    """Generate self-contained HTML/JS TODO canvas component."""

    todos_json = json.dumps(todos, default=str)
    label_colors_json = json.dumps(LABEL_COLORS)

    # Compute due classes server-side for initial render
    for t in todos:
        t["_due_class"] = _due_class(t.get("due"))

    todos_json = json.dumps(todos, default=str)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wee TODOs</title>
<style>
  :root {{
    --bg: #0f172a;
    --surface: #1e293b;
    --surface2: #334155;
    --border: #475569;
    --text: #e2e8f0;
    --text-muted: #94a3b8;
    --accent: #10b981;
    --accent-hover: #059669;
    --danger: #ef4444;
    --warn: #f59e0b;
    --pending-col: #1e293b;
    --inprog-col: #1e3a5f;
    --done-col: #1a3a2a;
    --radius: 8px;
    --shadow: 0 2px 8px rgba(0,0,0,0.4);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    font-size: 13px;
    min-height: 100vh;
    padding: 8px;
  }}
  /* Header */
  .header {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 4px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 8px;
    flex-wrap: wrap;
  }}
  .title {{
    font-size: 15px;
    font-weight: 700;
    color: var(--accent);
    flex: 1;
    min-width: 120px;
  }}
  .updated {{
    font-size: 10px;
    color: var(--text-muted);
  }}
  /* View toggle */
  .view-toggle {{
    display: flex;
    gap: 4px;
  }}
  .btn {{
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 4px 10px;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 12px;
    transition: all 0.15s;
  }}
  .btn:hover {{ background: var(--border); }}
  .btn.active {{
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
  }}
  .btn-icon {{ padding: 4px 8px; }}
  /* Filters */
  .filters {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 8px;
    align-items: center;
  }}
  .filter-select {{
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 4px 8px;
    border-radius: var(--radius);
    font-size: 12px;
    cursor: pointer;
  }}
  .filter-input {{
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 4px 8px;
    border-radius: var(--radius);
    font-size: 12px;
    flex: 1;
    min-width: 100px;
  }}
  .filter-input::placeholder {{ color: var(--text-muted); }}
  /* Quick add */
  .quick-add {{
    display: flex;
    gap: 6px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }}
  .quick-add input {{
    flex: 1;
    min-width: 150px;
    background: var(--surface);
    border: 1px solid var(--accent);
    color: var(--text);
    padding: 6px 10px;
    border-radius: var(--radius);
    font-size: 12px;
  }}
  .quick-add input::placeholder {{ color: var(--text-muted); }}
  .quick-add .btn-add {{
    background: var(--accent);
    border: none;
    color: #fff;
    padding: 6px 14px;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    transition: background 0.15s;
  }}
  .quick-add .btn-add:hover {{ background: var(--accent-hover); }}
  /* List view */
  .list-view table {{
    width: 100%;
    border-collapse: collapse;
  }}
  .list-view th {{
    text-align: left;
    padding: 6px 8px;
    border-bottom: 2px solid var(--border);
    color: var(--text-muted);
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap;
  }}
  .list-view td {{
    padding: 6px 8px;
    border-bottom: 1px solid var(--surface2);
    vertical-align: top;
  }}
  .list-view tr:hover td {{ background: rgba(255,255,255,0.03); }}
  .todo-row.overdue td {{ background: rgba(239,68,68,0.08); }}
  .todo-row.due-soon td {{ background: rgba(245,158,11,0.08); }}
  .todo-row.completed td {{ opacity: 0.5; }}
  /* Status badge */
  .status-badge {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 9999px;
    white-space: nowrap;
  }}
  .status-pending {{ background: rgba(100,116,139,0.3); color: #94a3b8; }}
  .status-in_progress {{ background: rgba(59,130,246,0.2); color: #60a5fa; }}
  .status-completed, .status-done {{ background: rgba(16,185,129,0.2); color: #34d399; }}
  /* Label pill */
  .label-pill {{
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 9999px;
    color: #fff;
    margin-right: 3px;
    white-space: nowrap;
  }}
  /* Source icon */
  .source-icon {{ font-size: 11px; opacity: 0.7; }}
  /* Due date */
  .due-text {{ white-space: nowrap; font-size: 11px; }}
  .due-text.overdue {{ color: var(--danger); font-weight: 600; }}
  .due-text.due-soon {{ color: var(--warn); font-weight: 600; }}
  /* Checkbox */
  .check-btn {{
    background: none;
    border: 1.5px solid var(--border);
    color: var(--text-muted);
    width: 18px;
    height: 18px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
    flex-shrink: 0;
  }}
  .check-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
  .check-btn.checked {{
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
  }}
  /* Description */
  .desc-text {{
    cursor: pointer;
    transition: color 0.15s;
  }}
  .desc-text:hover {{ color: var(--accent); }}
  .todo-id {{ font-size: 10px; color: var(--text-muted); font-family: monospace; }}
  /* Detail panel */
  .detail-panel {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 10px;
    margin-top: 4px;
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
    display: none;
  }}
  .detail-panel.open {{ display: block; }}
  /* Kanban */
  .kanban-view {{
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding-bottom: 8px;
  }}
  .kanban-col {{
    flex: 1;
    min-width: 220px;
    background: var(--surface);
    border-radius: var(--radius);
    border: 1px solid var(--border);
    display: flex;
    flex-direction: column;
  }}
  .kanban-col-header {{
    padding: 8px 12px;
    font-weight: 700;
    font-size: 12px;
    border-bottom: 2px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .kanban-col-header .count {{
    background: var(--surface2);
    border-radius: 9999px;
    padding: 1px 6px;
    font-size: 10px;
    color: var(--text-muted);
  }}
  .col-pending .kanban-col-header {{ border-bottom-color: #64748b; }}
  .col-in_progress .kanban-col-header {{ border-bottom-color: #3b82f6; }}
  .col-completed .kanban-col-header {{ border-bottom-color: var(--accent); }}
  .kanban-cards {{
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex: 1;
    min-height: 60px;
    transition: background 0.15s;
  }}
  .kanban-cards.drag-over {{
    background: rgba(16,185,129,0.08);
    border-radius: 4px;
  }}
  .kanban-card {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 8px 10px;
    cursor: grab;
    transition: transform 0.1s, box-shadow 0.1s;
    user-select: none;
  }}
  .kanban-card:hover {{
    border-color: var(--accent);
    box-shadow: var(--shadow);
  }}
  .kanban-card.dragging {{
    opacity: 0.5;
    cursor: grabbing;
    transform: rotate(1deg);
  }}
  .kanban-card.overdue {{
    border-left: 3px solid var(--danger);
  }}
  .kanban-card.due-soon {{
    border-left: 3px solid var(--warn);
  }}
  .card-desc {{
    font-size: 12px;
    font-weight: 500;
    margin-bottom: 5px;
    line-height: 1.4;
  }}
  .card-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    align-items: center;
  }}
  .card-due {{
    font-size: 10px;
    color: var(--text-muted);
  }}
  .card-due.overdue {{ color: var(--danger); font-weight: 600; }}
  .card-due.due-soon {{ color: var(--warn); font-weight: 600; }}
  /* Stats bar */
  .stats-bar {{
    display: flex;
    gap: 12px;
    padding: 6px 4px;
    border-top: 1px solid var(--border);
    margin-top: 8px;
    font-size: 11px;
    color: var(--text-muted);
    flex-wrap: wrap;
  }}
  .stat {{ display: flex; align-items: center; gap: 4px; }}
  /* Empty state */
  .empty-state {{
    text-align: center;
    padding: 40px 20px;
    color: var(--text-muted);
  }}
  .empty-state .emoji {{ font-size: 32px; display: block; margin-bottom: 8px; }}
  /* Scrollbar */
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: var(--surface); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}
  /* Responsive */
  @media (max-width: 480px) {{
    .kanban-view {{ flex-direction: column; }}
    .kanban-col {{ min-width: 0; }}
    .list-view .hide-mobile {{ display: none; }}
  }}
</style>
</head>
<body>
<div class="header">
  <div class="title">✅ Wee TODOs</div>
  <div class="updated" id="last-updated">{last_updated}</div>
  <div class="view-toggle">
    <button class="btn active" id="btn-list" onclick="setView('list')">☰ List</button>
    <button class="btn" id="btn-kanban" onclick="setView('kanban')">⬜ Kanban</button>
  </div>
</div>

<div class="quick-add">
  <input type="text" id="new-todo-text" placeholder="Add a TODO... (press Enter)" 
         onkeydown="if(event.key==='Enter')addTodo()">
  <input type="text" id="new-todo-due" placeholder="Due (MM/DD/YYYY)" style="max-width:130px">
  <input type="text" id="new-todo-labels" placeholder="Labels (WORK,URGENT)" style="max-width:150px">
  <button class="btn-add" onclick="addTodo()">+ Add</button>
</div>

<div class="filters">
  <select class="filter-select" id="filter-status" onchange="applyFilters()">
    <option value="all">All Status</option>
    <option value="pending">Pending</option>
    <option value="in_progress">In Progress</option>
    <option value="completed">Completed</option>
  </select>
  <select class="filter-select" id="filter-source" onchange="applyFilters()">
    <option value="all">All Sources</option>
    <option value="github">GitHub</option>
    <option value="flatfile">Flat File</option>
  </select>
  <select class="filter-select" id="filter-label" onchange="applyFilters()">
    <option value="all">All Labels</option>
  </select>
  <input type="text" class="filter-input" id="filter-search" 
         placeholder="Search TODOs..." oninput="applyFilters()">
</div>

<div id="list-view" class="list-view">
  <table>
    <thead>
      <tr>
        <th style="width:24px"></th>
        <th>TODO</th>
        <th class="hide-mobile">Labels</th>
        <th class="hide-mobile">Due</th>
        <th class="hide-mobile">Source</th>
      </tr>
    </thead>
    <tbody id="list-body"></tbody>
  </table>
</div>

<div id="kanban-view" class="kanban-view" style="display:none">
  <div class="kanban-col col-pending" id="col-pending">
    <div class="kanban-col-header">
      <span>⏳ Pending</span>
      <span class="count" id="count-pending">0</span>
    </div>
    <div class="kanban-cards" id="cards-pending"
         ondragover="onDragOver(event,'pending')"
         ondragleave="onDragLeave(event)"
         ondrop="onDrop(event,'pending')"></div>
  </div>
  <div class="kanban-col col-in_progress" id="col-in_progress">
    <div class="kanban-col-header">
      <span>🔵 In Progress</span>
      <span class="count" id="count-in_progress">0</span>
    </div>
    <div class="kanban-cards" id="cards-in_progress"
         ondragover="onDragOver(event,'in_progress')"
         ondragleave="onDragLeave(event)"
         ondrop="onDrop(event,'in_progress')"></div>
  </div>
  <div class="kanban-col col-completed" id="col-completed">
    <div class="kanban-col-header">
      <span>✅ Completed</span>
      <span class="count" id="count-completed">0</span>
    </div>
    <div class="kanban-cards" id="cards-completed"
         ondragover="onDragOver(event,'completed')"
         ondragleave="onDragLeave(event)"
         ondrop="onDrop(event,'completed')"></div>
  </div>
</div>

<div class="stats-bar" id="stats-bar"></div>

<script>
const LABEL_COLORS = {label_colors_json};
const ALL_TODOS = {todos_json};

let currentView = 'list';
let filteredTodos = [...ALL_TODOS];
let draggingId = null;
let openDetails = new Set();

// Populate label filter
(function initFilters() {{
  const labelSet = new Set();
  ALL_TODOS.forEach(t => (t.labels||[]).forEach(l => labelSet.add(l)));
  const sel = document.getElementById('filter-label');
  [...labelSet].sort().forEach(l => {{
    const opt = document.createElement('option');
    opt.value = l; opt.textContent = l;
    sel.appendChild(opt);
  }});
}})();

function labelColor(label) {{
  return LABEL_COLORS[label.toUpperCase()] || '#6b7280';
}}

function dueClass(dueStr) {{
  if (!dueStr) return '';
  try {{
    const d = new Date(dueStr.replace(/([0-9]+)[/]([0-9]+)[/]([0-9]+)/, '$3-$1-$2'));
    if (isNaN(d)) return '';
    const now = new Date();
    if (d < now) return 'overdue';
    if (d < new Date(now.getTime() + 24*3600*1000)) return 'due-soon';
  }} catch(e) {{}}
  return '';
}}

function formatDue(dueStr) {{
  if (!dueStr) return '';
  return dueStr.replace(/([0-9]{{2}}[/][0-9]{{2}}[/][0-9]{{4}}) 00:00:00/, '$1');
}}

function statusLabel(t) {{
  if (t.completed) return 'completed';
  const s = (t.status || 'pending').toLowerCase();
  return s;
}}

function renderLabelPills(labels) {{
  return (labels||[]).map(l =>
    `<span class="label-pill" style="background:${{labelColor(l)}}">${{l}}</span>`
  ).join('');
}}

function sourceIcon(t) {{
  if (t.source === 'github') return '🐙';
  if (t.source === 'flatfile') return '📄';
  return '';
}}

function applyFilters() {{
  const status = document.getElementById('filter-status').value;
  const source = document.getElementById('filter-source').value;
  const label = document.getElementById('filter-label').value;
  const search = document.getElementById('filter-search').value.toLowerCase();
  
  filteredTodos = ALL_TODOS.filter(t => {{
    const ts = statusLabel(t);
    if (status !== 'all' && ts !== status) return false;
    if (source !== 'all' && t.source !== source) return false;
    if (label !== 'all' && !(t.labels||[]).includes(label)) return false;
    if (search && !t.description.toLowerCase().includes(search)) return false;
    return true;
  }});
  renderCurrent();
}}

function renderCurrent() {{
  if (currentView === 'list') renderList();
  else renderKanban();
  renderStats();
}}

function setView(v) {{
  currentView = v;
  document.getElementById('list-view').style.display = v === 'list' ? 'block' : 'none';
  document.getElementById('kanban-view').style.display = v === 'kanban' ? 'flex' : 'none';
  document.getElementById('btn-list').className = 'btn' + (v==='list'?' active':'');
  document.getElementById('btn-kanban').className = 'btn' + (v==='kanban'?' active':'');
  renderCurrent();
}}

function renderList() {{
  const tbody = document.getElementById('list-body');
  if (!filteredTodos.length) {{
    tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><span class="emoji">🎉</span>No TODOs match your filters</div></td></tr>';
    return;
  }}
  tbody.innerHTML = filteredTodos.map(t => {{
    const dc = t._due_class || dueClass(t.due);
    const status = statusLabel(t);
    const checked = t.completed || status === 'completed';
    const detailOpen = openDetails.has(t.id);
    return `
    <tr class="todo-row ${{dc}} ${{checked ? 'completed' : ''}}" data-id="${{t.id||''}}">
      <td>
        <button class="check-btn ${{checked ? 'checked' : ''}}" 
                onclick="toggleComplete('${{t.id||t.description}}')" 
                title="${{checked ? 'Mark incomplete' : 'Mark complete'}}">
          ${{checked ? '✓' : ''}}
        </button>
      </td>
      <td>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <span class="desc-text" onclick="toggleDetail('${{t.id}}')">${{escHtml(t.description)}}</span>
          <span class="todo-id">${{t.id||''}}</span>
          <span class="status-badge status-${{status}}">${{status.replace('_',' ')}}</span>
        </div>
        ${{detailOpen && t.notes ? `<div class="detail-panel open">${{escHtml(t.notes)}}</div>` : ''}}
        ${{detailOpen && t.github_url ? `<div style="margin-top:4px;font-size:11px"><a href="${{t.github_url}}" style="color:#60a5fa" target="_blank">View on GitHub →</a></div>` : ''}}
      </td>
      <td class="hide-mobile">${{renderLabelPills(t.labels)}}</td>
      <td class="hide-mobile">
        ${{t.due ? `<span class="due-text ${{dc}}">${{formatDue(t.due)}}</span>` : ''}}
      </td>
      <td class="hide-mobile">
        <span class="source-icon" title="${{t.source||''}}">${{sourceIcon(t)}}</span>
      </td>
    </tr>`;
  }}).join('');
}}

function renderKanban() {{
  const cols = {{ pending: [], in_progress: [], completed: [] }};
  filteredTodos.forEach(t => {{
    const s = statusLabel(t);
    const key = s === 'completed' || s === 'done' ? 'completed' : 
                s === 'in_progress' ? 'in_progress' : 'pending';
    cols[key].push(t);
  }});
  
  ['pending','in_progress','completed'].forEach(col => {{
    const container = document.getElementById('cards-' + col);
    document.getElementById('count-' + col).textContent = cols[col].length;
    if (!cols[col].length) {{
      container.innerHTML = '<div style="text-align:center;padding:20px;color:#475569;font-size:11px">Drop here</div>';
      return;
    }}
    container.innerHTML = cols[col].map(t => {{
      const dc = t._due_class || dueClass(t.due);
      return `
      <div class="kanban-card ${{dc}}" 
           draggable="true" data-id="${{t.id||t.description}}"
           ondragstart="onDragStart(event,'${{t.id||t.description}}')"
           ondragend="onDragEnd(event)"
           onclick="toggleDetail('${{t.id}}')">
        <div class="card-desc">${{escHtml(t.description)}}</div>
        <div class="card-meta">
          ${{renderLabelPills(t.labels)}}
          ${{t.due ? `<span class="card-due ${{dc}}">📅 ${{formatDue(t.due)}}</span>` : ''}}
          <span class="source-icon">${{sourceIcon(t)}}</span>
        </div>
      </div>`;
    }}).join('');
  }});
}}

function renderStats() {{
  const total = ALL_TODOS.length;
  const done = ALL_TODOS.filter(t => t.completed || statusLabel(t)==='completed').length;
  const overdue = ALL_TODOS.filter(t => !t.completed && (t._due_class||dueClass(t.due))==='overdue').length;
  const shown = filteredTodos.length;
  document.getElementById('stats-bar').innerHTML = `
    <span class="stat">📋 ${{total}} total</span>
    <span class="stat">✅ ${{done}} done</span>
    <span class="stat">⏳ ${{total - done}} active</span>
    ${{overdue ? `<span class="stat" style="color:var(--danger)">🔴 ${{overdue}} overdue</span>` : ''}}
    ${{shown < total ? `<span class="stat" style="color:var(--text-muted)">Showing ${{shown}}</span>` : ''}}
  `;
}}

function toggleDetail(id) {{
  if (openDetails.has(id)) openDetails.delete(id);
  else openDetails.add(id);
  if (currentView === 'list') renderList();
}}

function toggleComplete(identifier) {{
  postAction({{ action: 'complete', id: identifier }});
}}

function addTodo() {{
  const text = document.getElementById('new-todo-text').value.trim();
  if (!text) return;
  const due = document.getElementById('new-todo-due').value.trim();
  const labels = document.getElementById('new-todo-labels').value.trim();
  postAction({{
    action: 'add',
    description: text,
    due: due || null,
    labels: labels ? labels.split(',').map(s => s.trim()) : []
  }});
  document.getElementById('new-todo-text').value = '';
  document.getElementById('new-todo-due').value = '';
  document.getElementById('new-todo-labels').value = '';
}}

function onDragStart(e, id) {{
  draggingId = id;
  e.target.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
}}

function onDragEnd(e) {{
  e.target.classList.remove('dragging');
  document.querySelectorAll('.kanban-cards').forEach(c => c.classList.remove('drag-over'));
}}

function onDragOver(e, col) {{
  e.preventDefault();
  e.currentTarget.classList.add('drag-over');
}}

function onDragLeave(e) {{
  e.currentTarget.classList.remove('drag-over');
}}

function onDrop(e, newStatus) {{
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');
  if (!draggingId) return;
  postAction({{ action: 'status', id: draggingId, status: newStatus }});
  draggingId = null;
}}

function postAction(data) {{
  try {{
    parent.postMessage({{ type: 'canvas_action', payload: data }}, '*');
  }} catch(e) {{
    console.log('Action (no parent):', JSON.stringify(data));
  }}
}}

function escHtml(s) {{
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

// Initial render
applyFilters();

// Auto-resize iframe
function resize() {{
  const h = Math.max(document.body.scrollHeight, 300);
  try {{ parent.postMessage({{ type: 'resize', height: h }}, '*'); }} catch(e) {{}}
}}
setTimeout(resize, 100);
window.addEventListener('resize', resize);
</script>
</body>
</html>"""

    return html
