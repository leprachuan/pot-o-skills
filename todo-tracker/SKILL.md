---
name: todo-tracker
description: Production-ready TODO management with markdown storage, due dates, labels, and automatic reminders. Fully portable with environment variable configuration.
---

# TODO Tracker Skill

A comprehensive TODO management system with markdown-based storage, due dates, labels, and automatic reminders. Fully portable and configurable for multi-host deployments.

## Features

- ✅ **Markdown Storage** - TODOs stored in human-readable markdown format
- ✅ **Due Dates** - Support for date-only and timed due dates
- ✅ **Labels** - Organize TODOs by labels (FAMILY, WORK, HOME_LAB, URGENT, etc)
- ✅ **Automatic Reminders** - Smart reminder tiers (1 day, 1 hour, 15 min before, at time, overdue)
- ✅ **Snooze Support** - Temporarily silence reminders until snooze expires
- ✅ **State Tracking** - Prevents reminder spam by tracking which reminders have fired
- ✅ **Fully Portable** - Environment variables for all paths and configurations
- ✅ **Multi-Host** - Works on CLI-Tools, MacBook, Docker, or any environment
- ✅ **No Credentials in Code** - All credentials loaded from external config files

## Configuration

All paths and settings are configurable via environment variables:

```bash
export TODO_FILE="/path/to/TODOs.md"
export TODO_STATE_FILE="~/.todo-reminder-state.json"
export TODO_REMINDER_CHANNEL="telegram"  # or "webex"
export TELEGRAM_CONFIG_PATHS="/path/to/config.json"
export TELEGRAM_SKILL_PATH="/opt/skills/telegram-notify"
```

See README.md for complete configuration options.

## Usage

### Add a TODO
```bash
python3 copilot/todo_cli.py add "Buy milk" --due 03/15/2026 --labels SHOPPING
```

### List TODOs
```bash
python3 copilot/todo_cli.py list active
python3 copilot/todo_cli.py list completed
```

### Complete a TODO
```bash
python3 copilot/todo_cli.py complete "Buy milk"
```

### Get Upcoming/Overdue
```bash
python3 copilot/todo_cli.py upcoming
python3 copilot/todo_cli.py overdue
```

### Run Reminder Service
```bash
python3 todo_reminder.py
```

## Runtimes

### Claude
Python-based implementation with full TODO management capabilities.

### Copilot CLI
Python CLI tool for terminal-based TODO management.

### Gemini
JavaScript implementation for web-based TODO interfaces.

## Storage Format

TODOs are stored as individual files in ACTIVE/ and COMPLETED/ directories:

```
/opt/fosterbot-home/TODOs/
├── ACTIVE/
│   ├── 🐛 Investigate Claude session ID handling for 404 errors
│   ├── 📏 Measure all rooms
│   ├── 💰 Taxes due end of March
│   └── 🎒 Purchase Italy Travel Gear
└── COMPLETED/
    ├── ✅ Auto-Runtime
    ├── ✅ Proactive Watchers - Poll to trigger AI
    └── ✅ TODO Channel Updates
```

**Format:**
- Each file = one TODO
- Filename = TODO description
- File contents = Due date, labels, notes (optional)

## Reminder Behavior

Reminders fire at these times:
- **1 day before**: Early notification
- **1 hour before**: Medium priority reminder
- **15 minutes before**: Urgent reminder
- **At due time**: Deadline reached
- **1+ hours overdue**: Overdue alert

Each reminder fires only ONCE per TODO to prevent spam. Snooze feature allows temporarily disabling reminders.

## Requirements

- Python 3.7+
- `pyyaml` - YAML parsing
- `python-dateutil` - Date/time utilities
- `telegram-notify` skill (for Telegram reminders)
- `webex-notify` skill (for WebEx reminders)

## Security

- ✅ No hardcoded credentials
- ✅ Credentials loaded from external config files
- ✅ All paths configurable via environment variables
- ✅ Git-safe (all config in .gitignore)
- ✅ No secrets in repository

## License

MIT
