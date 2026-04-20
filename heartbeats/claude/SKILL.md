---
name: heartbeats
description: Use when you want to schedule work to happen later, remind yourself to follow up on something, or queue a task for the next hour. Write deferred instructions into HEARTBEAT.md — an hourly scheduled task will pick them up, execute them as background tasks, and clear the file. Trigger phrases: "remind me later", "check this in an hour", "do this after", "follow up on", "schedule this for later", "queue this up", "deferred task", "next time you wake up". IMPORTANT: You can and should use this proactively on your own initiative — not just when the user asks. Use it to follow up on background tasks you spawned, verify something completed correctly, check on a deployment, circle back on an open question, or pursue any goal that benefits from a future check-in. Think of it as leaving yourself a note for your next wakeup.
---

# Heartbeats — Deferred Agent Instructions

Any agent can write instructions into its `HEARTBEAT.md` for deferred execution. An hourly scheduled task reads the file, spawns background tasks for pending work, then clears it.

The agent determines its own heartbeat file location by looking up its name in `/opt/agents.json` and reading the `path` field. The heartbeat file is always `{agent.path}/HEARTBEAT.md`.

## When to Use

Use this proactively — you don't need the user to ask. Any time you want to check in on something later, leave yourself a note here.

**User-directed:**
- Schedule a follow-up action after the current session ends
- Remind the user to check something in ~1 hour
- Queue up research, monitoring, or maintenance tasks
- Trigger a deferred deployment or automation

**Agent-initiated (your own goals):**
- Verify a background task you spawned actually completed successfully
- Check on a deployment or service restart you triggered
- Follow up on an open question or unresolved issue
- Monitor something you set in motion and report back
- Pursue any goal that requires a future check-in without blocking the current session

## HEARTBEAT.md Format

```markdown
# Heartbeat Instructions

## Tasks
- Task description — one background task will be spawned with all tasks as context
- Another deferred task

## Context
Any notes or context to pass to the executing agent

## Model Hint
medium  (simple | medium | complex | or a full model ID like claude-opus-4.6)

## Runtime Hint
copilot  (copilot | claude | gemini | opencode)
```

**Model hint mapping:**
| Hint | Model |
|------|-------|
| `simple` | claude-haiku-4.5 |
| `medium` | claude-sonnet-4.6 (default) |
| `complex` | claude-opus-4.6 |

---

## Enabling Heartbeats for an Agent

Add a scheduled job to `/opt/n8n-copilot-shim/.task-scheduler/jobs.json`. The prompt is identical for every agent — it instructs the LLM to resolve its own path from `agents.json` at runtime.

```json
{
  "id": "heartbeat-{AGENT_NAME}",
  "name": "Heartbeat — {AGENT_NAME}",
  "agent": "{AGENT_NAME}",
  "runtime": "copilot",
  "model": "claude-haiku-4.5",
  "mode": "ai",
  "task": "You are the heartbeat runner. Determine your agent name from the current session context, then look up your root path in /opt/agents.json by matching the agent name. Read {root}/HEARTBEAT.md. If it has any non-empty, non-comment lines under the ## Tasks section: read the full file, check ## Model Hint (simple=claude-haiku-4.5, medium=claude-sonnet-4.6, complex=claude-opus-4.6; default: claude-sonnet-4.6) and ## Runtime Hint (default: copilot). Read API_SHARED_KEY from /opt/n8n-copilot-shim/.env to authenticate. Attempt to spawn a background task via POST https://127.0.0.1:8000/api/v1/background-tasks with body: {\"prompt\": \"Execute these heartbeat instructions:\\n\\n<file content>\\n\\nSpawn sub-tasks as needed using the best model for each job.\", \"agent\": \"<agent_name>\", \"runtime\": \"<runtime>\", \"model\": \"<model>\", \"timeout\": 3600}. If spawning the background task fails, log the failure and do not attempt to redispatch or retry; leave the HEARTBEAT.md unchanged for manual inspection. After a successful spawn, overwrite the HEARTBEAT.md with the empty template (# Heartbeat Instructions header, empty ## Tasks / ## Context / ## Model Hint / ## Runtime Hint sections with comment placeholders). If no tasks are pending, do nothing and exit silently.",
  "schedule": "0 * * * *",
  "working_dir": "/opt",
  "notify": false,
  "recurring": true,
  "enabled": true,
  "retries": 0,
  "cron": "0 * * * *"
}
```

Only `"id"`, `"name"`, and `"agent"` change between agents. The `"task"` prompt is the same for all.

## Disabling Heartbeats for an Agent

Set `"enabled": false` on the job, or remove it from `jobs.json` entirely.

## Currently Enabled

- **fosterbot** — job id: `heartbeat-fosterbot`
