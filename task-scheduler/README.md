# Task Scheduler Skill

Schedule and manage agent tasks with natural language timing.

## ⚠️ Dependencies

**Required**: Wee-Orchestrator (n8n-copilot-shim)
- Repository: https://github.com/leprachuan/Wee-Orchestrator.git
- Location: `/opt/n8n-copilot-shim/`
- Purpose: Executes scheduled tasks via agent_manager.py

Clone with:
```bash
git clone https://github.com/leprachuan/Wee-Orchestrator.git /opt/n8n-copilot-shim
```

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
   scheduler.schedule_task(
       name="Hello World",
       schedule="in 5 minutes",
       agent="orchestrator",
       runtime="claude",
       task="Say hello",
       notify=True
   )
   ```

See SETUP.md for detailed setup instructions.
