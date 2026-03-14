#!/usr/bin/env python3
"""
gws-workspace helper — thin wrapper around the gws CLI for common Google
Workspace operations. All credentials are managed by gws itself via
~/.config/gws/. No credentials are stored in this script.

Usage:
    python3 gws_helper.py --action <action> [options]

Actions:
    auth_status          Show current auth state
    list_calendars       List all calendars
    list_events          List calendar events (--start / --end / --calendar)
    create_event         Create a calendar event (--title --start-dt --end-dt [--allday] [--description] [--calendar])
    list_drive           List Drive files (--query / --max)
    list_inbox           List recent inbox messages (--max / --query)
    send_email           Send email (--to --subject --body [--html] [--cc] [--bcc])
    triage_inbox         Show inbox triage summary (--max)
    agenda               Show upcoming calendar agenda
    standup              Show standup report (calendar + tasks)
    weekly_digest        Weekly digest (meetings + email)
    list_tasks           List tasks from default task list
    add_task             Add task to default task list (--title [--notes] [--due])
    read_sheet           Read a Google Sheet range (--spreadsheet --range)
    append_sheet         Append row to Sheet (--spreadsheet --values)
"""

import argparse
import subprocess
import sys
import json


def run_gws(args: list, capture: bool = True) -> dict | str | None:
    """Run a gws command and return parsed JSON or raw output."""
    cmd = ["gws"] + args
    result = subprocess.run(cmd, capture_output=capture, text=True)

    if result.returncode != 0:
        print(f"Error (exit {result.returncode}):", file=sys.stderr)
        print(result.stderr.strip(), file=sys.stderr)
        return None

    if capture and result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return result.stdout
    return result.stdout if capture else None


def auth_status():
    data = run_gws(["auth", "status"])
    if data:
        print(f"User:       {data.get('user', 'unknown')}")
        print(f"Valid:      {data.get('token_valid', False)}")
        print(f"Auth:       {data.get('auth_method', 'none')}")
        print(f"Scopes:     {data.get('scope_count', 0)}")


def list_calendars():
    run_gws(["calendar", "calendarList", "list", "--format", "table"], capture=False)


def list_events(args):
    params = {"calendarId": args.calendar or "primary", "maxResults": args.max or 20}
    if args.start:
        params["timeMin"] = f"{args.start}T00:00:00Z"
    if args.end:
        params["timeMax"] = f"{args.end}T23:59:59Z"
    run_gws([
        "calendar", "events", "list",
        "--params", json.dumps(params),
        "--format", "table"
    ], capture=False)


def create_event(args):
    if args.allday:
        event = {
            "summary": args.title,
            "start": {"date": args.start_dt},
            "end": {"date": args.end_dt},
        }
    else:
        tz = args.timezone or "America/New_York"
        event = {
            "summary": args.title,
            "start": {"dateTime": args.start_dt, "timeZone": tz},
            "end": {"dateTime": args.end_dt, "timeZone": tz},
        }
    if args.description:
        event["description"] = args.description

    data = run_gws([
        "calendar", "events", "insert",
        "--params", json.dumps({"calendarId": args.calendar or "primary"}),
        "--json", json.dumps(event)
    ])
    if data:
        print(f"Created: {data.get('summary')} [{data.get('id')}]")
        print(f"Link:    {data.get('htmlLink', '')}")


def list_drive(args):
    params = {"pageSize": args.max or 20}
    if args.query:
        params["q"] = args.query
    run_gws(["drive", "files", "list", "--params", json.dumps(params), "--format", "table"], capture=False)


def list_inbox(args):
    params = {"userId": "me", "maxResults": args.max or 10}
    if args.query:
        params["q"] = args.query
    else:
        params["q"] = "in:inbox"
    run_gws(["gmail", "users", "messages", "list", "--params", json.dumps(params), "--format", "table"], capture=False)


def send_email(args):
    cmd = ["gmail", "+send", "--to", args.to, "--subject", args.subject, "--body", args.body]
    if args.html:
        cmd.append("--html")
    if args.cc:
        cmd += ["--cc", args.cc]
    if args.bcc:
        cmd += ["--bcc", args.bcc]
    run_gws(cmd, capture=False)


def triage_inbox(args):
    cmd = ["gmail", "+triage", "--max", str(args.max or 20), "--format", "table"]
    run_gws(cmd, capture=False)


def agenda():
    run_gws(["calendar", "+agenda"], capture=False)


def standup():
    run_gws(["workflow", "+standup-report", "--format", "table"], capture=False)


def weekly_digest():
    run_gws(["workflow", "+weekly-digest"], capture=False)


def list_tasks(args):
    run_gws(["tasks", "tasks", "list", "--params", '{"tasklist": "@default"}', "--format", "table"], capture=False)


def add_task(args):
    task = {"title": args.title}
    if args.notes:
        task["notes"] = args.notes
    if args.due:
        task["due"] = f"{args.due}T00:00:00.000Z"
    data = run_gws([
        "tasks", "tasks", "insert",
        "--params", '{"tasklist": "@default"}',
        "--json", json.dumps(task)
    ])
    if data:
        print(f"Created task: {data.get('title')} [{data.get('id')}]")


def read_sheet(args):
    run_gws([
        "sheets", "+read",
        "--spreadsheet", args.spreadsheet,
        "--range", args.range or "Sheet1"
    ], capture=False)


def append_sheet(args):
    cmd = ["sheets", "+append", "--spreadsheet", args.spreadsheet]
    if args.values:
        cmd += ["--values", args.values]
    elif args.json_values:
        cmd += ["--json-values", args.json_values]
    run_gws(cmd, capture=False)


ACTIONS = {
    "auth_status": auth_status,
    "list_calendars": list_calendars,
    "list_events": list_events,
    "create_event": create_event,
    "list_drive": list_drive,
    "list_inbox": list_inbox,
    "send_email": send_email,
    "triage_inbox": triage_inbox,
    "agenda": agenda,
    "standup": standup,
    "weekly_digest": weekly_digest,
    "list_tasks": list_tasks,
    "add_task": add_task,
    "read_sheet": read_sheet,
    "append_sheet": append_sheet,
}


def main():
    parser = argparse.ArgumentParser(description="GWS Google Workspace helper")
    parser.add_argument("--action", required=True, choices=ACTIONS.keys())

    # Calendar
    parser.add_argument("--calendar", help="Calendar ID (default: primary)")
    parser.add_argument("--start", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", help="End date YYYY-MM-DD")
    parser.add_argument("--title", help="Event/task title")
    parser.add_argument("--start-dt", help="Event start datetime (ISO 8601 or YYYY-MM-DD for all-day)")
    parser.add_argument("--end-dt", help="Event end datetime (ISO 8601 or YYYY-MM-DD for all-day)")
    parser.add_argument("--allday", action="store_true", help="All-day event")
    parser.add_argument("--description", help="Event description")
    parser.add_argument("--timezone", help="Timezone (default: America/New_York)")

    # Email
    parser.add_argument("--to", help="Recipient email")
    parser.add_argument("--subject", help="Email subject")
    parser.add_argument("--body", help="Email body")
    parser.add_argument("--html", action="store_true", help="Send as HTML email")
    parser.add_argument("--cc", help="CC recipient")
    parser.add_argument("--bcc", help="BCC recipient")

    # General
    parser.add_argument("--max", type=int, help="Max results")
    parser.add_argument("--query", help="Search query")

    # Tasks
    parser.add_argument("--notes", help="Task notes")
    parser.add_argument("--due", help="Task due date YYYY-MM-DD")

    # Sheets
    parser.add_argument("--spreadsheet", help="Spreadsheet ID")
    parser.add_argument("--range", help="Sheet range (e.g. Sheet1!A1:D10)")
    parser.add_argument("--values", help="CSV row values to append")
    parser.add_argument("--json-values", help="JSON array of rows to append")

    args = parser.parse_args()
    action = ACTIONS[args.action]

    # Actions that take no args
    if args.action in ("auth_status", "list_calendars", "agenda", "standup", "weekly_digest"):
        action()
    else:
        action(args)


if __name__ == "__main__":
    main()
