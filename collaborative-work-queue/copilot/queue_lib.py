"""Core library for collaborative work queue management.

Parses markdown tables, enforces state machine transitions,
and provides atomic queue operations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class InvalidTransitionError(Exception):
    """Raised when a status transition violates the state machine."""


@dataclass
class StatusConfig:
    transitions_to: list[str] = field(default_factory=list)
    terminal: bool = False
    move_to_section: str | None = None


@dataclass
class RoleConfig:
    agent: str = ""
    handles_statuses: list[str] = field(default_factory=list)
    sets_status_to: str = ""
    max_concurrent: int = 1
    model: str = "claude-sonnet-4.6"
    timeout: int = 3600
    prompt_template: str = ""
    trigger_after: list[str] = field(default_factory=list)


@dataclass
class QueueConfig:
    name: str = ""
    queue_dir: str = "."
    queue_files: list[str] = field(default_factory=list)
    lock_file: str = "WORK_QUEUE.lock.json"
    lock_ttl_seconds: int = 7200
    statuses: dict[str, StatusConfig] = field(default_factory=dict)
    roles: dict[str, RoleConfig] = field(default_factory=dict)
    dispatch_api_url: str = "https://127.0.0.1:8000/api/v1/background-tasks"
    dispatch_api_token_env: str = "WEE_API_TOKEN"
    dispatch_stall_threshold_seconds: int = 7200
    dispatch_runtime: str = "copilot"

    @classmethod
    def from_yaml(cls, path: Path) -> QueueConfig:
        with open(path) as f:
            raw = yaml.safe_load(f)

        q = raw.get("queue", {})
        lock = raw.get("lock", {})
        dispatch = raw.get("dispatch", {})

        statuses: dict[str, StatusConfig] = {}
        for name, cfg in raw.get("statuses", {}).items():
            statuses[name] = StatusConfig(
                transitions_to=cfg.get("transitions_to", []),
                terminal=cfg.get("terminal", False),
                move_to_section=cfg.get("move_to_section"),
            )

        roles: dict[str, RoleConfig] = {}
        for name, cfg in raw.get("roles", {}).items():
            roles[name] = RoleConfig(
                agent=cfg.get("agent", ""),
                handles_statuses=cfg.get("handles_statuses", []),
                sets_status_to=cfg.get("sets_status_to", ""),
                max_concurrent=cfg.get("max_concurrent", 1),
                model=cfg.get("model", "claude-sonnet-4.6"),
                timeout=cfg.get("timeout", 3600),
                prompt_template=cfg.get("prompt_template", ""),
                trigger_after=cfg.get("trigger_after", []),
            )

        return cls(
            name=q.get("name", ""),
            queue_dir=q.get("queue_dir", "."),
            queue_files=q.get("queue_files", []),
            lock_file=lock.get("file", "WORK_QUEUE.lock.json"),
            lock_ttl_seconds=lock.get("ttl_seconds", 7200),
            statuses=statuses,
            roles=roles,
            dispatch_api_url=dispatch.get("api_url", "https://127.0.0.1:8000/api/v1/background-tasks"),
            dispatch_api_token_env=dispatch.get("api_token_env", "WEE_API_TOKEN"),
            dispatch_stall_threshold_seconds=dispatch.get("stall_threshold_seconds", 7200),
            dispatch_runtime=dispatch.get("runtime", "copilot"),
        )


@dataclass
class WorkItem:
    id: str
    title: str
    priority: str = ""
    status: str = "queued"
    notes: str = ""
    qa_status: str = ""
    commit_sha: str = ""
    last_updated: str = ""

    def to_row(self) -> str:
        cols = [
            self.id, self.title, self.priority, self.status,
            self.notes, self.qa_status, self.commit_sha, self.last_updated,
        ]
        return "| " + " | ".join(cols) + " |"


# Regex for markdown table rows (pipe-delimited, 8 columns)
_TABLE_ROW_RE = re.compile(
    r"^\|"
    r"\s*(?P<id>[^|]+?)\s*\|"
    r"\s*(?P<title>[^|]+?)\s*\|"
    r"\s*(?P<priority>[^|]*?)\s*\|"
    r"\s*(?P<status>[^|]*?)\s*\|"
    r"\s*(?P<notes>[^|]*?)\s*\|"
    r"\s*(?P<qa_status>[^|]*?)\s*\|"
    r"\s*(?P<commit_sha>[^|]*?)\s*\|"
    r"\s*(?P<last_updated>[^|]*?)\s*\|"
    r"\s*$"
)

_SEPARATOR_RE = re.compile(r"^\|\s*[-:]+")


class WorkQueue:
    """Manages a markdown-table-based work queue with state machine enforcement."""

    def __init__(self, config: QueueConfig):
        self.config = config
        self._queue_dir = Path(config.queue_dir)

    def _resolve_path(self, queue_path: Path) -> Path:
        if queue_path.is_absolute():
            return queue_path
        return self._queue_dir / queue_path

    def parse(self, queue_path: Path) -> list[WorkItem]:
        """Parse a single markdown queue file into WorkItems."""
        resolved = self._resolve_path(queue_path)
        if not resolved.exists():
            return []

        items: list[WorkItem] = []
        for line in resolved.read_text().splitlines():
            line = line.strip()
            if not line or _SEPARATOR_RE.match(line):
                continue
            m = _TABLE_ROW_RE.match(line)
            if not m:
                continue
            d = m.groupdict()
            # Skip header row
            if d["id"].lower() in ("id", "item id", "item_id"):
                continue
            items.append(WorkItem(
                id=d["id"].strip(),
                title=d["title"].strip(),
                priority=d["priority"].strip(),
                status=d["status"].strip(),
                notes=d["notes"].strip(),
                qa_status=d["qa_status"].strip(),
                commit_sha=d["commit_sha"].strip(),
                last_updated=d["last_updated"].strip(),
            ))
        return items

    def parse_all(self) -> list[WorkItem]:
        """Parse and merge all queue files from config."""
        all_items: list[WorkItem] = []
        for qf in self.config.queue_files:
            all_items.extend(self.parse(Path(qf)))
        return all_items

    def find(self, item_id: str) -> WorkItem | None:
        for item in self.parse_all():
            if item.id == item_id:
                return item
        return None

    def items_by_status(self, status: str) -> list[WorkItem]:
        return [i for i in self.parse_all() if i.status == status]

    def next_actionable(self, handles_statuses: list[str]) -> WorkItem | None:
        """Return the highest-priority actionable item for the given statuses.

        Priority order: P0 > P1 > P2 > P3 > empty, then by queue order.
        """
        candidates = [i for i in self.parse_all() if i.status in handles_statuses]
        if not candidates:
            return None

        def priority_key(item: WorkItem) -> tuple[int, int]:
            prio = item.priority.upper()
            rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(prio, 99)
            return (rank, 0)

        candidates.sort(key=priority_key)
        return candidates[0]

    def validate_transition(self, item: WorkItem, new_status: str) -> bool:
        """Check if a status transition is valid per the state machine."""
        current = item.status
        sc = self.config.statuses.get(current)
        if sc is None:
            return False
        if sc.terminal:
            return False
        return new_status in sc.transitions_to

    def transition(
        self,
        item_id: str,
        new_status: str,
        force: bool = False,
        **field_updates: str,
    ) -> WorkItem:
        """Atomically transition an item to a new status.

        Updates the item in the markdown file, moves to completed section
        if the new status is terminal with move_to_section.
        """
        # Find which file contains this item
        target_file: Path | None = None
        target_items: list[WorkItem] = []

        for qf in self.config.queue_files:
            qpath = Path(qf)
            items = self.parse(qpath)
            for item in items:
                if item.id == item_id:
                    target_file = qpath
                    target_items = items
                    break
            if target_file:
                break

        if target_file is None:
            raise ValueError(f"Item {item_id!r} not found in any queue file")

        item = next(i for i in target_items if i.id == item_id)

        if not force and not self.validate_transition(item, new_status):
            raise InvalidTransitionError(
                f"Cannot transition {item_id!r} from {item.status!r} to {new_status!r}"
            )

        item.status = new_status
        item.last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

        for k, v in field_updates.items():
            if hasattr(item, k):
                setattr(item, k, v)

        # Check if we need to move to a completed section
        sc = self.config.statuses.get(new_status)
        move_section = sc.move_to_section if sc else None

        self._rewrite_file(target_file, target_items, item_id, move_section)
        return item

    def _rewrite_file(
        self,
        queue_path: Path,
        items: list[WorkItem],
        changed_id: str,
        move_to_section: str | None,
    ) -> None:
        """Rewrite the markdown file, preserving structure outside the table."""
        resolved = self._resolve_path(queue_path)
        original = resolved.read_text()
        lines = original.splitlines()

        items_by_id = {i.id: i for i in items}
        moved_item: WorkItem | None = None
        if move_to_section:
            moved_item = items_by_id.get(changed_id)

        new_lines: list[str] = []
        in_table = False
        header_seen = False

        for line in lines:
            stripped = line.strip()

            if _SEPARATOR_RE.match(stripped):
                in_table = True
                new_lines.append(line)
                continue

            m = _TABLE_ROW_RE.match(stripped)
            if m and in_table:
                row_id = m.group("id").strip()
                if row_id.lower() in ("id", "item id", "item_id"):
                    header_seen = True
                    new_lines.append(line)
                    continue
                if row_id in items_by_id:
                    item = items_by_id[row_id]
                    if move_to_section and row_id == changed_id:
                        # Skip this row — it will be appended to completed section
                        continue
                    new_lines.append(item.to_row())
                    continue
            elif m and not in_table:
                # Could be a header row
                row_id = m.group("id").strip()
                if row_id.lower() in ("id", "item id", "item_id"):
                    header_seen = True
                    in_table = True
                    new_lines.append(line)
                    continue

            if stripped and not stripped.startswith("|"):
                in_table = False

            new_lines.append(line)

        # Append moved item to completed section
        if moved_item and move_to_section:
            section_header = f"## {move_to_section}"
            section_idx = None
            for i, line in enumerate(new_lines):
                if line.strip().startswith(section_header):
                    section_idx = i
                    break

            if section_idx is not None:
                # Find end of existing table or section
                insert_at = section_idx + 1
                for i in range(section_idx + 1, len(new_lines)):
                    stripped = new_lines[i].strip()
                    if stripped.startswith("|") or _SEPARATOR_RE.match(stripped):
                        insert_at = i + 1
                    elif stripped.startswith("#"):
                        break
                    elif stripped == "":
                        insert_at = i
                        continue
                    else:
                        break
                new_lines.insert(insert_at, moved_item.to_row())
            else:
                # Create the section at end of file
                new_lines.append("")
                new_lines.append(section_header)
                new_lines.append("")
                new_lines.append("| ID | Title | Priority | Status | Notes | QA Status | Commit SHA | Last Updated |")
                new_lines.append("|----|-------|----------|--------|-------|-----------|------------|--------------|")
                new_lines.append(moved_item.to_row())

        resolved.write_text("\n".join(new_lines) + "\n")

    def write(self, queue_path: Path, items: list[WorkItem]) -> None:
        """Write a complete queue file from a list of WorkItems."""
        resolved = self._resolve_path(queue_path)
        lines = [
            "| ID | Title | Priority | Status | Notes | QA Status | Commit SHA | Last Updated |",
            "|----|-------|----------|--------|-------|-----------|------------|--------------|",
        ]
        for item in items:
            lines.append(item.to_row())
        resolved.write_text("\n".join(lines) + "\n")
