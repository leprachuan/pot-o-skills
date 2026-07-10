"""Telegram notify for Claude."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared_infrastructure import TelegramNotifier

class TelegramNotifySkill:
    def __init__(self):
        self.notifier = TelegramNotifier()
    
    def send_notification(self, text: str):
        return self.notifier.send_notification(text)
    
    def send_alert(self, text: str):
        return self.notifier.send_alert(text)
    
    def get_message_history(self):
        return self.notifier.get_message_history()
    
    def test_connection(self):
        return self.notifier.test_connection()
    
    def configure(self, token: str, chat_id: str):
        return self.notifier.configure(token, chat_id)
