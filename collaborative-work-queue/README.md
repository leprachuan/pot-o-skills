# collaborative-work-queue

Reusable multi-agent work queue with markdown tables, JSON locks, state machine enforcement, TTL-based stale detection, and scheduler-driven dispatch.

## Overview

Drop-in replacement for bespoke multi-agent pipelines. Define your statuses, roles, and dispatch rules in a single YAML config file. The skill handles:

- **Markdown table parsing** — 8-column work queue tables (ID, Title, Priority, Status, Notes, QA Status, Commit SHA, Last Updated)
- **State machine enforcement** — configurable transitions with validation
- **Atomic file locking** — JSON lock files with TTL expiration and reconciliation
- **Dispatch engine** — integrates with Wee Orchestrator background-tasks API
- **Multi-role support** — developer, reviewer, documenter (or any custom roles)

## Quick Start

```bash
# List work items
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py list \
  --config /path/to/queue_config.yaml

# Transition an item
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py transition F001 in-progress \
  --config /path/to/queue_config.yaml

# Run a dispatch cycle
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py dispatch run \
  --config /path/to/queue_config.yaml
```

## Installation

No external dependencies beyond Python 3.10+ stdlib and PyYAML.

1. Copy or symlink this skill to your skills directory
2. Create a `queue_config.yaml` for your pipeline (see `examples/`)
3. Create your `WORK_QUEUE.md` markdown table

## Configuration

See `examples/wee-dev-pipeline/queue_config.yaml` for a complete example.

### Key Sections

| Section | Purpose |
|---------|---------|
| `queue` | Queue name, directory, and markdown file paths |
| `lock` | Lock file path and TTL in seconds |
| `statuses` | State machine definition with transitions |
| `roles` | Agent roles, models, concurrency limits, prompts |
| `dispatch` | API endpoint, token, stall detection threshold |

## CLI Reference

| Command | Description |
|---------|-------------|
| `list` | List work items with optional filters |
| `transition <id> <status>` | Move item to new status |
| `lock status` | Show current lock state |
| `lock acquire <id> --owner NAME` | Claim the lock |
| `lock release` | Release the lock |
| `lock refresh` | Extend lock TTL |
| `lock reconcile` | Auto-clear stale locks |
| `lock force-idle --reason TEXT` | Admin override |
| `dispatch run [--dry-run]` | Execute dispatch cycle |
| `dispatch status` | Preview pending dispatches |

## State Machine

```
queued ──→ in-progress ──→ implemented ──→ qa-review ──→ done
  │            │                              │
  ├→ blocked   ├→ blocked                     └→ qa-failed ──→ in-progress
  └→ skipped

Terminal: done, blocked, skipped
```

## Architecture

```
queue_config.yaml     ← Pipeline definition
WORK_QUEUE.md         ← Markdown table (human + agent readable)
WORK_QUEUE.lock.json  ← Atomic lock file

queue_lib.py          ← Core: parse, validate, transition
lock_manager.py       ← Lock: acquire, release, reconcile, TTL
dispatcher.py         ← Dispatch: API integration, stall detection
queue_cli.py          ← CLI: argparse interface to all above
```

## Runtimes

Works with all three runtimes (Copilot, Claude, Gemini). Each has a `prompt.md` with usage instructions tailored to that runtime.

## License

Internal skill — part of the FosterbotHome ecosystem.
