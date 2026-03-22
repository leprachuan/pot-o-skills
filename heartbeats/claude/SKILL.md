---
name: heartbeats
description: Enable agents to write deferred instructions to HEARTBEAT.md for future execution. An hourly scheduler checks all agent roots and spawns background tasks for pending instructions. Use when you want to schedule a follow-up action, queue research, or trigger a deferred task.
---

# Heartbeats — Deferred Agent Instructions

Agents can write instructions into `HEARTBEAT.md` at their agent root for future execution. An hourly runner checks all agent HEARTBEAT.md files. When instructions are found, background tasks are spawned to execute them. After spawning, HEARTBEAT.md is cleared.

Agent paths are loaded dynamically from `/opt/agents.json` — no hardcoded locations.

## When to Use

- Schedule a follow-up action after current session ends
- Remind self to check something in ~1 hour
- Queue up research or monitoring tasks
- Trigger a deferred deployment or maintenance task

## HEARTBEAT.md Format

```markdown
# Heartbeat Instructions

## Tasks
- Task description (the runner will spawn a background task for this)
- Another deferred task

## Context
Any context/notes to pass to the executing agent

## Model Hint
complex  (or: simple | medium | complex | full model ID like claude-opus-4.6)

## Runtime Hint
copilot  (or: claude | gemini | opencode)
```

Resolution order for model and runtime:
1. `## Model Hint` / `## Runtime Hint` in HEARTBEAT.md
2. `heartbeat.default_model` / `heartbeat.default_runtime` in agents.json for that agent
3. `HEARTBEAT_DEFAULT_MODEL` / `HEARTBEAT_DEFAULT_RUNTIME` env vars
4. Built-in defaults: `claude-sonnet-4.6` / `copilot`

## How to Write a Heartbeat

```bash
cat > /opt/n8n-copilot-shim/HEARTBEAT.md << 'EOF'
# Heartbeat Instructions

## Tasks
- Check if the Italy trip TODO backpack was purchased and send a Telegram reminder if not

## Model Hint
simple

## Runtime Hint
copilot
EOF
```

## Per-Agent Configuration (agents.json)

Add a `heartbeat` block to any agent in `/opt/agents.json` to set per-agent defaults:

```json
{
  "name": "fosterbot",
  "path": "/opt/n8n-copilot-shim",
  "heartbeat": {
    "default_model": "claude-sonnet-4.6",
    "default_runtime": "copilot",
    "model_map": {
      "simple": "claude-haiku-4.5",
      "medium": "claude-sonnet-4.6",
      "complex": "claude-opus-4.6"
    }
  }
}
```

## Model Hints (built-in defaults)

| Hint | Model |
|------|-------|
| `simple` | claude-haiku-4.5 |
| `medium` | claude-sonnet-4.6 (default) |
| `complex` | claude-opus-4.6 |
| *(any model ID)* | used as-is |

## Runner Script

`/opt/pot-o-skills/heartbeats/copilot/heartbeat_runner.py`

Run manually: `python3 /opt/pot-o-skills/heartbeats/copilot/heartbeat_runner.py`

Env var overrides:
- `AGENTS_JSON` — path to agents.json (default: `/opt/agents.json`)
- `HEARTBEAT_DEFAULT_MODEL` — global fallback model
- `HEARTBEAT_DEFAULT_RUNTIME` — global fallback runtime
