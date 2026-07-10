"""Dispatch engine for collaborative work queues.

Integrates with the Wee Orchestrator background-tasks API to
dispatch agents for queue items and detect stalled work.
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from queue_lib import QueueConfig, WorkQueue, WorkItem
from lock_manager import LockManager


def _get_api_token(config: QueueConfig) -> str:
    """Resolve the API token from env var or fallback."""
    token = os.environ.get(config.dispatch_api_token_env, "")
    if not token:
        token = "shared_R6R6wReORUV6bouLntScMTowbsh30Rzqa3hzjs3bWgU"
    return token


def _api_request(
    url: str,
    token: str,
    method: str = "GET",
    data: dict | None = None,
) -> dict:
    """Make an HTTP request to the orchestrator API."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        return {"error": f"HTTP {e.code}: {body_text}"}
    except Exception as e:
        return {"error": str(e)}


class QueueDispatcher:
    """Dispatches agents for work queue items via the orchestrator API."""

    def __init__(self, config: QueueConfig):
        self.config = config
        self.queue = WorkQueue(config)
        self._lock_path = Path(config.queue_dir) / config.lock_file
        self.lock = LockManager(self._lock_path, config.lock_ttl_seconds)
        self._token = _get_api_token(config)

    def check_running_agents(self, agent_name: str) -> int:
        """Count running background tasks for a given agent."""
        url = f"{self.config.dispatch_api_url}?status=running"
        result = _api_request(url, self._token)

        if "error" in result:
            return 0

        tasks = result.get("tasks", result.get("data", []))
        if not isinstance(tasks, list):
            return 0

        count = 0
        for task in tasks:
            if isinstance(task, dict) and task.get("agent") == agent_name:
                count += 1
        return count

    def detect_stalls(self, stall_threshold_seconds: int | None = None) -> list[dict]:
        """Detect tasks that have been running longer than the threshold."""
        threshold = stall_threshold_seconds or self.config.dispatch_stall_threshold_seconds
        url = f"{self.config.dispatch_api_url}?status=running"
        result = _api_request(url, self._token)

        if "error" in result:
            return []

        tasks = result.get("tasks", result.get("data", []))
        if not isinstance(tasks, list):
            return []

        stalled: list[dict] = []
        now = datetime.now(timezone.utc)

        for task in tasks:
            if not isinstance(task, dict):
                continue
            started = task.get("started_at") or task.get("created_at", "")
            if not started:
                continue
            try:
                start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                elapsed = (now - start_dt).total_seconds()
                if elapsed > threshold:
                    stalled.append({
                        "task_id": task.get("task_id", "unknown"),
                        "agent": task.get("agent", "unknown"),
                        "elapsed_seconds": int(elapsed),
                        "prompt": task.get("prompt", "")[:100],
                    })
            except (ValueError, TypeError):
                continue

        return stalled

    def dispatch_role(self, role_name: str, item: WorkItem) -> str:
        """Dispatch a background task for a role and work item.

        Returns the task_id on success, or an error string prefixed with 'ERROR:'.
        """
        role = self.config.roles.get(role_name)
        if role is None:
            return f"ERROR: role {role_name!r} not found in config"

        prompt = role.prompt_template.format(
            item_id=item.id,
            item_title=item.title,
            item_priority=item.priority,
            item_status=item.status,
            item_notes=item.notes,
        )

        payload = {
            "prompt": prompt,
            "agent": role.agent,
            "runtime": self.config.dispatch_runtime,
            "model": role.model,
            "timeout": role.timeout,
        }

        result = _api_request(self.config.dispatch_api_url, self._token, method="POST", data=payload)

        if "error" in result:
            return f"ERROR: {result['error']}"

        task_id = result.get("task_id", result.get("id", "unknown"))
        return str(task_id)

    def run_cycle(self, dry_run: bool = False) -> dict:
        """Run a full dispatch cycle.

        Steps:
        1. Reconcile stale locks
        2. Detect stalled tasks
        3. For each role, check for actionable items and dispatch
        4. Return summary

        Args:
            dry_run: If True, don't actually dispatch — just report what would happen.
        """
        summary: dict[str, Any] = {
            "lock_reconciled": False,
            "stalled_tasks": [],
            "dispatched": [],
            "skipped": [],
            "errors": [],
        }

        # 1. Reconcile locks
        terminal_statuses = {
            name for name, sc in self.config.statuses.items() if sc.terminal
        }
        all_items = self.queue.parse_all()
        reconciled = self.lock.reconcile_with_config(all_items, terminal_statuses)
        summary["lock_reconciled"] = reconciled

        # 2. Detect stalls
        stalled = self.detect_stalls()
        summary["stalled_tasks"] = stalled

        # 3. Dispatch per role
        for role_name, role in self.config.roles.items():
            # Skip trigger_after roles (they fire on completion, not in dispatch cycle)
            if role.trigger_after:
                continue

            if not role.handles_statuses:
                continue

            # Check concurrency
            running = self.check_running_agents(role.agent)
            if running >= role.max_concurrent:
                summary["skipped"].append({
                    "role": role_name,
                    "reason": f"agent {role.agent} at max concurrency ({running}/{role.max_concurrent})",
                })
                continue

            # Find next actionable item
            item = self.queue.next_actionable(role.handles_statuses)
            if item is None:
                summary["skipped"].append({
                    "role": role_name,
                    "reason": "no actionable items",
                })
                continue

            # Check lock
            lock_state = self.lock.read()
            if lock_state.state == "active" and not self.lock.is_stale():
                summary["skipped"].append({
                    "role": role_name,
                    "item_id": item.id,
                    "reason": f"lock held by {lock_state.owner} on {lock_state.item_id}",
                })
                continue

            if dry_run:
                summary["dispatched"].append({
                    "role": role_name,
                    "item_id": item.id,
                    "item_title": item.title,
                    "agent": role.agent,
                    "dry_run": True,
                })
                continue

            # Acquire lock and dispatch
            acquired = self.lock.acquire(item.id, owner=role.agent, reason=f"dispatch:{role_name}")
            if not acquired:
                summary["errors"].append({
                    "role": role_name,
                    "item_id": item.id,
                    "error": "failed to acquire lock",
                })
                continue

            # Transition item to in-progress (or role's sets_status_to)
            new_status = role.sets_status_to or "in-progress"
            try:
                self.queue.transition(item.id, new_status)
            except Exception as e:
                summary["errors"].append({
                    "role": role_name,
                    "item_id": item.id,
                    "error": f"transition failed: {e}",
                })
                self.lock.release(reason="transition failed")
                continue

            task_id = self.dispatch_role(role_name, item)
            if task_id.startswith("ERROR:"):
                summary["errors"].append({
                    "role": role_name,
                    "item_id": item.id,
                    "error": task_id,
                })
                self.lock.release(reason="dispatch failed")
            else:
                summary["dispatched"].append({
                    "role": role_name,
                    "item_id": item.id,
                    "item_title": item.title,
                    "agent": role.agent,
                    "task_id": task_id,
                })

        return summary
