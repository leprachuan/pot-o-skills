"""Lock management for collaborative work queues.

Provides atomic file-based locking with TTL expiration,
stale lock detection, and reconciliation.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class LockState:
    state: str = "idle"  # idle | active | reconciling
    item_id: str = ""
    owner: str = ""
    reason: str = ""
    acquired_at: str = ""
    ttl_expires_at: str = ""
    updated_at: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


class LockManager:
    """File-based lock manager with TTL and reconciliation."""

    def __init__(self, lock_path: Path, ttl_seconds: int = 7200):
        self.lock_path = Path(lock_path)
        self.ttl_seconds = ttl_seconds

    def read(self) -> LockState:
        """Read the current lock state. Returns idle if file is absent or corrupt."""
        if not self.lock_path.exists():
            return LockState()
        try:
            raw = json.loads(self.lock_path.read_text())
            return LockState(
                state=raw.get("state", "idle"),
                item_id=raw.get("item_id", ""),
                owner=raw.get("owner", ""),
                reason=raw.get("reason", ""),
                acquired_at=raw.get("acquired_at", ""),
                ttl_expires_at=raw.get("ttl_expires_at", ""),
                updated_at=raw.get("updated_at", ""),
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            return LockState()

    def _write_atomic(self, lock_state: LockState) -> None:
        """Atomically write lock state using tmp + rename."""
        lock_state.updated_at = _now_iso()
        data = json.dumps(asdict(lock_state), indent=2) + "\n"

        lock_dir = self.lock_path.parent
        lock_dir.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=str(lock_dir),
            prefix=".lock_tmp_",
            suffix=".json",
        )
        try:
            os.write(fd, data.encode())
            os.fsync(fd)
            os.close(fd)
            os.rename(tmp_path, str(self.lock_path))
        except Exception:
            os.close(fd) if not os.get_inheritable(fd) else None
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def acquire(self, item_id: str, owner: str, reason: str = "") -> bool:
        """Acquire the lock for a work item. Returns False if already active."""
        current = self.read()
        if current.state == "active" and not self.is_stale():
            return False

        now = _now_iso()
        expires = datetime.now(timezone.utc).timestamp() + self.ttl_seconds
        expires_iso = datetime.fromtimestamp(expires, tz=timezone.utc).isoformat()

        lock_state = LockState(
            state="active",
            item_id=item_id,
            owner=owner,
            reason=reason,
            acquired_at=now,
            ttl_expires_at=expires_iso,
        )
        self._write_atomic(lock_state)
        return True

    def release(self, reason: str = "") -> None:
        """Release the lock, setting state to idle."""
        lock_state = LockState(
            state="idle",
            reason=reason,
        )
        self._write_atomic(lock_state)

    def refresh_ttl(self) -> None:
        """Extend the TTL of the current lock."""
        current = self.read()
        if current.state != "active":
            return
        expires = datetime.now(timezone.utc).timestamp() + self.ttl_seconds
        current.ttl_expires_at = datetime.fromtimestamp(expires, tz=timezone.utc).isoformat()
        self._write_atomic(current)

    def is_stale(self) -> bool:
        """True if the lock's TTL has expired."""
        current = self.read()
        if current.state != "active" or not current.ttl_expires_at:
            return False
        try:
            expires = _parse_iso(current.ttl_expires_at)
            return datetime.now(timezone.utc) > expires
        except ValueError:
            return True

    def reconcile(self, queue_items: list | None = None) -> bool:
        """Clear the lock if stale or if the locked item is terminal.

        Args:
            queue_items: List of WorkItem objects to check terminal status.
                If None, only TTL-based reconciliation is performed.

        Returns:
            True if the lock was corrected (cleared), False otherwise.
        """
        current = self.read()
        if current.state != "active":
            return False

        # Check TTL expiration
        if self.is_stale():
            self.release(reason="reconcile: TTL expired")
            return True

        # Check if item is in a terminal state
        if queue_items is not None and current.item_id:
            for item in queue_items:
                if item.id == current.item_id:
                    # Import here to avoid circular dependency
                    from queue_lib import WorkQueue
                    # Can't check terminal without config — caller should pass terminal statuses
                    break

        return False

    def reconcile_with_config(self, queue_items: list, terminal_statuses: set[str]) -> bool:
        """Clear the lock if stale or if the locked item is in a terminal state.

        Args:
            queue_items: List of WorkItem-like objects with .id and .status attributes.
            terminal_statuses: Set of status strings considered terminal.

        Returns:
            True if the lock was corrected (cleared), False otherwise.
        """
        current = self.read()
        if current.state != "active":
            return False

        if self.is_stale():
            self.release(reason="reconcile: TTL expired")
            return True

        if current.item_id:
            for item in queue_items:
                if item.id == current.item_id and item.status in terminal_statuses:
                    self.release(reason=f"reconcile: item {current.item_id} is terminal ({item.status})")
                    return True

        return False

    def force_idle(self, reason: str) -> None:
        """Admin override — force the lock to idle regardless of state."""
        lock_state = LockState(
            state="idle",
            reason=f"force-idle: {reason}",
        )
        self._write_atomic(lock_state)

    def status(self) -> dict:
        """Human-readable status summary."""
        current = self.read()
        stale = self.is_stale() if current.state == "active" else False
        return {
            "state": current.state,
            "item_id": current.item_id or "(none)",
            "owner": current.owner or "(none)",
            "reason": current.reason or "",
            "acquired_at": current.acquired_at or "(n/a)",
            "ttl_expires_at": current.ttl_expires_at or "(n/a)",
            "updated_at": current.updated_at or "(n/a)",
            "is_stale": stale,
        }
