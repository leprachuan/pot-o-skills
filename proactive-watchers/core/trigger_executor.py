"""Trigger executor - runs AI prompts when watcher conditions are met."""

import json
import os
import re
import subprocess
import time
import logging
from typing import Any, Optional

logger = logging.getLogger("proactive-watchers.trigger")


class TriggerExecutor:
    """Executes AI prompts when watcher triggers fire."""

    def __init__(self, api_base: str = "https://127.0.0.1:8000",
                 api_token: Optional[str] = None):
        self.api_base = api_base
        self.api_token = api_token or os.environ.get(
            "ORCHESTRATOR_API_TOKEN",
            "shared_R6R6wReORUV6bouLntScMTowbsh30Rzqa3hzjs3bWgU"
        )
        self.user_identity = os.environ.get("WATCHER_USER_IDENTITY", "8193231291")
        self.auth_channel = os.environ.get("WATCHER_AUTH_CHANNEL", "telegram")

    def execute_trigger(self, watcher: dict, evaluation_result: dict,
                        response_data: Any) -> dict:
        """
        Execute the on_trigger action for a watcher.

        Returns dict with: success, method, response, error
        """
        on_trigger = watcher.get("on_trigger", {})
        if not on_trigger:
            return {"success": False, "error": "No on_trigger configured", "method": "none"}

        prompt = self._render_prompt(
            on_trigger.get("prompt_template", "Watcher '{{watcher_name}}' triggered: {{reason}}"),
            watcher, evaluation_result, response_data
        )

        method = on_trigger.get("method", "background_task")

        if method == "background_task":
            return self._execute_background_task(on_trigger, prompt)
        elif method == "shell":
            return self._execute_shell(on_trigger, prompt)
        elif method == "webhook":
            return self._execute_webhook(on_trigger, prompt, response_data)
        elif method == "log_only":
            return self._execute_log_only(prompt)
        else:
            return self._execute_background_task(on_trigger, prompt)

    def _render_prompt(self, template: str, watcher: dict,
                       evaluation_result: dict, response_data: Any) -> str:
        """Render a prompt template with {{variable}} substitution."""
        context = {
            "watcher_name": watcher.get("name", "unknown"),
            "watcher_url": watcher.get("url", ""),
            "watcher_type": watcher.get("type", ""),
            "condition": watcher.get("condition", ""),
            "reason": evaluation_result.get("reason", ""),
            "extracted_value": json.dumps(evaluation_result.get("extracted_value"), default=str),
            "triggered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        if isinstance(response_data, dict):
            for key, value in response_data.items():
                context[f"response_data.{key}"] = json.dumps(value, default=str) if not isinstance(value, str) else value

        result = template
        for key, value in context.items():
            result = result.replace("{{" + key + "}}", str(value))

        # Clean up any unreplaced variables
        result = re.sub(r"\{\{[^}]+\}\}", "[unavailable]", result)
        return result

    def _execute_background_task(self, on_trigger: dict, prompt: str) -> dict:
        """Submit a background task to the orchestrator API."""
        agent = on_trigger.get("agent", os.environ.get("WATCHER_DEFAULT_AGENT", "fosterbot"))
        timeout = on_trigger.get("timeout", 600)

        payload = {
            "prompt": prompt,
            "agent": agent,
            "timeout": timeout,
        }

        try:
            cmd = [
                "curl", "-s", "-k", "-X", "POST",
                f"{self.api_base}/api/v1/background-tasks",
                "-H", "Content-Type: application/json",
                "-H", f"Authorization: Bearer {self.api_token}",
                "-H", f"X-User-Identity: {self.user_identity}",
                "-H", f"X-Auth-Channel: {self.auth_channel}",
                "-d", json.dumps(payload),
                "--connect-timeout", "10",
                "--max-time", "30",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)

            if result.returncode == 0:
                try:
                    resp = json.loads(result.stdout)
                    logger.info(f"Background task created: {resp.get('task_id', 'unknown')}")
                    return {"success": True, "method": "background_task", "response": resp}
                except json.JSONDecodeError:
                    return {"success": False, "method": "background_task",
                            "error": f"Invalid JSON response: {result.stdout[:200]}"}
            else:
                return {"success": False, "method": "background_task",
                        "error": f"curl failed: {result.stderr[:200]}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "method": "background_task", "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "method": "background_task", "error": str(e)}

    def _execute_shell(self, on_trigger: dict, prompt: str) -> dict:
        """Execute a shell command as the trigger action."""
        command = on_trigger.get("command", "")
        if not command:
            return {"success": False, "method": "shell", "error": "No command specified"}

        command = command.replace("{{prompt}}", prompt)

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=on_trigger.get("timeout", 60),
                cwd=on_trigger.get("cwd"),
            )
            return {
                "success": result.returncode == 0,
                "method": "shell",
                "response": {
                    "stdout": result.stdout[:2000],
                    "stderr": result.stderr[:500],
                    "returncode": result.returncode,
                },
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "method": "shell", "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "method": "shell", "error": str(e)}

    def _execute_webhook(self, on_trigger: dict, prompt: str,
                         response_data: Any) -> dict:
        """Send a webhook POST with trigger data."""
        webhook_url = on_trigger.get("webhook_url", "")
        if not webhook_url:
            return {"success": False, "method": "webhook", "error": "No webhook_url specified"}

        payload = json.dumps({
            "prompt": prompt,
            "response_data": response_data,
            "timestamp": time.time(),
        })

        try:
            cmd = [
                "curl", "-s", "-X", "POST", webhook_url,
                "-H", "Content-Type: application/json",
                "-d", payload,
                "--connect-timeout", "10",
                "--max-time", "30",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            return {
                "success": result.returncode == 0,
                "method": "webhook",
                "response": result.stdout[:500],
            }
        except Exception as e:
            return {"success": False, "method": "webhook", "error": str(e)}

    def _execute_log_only(self, prompt: str) -> dict:
        """Log the trigger without taking action (useful for testing)."""
        logger.info(f"[LOG_ONLY] Trigger fired: {prompt[:200]}")
        return {"success": True, "method": "log_only", "response": {"prompt": prompt}}
