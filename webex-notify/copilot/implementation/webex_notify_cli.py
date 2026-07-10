#!/usr/bin/env python3
"""WebEx notify CLI for Copilot."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared_infrastructure import WebExNotifier


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Action required"}))
        return

    try:
        notifier = WebExNotifier()
        action = sys.argv[1]

        if action == "send_notification":
            text = sys.argv[2]
            result = notifier.send_notification(text)
        elif action == "send_alert":
            text = sys.argv[2]
            result = notifier.send_alert(text)
        elif action == "get_message_history":
            result = notifier.get_message_history()
        elif action == "test_connection":
            result = notifier.test_connection()
        elif action == "configure":
            token = sys.argv[2]
            room_id = sys.argv[3]
            result = notifier.configure(token, room_id)
        else:
            result = {"success": False, "message": f"Unknown action: {action}"}

        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))


if __name__ == "__main__":
    main()
