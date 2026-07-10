# Proactive Watchers

> Monitor URLs and APIs, trigger AI actions on changes.

Proactive Watchers is a universal monitoring skill that polls external URLs or APIs at configurable intervals. When a watched resource changes or meets defined criteria, it automatically triggers an AI agent to run a prompt — perfect for monitoring, alerting, and reactive automation.

## Features

- ✅ **Background polling** — async, non-blocking concurrent watchers
- ✅ **State caching** — avoids redundant triggers across polls
- ✅ **Exponential backoff** — graceful error handling with configurable retries
- ✅ **Configurable intervals** — from 5 seconds to days
- ✅ **Multiple conditions** — value_changed, new_item, text_contains, value_exceeds, regex_match, and more
- ✅ **Prompt templates** — `{{variable}}` substitution with response data
- ✅ **Multi-runtime** — Claude (Python), Copilot (Python), Gemini (Node.js)
- ✅ **Event logging** — full history with JSONL event logs
- ✅ **Multiple trigger methods** — AI background tasks, shell commands, webhooks, log-only
- ✅ **Rate limit awareness** — configurable intervals prevent API abuse
- ✅ **Zero dependencies** — uses only Python stdlib and curl

## Quick Start

### 1. Create a Watcher

```bash
# From a template
python3 claude/proactive_watchers.py create --config templates/github_releases.json

# Or inline (Copilot CLI)
python3 copilot/proactive_watchers.py create \
  --name my-api-check \
  --url https://api.example.com/health \
  --condition text_contains \
  --trigger-field status \
  --interval 120
```

### 2. Test It

```bash
python3 claude/proactive_watchers.py test --watcher github-releases
```

### 3. Start Watching

```bash
# Single watcher (blocks)
python3 claude/proactive_watchers.py start --watcher github-releases

# All watchers in background
python3 claude/proactive_watchers.py start --watcher all --detach
```

### 4. Manage

```bash
python3 claude/proactive_watchers.py list
python3 claude/proactive_watchers.py history --watcher github-releases
python3 claude/proactive_watchers.py stop --watcher github-releases
python3 claude/proactive_watchers.py delete --watcher github-releases
```

## Watcher Configuration

```json
{
  "name": "github-releases",
  "type": "url_field_change",
  "url": "https://api.github.com/repos/user/repo/releases/latest",
  "check_interval": 300,
  "method": "GET",
  "headers": {"Accept": "application/vnd.github+json"},
  "condition": "value_changed",
  "trigger_field": "tag_name",
  "on_trigger": {
    "method": "background_task",
    "agent": "fosterbot",
    "timeout": 600,
    "prompt_template": "New release: {{response_data.tag_name}}. Summarize the release notes."
  }
}
```

### Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | *required* | Unique watcher identifier |
| `url` | string | *required* | URL to poll |
| `type` | string | `url_change` | Watcher type category |
| `check_interval` | int | `300` | Seconds between polls |
| `method` | string | `GET` | HTTP method |
| `headers` | object | `{}` | HTTP headers |
| `body` | string/object | | Request body for POST/PUT |
| `condition` | string | `value_changed` | Trigger condition type |
| `trigger_field` | string | | Dot-notation path to monitored field |
| `enabled` | bool | `true` | Whether watcher is active |
| `verify_ssl` | bool | `true` | Verify SSL certificates |
| `timeout` | int | `30` | HTTP request timeout (seconds) |
| `auth_env` | string | | Environment variable name for Bearer token |
| `on_trigger` | object | | Action to take when triggered |

### Condition Types

| Condition | Description | Extra Fields |
|-----------|-------------|-------------|
| `value_changed` | Value differs from last poll | `trigger_field` |
| `new_item` | New items in an array | `trigger_field`, `id_field` |
| `status_code_change` | HTTP status code changed | `expected_from`, `expected_to` |
| `text_contains` | Text pattern found/lost | `search_text`, `case_sensitive`, `trigger_on` |
| `value_exceeds` | Numeric value crosses threshold | `threshold`, `comparator` (gt/gte/lt/lte/eq/neq), `trigger_mode` |
| `regex_match` | Regex pattern matches | `pattern`, `case_sensitive`, `trigger_on` |
| `content_hash_changed` | SHA-256 hash of content changed | — |

### Trigger Methods

| Method | Description | Extra Fields |
|--------|-------------|-------------|
| `background_task` | Submit to orchestrator API | `agent`, `timeout` |
| `shell` | Execute shell command | `command`, `cwd`, `timeout` |
| `webhook` | POST to webhook URL | `webhook_url` |
| `log_only` | Log without action | — |

### Template Variables

| Variable | Description |
|----------|-------------|
| `{{watcher_name}}` | Watcher name |
| `{{watcher_url}}` | Monitored URL |
| `{{watcher_type}}` | Watcher type |
| `{{condition}}` | Condition type |
| `{{reason}}` | Human-readable trigger reason |
| `{{extracted_value}}` | Value that was evaluated |
| `{{triggered_at}}` | ISO 8601 timestamp |
| `{{response_data.field}}` | Any top-level response field |

## Example Templates

| Template | Use Case |
|----------|----------|
| `github_releases.json` | Monitor GitHub repo releases |
| `price_monitor.json` | Watch for price drops |
| `website_status.json` | Detect website downtime |
| `api_monitor.json` | Monitor API health endpoints |

## Architecture

```
proactive-watchers/
├── skill_metadata.json       # Skill registration metadata
├── SKILL.md                  # Agent instructions
├── README.md                 # This file
├── requirements.txt          # Dependencies (none)
├── core/                     # Shared engine
│   ├── __init__.py
│   ├── watcher_engine.py     # Main polling loop & orchestration
│   ├── condition_evaluator.py # Condition evaluation logic
│   ├── state_manager.py      # Watcher persistence & history
│   └── trigger_executor.py   # AI prompt execution & triggers
├── claude/                   # Claude runtime
│   ├── __init__.py
│   └── proactive_watchers.py # Full-featured CLI
├── copilot/                  # Copilot runtime
│   ├── __init__.py
│   └── proactive_watchers.py # Terminal-optimized CLI
├── gemini/                   # Gemini runtime
│   ├── package.json
│   └── proactive_watchers.js # Node.js implementation
└── templates/                # Example watcher configs
    ├── github_releases.json
    ├── price_monitor.json
    ├── website_status.json
    └── api_monitor.json
```

## Storage

State is stored in `~/.proactive-watchers/`:

```
~/.proactive-watchers/
├── watchers.json              # All watcher definitions
├── history/
│   ├── {watcher_name}.log     # Event log (JSONL format)
│   └── {watcher_name}_state.json  # Last known state
└── templates/                 # User-created templates
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WATCHERS_DIR` | `~/.proactive-watchers` | Storage directory |
| `WATCHER_LOG_LEVEL` | `info` | Logging level |
| `WATCHER_MAX_RETRIES` | `3` | Max retries on error |
| `WATCHER_BACKOFF_FACTOR` | `2` | Exponential backoff multiplier |
| `WATCHER_DEFAULT_AGENT` | `fosterbot` | Default agent for triggers |
| `WATCHER_DEFAULT_RUNTIME` | `claude` | Default runtime |
| `WATCHER_DEFAULT_MODEL` | `claude-opus-4.6` | Default model |
| `ORCHESTRATOR_API_TOKEN` | (built-in) | API authentication token |
| `WATCHER_USER_IDENTITY` | `8193231291` | User identity for API calls |
| `WATCHER_AUTH_CHANNEL` | `telegram` | Auth channel for API calls |

## Use Cases

### GitHub Release Monitor
Watch for new releases, auto-summarize release notes, notify team.

### Price Alert System
Poll product APIs, trigger on price drops below threshold, send alerts.

### Website Uptime Monitor
Poll endpoints every 60s, trigger on status code changes, run diagnostics.

### API Health Dashboard
Monitor /health endpoints, trigger on degradation keywords, auto-investigate.

### CI/CD Pipeline Watcher
Poll build status APIs, trigger notifications on failures.

## License

MIT
