# Task Scheduler Skill

Schedule and manage agent tasks with natural language timing.

## 🖥️ Host Requirements

**CLI-Tools host only** (`/opt/` on Linux)

This skill can **ONLY** be executed on the CLI-Tools host. It is **NOT available** on:
- ❌ MacBook (`~/Documents/fosterbot-home/`)
- ❌ lepbuntu or other hosts

**Reason**: The skill requires:
- `/opt/n8n-copilot-shim/` (Wee-Orchestrator with agent_manager.py)
- `/opt/.task-scheduler/` directories
- `task-scheduler-executor` systemd service
- APScheduler with Linux-based scheduling

## ⚠️ Dependencies

**Required**: Wee-Orchestrator
- **Project Name**: Wee-Orchestrator (formerly n8n-copilot-shim)
- **Repository**: https://github.com/leprachuan/Wee-Orchestrator.git
- **Local Folder** (legacy name): `/opt/n8n-copilot-shim/`
- **Purpose**: Executes scheduled tasks via agent_manager.py

Clone with:
```bash
git clone https://github.com/leprachuan/Wee-Orchestrator.git /opt/n8n-copilot-shim
```

> **Note**: The project was renamed to **Wee-Orchestrator**, but the local folder remains named `n8n-copilot-shim` for backwards compatibility with existing configurations.

## Features

✅ Natural language scheduling ("every day at 9am", "in 5 minutes")
✅ One-time and recurring jobs
✅ Full job management (create, list, pause, resume, delete)
✅ Complete execution results logging (JSONL format)
✅ Optional Telegram notifications
✅ Configurable storage (.env)
✅ Diagnostic doctor tool
✅ Cross-runtime support (Claude, Copilot, Gemini)

## Quick Start

1. **Install Wee-Orchestrator**: Clone the repo (see Dependencies above)
2. **Setup skill**: Follow SETUP.md
3. **Start service**: `sudo systemctl start task-scheduler-executor`
4. **Schedule a task**:
   ```python
   from shared_infrastructure import TaskScheduler
   scheduler = TaskScheduler()

   # Agent and runtime default to env vars (SCHEDULER_DEFAULT_AGENT, SCHEDULER_DEFAULT_RUNTIME)
   scheduler.schedule_task(
       name="Hello World",
       schedule="in 5 minutes",
       task="Say hello",
       notify=True
   )

   # Or override defaults:
   scheduler.schedule_task(
       name="Custom Agent Task",
       schedule="every day at 9am",
       agent="my-agent",
       runtime="gemini",
       task="Do something",
       recurring=True
   )
   ```

## Configuration

Configure defaults via environment variables (see SETUP.md):
- `SCHEDULER_DEFAULT_AGENT` - Default agent name (default: `orchestrator`)
- `SCHEDULER_DEFAULT_RUNTIME` - Default runtime (default: `claude`)

See SETUP.md for detailed setup and configuration instructions.
