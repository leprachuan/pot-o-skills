#!/usr/bin/env python3
"""Proactive Watchers - Copilot CLI runtime implementation.

Identical feature set to the Claude implementation, optimized for
Copilot CLI terminal workflows.
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
logger = logging.getLogger("proactive-watchers.copilot")


def format_table(rows: list[dict], columns: list[tuple[str, str, int]]) -> str:
    """Format data as an aligned ASCII table for terminal output."""
    header = ""
    sep = ""
    for label, _, width in columns:
        header += f"{label:<{width}} "
        sep += "─" * width + " "

    lines = [header.rstrip(), sep.rstrip()]
    for row in rows:
        line = ""
        for _, key, width in columns:
            val = str(row.get(key, ""))
            if len(val) > width:
                val = val[:width - 1] + "…"
            line += f"{val:<{width}} "
        lines.append(line.rstrip())
    return "\n".join(lines)


def cmd_create(args, engine: WatcherEngine):
    if args.config:
        with open(args.config, "r") as f:
            config = json.load(f)
    elif args.json:
        config = json.loads(args.json)
    elif args.name and args.url:
        config = {
            "name": args.name,
            "url": args.url,
            "type": args.type or "url_change",
            "condition": args.condition or "value_changed",
            "check_interval": args.interval or 300,
            "method": "GET",
            "on_trigger": {
                "method": args.trigger_method or "log_only",
                "prompt_template": args.prompt or "Watcher '{{watcher_name}}' triggered: {{reason}}",
            },
        }
        if args.trigger_field:
            config["trigger_field"] = args.trigger_field
        if args.headers:
            config["headers"] = json.loads(args.headers)
    else:
        print("Error: Provide --config, --json, or --name + --url")
        sys.exit(1)

    result = engine.create_watcher(config)
    if result["success"]:
        print(f"Created watcher: {config['name']}")
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)


def cmd_list(args, engine: WatcherEngine):
    watchers = engine.list_watchers()
    if not watchers:
        print("No watchers defined.")
        return

    for w in watchers:
        w["status"] = "running" if w.get("running") else ("disabled" if not w.get("enabled", True) else "stopped")
        w["interval_s"] = str(w.get("check_interval", 300)) + "s"
        w["triggers"] = str(w.get("trigger_count", 0))

    columns = [
        ("NAME", "name", 25),
        ("TYPE", "type", 18),
        ("INTERVAL", "interval_s", 10),
        ("STATUS", "status", 10),
        ("TRIGGERS", "triggers", 9),
    ]
    print(format_table(watchers, columns))


def cmd_test(args, engine: WatcherEngine):
    result = engine.test_watcher(args.watcher)
    if result.get("error"):
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"Watcher:   {result.get('watcher')}")
    print(f"Status:    {result.get('status_code')}")
    print(f"Triggered: {'YES' if result.get('triggered') else 'No'}")
    print(f"Reason:    {result.get('reason')}")
    val = result.get("extracted_value")
    if val is not None:
        val_str = str(val)
        if len(val_str) > 200:
            val_str = val_str[:200] + "..."
        print(f"Value:     {val_str}")


def cmd_start(args, engine: WatcherEngine):
    if args.watcher == "all":
        result = engine.start_all()
        print(f"Started {result['count']} watcher(s)")
    else:
        result = engine.start_watcher(args.watcher)
        if result["success"]:
            print(result["message"])
        else:
            print(f"Error: {result['error']}")
            sys.exit(1)

    if not args.detach:
        print("Watching... (Ctrl+C to stop)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            engine.shutdown()
            print("Stopped.")


def cmd_stop(args, engine: WatcherEngine):
    if args.watcher == "all":
        result = engine.stop_all()
        print(f"Stopped {result['count']} watcher(s)")
    else:
        result = engine.stop_watcher(args.watcher)
        print(result.get("message", result.get("error", "")))


def cmd_delete(args, engine: WatcherEngine):
    result = engine.delete_watcher(args.watcher)
    print(result.get("message", result.get("error", "")))


def cmd_history(args, engine: WatcherEngine):
    events = engine.state_manager.get_history(args.watcher, limit=args.limit)
    if not events:
        print(f"No history for '{args.watcher}'")
        return

    for event in events:
        ts = event.get("iso_time", "?")
        etype = event.get("type", "?")
        triggered = " TRIGGERED" if event.get("triggered") else ""
        detail = event.get("reason", event.get("error", ""))
        print(f"[{ts}] {etype}{triggered}: {detail}")


def main():
    parser = argparse.ArgumentParser(description="Proactive Watchers CLI")
    parser.add_argument("--watchers-dir", default=os.environ.get("WATCHERS_DIR"))
    parser.add_argument("--api-base", default="https://127.0.0.1:8000")

    sub = parser.add_subparsers(dest="command")

    p_create = sub.add_parser("create")
    p_create.add_argument("--config")
    p_create.add_argument("--json")
    p_create.add_argument("--name")
    p_create.add_argument("--url")
    p_create.add_argument("--type", default="url_change")
    p_create.add_argument("--condition", default="value_changed")
    p_create.add_argument("--interval", type=int, default=300)
    p_create.add_argument("--trigger-field")
    p_create.add_argument("--trigger-method", default="log_only")
    p_create.add_argument("--prompt")
    p_create.add_argument("--headers")

    sub.add_parser("list")

    p_test = sub.add_parser("test")
    p_test.add_argument("--watcher", required=True)

    p_start = sub.add_parser("start")
    p_start.add_argument("--watcher", required=True)
    p_start.add_argument("--detach", action="store_true")

    p_stop = sub.add_parser("stop")
    p_stop.add_argument("--watcher", required=True)

    p_del = sub.add_parser("delete")
    p_del.add_argument("--watcher", required=True)

    p_hist = sub.add_parser("history")
    p_hist.add_argument("--watcher", required=True)
    p_hist.add_argument("--limit", type=int, default=50)

    p_en = sub.add_parser("enable")
    p_en.add_argument("--watcher", required=True)
    p_dis = sub.add_parser("disable")
    p_dis.add_argument("--watcher", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    engine = WatcherEngine(watchers_dir=args.watchers_dir, api_base=args.api_base)

    signal.signal(signal.SIGINT, lambda s, f: (engine.shutdown(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (engine.shutdown(), sys.exit(0)))

    commands = {
        "create": cmd_create, "list": cmd_list, "test": cmd_test,
        "start": cmd_start, "stop": cmd_stop, "delete": cmd_delete,
        "history": cmd_history,
        "enable": lambda a, e: print("Enabled" if e.state_manager.update_watcher(a.watcher, {"enabled": True}) else "Not found"),
        "disable": lambda a, e: print("Disabled" if e.state_manager.update_watcher(a.watcher, {"enabled": False}) else "Not found"),
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args, engine)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
