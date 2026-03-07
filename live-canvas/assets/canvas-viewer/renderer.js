/**
 * renderer.js — JSON component tree → DOM
 * Depends on: chart-helpers.js (for chart components), mermaid (global)
 */

// ── Node registry for partial updates ────────────────────────────────────────
const nodeRegistry = new Map(); // id -> element

function renderComponents(container, components) {
  // Clear old nodes from registry that belong to this container
  nodeRegistry.clear();
  container.innerHTML = '';

  for (const comp of (components || [])) {
    const el = renderComponent(comp);
    if (el) container.appendChild(el);
  }

  // Re-run Mermaid on any flowchart nodes
  const flowcharts = container.querySelectorAll('.mermaid-src');
  flowcharts.forEach(node => renderMermaid(node));
}

function renderComponent(comp) {
  if (!comp || typeof comp !== 'object') return null;

  const el = _dispatch(comp);
  if (!el) return null;

  // Register by id for future updates
  if (comp.id) {
    el.dataset.nodeId = comp.id;
    nodeRegistry.set(comp.id, el);
  }

  el.classList.add('anim-in');
  return el;
}

function _dispatch(comp) {
  const { type } = comp;
  switch (type) {
    // Layout
    case 'board':       return _renderBoard(comp);
    case 'card':        return _renderCard(comp);
    case 'grid':        return _renderGrid(comp);
    case 'row':         return _renderRow(comp);
    case 'col':         return _renderCol(comp);
    // Data
    case 'table':       return _renderTable(comp);
    case 'chart_bar':   return _renderChart(comp, 'bar');
    case 'chart_line':  return _renderChart(comp, 'line');
    case 'metric':      return _renderMetric(comp);
    case 'progress':    return _renderProgress(comp);
    case 'badge':       return _renderBadge(comp);
    case 'log':         return _renderLog(comp);
    // Interactive
    case 'button':      return _renderButton(comp);
    case 'form':        return _renderForm(comp);
    case 'input':       return _renderInput(comp);
    case 'confirm':     return _renderConfirm(comp);
    // Content
    case 'heading':     return _renderHeading(comp);
    case 'text':        return _renderText(comp);
    case 'list':        return _renderList(comp);
    case 'divider':     return _renderDivider();
    case 'flowchart':   return _renderFlowchart(comp);
    case 'code':        return _renderCode(comp);
    default:
      const div = document.createElement('div');
      div.style.color = 'var(--text-muted)';
      div.style.fontSize = '12px';
      div.textContent = `[unknown component: ${type}]`;
      return div;
  }
}

// ── Partial update ────────────────────────────────────────────────────────────
function applyUpdate(nodeId, changes) {
  if (!nodeId || !changes) return;

  const el = nodeRegistry.get(nodeId);
  if (!el) return;

  const dataNodeId = el.dataset.nodeId;

  // Reconstruct the element with merged data
  // We store original comp data as a JSON attribute for this purpose
  const origData = el._compData;
  if (origData) {
    Object.assign(origData, changes);
    const newEl = renderComponent(origData);
    if (newEl && el.parentNode) {
      el.parentNode.replaceChild(newEl, el);
      nodeRegistry.set(nodeId, newEl);
    }
  }
}

// ── Layout components ─────────────────────────────────────────────────────────

function _renderBoard(comp) {
  const wrap = document.createElement('div');
  wrap.className = 'board-wrap glass-panel';
  _storeComp(wrap, comp);

  for (const col of (comp.columns || [])) {
    const colEl = document.createElement('div');
    colEl.className = 'board-col';
    if (col.id) { colEl.dataset.nodeId = col.id; nodeRegistry.set(col.id, colEl); }

    const titleEl = document.createElement('div');
    titleEl.className = 'board-col-title';
    titleEl.textContent = col.title || '';
    colEl.appendChild(titleEl);

    for (const item of (col.items || [])) {
      const itemEl = _renderBoardItem(item);
      if (itemEl) colEl.appendChild(itemEl);
    }

    wrap.appendChild(colEl);
  }
  return wrap;
}

function _renderBoardItem(item) {
  const el = document.createElement('div');
  el.className = 'board-item anim-in';
  if (item.id) { el.dataset.nodeId = item.id; nodeRegistry.set(item.id, el); }
  _storeComp(el, item);

  el.textContent = item.title || item.name || '';

  if (item.status) {
    el.style.borderLeft = `3px solid ${_statusColor(item.status)}`;
  }
  return el;
}

function _renderCard(comp) {
  const wrap = document.createElement('div');
  wrap.className = 'glass-card';
  _storeComp(wrap, comp);

  if (comp.title) {
    const h = document.createElement('div');
    h.style.cssText = 'font-weight:600;font-size:14px;margin-bottom:10px;';
    h.textContent = comp.title;
    wrap.appendChild(h);
  }

  for (const child of (comp.children || [])) {
    const el = renderComponent(child);
    if (el) wrap.appendChild(el);
  }

  if (comp.content && typeof comp.content === 'string') {
    const p = document.createElement('p');
    p.style.cssText = 'font-size:13px;color:var(--text-secondary);';
    p.textContent = comp.content;
    wrap.appendChild(p);
  }

  return wrap;
}

function _renderGrid(comp) {
  const cols = comp.cols || 2;
  const wrap = document.createElement('div');
  wrap.className = 'c-grid';
  wrap.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
  _storeComp(wrap, comp);

  for (const child of (comp.children || [])) {
    const el = renderComponent(child);
    if (el) wrap.appendChild(el);
  }
  return wrap;
}

function _renderRow(comp) {
  const wrap = document.createElement('div');
  wrap.className = 'c-row';
  _storeComp(wrap, comp);

  for (const child of (comp.children || [])) {
    const el = renderComponent(child);
    if (el) wrap.appendChild(el);
  }
  return wrap;
}

function _renderCol(comp) {
  const wrap = document.createElement('div');
  wrap.className = 'c-col';
  _storeComp(wrap, comp);

  for (const child of (comp.children || [])) {
    const el = renderComponent(child);
    if (el) wrap.appendChild(el);
  }
  return wrap;
}

// ── Data components ───────────────────────────────────────────────────────────

function _renderTable(comp) {
  const wrap = document.createElement('div');
  wrap.className = 'glass-panel';
  wrap.style.overflowX = 'auto';
  _storeComp(wrap, comp);

  if (comp.label || comp.title) {
    const h = document.createElement('div');
    h.style.cssText = 'font-weight:600;font-size:13px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;';
    h.textContent = comp.label || comp.title;
    wrap.appendChild(h);
  }

  const table = document.createElement('table');
  table.className = 'glass-table';

  if (comp.headers && comp.headers.length) {
    const thead = document.createElement('thead');
    const tr = document.createElement('tr');
    for (const h of comp.headers) {
      const th = document.createElement('th');
      th.textContent = h;
      tr.appendChild(th);
    }
    thead.appendChild(tr);
    table.appendChild(thead);
  }

  const tbody = document.createElement('tbody');
  for (const row of (comp.rows || [])) {
    const tr = document.createElement('tr');
    const cells = Array.isArray(row) ? row : Object.values(row);
    for (const cell of cells) {
      const td = document.createElement('td');
      td.textContent = cell;
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  wrap.appendChild(table);
  return wrap;
}

function _renderChart(comp, defaultType) {
  const wrap = document.createElement('div');
  wrap.className = 'glass-panel';
  _storeComp(wrap, comp);

  if (comp.label || comp.title) {
    const h = document.createElement('div');
    h.style.cssText = 'font-weight:600;font-size:13px;color:var(--text-muted);margin-bottom:12px;';
    h.textContent = comp.label || comp.title;
    wrap.appendChild(h);
  }

  const canvas = document.createElement('canvas');
  canvas.style.maxHeight = '300px';
  wrap.appendChild(canvas);

  // Defer chart creation so the canvas is in the DOM
  setTimeout(() => {
    const type = comp.chart_type || defaultType;
    createChart(canvas, type, comp.labels || [], comp.datasets || []);
  }, 50);

  return wrap;
}

function _renderMetric(comp) {
  const wrap = document.createElement('div');
  wrap.className = 'glass-card';
  wrap.style.minWidth = '120px';
  wrap.style.textAlign = 'center';
  _storeComp(wrap, comp);

  const val = document.createElement('div');
  val.className = 'metric-value';
  if (comp.trend === 'up') val.classList.add('trend-up');
  if (comp.trend === 'down') val.classList.add('trend-down');
  val.textContent = comp.value || '—';
  wrap.appendChild(val);

  if (comp.trend === 'up') { const t = document.createElement('span'); t.textContent = ' ↑'; t.className = 'trend-up'; val.appendChild(t); }
  if (comp.trend === 'down') { const t = document.createElement('span'); t.textContent = ' ↓'; t.className = 'trend-down'; val.appendChild(t); }

  const lbl = document.createElement('div');
  lbl.className = 'metric-label';
  lbl.textContent = comp.label || '';
  wrap.appendChild(lbl);

  if (comp.sub) {
    const sub = document.createElement('div');
    sub.style.cssText = 'font-size:11px;color:var(--text-muted);margin-top:4px;';
    sub.textContent = comp.sub;
    wrap.appendChild(sub);
  }

  return wrap;
}

function _renderProgress(comp) {
  const wrap = document.createElement('div');
  wrap.className = 'glass-panel';
  wrap.style.padding = '16px';
  _storeComp(wrap, comp);

  const topRow = document.createElement('div');
  topRow.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;';

  const label = document.createElement('span');
  label.style.cssText = 'font-size:13px;color:var(--text-secondary);';
  label.textContent = comp.label || '';
  topRow.appendChild(label);

  const pct = Math.max(0, Math.min(100, comp.pct || 0));
  const pctLabel = document.createElement('span');
  pctLabel.style.cssText = 'font-size:13px;font-weight:600;color:var(--accent);';
  pctLabel.textContent = `${pct}%`;
  topRow.appendChild(pctLabel);

  wrap.appendChild(topRow);

  const track = document.createElement('div');
  track.className = 'progress-wrap';
  const bar = document.createElement('div');
  bar.className = 'progress-bar';
  bar.style.width = `${pct}%`;
  track.appendChild(bar);
  wrap.appendChild(track);

  return wrap;
}

function _renderBadge(comp) {
  const el = document.createElement('span');
  el.className = `badge badge-${comp.variant || 'neutral'}`;
  _storeComp(el, comp);
  el.textContent = comp.text || comp.label || '';
  return el;
}

function _renderLog(comp) {
  const wrap = document.createElement('div');
  wrap.className = 'glass-panel';
  wrap.style.padding = '12px';
  _storeComp(wrap, comp);

  if (comp.label) {
    const h = document.createElement('div');
    h.style.cssText = 'font-size:11px;color:var(--text-muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:.06em;';
    h.textContent = comp.label;
    wrap.appendChild(h);
  }

  const pre = document.createElement('div');
  pre.className = 'log-area';
  const lines = comp.lines || comp.content || '';
  pre.textContent = Array.isArray(lines) ? lines.join('\n') : String(lines);
  // Auto-scroll to bottom
  requestAnimationFrame(() => { pre.scrollTop = pre.scrollHeight; });
  wrap.appendChild(pre);
  return wrap;
}

// ── Interactive components ────────────────────────────────────────────────────

function _renderButton(comp) {
  const btn = document.createElement('button');
  const variantMap = { primary: 'btn-primary', ghost: 'btn-ghost', danger: 'btn-danger', gold: 'btn-gold', secondary: 'btn-ghost' };
  btn.className = `btn ${variantMap[comp.variant] || 'btn-primary'}`;
  _storeComp(btn, comp);

  btn.textContent = comp.label || comp.text || 'Button';
  if (comp.disabled) btn.disabled = true;

  btn.addEventListener('click', () => {
    if (comp.action_id) {
      window.sendAction(comp.action_id, {});
    }
  });

  return btn;
}

function _renderForm(comp) {
  const wrap = document.createElement('div');
  wrap.className = 'glass-panel';
  _storeComp(wrap, comp);

  const fieldValues = {};

  for (const field of (comp.fields || [])) {
    const fwrap = document.createElement('div');
    fwrap.style.marginBottom = '16px';

    if (field.label) {
      const lbl = document.createElement('label');
      lbl.style.cssText = 'display:block;font-size:12px;color:var(--text-muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em;';
      lbl.textContent = field.label;
      fwrap.appendChild(lbl);
    }

    const inputType = field.type || field.input_type || 'text';

    if (inputType === 'select' || (field.options && field.options.length)) {
      const sel = document.createElement('select');
      sel.className = 'glass-select';
      for (const opt of (field.options || [])) {
        const o = document.createElement('option');
        o.value = o.textContent = opt;
        if (field.default && opt === field.default) o.selected = true;
        sel.appendChild(o);
      }
      sel.addEventListener('change', () => { fieldValues[field.name] = sel.value; });
      fieldValues[field.name] = sel.value;
      fwrap.appendChild(sel);
    } else if (inputType === 'checkbox') {
      const row = document.createElement('div');
      row.style.cssText = 'display:flex;align-items:center;gap:8px;';
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.style.accentColor = 'var(--accent)';
      cb.checked = !!field.default;
      cb.addEventListener('change', () => { fieldValues[field.name] = cb.checked; });
      fieldValues[field.name] = cb.checked;
      row.appendChild(cb);
      if (field.label) {
        const span = document.createElement('span');
        span.style.cssText = 'font-size:13px;color:var(--text-secondary);';
        span.textContent = field.label;
        row.appendChild(span);
      }
      fwrap.innerHTML = '';
      fwrap.appendChild(row);
    } else {
      const inp = document.createElement('input');
      inp.type = inputType === 'number' ? 'number' : 'text';
      inp.className = 'glass-input';
      inp.placeholder = field.placeholder || '';
      inp.value = field.default || '';
      inp.addEventListener('input', () => { fieldValues[field.name] = inp.value; });
      fieldValues[field.name] = inp.value;
      fwrap.appendChild(inp);
    }

    wrap.appendChild(fwrap);
  }

  // Action buttons
  if (comp.actions && comp.actions.length) {
    const btnRow = document.createElement('div');
    btnRow.style.cssText = 'display:flex;gap:10px;justify-content:flex-end;margin-top:20px;';

    for (const act of comp.actions) {
      const btn = document.createElement('button');
      const variantMap = { primary: 'btn-primary', ghost: 'btn-ghost', danger: 'btn-danger' };
      btn.className = `btn ${variantMap[act.variant] || 'btn-primary'}`;
      btn.textContent = act.label;
      btn.addEventListener('click', () => {
        window.sendAction(act.action_id, { ...fieldValues });
      });
      btnRow.appendChild(btn);
    }

    wrap.appendChild(btnRow);
  }

  return wrap;
}

function _renderInput(comp) {
  // Standalone input (for use inside row/col etc.)
  const wrap = document.createElement('div');
  _storeComp(wrap, comp);

  if (comp.label) {
    const lbl = document.createElement('label');
    lbl.style.cssText = 'display:block;font-size:12px;color:var(--text-muted);margin-bottom:6px;';
    lbl.textContent = comp.label;
    wrap.appendChild(lbl);
  }

  const inp = document.createElement('input');
  inp.type = comp.input_type || 'text';
  inp.className = 'glass-input';
  inp.placeholder = comp.placeholder || '';
  inp.value = comp.default || comp.value || '';
  wrap.appendChild(inp);

  return wrap;
}

function _renderConfirm(comp) {
  // Inline confirm section (not a modal for simplicity)
  const wrap = document.createElement('div');
  wrap.className = 'glass-card';
  wrap.style.borderLeft = '3px solid var(--gold)';
  _storeComp(wrap, comp);

  const msg = document.createElement('div');
  msg.style.cssText = 'font-size:14px;margin-bottom:16px;';
  msg.textContent = comp.message || comp.text || 'Are you sure?';
  wrap.appendChild(msg);

  const btnRow = document.createElement('div');
  btnRow.style.cssText = 'display:flex;gap:10px;';

  const cancel = document.createElement('button');
  cancel.className = 'btn btn-ghost';
  cancel.textContent = comp.cancel_label || 'Cancel';
  cancel.addEventListener('click', () => window.sendAction(comp.cancel_id || 'cancel', {}));

  const confirm = document.createElement('button');
  confirm.className = 'btn btn-primary';
  confirm.textContent = comp.confirm_label || 'Confirm';
  confirm.addEventListener('click', () => window.sendAction(comp.confirm_id || 'confirm', {}));

  btnRow.appendChild(cancel);
  btnRow.appendChild(confirm);
  wrap.appendChild(btnRow);

  return wrap;
}

// ── Content components ────────────────────────────────────────────────────────

function _renderHeading(comp) {
  const level = Math.min(4, Math.max(1, comp.level || 2));
  const el = document.createElement(`h${level}`);
  el.className = `c-h${level}`;
  _storeComp(el, comp);
  el.textContent = comp.text || '';
  return el;
}

function _renderText(comp) {
  const el = document.createElement('p');
  el.style.cssText = `font-size:14px;line-height:1.6;color:${comp.muted ? 'var(--text-muted)' : 'var(--text-secondary)'};`;
  _storeComp(el, comp);
  el.textContent = comp.text || comp.content || '';
  return el;
}

function _renderList(comp) {
  const el = document.createElement(comp.ordered ? 'ol' : 'ul');
  el.style.cssText = 'padding-left:20px;font-size:14px;color:var(--text-secondary);display:flex;flex-direction:column;gap:4px;';
  _storeComp(el, comp);

  for (const item of (comp.items || [])) {
    const li = document.createElement('li');
    li.textContent = typeof item === 'string' ? item : item.text || '';
    el.appendChild(li);
  }
  return el;
}

function _renderDivider() {
  const hr = document.createElement('hr');
  hr.className = 'glass-divider';
  return hr;
}

function _renderFlowchart(comp) {
  const wrap = document.createElement('div');
  wrap.className = 'glass-panel mermaid-wrap';
  _storeComp(wrap, comp);

  const mermaidDiv = document.createElement('div');
  mermaidDiv.className = 'mermaid-src';
  mermaidDiv.dataset.mermaidSrc = comp.content || 'flowchart TD\n  A[No content]';
  wrap.appendChild(mermaidDiv);

  // Render mermaid async
  setTimeout(() => renderMermaid(mermaidDiv), 100);
  return wrap;
}

function _renderCode(comp) {
  const wrap = document.createElement('div');
  wrap.className = 'glass-panel';
  wrap.style.padding = '0';
  _storeComp(wrap, comp);

  if (comp.label || comp.language) {
    const header = document.createElement('div');
    header.style.cssText = 'padding:8px 16px;font-size:11px;color:var(--text-muted);border-bottom:1px solid var(--glass-border);font-family:var(--font-mono);';
    header.textContent = comp.label || comp.language;
    wrap.appendChild(header);
  }

  const pre = document.createElement('div');
  pre.className = 'code-block';
  pre.style.borderRadius = comp.label ? '0 0 var(--radius) var(--radius)' : 'var(--radius)';
  pre.textContent = comp.content || comp.code || '';
  wrap.appendChild(pre);
  return wrap;
}

// ── Mermaid renderer ──────────────────────────────────────────────────────────
async function renderMermaid(el) {
  const src = (el.dataset.mermaidSrc || el.textContent || '').trim();
  if (!src) return;
  el.innerHTML = '';
  try {
    const id = 'mermaid-' + Date.now() + '-' + Math.random().toString(36).slice(2);
    const { svg } = await mermaid.render(id, src);
    el.innerHTML = svg;
  } catch (e) {
    el.style.cssText = 'color:var(--danger);font-family:var(--font-mono);font-size:12px;';
    el.textContent = 'Mermaid error: ' + e.message;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function _storeComp(el, comp) {
  el._compData = comp;
}

function _statusColor(status) {
  const colors = { done: '#3ecf8e', running: '#f5c542', pending: 'rgba(255,255,255,0.3)', error: '#ff5f6d' };
  return colors[status] || 'rgba(255,255,255,0.2)';
}
