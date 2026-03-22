#!/usr/bin/env python3
"""
Heartbeat Runner — checks all agent HEARTBEAT.md files and spawns background tasks.
Runs hourly via task scheduler. Clears HEARTBEAT.md after successful task dispatch.

Agent paths, models, and runtimes are loaded from /opt/agents.json.

Per-agent config (optional heartbeat block in agents.json):
  "heartbeat": {
    "default_model": "claude-sonnet-4.6",
    "default_runtime": "copilot",
    "model_map": {
      "simple": "claude-haiku-4.5",
      "medium": "claude-sonnet-4.6",
      "complex": "claude-opus-4.6"
    }
  }

Global env var overrides:
  AGENTS_JSON              path to agents.json (default: /opt/agents.json)
  HEARTBEAT_DEFAULT_MODEL  fallback model when no hint/config present
  HEARTBEAT_DEFAULT_RUNTIME fallback runtime when no hint/config present
"""

import os
import json
import urllib.request
import ssl
import datetime

API_URL = "https://127.0.0.1:8000/api/v1/background-tasks"
API_TOKEN = "shared_R6R6wReORUV6bouLntScMTowbsh30Rzqa3hzjs3bWgU"
AGENTS_JSON = os.environ.get("AGENTS_JSON", "/opt/agents.json")

GLOBAL_DEFAULT_MODEL = os.environ.get("HEARTBEAT_DEFAULT_MODEL", "claude-sonnet-4.6")
GLOBAL_DEFAULT_RUNTIME = os.environ.get("HEARTBEAT_DEFAULT_RUNTIME", "copilot")

BUILTIN_MODEL_MAP = {
    "simple": "claude-haiku-4.5",
    "medium": "claude-sonnet-4.6",
    "complex": "claude-opus-4.6",
}

EMPTY_TEMPLATE = """# Heartbeat Instructions

<!-- Write tasks here. An hourly runner will execute them and clear this file. -->

## Tasks

## Context

## Model Hint
<!-- simple | medium | complex  — or a full model ID e.g. claude-opus-4.6 -->

## Runtime Hint
<!-- copilot | claude | gemini | opencode -->
"""


def load_agents(agents_json_path: str) -> list[dict]:
    """
    Read agents.json and return a list of agent configs, each with:
      name, path, hb_path, default_model, default_runtime, model_map
    """
    with open(agents_json_path, "r") as f:
        data = json.load(f)

    agents = []
    for agent in data.get("agents", []):
        name = agent.get("name", "")
        path = agent.get("path", "").rstrip("/")
        if not name or not path:
            continue

        hb_cfg = agent.get("heartbeat", {})
        agents.append({
            "name": name,
            "path": path,
            "hb_path": os.path.join(path, "HEARTBEAT.md"),
            "default_model": hb_cfg.get("default_model", GLOBAL_DEFAULT_MODEL),
            "default_runtime": hb_cfg.get("default_runtime", GLOBAL_DEFAULT_RUNTIME),
            "model_map": hb_cfg.get("model_map", BUILTIN_MODEL_MAP),
        })
    return agents


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


def extract_hint(content: str, section: str) -> str:
    """Extract the first non-comment value from a ## {section} block."""
    in_section = False
    for line in content.splitlines():
        if line.strip() == f"## {section}":
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("<!--"):
                return stripped.lower()
    return ""


def resolve_model(content: str, agent_cfg: dict) -> str:
    """Resolve model: HEARTBEAT hint > agent default > global default."""
    hint = extract_hint(content, "Model Hint")
    if not hint:
        return agent_cfg["default_model"]
    # Check model_map keys (simple/medium/complex)
    model_map = agent_cfg["model_map"]
    for key, model in model_map.items():
        if key in hint:
            return model
    # Treat as a literal model ID if it looks like one (contains a dash)
    if "-" in hint:
        return hint
    return agent_cfg["default_model"]


def resolve_runtime(content: str, agent_cfg: dict) -> str:
    """Resolve runtime: HEARTBEAT hint > agent default > global default."""
    hint = extract_hint(content, "Runtime Hint")
    if hint:
        return hint
    return agent_cfg["default_runtime"]


def spawn_background_task(agent_name: str, heartbeat_content: str, model: str, runtime: str) -> dict:
    """POST to Wee-Orchestrator background tasks API."""
    prompt = (
        f"Execute the following heartbeat instructions from agent [{agent_name}]:\n\n"
        f"{heartbeat_content}\n\n"
        "Spawn sub-background-tasks as needed using the best model for each job. "
        f"Use the Wee-Orchestrator background task API at https://127.0.0.1:8000."
    )
    payload = json.dumps({
        "prompt": prompt,
        "agent": agent_name,
        "runtime": runtime,
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
    print(f"Loading agents from {AGENTS_JSON}")
    print(f"Global defaults — model: {GLOBAL_DEFAULT_MODEL}, runtime: {GLOBAL_DEFAULT_RUNTIME}")

    try:
        agents = load_agents(AGENTS_JSON)
    except Exception as e:
        print(f"ERROR: Failed to load {AGENTS_JSON}: {e}")
        return

    print(f"Found {len(agents)} agents: {[a['name'] for a in agents]}")

    spawned = []
    skipped = []
    errors = []

    for agent in agents:
        name = agent["name"]
        hb_path = agent["hb_path"]

        if not os.path.exists(hb_path):
            skipped.append(f"{name}: file not found ({hb_path})")
            continue

        with open(hb_path, "r") as f:
            content = f.read()

        if not has_pending_tasks(content):
            skipped.append(f"{name}: no pending tasks")
            continue

        model = resolve_model(content, agent)
        runtime = resolve_runtime(content, agent)
        print(f"[{name}] Pending tasks found — spawning (model: {model}, runtime: {runtime})")

        try:
            result = spawn_background_task(name, content, model, runtime)
            task_id = result.get("task_id", result.get("id", "unknown"))
            clear_heartbeat(hb_path)
            spawned.append(f"{name}: task_id={task_id}, model={model}, runtime={runtime}")
            print(f"[{name}] ✓ Spawned {task_id}, cleared HEARTBEAT.md")
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"[{name}] ✗ Error: {e}")

    print("\n--- Summary ---")
    print(f"Spawned ({len(spawned)}): {spawned or 'none'}")
    print(f"Skipped ({len(skipped)}): {skipped}")
    if errors:
        print(f"Errors  ({len(errors)}): {errors}")


if __name__ == "__main__":
    run()
