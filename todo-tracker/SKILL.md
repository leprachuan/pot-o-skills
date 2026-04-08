---
name: todo-tracker
description: Production-ready TODO management with dual-source support (GitHub Issues + flat files), due dates, labels, and automatic reminders. Fully portable with environment variable configuration.
---

# TODO Tracker Skill

A comprehensive TODO management system with dual-source support — reads from **GitHub Issues** (primary) and **flat files** (fallback). Includes markdown-based storage, due dates, labels, and automatic reminders.

## Features

- ✅ **Dual Source** - GitHub Issues (primary) + flat files (fallback), deduplicated by title
- ✅ **Short IDs** - Every TODO gets a unique 5-char ID (T + 4 alphanumeric) for easy reference
- ✅ **GitHub Issues** - TODOs as issues in `leprachuan/fosterbot-home` with labels & metadata
- ✅ **Markdown Storage** - Flat-file TODOs stored in human-readable markdown format
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

### TODO IDs

Every TODO is automatically assigned a unique short ID in the format `Txxxx` (e.g. `Tktbj`).
All commands accept either the ID or the full description.

```bash
# These are equivalent:
python3 copilot/todo_cli.py note Tktbj "Checked Amazon"
python3 copilot/todo_cli.py note "Get a label maker" "Checked Amazon"
```

To backfill IDs onto existing TODOs that don't have one:
```bash
python3 copilot/todo_cli.py backfill-ids
```

### Add a TODO
```bash
python3 copilot/todo_cli.py add "Buy milk" --due 03/15/2026 --labels SHOPPING
```

### List TODOs
```bash
# Dual-source (GitHub + flat files, deduplicated)
python3 copilot/todo_cli.py list active

# GitHub Issues only
python3 copilot/todo_cli.py list active --source github

# Flat files only
python3 copilot/todo_cli.py list active --source flat

# Standalone dual-source provider
python3 github_todo_provider.py summary
python3 github_todo_provider.py list
python3 github_todo_provider.py github-only
python3 github_todo_provider.py flat-only
```

### Create a TODO (GitHub Issue)
```bash
python3 github_todo_provider.py create --title "New task" --due "2026-05-01" --labels "home,todo"
```

### Complete a TODO
```bash
python3 copilot/todo_cli.py complete "Buy milk"
```

### Append a Progress Note
```bash
python3 copilot/todo_cli.py note "Buy milk" "Checked store — out of stock, trying Costco tomorrow"
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

## Progress Tracking

**When working on a TODO, always record progress into its notes.** This creates a timestamped activity log inside the TODO file so anyone (human or agent) can see what was done, what's pending, and what decisions were made.

### When to Add Notes

- **Starting work** — note what you're about to do
- **Key milestones** — completed a sub-step, deployed something, got a result
- **Decisions made** — chose approach A over B, skipped something and why
- **Blockers or handoffs** — waiting on X, handed off to Y
- **Completion** — summarize what was done before marking complete

### How

```bash
# CLI
python3 /opt/pot-o-skills/todo-tracker/copilot/todo_cli.py note "Task name" "Started investigating the root cause"
python3 /opt/pot-o-skills/todo-tracker/copilot/todo_cli.py note "Task name" "Fixed — updated config in /etc/foo.conf"

# Python (from agent code)
from todo_manager import TodoManager
manager = TodoManager()
manager.append_note("Task name", "Deployed fix to dev, awaiting QA")
```

Notes are appended with a timestamp, so the file builds up a log:
```
ID: Ta3f7
DUE: 2026-04-01 10:00
LABELS: {HOME_LAB}
[2026-03-31 14:22] Started investigating DNS resolution failures
[2026-03-31 14:35] Root cause: stale /etc/resolv.conf after DHCP renewal
[2026-03-31 14:40] Fixed — pointed to local DNS server 192.168.0.1
```

## Runtimes

### Claude
Python-based implementation with full TODO management capabilities.

### Copilot CLI
Python CLI tool for terminal-based TODO management.

### Gemini
JavaScript implementation for web-based TODO interfaces.

## Storage

### Primary: GitHub Issues (`leprachuan/fosterbot-home`)

TODOs are stored as GitHub Issues labelled `todo`. Additional labels (`financial`, `health`, `home`, `tech`, `synced-from-reminders`) categorize them. Due dates are embedded in the issue body.

```bash
# Set custom repo
export TODO_GITHUB_REPO="leprachuan/fosterbot-home"
```

### Fallback: Flat Files

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
- First line = `ID: Txxxx` (unique short ID)
- File contents = ID, due date, labels, notes (optional)

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
