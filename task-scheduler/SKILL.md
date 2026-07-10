---
name: task-scheduler
description: Use when you need to schedule tasks to run at specific times or intervals - supports natural language timing like "every day at 9am" and manages job creation, listing, pausing, resuming, and deletion
---

# Task Scheduler

## Overview

Schedule and manage agent tasks with natural language timing. Create jobs that run at specific times or intervals with full lifecycle management.

**Core principle:** Simple natural language scheduling with comprehensive job management.

## When to Use

- Need to schedule a task for specific time
- Want recurring jobs (daily, weekly, etc.)
- Need to manage scheduled tasks (pause, resume, delete)
- Track execution logs
- Create background automation

## Quick Reference

| Action | Natural Language | Result |
|--------|------------------|--------|
| **Create** | "every day at 9am" | Job scheduled daily |
| **Once** | "tomorrow at 2pm" | Single execution |
| **Interval** | "every 6 hours" | Recurring interval |
| **List** | View all jobs | See all scheduled tasks |
| **Pause** | Temporarily stop | Job doesn't run |
| **Resume** | Start again | Job runs again |
| **Delete** | Remove job | Permanently stop |

## Natural Language Examples

| Input | Scheduling |
|-------|-----------|
| "every day at 9am" | Daily at 09:00 |
| "every weekday at 3pm" | Mon-Fri at 15:00 |
| "every Monday at 8am" | Weekly Monday 08:00 |
| "every 6 hours" | Repeat every 6 hours |
| "every 1 minute" | Repeat every 60 seconds |
| "tomorrow at 2:30pm" | Single run tomorrow |
| "in 30 minutes" | Single run 30 min from now |

> ⚠️ **Minimum resolution: 1 minute.** Do not schedule jobs with `every N second(s)` — the scheduler parser does not support sub-minute intervals and will disable the job after the first run.

## Features

- ✅ Natural language timing parsing
- ✅ Full job lifecycle (create, list, pause, resume, delete)
- ✅ Execution logging with timestamps
- ✅ Diagnostic tools for troubleshooting
- ✅ Cross-runtime support (Claude, Copilot, Gemini)
- ✅ Configurable storage (.env)

## Job Management

**Create Job:**
```
Schedule: "every day at 9am"
Action: "Check email and triage high-priority messages"
```

**List Jobs:**
View all scheduled tasks with status, next run time, and last execution.

**Pause/Resume:**
Stop a job without deleting, then resume when ready.

**Delete:**
Permanently remove scheduled job.

## Storage

Job configuration stored in `.env` file:
```
SCHEDULER_DATABASE=/home/n8n/.claude/jobs.db
SCHEDULER_LOG_DIR=/home/n8n/.copilot/logs/scheduler
```

## Diagnostics

Built-in doctor tool to verify:
- Scheduler service running
- Storage accessible
- Permissions correct
- Recent execution logs

## Execution

When scheduled time arrives:
1. Job executes in background
2. Execution logged with timestamp
3. Results stored or reported
4. Next execution scheduled

See README.md for complete documentation.
