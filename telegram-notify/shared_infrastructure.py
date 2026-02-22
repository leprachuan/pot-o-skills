"""Shared Telegram notification infrastructure."""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

class TelegramNotifier:
    def _load_env_file(self):
        """Load .env file from skill directory or parent directories."""
        env_paths = [
            Path(__file__).parent / ".env",  # /opt/skills/telegram-notify/.env
            Path("/opt/skills/telegram-notify/.env",),
        ]

        for env_path in env_paths:
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            if key not in os.environ:  # Don't override existing env vars
                                os.environ[key] = value
                return True
        return False

    def __init__(self):
        # Load from .env file first, then environment variables
        self._load_env_file()

        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.max_retries = int(os.getenv("TELEGRAM_MAX_RETRIES", 3))
        self.logs_dir = Path(os.getenv("TELEGRAM_LOGS_DIR", "/opt/.telegram-notify/logs/"))
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
    
    def send_notification(self, text: str, priority: bool = False) -> dict:
        """Send text notification via Telegram."""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            
            for attempt in range(self.max_retries):
                try:
                    response = requests.post(url, json=payload, timeout=5)
                    if response.status_code == 200:
                        msg_id = response.json().get("result", {}).get("message_id")
                        self._log(f"Sent: {text[:50]}... (msg_id: {msg_id})")
                        return {"success": True, "message": "Notification sent", "result": {"message_id": msg_id}}
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        continue
                    raise e
        except Exception as e:
            self._log(f"Error: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def send_alert(self, text: str) -> dict:
        """Send high-priority alert."""
        alert_text = f"🚨 *ALERT*\n{text}"
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
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return {"success": True, "message": "Connection OK"}
            return {"success": False, "message": f"API error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def configure(self, token: str, chat_id: str) -> dict:
        """Update configuration."""
        os.environ["TELEGRAM_BOT_TOKEN"] = token
        os.environ["TELEGRAM_CHAT_ID"] = chat_id
        self.bot_token = token
        self.chat_id = chat_id
        return {"success": True, "message": "Configuration updated"}
    
    def send_photo(self, file_path: str, caption: Optional[str] = None) -> dict:
        """Send a photo file via Telegram."""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            files = {"photo": open(file_path, "rb")}
            data = {"chat_id": self.chat_id}
            if caption:
                data["caption"] = caption
                data["parse_mode"] = "Markdown"
            for attempt in range(self.max_retries):
                try:
                    response = requests.post(url, data=data, files=files, timeout=10)
                    if response.status_code == 200:
                        msg_id = response.json().get("result", {}).get("message_id")
                        self._log(f"Sent photo: {file_path} (msg_id: {msg_id})")
                        return {"success": True, "message": "Photo sent", "result": {"message_id": msg_id}}
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        continue
                    raise e
        except Exception as e:
            self._log(f"Error sending photo: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _log(self, message: str):
        """Log to message history."""
        log_file = self.logs_dir / "messages.log"
        timestamp = datetime.utcnow().isoformat() + "Z"
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
