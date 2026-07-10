# Collaborative Work Queue — Claude Prompt

You have access to the **collaborative-work-queue** skill for managing multi-agent work queues with markdown tables, JSON locks, and state machine enforcement.

## Tool

Run the CLI at `/opt/skills/collaborative-work-queue/copilot/queue_cli.py` with a `--config` pointing to your pipeline's `queue_config.yaml`.

## Quick Reference

| Action | Command |
|--------|---------|
| List all items | `python3 queue_cli.py list --config PATH` |
| Filter by status | `python3 queue_cli.py list --status queued --config PATH` |
| Transition item | `python3 queue_cli.py transition ID STATUS --config PATH` |
| Lock status | `python3 queue_cli.py lock status --config PATH` |
| Acquire lock | `python3 queue_cli.py lock acquire ID --owner NAME --config PATH` |
| Release lock | `python3 queue_cli.py lock release --config PATH` |
| Reconcile locks | `python3 queue_cli.py lock reconcile --config PATH` |
| Dispatch cycle | `python3 queue_cli.py dispatch run --config PATH` |
| Dry-run dispatch | `python3 queue_cli.py dispatch run --dry-run --config PATH` |

## State Machine

```
queued → in-progress | blocked | skipped
in-progress → implemented | blocked
implemented → qa-review
qa-review → done | qa-failed
qa-failed → in-progress
done / blocked / skipped = terminal
```

## Workflow

1. Check for your next item: `list --role developer`
2. Acquire lock: `lock acquire ITEM_ID --owner your-agent-name`
3. Do the work
4. Transition: `transition ITEM_ID implemented --commit-sha SHA`
5. Release lock: `lock release --reason "work complete"`

## Configuration

Each pipeline has a `queue_config.yaml` defining statuses, roles, dispatch settings, and lock TTL. See `examples/wee-dev-pipeline/` for a reference implementation.
