# Heartbeats Skill

Enable agents to write deferred instructions to `HEARTBEAT.md` for future execution. An hourly scheduler checks all agent roots and spawns background tasks for any pending instructions.

## Overview

The heartbeats system provides a simple mechanism for agents to "leave a note to self" — instructions that will be picked up and executed in the next hourly cycle without requiring the current session to remain active.

## Agent Roots

| Agent | HEARTBEAT.md Location |
|-------|----------------------|
| fosterbot | `/opt/n8n-copilot-shim/HEARTBEAT.md` |
| email_triage | `/opt/email_triage/HEARTBEAT.md` |
| family_knowledge | `/opt/family_knowledge/HEARTBEAT.md` |
| opencode | `/opt/opencode/HEARTBEAT.md` |
| smart_home | `/opt/smart_home/HEARTBEAT.md` |
| MyHomeDevops | `/opt/MyHomeDevops/HEARTBEAT.md` |
| nanocode | `/opt/nanocode/HEARTBEAT.md` |

## HEARTBEAT.md Format

```markdown
# Heartbeat Instructions

## Tasks
- Task description here
- Another deferred task

## Context
Any context or notes to pass to the executing agent

## Model Hint
simple  (or: medium, complex)
```

## Model Hint → Model Mapping

| Hint | Model |
|------|-------|
| simple | claude-haiku-4.5 |
| medium | claude-sonnet-4.6 (default) |
| complex | claude-opus-4.6 |

## Runner

The runner script is at `/opt/foster-skills/heartbeats/copilot/heartbeat_runner.py`.

Run manually:
```bash
python3 /opt/foster-skills/heartbeats/copilot/heartbeat_runner.py
```

## Scheduled Job

An hourly cron job (`heartbeat-runner`) runs the runner automatically via the task scheduler.

## Use Cases

- Schedule a follow-up action after current session ends
- Remind self to check something in ~1 hour
- Queue up research or monitoring tasks
- Trigger a deferred deployment or maintenance task
