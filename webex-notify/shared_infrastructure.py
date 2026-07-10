"""Shared WebEx notification infrastructure."""
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class WebExNotifier:
    def __init__(self):
        self.bot_token = os.getenv("WEBEX_BOT_TOKEN")
        self.room_id = os.getenv("WEBEX_ROOM_ID", None)
        self.person_email = os.getenv("WEBEX_PERSON_EMAIL", None)
        self.max_retries = int(os.getenv("WEBEX_MAX_RETRIES", 3))
        self.retry_delay = float(os.getenv("WEBEX_RETRY_DELAY", 2))
        self.rate_limit_messages = int(os.getenv("WEBEX_RATE_LIMIT_MESSAGES", 30))
        self.rate_limit_window = int(os.getenv("WEBEX_RATE_LIMIT_WINDOW", 60))
        self.logs_dir = Path(os.getenv("WEBEX_LOGS_DIR", "/opt/.webex-notify/logs/"))
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Rate limiting tracking
        self.message_timestamps = []

        if not self.bot_token:
            raise ValueError("WEBEX_BOT_TOKEN must be set in .env")
        if not self.room_id and not self.person_email:
            raise ValueError("Either WEBEX_ROOM_ID or WEBEX_PERSON_EMAIL must be set in .env")

    def _rate_limit_check(self) -> None:
        """Check and enforce rate limiting."""
        now = time.time()
        # Remove timestamps outside the window
        self.message_timestamps = [ts for ts in self.message_timestamps
                                   if now - ts < self.rate_limit_window]

        # If we've hit the limit, wait
        if len(self.message_timestamps) >= self.rate_limit_messages:
            oldest = self.message_timestamps[0]
            wait_time = self.rate_limit_window - (now - oldest)
            if wait_time > 0:
                time.sleep(wait_time)

        self.message_timestamps.append(now)

    def send_notification(self, text: str, priority: bool = False, to_email: str = None) -> dict:
        """Send text notification via WebEx to room or direct message to person."""
        try:
            import requests

            # Rate limiting
            self._rate_limit_check()

            url = "https://webexapis.com/v1/messages"
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            }

            # Use provided email or environment variable, or room
            if to_email:
                payload = {
                    "toPersonEmail": to_email,
                    "markdown": text
                }
            elif self.person_email:
                payload = {
                    "toPersonEmail": self.person_email,
                    "markdown": text
                }
            else:
                payload = {
                    "roomId": self.room_id,
                    "markdown": text
                }

            for attempt in range(self.max_retries):
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=5)
                    if response.status_code == 200:
                        msg_id = response.json().get("id")
                        self._log(f"Sent: {text[:50]}... (msg_id: {msg_id})")
                        return {"success": True, "message": "Notification sent", "result": {"message_id": msg_id}}
                    elif response.status_code >= 400:
                        # Don't retry on 4xx errors (bad token, room not found, etc)
                        error_msg = response.json().get("message", f"HTTP {response.status_code}")
                        self._log(f"Error (attempt {attempt + 1}): {error_msg}")
                        if response.status_code < 500:
                            raise Exception(error_msg)
                        # For 5xx, try again
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                        raise Exception(error_msg)
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    raise e
        except Exception as e:
            self._log(f"Error: {str(e)}")
            return {"success": False, "message": str(e)}

    def send_alert(self, text: str) -> dict:
        """Send high-priority alert."""
        alert_text = f"**🚨 ALERT**\n{text}"
        return self.send_notification(alert_text, priority=True)

    def get_message_history(self) -> dict:
        """Get message history."""
        log_file = self.logs_dir / "messages.log"
        if log_file.exists():
            return {"success": True, "result": log_file.read_text()}
        return {"success": False, "message": "No message history"}

    def test_connection(self) -> dict:
        """Test bot connectivity."""
        try:
            import requests
            url = "https://webexapis.com/v1/people/me"
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                bot_info = response.json()
                return {"success": True, "message": f"Connection OK - Bot: {bot_info.get('displayName', 'Unknown')}"}
            return {"success": False, "message": f"API error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def configure(self, token: str, room_id: str) -> dict:
        """Update configuration."""
        os.environ["WEBEX_BOT_TOKEN"] = token
        os.environ["WEBEX_ROOM_ID"] = room_id
        self.bot_token = token
        self.room_id = room_id
        return {"success": True, "message": "Configuration updated"}

    def _log(self, message: str):
        """Log to message history."""
        log_file = self.logs_dir / "messages.log"
        timestamp = datetime.utcnow().isoformat() + "Z"
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
