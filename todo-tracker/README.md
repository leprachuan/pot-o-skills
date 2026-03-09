# TODO Tracker Skill

Production-ready TODO management system with markdown-based storage, due dates, labels, and automatic reminders. Fully portable with environment variable configuration for multi-host deployments (CLI-Tools, MacBook, Docker, etc).

## Quick Start

### Add a TODO
```bash
python3 copilot/todo_cli.py add "Buy milk" --due 03/15/2026 --labels SHOPPING
```

### List TODOs
```bash
python3 copilot/todo_cli.py list active
python3 copilot/todo_cli.py list completed
python3 copilot/todo_cli.py list all
```

### Complete a TODO
```bash
python3 copilot/todo_cli.py complete "Buy milk"
```

### Get Reminders
```bash
python3 copilot/todo_cli.py upcoming  # Due soon
python3 copilot/todo_cli.py overdue   # Past due
```

## Configuration

All paths are configurable via environment variables for portability across hosts.

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `TODO_FILE` | (auto-detected) | Path to TODO markdown file |
| `TODO_STATE_FILE` | `~/.todo-reminder-state.json` | Where reminder state is tracked |
| `TODO_CONFIG_FILE` | `~/.todo-reminder-config.json` | Optional config file for reminders |
| `TODO_REMINDER_CHANNEL` | `telegram` | Notification channel: `telegram` or `webex` |
| `TELEGRAM_CONFIG_PATHS` | `/opt/n8n-copilot-shim/telegram_config.json:/opt/n8n-copilot-shim-dev/telegram_config.json` | Colon-separated paths to telegram config |
| `TELEGRAM_SKILL_PATH` | `/opt/skills/telegram-notify` | Path to telegram-notify skill |
| `WEBEX_CONFIG_PATHS` | `/opt/n8n-copilot-shim/webex_config.json:/opt/n8n-copilot-shim-dev/webex_config.json` | Colon-separated paths to webex config |
| `WEBEX_SKILL_PATH` | `/opt/skills/webex-notify` | Path to webex-notify skill |

### Example: Setup on MacBook

```bash
export TODO_FILE="$HOME/Documents/TODOs.md"
export TODO_STATE_FILE="$HOME/.local/share/todo-tracker/reminder-state.json"
export TODO_CONFIG_FILE="$HOME/.local/share/todo-tracker/config.json"
export TELEGRAM_SKILL_PATH="$HOME/Documents/fosterbot-home/skills/telegram-notify"
export WEBEX_SKILL_PATH="$HOME/Documents/fosterbot-home/skills/webex-notify"

# Then run CLI or reminders
python3 /path/to/todo-tracker/copilot/todo_cli.py list
python3 /path/to/todo-tracker/todo_reminder.py
```

### Example: Setup on Docker

```dockerfile
ENV TODO_FILE="/data/TODOs.md"
ENV TODO_STATE_FILE="/data/.todo-reminder-state.json"
ENV TELEGRAM_CONFIG_PATHS="/config/telegram.json"
ENV TELEGRAM_SKILL_PATH="/app/skills/telegram-notify"

VOLUME /data
VOLUME /config
```

## Storage Details

TODOs are stored in markdown format for easy editing and version control:

```markdown
# TODOs

## Active

[ ] Buy groceries (due 03/15/2026)
    Need: milk, eggs, bread

[ ] Deploy app (due 03/14/2026 09:00:00) {WORK,URGENT}
    - Test on staging first
    - Notify team 30 min before

[X] Fix kitchen light (due 03/12/2026 14:30:00)

## Completed

[X] Review PR (due 03/11/2026)
```

## Format Specification

### Basic TODO
```markdown
[ ] Task description
```

### TODO with Due Date (date only)
```markdown
[ ] Task description (due 03/15/2026)
```

### TODO with Due Date and Time
```markdown
[ ] Task description (due 03/15/2026 14:30:00)
```

### TODO with Labels
```markdown
[ ] Task description {LABEL1,LABEL2}
```

### TODO with Notes
```markdown
[ ] Task description
    Additional details and notes here
```

### Completed TODO
```markdown
[X] Task description (due 03/15/2026)
```

## Features

- ✅ Markdown-based storage (easily version controlled)
- ✅ Due dates (date-only or with specific times)
- ✅ Labels for organization (FAMILY, HOME_LAB, WORK, URGENT, etc)
- ✅ Automatic reminders via Telegram or WebEx
- ✅ Smart reminder tiers (1 day before, 1 hour before, 15 min before, at due time, overdue)
- ✅ Snooze/reschedule functionality
- ✅ State tracking to prevent reminder spam
- ✅ Fully configurable via environment variables
- ✅ No hardcoded paths or credentials
- ✅ Multi-host deployment support

## Installation

### 1. Clone pot-o-skills (if not already done)
```bash
cd /opt
git clone https://github.com/leprachuan/pot-o-skills.git
```

### 2. Configure Environment (Optional)
Set environment variables for your deployment:
```bash
export TODO_FILE="/path/to/your/TODOs.md"
export TODO_STATE_FILE="/path/to/reminder-state.json"
```

### 3. Run TODO Reminder Service
The scheduler runs `todo_reminder.py` every minute:
```bash
python3 /opt/pot-o-skills/todo-tracker/todo_reminder.py
```

### 4. Use the CLI
```bash
python3 /opt/pot-o-skills/todo-tracker/copilot/todo_cli.py add "Your task"
```

## Troubleshooting

### Reminders not sending
1. Verify `TODO_REMINDER_CHANNEL` is set (default: `telegram`)
2. Check that notification credentials are loaded from config files
3. Verify `TELEGRAM_CONFIG_PATHS` or `WEBEX_CONFIG_PATHS` point to valid files
4. Check logs in `TODO_STATE_FILE` location

### TODOs not saving
1. Verify `TODO_FILE` environment variable is set
2. Check that the directory is writable
3. Verify `TODO_STATE_FILE` directory exists and is writable

### Import errors
1. Install dependencies: `pip install pyyaml python-dateutil`
2. Verify Python path includes skill directory
3. Check that notification skill paths are correct

## License

MIT
