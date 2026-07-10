# Collaborative Work Queue — Copilot Prompt

You have access to the **collaborative-work-queue** skill for managing multi-agent work queues.

## CLI Location

```
/opt/skills/collaborative-work-queue/copilot/queue_cli.py
```

## Commands

### List items
```bash
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py list --config /path/to/queue_config.yaml
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py list --status queued --config /path/to/queue_config.yaml
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py list --role developer --config /path/to/queue_config.yaml
```

### Transition a work item
```bash
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py transition F042 in-progress --config /path/to/queue_config.yaml
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py transition F042 implemented --notes "Completed refactor" --commit-sha abc123 --config /path/to/queue_config.yaml
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py transition F042 done --force --config /path/to/queue_config.yaml
```

### Lock management
```bash
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py lock status --config /path/to/queue_config.yaml
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py lock acquire F042 --owner wee-dev --config /path/to/queue_config.yaml
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py lock release --reason "work complete" --config /path/to/queue_config.yaml
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py lock reconcile --config /path/to/queue_config.yaml
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py lock force-idle --reason "manual reset" --config /path/to/queue_config.yaml
```

### Dispatch engine
```bash
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py dispatch run --config /path/to/queue_config.yaml
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py dispatch run --dry-run --config /path/to/queue_config.yaml
python3 /opt/skills/collaborative-work-queue/copilot/queue_cli.py dispatch status --config /path/to/queue_config.yaml
```

## State Machine

Valid transitions (enforced unless `--force` is used):

```
queued → in-progress, blocked, skipped
in-progress → implemented, blocked
implemented → qa-review
qa-review → done, qa-failed
qa-failed → in-progress
done, blocked, skipped = terminal (no further transitions)
```

## Queue File Format

Markdown table with 8 columns:

```markdown
| ID | Title | Priority | Status | Notes | QA Status | Commit SHA | Last Updated |
|----|-------|----------|--------|-------|-----------|------------|--------------|
| F001 | Add auth | P1 | queued | | | | |
```

## Lock File Format

JSON file with fields: state, item_id, owner, reason, acquired_at, ttl_expires_at, updated_at.

## Configuration

YAML file — see `examples/wee-dev-pipeline/queue_config.yaml` for a full example.

## When to Use

- Managing multi-step dev → QA → doc pipelines
- Coordinating work across multiple AI agents
- Any sequential work queue with state tracking
- Replacing bespoke queue scripts with a reusable tool
