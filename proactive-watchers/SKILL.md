---
name: proactive-watchers
description: Monitor URLs and APIs, trigger AI actions on changes. Polls external resources at configurable intervals and fires agent prompts when conditions are met — perfect for monitoring, alerting, and reactive automation.
---

# Proactive Watchers

## Overview

Poll external URLs or APIs at configurable intervals. When a watched resource changes or meets criteria, automatically trigger an agent to run a prompt. Supports multiple concurrent watchers with state persistence, exponential backoff, and event logging.

## When to Use

- Monitor GitHub repos for new releases
- Watch API health endpoints for degradation
- Track website availability and status changes
- Monitor prices or stock levels for thresholds
- Detect content changes on any URL
- Trigger AI workflows on external events
- Set up automated alerting pipelines

## Quick Reference

| Feature | Description |
|---------|-------------|
| **Watcher Types** | url_change, url_field_change, url_status_code, url_text_match, url_comparison, api_response |
| **Conditions** | value_changed, new_item, status_code_change, text_contains, value_exceeds, regex_match, content_hash_changed |
| **Triggers** | background_task (AI agent), shell command, webhook POST, log_only |
| **Storage** | `~/.proactive-watchers/` (watchers.json, history/, templates/) |
| **Runtimes** | Claude (Python), Copilot (Python), Gemini (Node.js) |
| **Dependencies** | Python stdlib + curl (no pip packages required) |

## Commands

### Create a Watcher
```bash
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py create --config /opt/skills/proactive-watchers/templates/github_releases.json
```

### List Watchers
```bash
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py list
```

### Test a Watcher (Single Poll, Dry Run)
```bash
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py test --watcher github-releases
```

### Start Watching
```bash
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py start --watcher github-releases
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py start --watcher all --detach
```

### Stop Watching
```bash
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py stop --watcher github-releases
```

### View History
```bash
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py history --watcher github-releases
```

### Delete a Watcher
```bash
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py delete --watcher github-releases
```

## Watcher Configuration

Watchers are defined as JSON objects:

```json
{
  "name": "my-watcher",
  "type": "url_field_change",
  "url": "https://api.example.com/data",
  "check_interval": 300,
  "method": "GET",
  "headers": {"Accept": "application/json"},
  "condition": "value_changed",
  "trigger_field": "version",
  "on_trigger": {
    "method": "background_task",
    "agent": "fosterbot",
    "timeout": 600,
    "prompt_template": "Value changed: {{extracted_value}}"
  }
}
```

### Condition Types

| Condition | What It Does | Key Fields |
|-----------|-------------|------------|
| `value_changed` | Fires when monitored value differs from last poll | `trigger_field` |
| `new_item` | Fires when new items appear in an array | `trigger_field`, `id_field` |
| `status_code_change` | Fires when HTTP status changes | `expected_from`, `expected_to` |
| `text_contains` | Fires when text pattern found/lost | `search_text`, `trigger_on` |
| `value_exceeds` | Fires when numeric value crosses threshold | `threshold`, `comparator` |
| `regex_match` | Fires when regex pattern matches | `pattern`, `trigger_on` |
| `content_hash_changed` | Fires when full content hash changes | (none) |

### Trigger Methods

| Method | Description |
|--------|-------------|
| `background_task` | Submit prompt to orchestrator API as background task |
| `shell` | Execute a shell command |
| `webhook` | POST trigger data to a webhook URL |
| `log_only` | Log the trigger without action (for testing) |

### Template Variables

Use `{{variable}}` in prompt templates:

| Variable | Value |
|----------|-------|
| `{{watcher_name}}` | Name of the watcher |
| `{{watcher_url}}` | Monitored URL |
| `{{reason}}` | Human-readable trigger reason |
| `{{extracted_value}}` | The value that triggered |
| `{{triggered_at}}` | ISO timestamp |
| `{{response_data.field}}` | Any top-level response field |

## Examples

### Monitor GitHub Releases
```bash
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py create --config /opt/skills/proactive-watchers/templates/github_releases.json
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py start --watcher github-releases
```

### Monitor Website Status
```bash
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py create --config /opt/skills/proactive-watchers/templates/website_status.json
python3 /opt/skills/proactive-watchers/claude/proactive_watchers.py start --watcher website-status
```

## Architecture

```
proactive-watchers/
├── core/                    # Shared engine (Python)
│   ├── watcher_engine.py    # Poll loop, orchestration
│   ├── condition_evaluator.py # Condition logic
│   ├── state_manager.py     # State persistence
│   └── trigger_executor.py  # AI prompt execution
├── claude/                  # Claude CLI
├── copilot/                 # Copilot CLI
├── gemini/                  # Gemini/Node.js CLI
└── templates/               # Example watcher configs
```

## Storage

```
~/.proactive-watchers/
├── watchers.json              # Active watcher definitions
├── history/
│   ├── {name}.log             # Event history (JSONL)
│   └── {name}_state.json     # Last known state
└── templates/                 # User templates
```
