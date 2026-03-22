---
name: heartbeats
description: Enable agents to write deferred instructions to HEARTBEAT.md for future execution. Each agent has its own heartbeat scheduled task — enabling/disabling heartbeats for an agent means adding/removing their job. The scheduled task is an AI prompt that reads the agent's HEARTBEAT.md, spawns background tasks for pending instructions, and clears the file.
---

# Heartbeats — Deferred Agent Instructions

Any agent can write instructions into its `HEARTBEAT.md` file. An hourly scheduled task (scoped to that agent) reads the file, spawns background tasks for pending work, and clears it.

**Each agent has its own scheduled task.** Heartbeats are enabled/disabled per agent by adding or removing their job from the task scheduler. The job runs *as* that agent, so it inherits all agent permissions and context.

## When to Use

- Schedule a follow-up action after the current session ends
- Remind yourself to check something in ~1 hour
- Queue up research, monitoring, or maintenance tasks
- Trigger a deferred deployment or automation

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

The next hourly run for fosterbot will pick it up, spawn a `claude-haiku-4.5` background task, and clear the file.

---

## Enabling Heartbeats for an Agent

Add a scheduled job to `/opt/n8n-copilot-shim/.task-scheduler/jobs.json` using this template. Replace `{AGENT_NAME}` and `{HEARTBEAT_PATH}` for each agent.

```json
{
  "id": "heartbeat-{AGENT_NAME}",
  "name": "Heartbeat — {AGENT_NAME}",
  "agent": "{AGENT_NAME}",
  "runtime": "copilot",
  "model": "claude-haiku-4.5",
  "mode": "ai",
  "task": "You are the heartbeat runner for the {AGENT_NAME} agent. Check {HEARTBEAT_PATH}/HEARTBEAT.md. If it has any non-empty, non-comment lines under the ## Tasks section: read the full file, check ## Model Hint (simple=claude-haiku-4.5, medium=claude-sonnet-4.6, complex=claude-opus-4.6; default: claude-sonnet-4.6) and ## Runtime Hint (default: copilot), then spawn a background task via POST https://127.0.0.1:8000/api/v1/background-tasks with headers 'Authorization: Bearer shared_R6R6wReORUV6bouLntScMTowbsh30Rzqa3hzjs3bWgU' and 'X-Auth-Channel: api', body: {\"prompt\": \"Execute these heartbeat instructions:\\n\\n<file content>\\n\\nSpawn sub-tasks as needed using the best model for each job.\", \"agent\": \"{AGENT_NAME}\", \"runtime\": \"<runtime>\", \"model\": \"<model>\", \"timeout\": 3600}. After a successful spawn, overwrite HEARTBEAT.md with the empty template (# Heartbeat Instructions header, empty ## Tasks / ## Context / ## Model Hint / ## Runtime Hint sections with comment placeholders). If no tasks are pending, do nothing and exit silently.",
  "schedule": "0 * * * *",
  "working_dir": "/opt",
  "notify": false,
  "recurring": true,
  "enabled": true,
  "retries": 0,
  "cron": "0 * * * *"
}
```

### Agent path reference (from agents.json)

| Agent | Path | HEARTBEAT.md |
|-------|------|--------------|
| fosterbot | /opt/n8n-copilot-shim | /opt/n8n-copilot-shim/HEARTBEAT.md |
| devops | /opt/MyHomeDevops | /opt/MyHomeDevops/HEARTBEAT.md |
| family_knowledge | /opt/family_knowledge | /opt/family_knowledge/HEARTBEAT.md |
| email_triage | /opt/email_triage | /opt/email_triage/HEARTBEAT.md |
| smart_home | /opt/smart_home | /opt/smart_home/HEARTBEAT.md |
| opencode | /opt/opencode | /opt/opencode/HEARTBEAT.md |
| nanocode | /opt/nanocode | /opt/nanocode/HEARTBEAT.md |

### Currently enabled

- **fosterbot** — job id: `heartbeat-fosterbot` ✅

## Disabling Heartbeats for an Agent

Either set `"enabled": false` on the job, or delete the job entry entirely from jobs.json.

## Scheduled Task Location

`/opt/n8n-copilot-shim/.task-scheduler/jobs.json`

Job IDs follow the pattern: `heartbeat-{agent_name}`
