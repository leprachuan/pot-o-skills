"""Watcher engine - core polling loop and orchestration for proactive watchers."""

import json
import os
import signal
import subprocess
import threading
import time
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from .state_manager import StateManager
from .condition_evaluator import ConditionEvaluator
from .trigger_executor import TriggerExecutor

logger = logging.getLogger("proactive-watchers.engine")


class WatcherEngine:
    """Main engine that polls URLs/APIs and evaluates conditions to trigger actions."""

    def __init__(self, watchers_dir: Optional[str] = None,
                 api_base: str = "https://127.0.0.1:8000",
                 api_token: Optional[str] = None):
        self.state_manager = StateManager(watchers_dir)
        self.evaluator = ConditionEvaluator()
        self.executor = TriggerExecutor(api_base, api_token)
        self._running_watchers: dict[str, threading.Event] = {}
        self._thread_pool = ThreadPoolExecutor(max_workers=20, thread_name_prefix="watcher")
        self._shutdown = threading.Event()

        max_retries = int(os.environ.get("WATCHER_MAX_RETRIES", "3"))
        backoff_factor = float(os.environ.get("WATCHER_BACKOFF_FACTOR", "2"))
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def create_watcher(self, config: dict) -> dict:
        """Create a new watcher from a configuration dict."""
        required = ["name", "url"]
        for field in required:
            if field not in config:
                return {"success": False, "error": f"Missing required field: {field}"}

        config.setdefault("type", "url_change")
        config.setdefault("condition", "value_changed")
        config.setdefault("check_interval", 300)
        config.setdefault("method", "GET")
        config.setdefault("headers", {})
        config.setdefault("enabled", True)
        config.setdefault("on_trigger", {
            "method": "log_only",
            "prompt_template": "Watcher '{{watcher_name}}' triggered: {{reason}}",
        })

        if self.state_manager.add_watcher(config):
            return {"success": True, "watcher": config}
        return {"success": False, "error": f"Watcher '{config['name']}' already exists"}

    def delete_watcher(self, name: str) -> dict:
        """Delete a watcher and stop it if running."""
        self.stop_watcher(name)
        if self.state_manager.remove_watcher(name):
            return {"success": True, "message": f"Watcher '{name}' deleted"}
        return {"success": False, "error": f"Watcher '{name}' not found"}

    def list_watchers(self) -> list[dict]:
        """List all watcher definitions with their current status."""
        watchers = self.state_manager.load_watchers()
        for w in watchers:
            w["running"] = w["name"] in self._running_watchers
            state = self.state_manager.get_state(w["name"])
            w["last_check"] = state.get("last_check_time")
            w["trigger_count"] = state.get("trigger_count", 0)
            w["error_count"] = state.get("error_count", 0)
        return watchers

    def start_watcher(self, name: str) -> dict:
        """Start polling for a specific watcher."""
        if name in self._running_watchers:
            return {"success": False, "error": f"Watcher '{name}' is already running"}

        watcher = self.state_manager.get_watcher(name)
        if not watcher:
            return {"success": False, "error": f"Watcher '{name}' not found"}

        if not watcher.get("enabled", True):
            return {"success": False, "error": f"Watcher '{name}' is disabled"}

        stop_event = threading.Event()
        self._running_watchers[name] = stop_event
        self._thread_pool.submit(self._poll_loop, watcher, stop_event)
        logger.info(f"Started watcher: {name}")
        return {"success": True, "message": f"Watcher '{name}' started"}

    def stop_watcher(self, name: str) -> dict:
        """Stop polling for a specific watcher."""
        stop_event = self._running_watchers.pop(name, None)
        if stop_event:
            stop_event.set()
            logger.info(f"Stopped watcher: {name}")
            return {"success": True, "message": f"Watcher '{name}' stopped"}
        return {"success": False, "error": f"Watcher '{name}' is not running"}

    def start_all(self) -> dict:
        """Start all enabled watchers."""
        watchers = self.state_manager.load_watchers()
        started = []
        for w in watchers:
            if w.get("enabled", True) and w["name"] not in self._running_watchers:
                result = self.start_watcher(w["name"])
                if result["success"]:
                    started.append(w["name"])
        return {"success": True, "started": started, "count": len(started)}

    def stop_all(self) -> dict:
        """Stop all running watchers."""
        stopped = []
        for name in list(self._running_watchers.keys()):
            result = self.stop_watcher(name)
            if result["success"]:
                stopped.append(name)
        return {"success": True, "stopped": stopped, "count": len(stopped)}

    def test_watcher(self, name: str) -> dict:
        """Run a single poll cycle for a watcher (for testing)."""
        watcher = self.state_manager.get_watcher(name)
        if not watcher:
            return {"success": False, "error": f"Watcher '{name}' not found"}
        return self._single_poll(watcher, dry_run=True)

    def shutdown(self):
        """Gracefully shut down the engine."""
        self._shutdown.set()
        self.stop_all()
        self._thread_pool.shutdown(wait=True, cancel_futures=True)

    def _poll_loop(self, watcher: dict, stop_event: threading.Event):
        """Main polling loop for a single watcher."""
        name = watcher["name"]
        interval = watcher.get("check_interval", 300)
        consecutive_errors = 0

        logger.info(f"[{name}] Poll loop started (interval={interval}s)")

        while not stop_event.is_set() and not self._shutdown.is_set():
            try:
                result = self._single_poll(watcher)

                if result.get("error"):
                    consecutive_errors += 1
                    backoff = min(interval * (self.backoff_factor ** consecutive_errors), 3600)
                    logger.warning(f"[{name}] Error #{consecutive_errors}, backing off {backoff:.0f}s: {result['error']}")
                    stop_event.wait(timeout=backoff)
                else:
                    consecutive_errors = 0
                    stop_event.wait(timeout=interval)

                # Reload watcher config to pick up changes
                updated = self.state_manager.get_watcher(name)
                if updated:
                    watcher = updated
                    interval = watcher.get("check_interval", 300)
                    if not watcher.get("enabled", True):
                        logger.info(f"[{name}] Watcher disabled, stopping")
                        break

            except Exception as e:
                logger.error(f"[{name}] Unexpected error in poll loop: {e}")
                consecutive_errors += 1
                stop_event.wait(timeout=min(60 * consecutive_errors, 3600))

        self._running_watchers.pop(name, None)
        logger.info(f"[{name}] Poll loop stopped")

    def _single_poll(self, watcher: dict, dry_run: bool = False) -> dict:
        """Execute a single poll cycle: fetch → evaluate → trigger."""
        name = watcher["name"]
        url = watcher.get("url", "")

        # Fetch
        fetch_result = self._fetch_url(watcher)
        if fetch_result.get("error"):
            state = self.state_manager.get_state(name)
            state["error_count"] = state.get("error_count", 0) + 1
            state["last_error"] = fetch_result["error"]
            state["last_check_time"] = time.time()
            self.state_manager.save_state(name, state)

            self.state_manager.log_event(name, {
                "type": "error",
                "error": fetch_result["error"],
                "url": url,
            })
            return fetch_result

        response_data = fetch_result["data"]
        status_code = fetch_result["status_code"]

        # Evaluate
        previous_state = self.state_manager.get_state(name)
        eval_result = self.evaluator.evaluate(watcher, response_data, status_code, previous_state)

        # Update state
        new_state = eval_result["new_state"]
        new_state["last_check_time"] = time.time()
        new_state["last_status_code"] = status_code
        self.state_manager.save_state(name, new_state)

        self.state_manager.log_event(name, {
            "type": "poll",
            "triggered": eval_result["triggered"],
            "reason": eval_result["reason"],
            "status_code": status_code,
            "dry_run": dry_run,
        })

        result = {
            "success": True,
            "watcher": name,
            "triggered": eval_result["triggered"],
            "reason": eval_result["reason"],
            "status_code": status_code,
            "extracted_value": eval_result.get("extracted_value"),
        }

        # Trigger
        if eval_result["triggered"] and not dry_run:
            new_state["trigger_count"] = new_state.get("trigger_count", 0) + 1
            self.state_manager.save_state(name, new_state)

            trigger_result = self.executor.execute_trigger(watcher, eval_result, response_data)
            result["trigger_result"] = trigger_result

            self.state_manager.log_event(name, {
                "type": "trigger",
                "reason": eval_result["reason"],
                "trigger_success": trigger_result.get("success"),
                "trigger_method": trigger_result.get("method"),
                "trigger_error": trigger_result.get("error"),
            })

            logger.info(f"[{name}] TRIGGERED: {eval_result['reason']} → {trigger_result.get('method')}")

        return result

    def _fetch_url(self, watcher: dict) -> dict:
        """Fetch a URL using curl and return parsed data."""
        url = watcher.get("url", "")
        method = watcher.get("method", "GET").upper()
        headers = watcher.get("headers", {})
        body = watcher.get("body")
        timeout = watcher.get("timeout", 30)
        verify_ssl = watcher.get("verify_ssl", True)

        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method]

        if not verify_ssl:
            cmd.append("-k")

        cmd.extend(["--connect-timeout", "10", "--max-time", str(timeout)])

        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])

        if body:
            cmd.extend(["-d", json.dumps(body) if isinstance(body, dict) else str(body)])

        # Append auth from environment if configured
        auth_header = watcher.get("auth_env")
        if auth_header:
            token = os.environ.get(auth_header, "")
            if token:
                cmd.extend(["-H", f"Authorization: Bearer {token}"])

        cmd.append(url)

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)

            if proc.returncode != 0:
                return {"error": f"curl failed (rc={proc.returncode}): {proc.stderr[:200]}"}

            output = proc.stdout.strip()
            lines = output.rsplit("\n", 1)

            if len(lines) == 2:
                body_text, status_str = lines
            else:
                body_text = output
                status_str = "0"

            try:
                status_code = int(status_str)
            except ValueError:
                status_code = 0

            # Try JSON parse
            try:
                data = json.loads(body_text)
            except (json.JSONDecodeError, ValueError):
                data = body_text

            return {"data": data, "status_code": status_code, "raw": body_text[:5000]}

        except subprocess.TimeoutExpired:
            return {"error": f"Request timed out after {timeout}s"}
        except Exception as e:
            return {"error": str(e)}
