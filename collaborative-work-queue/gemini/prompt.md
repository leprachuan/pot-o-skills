# Collaborative Work Queue — Gemini Prompt

You have access to the **collaborative-work-queue** skill for managing multi-agent work queues.

## Usage

Run the Python CLI at `/opt/skills/collaborative-work-queue/copilot/queue_cli.py` with `--config` pointing to a `queue_config.yaml`.

## Commands

- `list [--status STATUS] [--role ROLE]` — Show work items
- `transition <id> <status> [--notes TEXT] [--commit-sha SHA] [--force]` — Move an item to a new status
- `lock status` — Show current lock state
- `lock acquire <id> --owner NAME` — Take the lock
- `lock release [--reason TEXT]` — Release the lock
- `lock reconcile` — Auto-clear stale/expired locks
- `lock force-idle --reason TEXT` — Admin override
- `dispatch run [--dry-run]` — Run a dispatch cycle
- `dispatch status` — Preview what would be dispatched

## State Machine

Transitions are enforced: queued→in-progress→implemented→qa-review→done. Items can be blocked or skipped at appropriate stages. Use `--force` to override.

## Typical Agent Workflow

1. `list --role YOUR_ROLE` to find your next item
2. `lock acquire ITEM --owner YOUR_NAME` to claim it
3. Do the work
4. `transition ITEM implemented --commit-sha SHA`
5. `lock release`
