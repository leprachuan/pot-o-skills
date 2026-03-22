#!/usr/bin/env python3
"""
Heartbeat Runner — checks all agent HEARTBEAT.md files and spawns background tasks.
Runs hourly via task scheduler. Clears HEARTBEAT.md after successful task dispatch.
"""

import os
import re
import json
import urllib.request
import urllib.error
import ssl
import datetime

API_URL = "https://127.0.0.1:8000/api/v1/background-tasks"
API_TOKEN = "shared_R6R6wReORUV6bouLntScMTowbsh30Rzqa3hzjs3bWgU"

AGENT_ROOTS = {
    "fosterbot": "/opt/n8n-copilot-shim/HEARTBEAT.md",
    "email_triage": "/opt/email_triage/HEARTBEAT.md",
    "family_knowledge": "/opt/family_knowledge/HEARTBEAT.md",
    "opencode": "/opt/opencode/HEARTBEAT.md",
    "smart_home": "/opt/smart_home/HEARTBEAT.md",
    "MyHomeDevops": "/opt/MyHomeDevops/HEARTBEAT.md",
    "nanocode": "/opt/nanocode/HEARTBEAT.md",
}

MODEL_MAP = {
    "simple": "claude-haiku-4.5",
    "medium": "claude-sonnet-4.6",
    "complex": "claude-opus-4.6",
}
DEFAULT_MODEL = "claude-sonnet-4.6"

EMPTY_TEMPLATE = """# Heartbeat Instructions

<!-- Write tasks here. An hourly runner will execute them and clear this file. -->

## Tasks

## Context

## Model Hint
<!-- simple | medium | complex -->
"""


def has_pending_tasks(content: str) -> bool:
    """Return True if there are non-empty task lines under ## Tasks."""
    in_tasks = False
    for line in content.splitlines():
        if line.strip() == "## Tasks":
            in_tasks = True
            continue
        if in_tasks:
            if line.startswith("## "):
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("<!--"):
                return True
    return False


def extract_model_hint(content: str) -> str:
    """Extract model hint from ## Model Hint section."""
    in_hint = False
    for line in content.splitlines():
        if line.strip() == "## Model Hint":
            in_hint = True
            continue
        if in_hint:
            if line.startswith("## "):
                break
            stripped = line.strip().lower()
            if stripped and not stripped.startswith("<!--"):
                for key in MODEL_MAP:
                    if key in stripped:
                        return MODEL_MAP[key]
    return DEFAULT_MODEL


def spawn_background_task(agent_name: str, heartbeat_content: str, model: str) -> dict:
    """POST to Wee-Orchestrator background tasks API."""
    prompt = (
        f"Execute the following heartbeat instructions from agent [{agent_name}]:\n\n"
        f"{heartbeat_content}\n\n"
        "Spawn sub-background-tasks as needed using the best model for each job. "
        "Use the Wee-Orchestrator background task API at https://127.0.0.1:8000. "
        "Runtime: copilot."
    )
    payload = json.dumps({
        "prompt": prompt,
        "agent": "fosterbot",
        "runtime": "copilot",
        "model": model,
        "timeout": 3600,
    }).encode("utf-8")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
            "X-Auth-Channel": "api",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def clear_heartbeat(path: str) -> None:
    with open(path, "w") as f:
        f.write(EMPTY_TEMPLATE)


def run():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] Heartbeat runner started")
    spawned = []
    skipped = []
    errors = []

    for agent_name, hb_path in AGENT_ROOTS.items():
        if not os.path.exists(hb_path):
            skipped.append(f"{agent_name}: file not found ({hb_path})")
            continue

        with open(hb_path, "r") as f:
            content = f.read()

        if not has_pending_tasks(content):
            skipped.append(f"{agent_name}: no pending tasks")
            continue

        model = extract_model_hint(content)
        print(f"[{agent_name}] Pending tasks found — spawning background task (model: {model})")

        try:
            result = spawn_background_task(agent_name, content, model)
            task_id = result.get("task_id", result.get("id", "unknown"))
            clear_heartbeat(hb_path)
            spawned.append(f"{agent_name}: task_id={task_id}, model={model}")
            print(f"[{agent_name}] ✓ Spawned task {task_id}, cleared HEARTBEAT.md")
        except Exception as e:
            errors.append(f"{agent_name}: {e}")
            print(f"[{agent_name}] ✗ Error spawning task: {e}")

    print("\n--- Summary ---")
    print(f"Spawned ({len(spawned)}): {spawned or 'none'}")
    print(f"Skipped ({len(skipped)}): {skipped}")
    if errors:
        print(f"Errors  ({len(errors)}): {errors}")


if __name__ == "__main__":
    run()
