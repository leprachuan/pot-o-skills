#!/usr/bin/env python3
"""Telegram notify CLI for Copilot."""
import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared_infrastructure import TelegramNotifier

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Action required"}))
        return
    
    try:
        notifier = TelegramNotifier()
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
        elif action == "maybe_send_screenshot":
            # If the incoming platform is Telegram (argument or env var), send the given screenshot path (defaults to /tmp/snort_screenshot.png)
            platform = sys.argv[2] if len(sys.argv) > 2 else os.getenv("INCOMING_PLATFORM")
            file_path = sys.argv[3] if len(sys.argv) > 3 else "/tmp/snort_screenshot.png"
            caption = sys.argv[4] if len(sys.argv) > 4 else None
            if platform and platform.lower() == "telegram":
                if os.path.exists(file_path):
                    result = notifier.send_photo(file_path, caption)
                else:
                    result = {"success": False, "message": f"Screenshot not found: {file_path}"}
            else:
                result = {"success": False, "message": "Incoming platform is not Telegram"}
        elif action == "send_photo":
            file_path = sys.argv[2]
            caption = sys.argv[3] if len(sys.argv) > 3 else None
            result = notifier.send_photo(file_path, caption)
        elif action == "configure":
            token = sys.argv[2]
            chat_id = sys.argv[3]
            result = notifier.configure(token, chat_id)
        else:
            result = {"success": False, "message": f"Unknown action: {action}"}
        
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))

if __name__ == "__main__":
    main()
