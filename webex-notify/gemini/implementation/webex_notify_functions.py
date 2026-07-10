"""WebEx notify functions for Gemini."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared_infrastructure import WebExNotifier

notifier = WebExNotifier()


def send_notification(text: str):
    return notifier.send_notification(text)


def send_alert(text: str):
    return notifier.send_alert(text)


def get_message_history():
    return notifier.get_message_history()


def test_connection():
    return notifier.test_connection()


def configure(token: str, room_id: str):
    return notifier.configure(token, room_id)
