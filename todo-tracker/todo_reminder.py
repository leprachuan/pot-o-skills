#!/usr/bin/env python3
"""
TODO Reminder Task
Checks for upcoming/overdue TODOs and sends reminders via configurable channels (Telegram or WebEx).
Runs every 1 minute via wee-orchestrator task-scheduler.

Key design principles:
- Each reminder tier fires ONCE per todo (no repeated spam)
- Snooze support: snoozed todos are silenced until snooze expires
- State tracked via TODO_STATE_FILE env var or ~/.todo-reminder-state.json
- Notification channel configurable via TODO_REMINDER_CHANNEL env var or config file
- All paths configurable via environment variables for multi-host deployment
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from todo_manager import TodoManager

# Configurable paths — use environment variables or sensible defaults
# STATE_FILE: tracks which reminders have already fired for each TODO
STATE_FILE = Path(os.environ.get("TODO_STATE_FILE", str(Path.home() / ".todo-reminder-state.json")))

# CONFIG_FILE: optional configuration file for reminder settings and notifier tokens
CONFIG_FILE = Path(os.environ.get("TODO_CONFIG_FILE", str(Path.home() / ".todo-reminder-config.json")))

# Reminder tiers define WHEN to fire (seconds before due) and a label.
# Each tier fires exactly once per todo. Ordered latest-first so we
# always send the most relevant tier.
TIMED_TIERS = [
    ("1day",   86400),   # 24 hours before
    ("1hour",  3600),    # 1 hour before
    ("15min",  900),     # 15 minutes before
    ("now",    0),       # at due time
    ("overdue_1h", -3600),  # 1 hour past due
]

DATE_ONLY_TIERS = [
    ("1day",   86400),   # 1 day before (morning of prior day)
    ("today",  0),       # on the day
    ("overdue", -86400), # 1 day past due
]


def load_state() -> dict:
    """Load reminder state from disk"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(state: dict) -> None:
    """Save reminder state to disk"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except OSError as e:
        print(f"Warning: Could not save state: {e}", file=sys.stderr)


def send_telegram_reminder(message: str) -> bool:
    """Send reminder via Telegram using telegram-notify skill infrastructure"""
    try:
        if not os.getenv("TELEGRAM_BOT_TOKEN"):
            # Try to load from config file paths (env var or sensible defaults)
            cfg_paths = os.getenv("TELEGRAM_CONFIG_PATHS", "").split(":")
            if not cfg_paths or not cfg_paths[0]:  # Use defaults if not set
                cfg_paths = ["/opt/n8n-copilot-shim/telegram_config.json",
                             "/opt/n8n-copilot-shim-dev/telegram_config.json"]

            for cfg_path in cfg_paths:
                try:
                    cfg = json.load(open(cfg_path))
                    os.environ["TELEGRAM_BOT_TOKEN"] = cfg["token"]
                    pairings = cfg.get("user_pairings", {})
                    if pairings and not os.getenv("TELEGRAM_CHAT_ID"):
                        os.environ["TELEGRAM_CHAT_ID"] = str(next(iter(pairings)))
                    break
                except Exception:
                    continue

        # Remove webex from path to avoid conflicts
        sys.path = [p for p in sys.path if 'webex-notify' not in p]
        telegram_skill_path = os.getenv("TELEGRAM_SKILL_PATH", "/opt/skills/telegram-notify")
        sys.path.insert(0, telegram_skill_path)
        from shared_infrastructure import TelegramNotifier
        notifier = TelegramNotifier()
        result = notifier.send_notification(message)
        return result.get('success', False) if result else False
    except Exception as e:
        print(f"Warning: Could not send Telegram reminder: {e}", file=sys.stderr)
        return False


def send_webex_reminder(message: str) -> bool:
    """Send reminder via WebEx using webex-notify skill infrastructure"""
    try:
        # Load WebEx config from env var or sensible defaults
        webex_config = None
        cfg_paths = os.getenv("WEBEX_CONFIG_PATHS", "").split(":")
        if not cfg_paths or not cfg_paths[0]:  # Use defaults if not set
            cfg_paths = ["/opt/n8n-copilot-shim/webex_config.json",
                         "/opt/n8n-copilot-shim-dev/webex_config.json"]

        for cfg_path in cfg_paths:
            try:
                cfg = json.load(open(cfg_path))
                webex_config = cfg
                break
            except Exception:
                continue

        if not webex_config:
            print("Warning: No WebEx config found", file=sys.stderr)
            return False

        # Remove telegram from path to avoid conflicts
        sys.path = [p for p in sys.path if 'telegram-notify' not in p]
        webex_skill_path = os.getenv("WEBEX_SKILL_PATH", "/opt/skills/webex-notify")
        sys.path.insert(0, webex_skill_path)
        from shared_infrastructure import WebExNotifier
        notifier = WebExNotifier()
        result = notifier.send_notification(message)
        return result.get('success', False) if result else False
    except Exception as e:
        print(f"Warning: Could not send WebEx reminder: {e}", file=sys.stderr)
        return False


def send_reminder(message: str) -> bool:
    """Send notification via configured channel"""
    channel = os.getenv("TODO_REMINDER_CHANNEL", "telegram").lower()

    if channel == "telegram":
        return send_telegram_reminder(message)
    elif channel == "webex":
        return send_webex_reminder(message)
    else:
        print(f"Unknown reminder channel: {channel}", file=sys.stderr)
        return False


def check_reminders() -> None:
    """Check for TODOs that need reminders and send them"""
    manager = TodoManager()
    todos = manager.load_todos()
    state = load_state()
    current_time = datetime.now()

    for todo in todos:
        if todo.get("completed"):
            continue

        # State key is the todo description (stable identifier)
        key = todo.get("description")
        if not key:
            continue

        todo_state = state.get(key, {})
        snoozed_until_str = todo_state.get("snoozed_until")
        if snoozed_until_str:
            try:
                snoozed_dt = datetime.fromisoformat(snoozed_until_str)
                if current_time < snoozed_dt:
                    # Still snoozed, skip
                    continue
                else:
                    # Snooze expired, clear it
                    todo_state.pop("snoozed_until", None)
            except ValueError:
                pass

        due_str = todo.get("due")
        if not due_str:
            continue

        # Parse due date/time
        try:
            if " " in due_str:
                due_dt = datetime.fromisoformat(due_str)
                tiers = TIMED_TIERS
            else:
                due_dt = datetime.fromisoformat(due_str)
                tiers = DATE_ONLY_TIERS
        except ValueError:
            continue

        # Walk tiers from earliest (1day) to latest (overdue).
        # Fire only the most relevant tier.
        for tier_name, offset_seconds in reversed(tiers):
            tier_dt = due_dt + timedelta(seconds=offset_seconds)
            fired_key = f"fired_{tier_name}"

            if current_time >= tier_dt and not todo_state.get(fired_key):
                # Fire this tier
                message = f"📋 {tier_name.upper()}: {todo.get('description')}"
                if due_str:
                    message += f"\n📅 Due: {due_str}"
                if todo.get("notes"):
                    message += f"\n📝 {todo.get('notes')}"

                if send_reminder(message):
                    todo_state[fired_key] = True
                    state[key] = todo_state
                    save_state(state)
                break

    # Remove stale state entries for deleted todos
    active_descriptions = set(t.get("description") for t in todos if t.get("description"))
    stale_keys = [k for k in state if k not in active_descriptions]
    for k in stale_keys:
        del state[k]
    if stale_keys:
        save_state(state)


if __name__ == "__main__":
    check_reminders()
