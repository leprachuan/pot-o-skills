#!/usr/bin/env python3
"""CLI for collaborative work queue management.

Usage:
    queue_cli.py list [--status STATUS] [--role ROLE] [--config PATH]
    queue_cli.py transition <id> <new_status> [--notes TEXT] [--commit-sha SHA] [--force] [--config PATH]
    queue_cli.py lock status [--config PATH]
    queue_cli.py lock acquire <item_id> --owner OWNER [--config PATH]
    queue_cli.py lock release [--reason TEXT] [--config PATH]
    queue_cli.py lock refresh [--config PATH]
    queue_cli.py lock reconcile [--config PATH]
    queue_cli.py lock force-idle --reason TEXT [--config PATH]
    queue_cli.py dispatch run [--config PATH] [--dry-run]
    queue_cli.py dispatch status [--config PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow imports from the same directory
sys.path.insert(0, str(Path(__file__).parent))

from queue_lib import QueueConfig, WorkQueue, InvalidTransitionError
from lock_manager import LockManager
from dispatcher import QueueDispatcher


def _load_config(config_path: str) -> QueueConfig:
    return QueueConfig.from_yaml(Path(config_path))


def _lock_manager(config: QueueConfig) -> LockManager:
    lock_path = Path(config.queue_dir) / config.lock_file
    return LockManager(lock_path, config.lock_ttl_seconds)


def cmd_list(args: argparse.Namespace) -> None:
    config = _load_config(args.config)
    queue = WorkQueue(config)
    items = queue.parse_all()

    if args.status:
        items = [i for i in items if i.status == args.status]

    if args.role:
        role = config.roles.get(args.role)
        if role and role.handles_statuses:
            items = [i for i in items if i.status in role.handles_statuses]

    if not items:
        print("No items found.")
        return

    # Print as table
    header = f"{'ID':<12} {'Title':<40} {'Priority':<8} {'Status':<14} {'QA':<10} {'Updated':<16}"
    print(header)
    print("-" * len(header))
    for item in items:
        print(
            f"{item.id:<12} {item.title[:40]:<40} {item.priority:<8} "
            f"{item.status:<14} {item.qa_status:<10} {item.last_updated:<16}"
        )


def cmd_transition(args: argparse.Namespace) -> None:
    config = _load_config(args.config)
    queue = WorkQueue(config)

    kwargs: dict[str, str] = {}
    if args.notes:
        kwargs["notes"] = args.notes
    if args.commit_sha:
        kwargs["commit_sha"] = args.commit_sha

    try:
        item = queue.transition(args.id, args.new_status, force=args.force, **kwargs)
        print(f"✓ {item.id} → {item.status}")
    except InvalidTransitionError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)


def cmd_lock_status(args: argparse.Namespace) -> None:
    config = _load_config(args.config)
    lm = _lock_manager(config)
    info = lm.status()
    for k, v in info.items():
        print(f"  {k}: {v}")


def cmd_lock_acquire(args: argparse.Namespace) -> None:
    config = _load_config(args.config)
    lm = _lock_manager(config)
    ok = lm.acquire(args.item_id, args.owner)
    if ok:
        print(f"✓ Lock acquired for {args.item_id} by {args.owner}")
    else:
        print(f"✗ Lock already held", file=sys.stderr)
        sys.exit(1)


def cmd_lock_release(args: argparse.Namespace) -> None:
    config = _load_config(args.config)
    lm = _lock_manager(config)
    lm.release(reason=args.reason or "")
    print("✓ Lock released")


def cmd_lock_refresh(args: argparse.Namespace) -> None:
    config = _load_config(args.config)
    lm = _lock_manager(config)
    lm.refresh_ttl()
    print("✓ TTL refreshed")


def cmd_lock_reconcile(args: argparse.Namespace) -> None:
    config = _load_config(args.config)
    queue = WorkQueue(config)
    lm = _lock_manager(config)
    terminal = {name for name, sc in config.statuses.items() if sc.terminal}
    items = queue.parse_all()
    corrected = lm.reconcile_with_config(items, terminal)
    if corrected:
        print("✓ Stale lock cleared")
    else:
        print("· Lock is clean (no action needed)")


def cmd_lock_force_idle(args: argparse.Namespace) -> None:
    config = _load_config(args.config)
    lm = _lock_manager(config)
    lm.force_idle(args.reason)
    print(f"✓ Lock forced idle: {args.reason}")


def cmd_dispatch_run(args: argparse.Namespace) -> None:
    config = _load_config(args.config)
    dispatcher = QueueDispatcher(config)
    result = dispatcher.run_cycle(dry_run=args.dry_run)

    prefix = "[DRY RUN] " if args.dry_run else ""

    if result["lock_reconciled"]:
        print(f"{prefix}🔓 Stale lock cleared")

    for stall in result["stalled_tasks"]:
        print(f"{prefix}⚠️  Stalled: {stall['agent']} task {stall['task_id']} ({stall['elapsed_seconds']}s)")

    for d in result["dispatched"]:
        tid = d.get("task_id", "(dry-run)")
        print(f"{prefix}🚀 Dispatched {d['role']}: {d['item_id']} → {d['agent']} (task: {tid})")

    for s in result["skipped"]:
        print(f"{prefix}⏭️  Skipped {s['role']}: {s['reason']}")

    for e in result["errors"]:
        print(f"{prefix}❌ Error {e['role']}: {e.get('item_id', '?')} — {e['error']}")

    if not any([result["dispatched"], result["skipped"], result["errors"], result["stalled_tasks"]]):
        print(f"{prefix}· Nothing to do")


def cmd_dispatch_status(args: argparse.Namespace) -> None:
    config = _load_config(args.config)
    dispatcher = QueueDispatcher(config)
    result = dispatcher.run_cycle(dry_run=True)

    print("Dispatch Status (dry run):")
    for d in result["dispatched"]:
        print(f"  → Would dispatch {d['role']}: {d['item_id']} ({d['item_title'][:50]})")
    for s in result["skipped"]:
        print(f"  · Skip {s['role']}: {s['reason']}")
    if not result["dispatched"] and not result["skipped"]:
        print("  · No actions pending")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="queue_cli",
        description="Collaborative Work Queue — multi-agent queue management",
    )

    # Shared --config argument via parent parser
    config_parent = argparse.ArgumentParser(add_help=False)
    config_parent.add_argument("--config", default="./queue_config.yaml", help="Path to queue config YAML")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # list
    p_list = sub.add_parser("list", help="List work items", parents=[config_parent])
    p_list.add_argument("--status", help="Filter by status")
    p_list.add_argument("--role", help="Filter by role's handled statuses")

    # transition
    p_trans = sub.add_parser("transition", help="Transition a work item", parents=[config_parent])
    p_trans.add_argument("id", help="Work item ID")
    p_trans.add_argument("new_status", help="Target status")
    p_trans.add_argument("--notes", help="Update notes field")
    p_trans.add_argument("--commit-sha", help="Update commit SHA field")
    p_trans.add_argument("--force", action="store_true", help="Skip transition validation")

    # lock (with sub-subcommands)
    p_lock = sub.add_parser("lock", help="Lock management")
    lock_sub = p_lock.add_subparsers(dest="lock_command", help="Lock operations")

    lock_sub.add_parser("status", help="Show lock state", parents=[config_parent])

    p_lacq = lock_sub.add_parser("acquire", help="Acquire lock", parents=[config_parent])
    p_lacq.add_argument("item_id", help="Work item to lock")
    p_lacq.add_argument("--owner", required=True, help="Lock owner identity")

    p_lrel = lock_sub.add_parser("release", help="Release lock", parents=[config_parent])
    p_lrel.add_argument("--reason", help="Release reason")

    lock_sub.add_parser("refresh", help="Refresh lock TTL", parents=[config_parent])

    lock_sub.add_parser("reconcile", help="Auto-clear stale locks", parents=[config_parent])

    p_lfi = lock_sub.add_parser("force-idle", help="Force lock to idle", parents=[config_parent])
    p_lfi.add_argument("--reason", required=True, help="Reason for forcing idle")

    # dispatch
    p_disp = sub.add_parser("dispatch", help="Dispatch engine")
    disp_sub = p_disp.add_subparsers(dest="dispatch_command", help="Dispatch operations")

    p_drun = disp_sub.add_parser("run", help="Run one dispatch cycle", parents=[config_parent])
    p_drun.add_argument("--dry-run", action="store_true", help="Preview without executing")

    disp_sub.add_parser("status", help="Show dispatch status", parents=[config_parent])

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    dispatch_map = {
        "list": cmd_list,
        "transition": cmd_transition,
    }

    if args.command == "lock":
        lock_map = {
            "status": cmd_lock_status,
            "acquire": cmd_lock_acquire,
            "release": cmd_lock_release,
            "refresh": cmd_lock_refresh,
            "reconcile": cmd_lock_reconcile,
            "force-idle": cmd_lock_force_idle,
        }
        fn = lock_map.get(args.lock_command)
        if fn is None:
            parser.parse_args(["lock", "--help"])
            return
        fn(args)
    elif args.command == "dispatch":
        disp_map = {
            "run": cmd_dispatch_run,
            "status": cmd_dispatch_status,
        }
        fn = disp_map.get(args.dispatch_command)
        if fn is None:
            parser.parse_args(["dispatch", "--help"])
            return
        fn(args)
    elif args.command in dispatch_map:
        dispatch_map[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
