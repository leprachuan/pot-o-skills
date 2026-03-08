"""State manager for proactive watchers - persists watcher state and history."""

import json
import os
import time
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("proactive-watchers.state")

DEFAULT_WATCHERS_DIR = os.path.expanduser("~/.proactive-watchers")


class StateManager:
    """Manages watcher definitions, state persistence, and event history."""

    def __init__(self, watchers_dir: Optional[str] = None):
        self.watchers_dir = Path(watchers_dir or os.environ.get("WATCHERS_DIR", DEFAULT_WATCHERS_DIR))
        self.watchers_file = self.watchers_dir / "watchers.json"
        self.history_dir = self.watchers_dir / "history"
        self.templates_dir = self.watchers_dir / "templates"
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create storage directories if they don't exist."""
        self.watchers_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def load_watchers(self) -> list[dict]:
        """Load all watcher definitions from watchers.json."""
        if not self.watchers_file.exists():
            return []
        try:
            with open(self.watchers_file, "r") as f:
                data = json.load(f)
            return data.get("watchers", [])
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load watchers: {e}")
            return []

    def save_watchers(self, watchers: list[dict]):
        """Save watcher definitions to watchers.json."""
        with open(self.watchers_file, "w") as f:
            json.dump({"watchers": watchers, "updated_at": time.time()}, f, indent=2)

    def get_watcher(self, name: str) -> Optional[dict]:
        """Get a specific watcher by name."""
        for w in self.load_watchers():
            if w.get("name") == name:
                return w
        return None

    def add_watcher(self, watcher: dict) -> bool:
        """Add a new watcher definition. Returns False if name already exists."""
        watchers = self.load_watchers()
        if any(w["name"] == watcher["name"] for w in watchers):
            logger.error(f"Watcher '{watcher['name']}' already exists")
            return False
        watcher.setdefault("enabled", True)
        watcher.setdefault("created_at", time.time())
        watchers.append(watcher)
        self.save_watchers(watchers)
        logger.info(f"Added watcher: {watcher['name']}")
        return True

    def update_watcher(self, name: str, updates: dict) -> bool:
        """Update an existing watcher definition."""
        watchers = self.load_watchers()
        for i, w in enumerate(watchers):
            if w["name"] == name:
                watchers[i].update(updates)
                watchers[i]["updated_at"] = time.time()
                self.save_watchers(watchers)
                return True
        return False

    def remove_watcher(self, name: str) -> bool:
        """Remove a watcher by name."""
        watchers = self.load_watchers()
        filtered = [w for w in watchers if w["name"] != name]
        if len(filtered) == len(watchers):
            return False
        self.save_watchers(filtered)
        logger.info(f"Removed watcher: {name}")
        return True

    def get_state(self, watcher_name: str) -> dict:
        """Get the last known state for a watcher."""
        state_file = self.history_dir / f"{watcher_name}_state.json"
        if not state_file.exists():
            return {}
        try:
            with open(state_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def save_state(self, watcher_name: str, state: dict):
        """Save the current state for a watcher."""
        state_file = self.history_dir / f"{watcher_name}_state.json"
        state["updated_at"] = time.time()
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def log_event(self, watcher_name: str, event: dict):
        """Append an event to the watcher's history log."""
        log_file = self.history_dir / f"{watcher_name}.log"
        event.setdefault("timestamp", time.time())
        event.setdefault("iso_time", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        with open(log_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def get_history(self, watcher_name: str, limit: int = 50) -> list[dict]:
        """Get recent events from a watcher's history log."""
        log_file = self.history_dir / f"{watcher_name}.log"
        if not log_file.exists():
            return []
        events = []
        try:
            with open(log_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except IOError:
            return []
        return events[-limit:]

    def clear_history(self, watcher_name: str):
        """Clear a watcher's event history."""
        log_file = self.history_dir / f"{watcher_name}.log"
        if log_file.exists():
            log_file.unlink()

    def list_watcher_names(self) -> list[str]:
        """Get names of all defined watchers."""
        return [w["name"] for w in self.load_watchers()]
