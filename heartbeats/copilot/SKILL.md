---
name: heartbeats
description: Enable agents to write deferred instructions to HEARTBEAT.md for future execution. An hourly scheduler checks all agent roots and spawns background tasks for pending instructions. Use when you want to schedule a follow-up action, queue research, or trigger a deferred task.
---

# Heartbeats — Deferred Agent Instructions

Agents can write instructions into `HEARTBEAT.md` at their agent root for future execution. An hourly runner checks all agent HEARTBEAT.md files. When instructions are found, background tasks are spawned to execute them. After spawning, HEARTBEAT.md is cleared.

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
complex  (or: simple, medium, complex — helps runner pick the right model)
```

## How to Write a Heartbeat

```bash
cat > /opt/n8n-copilot-shim/HEARTBEAT.md << EOF
# Heartbeat Instructions

## Tasks
- Check if the Italy trip TODO backpack was purchased and send a Telegram reminder if not

## Model Hint
simple
EOF
```

## Agent Roots Map

| Agent | Root |
|-------|------|
| fosterbot | `/opt/n8n-copilot-shim/` |
| email_triage | `/opt/email_triage/` |
| family_knowledge | `/opt/family_knowledge/` |
| opencode | `/opt/opencode/` |
| smart_home | `/opt/smart_home/` |
| MyHomeDevops | `/opt/MyHomeDevops/` |
| nanocode | `/opt/nanocode/` |

## Model Hints

| Hint | Model |
|------|-------|
| simple | claude-haiku-4.5 |
| medium | claude-sonnet-4.6 (default) |
| complex | claude-opus-4.6 |

## Runner Script

`/opt/foster-skills/heartbeats/copilot/heartbeat_runner.py`

Run manually: `python3 /opt/foster-skills/heartbeats/copilot/heartbeat_runner.py`

