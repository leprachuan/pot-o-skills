#!/usr/bin/env python3
"""Proactive Watchers - Claude runtime implementation.

CLI and programmatic interface for creating, managing, and running URL/API watchers
that trigger AI actions when conditions are met.
"""

import argparse
import json
import os
import signal
import sys
import logging
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.watcher_engine import WatcherEngine

logging.basicConfig(
    level=getattr(logging, os.environ.get("WATCHER_LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("proactive-watchers")


def cmd_create(args, engine: WatcherEngine):
    """Create a new watcher from a JSON config file or inline JSON."""
    if args.config:
        with open(args.config, "r") as f:
            config = json.load(f)
    elif args.json:
        config = json.loads(args.json)
    else:
        print("Error: Provide --config <file> or --json '<json>'")
        sys.exit(1)

    result = engine.create_watcher(config)
    if result["success"]:
        print(f"✅ Watcher '{config['name']}' created")
        print(json.dumps(result["watcher"], indent=2, default=str))
    else:
        print(f"❌ Failed: {result['error']}")
        sys.exit(1)


def cmd_list(args, engine: WatcherEngine):
    """List all defined watchers and their status."""
    watchers = engine.list_watchers()
    if not watchers:
        print("No watchers defined. Create one with: proactive_watchers.py create --config <file>")
        return

    print(f"\n{'Name':<25} {'Type':<18} {'Interval':<10} {'Running':<8} {'Triggers':<9} {'Last Check'}")
    print("─" * 95)
    for w in watchers:
        last_check = ""
        if w.get("last_check"):
            last_check = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(w["last_check"]))
        running = "🟢 Yes" if w.get("running") else "⚪ No"
        print(f"{w['name']:<25} {w.get('type', 'url_change'):<18} {w.get('check_interval', 300):<10} "
              f"{running:<8} {w.get('trigger_count', 0):<9} {last_check}")
    print()


def cmd_show(args, engine: WatcherEngine):
    """Show detailed configuration of a specific watcher."""
    watcher = engine.state_manager.get_watcher(args.watcher)
    if not watcher:
        print(f"❌ Watcher '{args.watcher}' not found")
        sys.exit(1)

    state = engine.state_manager.get_state(args.watcher)
    watcher["_state"] = state
    print(json.dumps(watcher, indent=2, default=str))


def cmd_start(args, engine: WatcherEngine):
    """Start a watcher (or all watchers)."""
    if args.watcher == "all":
        result = engine.start_all()
        if result["started"]:
            print(f"✅ Started {result['count']} watcher(s): {', '.join(result['started'])}")
        else:
            print("No watchers to start")
    else:
        result = engine.start_watcher(args.watcher)
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['error']}")
            sys.exit(1)

    if not args.detach:
        print("\nWatchers running. Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping watchers...")
            engine.shutdown()
            print("Done.")


def cmd_stop(args, engine: WatcherEngine):
    """Stop a watcher (or all watchers)."""
    if args.watcher == "all":
        result = engine.stop_all()
        print(f"✅ Stopped {result['count']} watcher(s)")
    else:
        result = engine.stop_watcher(args.watcher)
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['error']}")


def cmd_test(args, engine: WatcherEngine):
    """Run a single poll cycle (dry run) for testing."""
    result = engine.test_watcher(args.watcher)
    if result.get("error"):
        print(f"❌ Error: {result['error']}")
        sys.exit(1)

    print(f"Watcher: {result.get('watcher')}")
    print(f"Status Code: {result.get('status_code')}")
    print(f"Triggered: {'🔔 YES' if result.get('triggered') else '⚪ No'}")
    print(f"Reason: {result.get('reason')}")
    if result.get("extracted_value") is not None:
        val = result["extracted_value"]
        if isinstance(val, str) and len(val) > 200:
            val = val[:200] + "..."
        print(f"Extracted Value: {val}")


def cmd_delete(args, engine: WatcherEngine):
    """Delete a watcher."""
    result = engine.delete_watcher(args.watcher)
    if result["success"]:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ {result['error']}")
        sys.exit(1)


def cmd_history(args, engine: WatcherEngine):
    """View event history for a watcher."""
    events = engine.state_manager.get_history(args.watcher, limit=args.limit)
    if not events:
        print(f"No history for watcher '{args.watcher}'")
        return

    print(f"\nHistory for '{args.watcher}' (last {len(events)} events):\n")
    for event in events:
        ts = event.get("iso_time", time.strftime("%Y-%m-%dT%H:%M:%SZ",
                        time.gmtime(event.get("timestamp", 0))))
        etype = event.get("type", "unknown")
        triggered = event.get("triggered", False)

        icon = {"poll": "🔍", "trigger": "🔔", "error": "❌"}.get(etype, "📋")
        marker = " 🔔" if triggered else ""

        print(f"  {icon} [{ts}] {etype}{marker}: {event.get('reason', event.get('error', ''))}")
    print()


def cmd_clear_history(args, engine: WatcherEngine):
    """Clear event history for a watcher."""
    engine.state_manager.clear_history(args.watcher)
    print(f"✅ History cleared for '{args.watcher}'")


def cmd_enable(args, engine: WatcherEngine):
    """Enable a watcher."""
    if engine.state_manager.update_watcher(args.watcher, {"enabled": True}):
        print(f"✅ Watcher '{args.watcher}' enabled")
    else:
        print(f"❌ Watcher '{args.watcher}' not found")
        sys.exit(1)


def cmd_disable(args, engine: WatcherEngine):
    """Disable a watcher."""
    if engine.state_manager.update_watcher(args.watcher, {"enabled": False}):
        print(f"✅ Watcher '{args.watcher}' disabled")
    else:
        print(f"❌ Watcher '{args.watcher}' not found")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Proactive Watchers - Monitor URLs/APIs and trigger AI actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create --config templates/github_releases.json
  %(prog)s list
  %(prog)s test --watcher github-releases
  %(prog)s start --watcher github-releases
  %(prog)s start --watcher all --detach
  %(prog)s stop --watcher github-releases
  %(prog)s history --watcher github-releases
  %(prog)s delete --watcher github-releases
""",
    )

    parser.add_argument("--watchers-dir", help="Watchers storage directory",
                        default=os.environ.get("WATCHERS_DIR"))
    parser.add_argument("--api-base", help="Orchestrator API base URL",
                        default="https://127.0.0.1:8000")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # create
    p_create = subparsers.add_parser("create", help="Create a new watcher")
    p_create.add_argument("--config", help="Path to watcher config JSON file")
    p_create.add_argument("--json", help="Inline JSON config")

    # list
    subparsers.add_parser("list", help="List all watchers")

    # show
    p_show = subparsers.add_parser("show", help="Show watcher details")
    p_show.add_argument("--watcher", required=True, help="Watcher name")

    # start
    p_start = subparsers.add_parser("start", help="Start watching")
    p_start.add_argument("--watcher", required=True, help="Watcher name or 'all'")
    p_start.add_argument("--detach", action="store_true", help="Run in background (don't block)")

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop watching")
    p_stop.add_argument("--watcher", required=True, help="Watcher name or 'all'")

    # test
    p_test = subparsers.add_parser("test", help="Test a watcher (single poll, dry run)")
    p_test.add_argument("--watcher", required=True, help="Watcher name")

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a watcher")
    p_delete.add_argument("--watcher", required=True, help="Watcher name")

    # history
    p_history = subparsers.add_parser("history", help="View watcher event history")
    p_history.add_argument("--watcher", required=True, help="Watcher name")
    p_history.add_argument("--limit", type=int, default=50, help="Max events to show")

    # clear-history
    p_clear = subparsers.add_parser("clear-history", help="Clear watcher history")
    p_clear.add_argument("--watcher", required=True, help="Watcher name")

    # enable / disable
    p_enable = subparsers.add_parser("enable", help="Enable a watcher")
    p_enable.add_argument("--watcher", required=True, help="Watcher name")
    p_disable = subparsers.add_parser("disable", help="Disable a watcher")
    p_disable.add_argument("--watcher", required=True, help="Watcher name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    engine = WatcherEngine(watchers_dir=args.watchers_dir, api_base=args.api_base)

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\nShutting down...")
        engine.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    commands = {
        "create": cmd_create,
        "list": cmd_list,
        "show": cmd_show,
        "start": cmd_start,
        "stop": cmd_stop,
        "test": cmd_test,
        "delete": cmd_delete,
        "history": cmd_history,
        "clear-history": cmd_clear_history,
        "enable": cmd_enable,
        "disable": cmd_disable,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args, engine)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
