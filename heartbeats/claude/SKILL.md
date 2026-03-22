---
name: heartbeats
description: Enable agents to write deferred instructions to HEARTBEAT.md for future execution. An hourly AI scheduled task reads all agent HEARTBEAT.md files, spawns background tasks for pending instructions, and clears the file. No runner script needed — the scheduler itself is the LLM.
---

# Heartbeats — Deferred Agent Instructions

Any agent can write instructions into its `HEARTBEAT.md` file for deferred execution. An hourly scheduled task (an LLM running as fosterbot) reads all agent HEARTBEAT.md files, spawns background tasks for anything pending, then clears the file.

Agent paths come from `/opt/agents.json` — adding a new agent there automatically makes it part of the heartbeat system.

## When to Use

- Schedule a follow-up action after the current session ends
- Remind yourself to check something in ~1 hour
- Queue up research, monitoring, or maintenance tasks
- Trigger a deferred deployment or automation

## HEARTBEAT.md Format

```markdown
# Heartbeat Instructions

## Tasks
- Task description — the hourly runner will spawn a background task for this
- Another deferred task

## Context
Any notes or context to pass to the executing agent

## Model Hint
medium  (simple | medium | complex | or a full model ID like claude-opus-4.6)

## Runtime Hint
copilot  (copilot | claude | gemini | opencode)
```

**Model hint mapping (defaults):**
| Hint | Model |
|------|-------|
| `simple` | claude-haiku-4.5 |
| `medium` | claude-sonnet-4.6 |
| `complex` | claude-opus-4.6 |

If no hint is given, defaults to `claude-sonnet-4.6` / `copilot`.

## How to Write a Heartbeat

```bash
cat > /opt/n8n-copilot-shim/HEARTBEAT.md << 'EOF'
# Heartbeat Instructions

## Tasks
- Check if the Italy trip backpack TODO is still open and send a Telegram reminder if so

## Model Hint
simple
EOF
```

The next hourly run will pick it up, spawn a `claude-haiku-4.5` background task, and clear the file.

## How It Works

There is no runner script. The scheduled job (`heartbeat-runner` in jobs.json) is an AI task with a prompt that instructs the LLM to:
1. Read `/opt/agents.json` for agent paths
2. Check each agent's `HEARTBEAT.md` for pending tasks
3. Spawn background tasks via the Wee-Orchestrator API
4. Clear the file after successful dispatch

Scheduled job location: `/opt/n8n-copilot-shim/.task-scheduler/jobs.json` (id: `heartbeat-runner`)
Schedule: `0 * * * *` (every hour on the hour)
