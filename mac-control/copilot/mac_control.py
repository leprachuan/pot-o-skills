#!/usr/bin/env python3
"""
Simple mac-control copilot runtime helper.

Usage:
  python3 mac_control.py --host user@host.example.com --cmd "ls -la" [--local]
If --local is set, runs osascript on the local machine.

This is a minimal implementation; production setups should use SSH keys and proper credential management.
"""

import argparse
import subprocess
import sys


def run_ssh(host, cmd):
    ssh_cmd = ["ssh", host, cmd]
    proc = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    return proc.returncode


def run_local_applescript(cmd):
    as_cmd = ["osascript", "-e", cmd]
    proc = subprocess.run(as_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description="mac-control helper")
    parser.add_argument("--host", help="SSH destination (user@host) or 'local'", required=True)
    parser.add_argument("--cmd", help="Command or AppleScript to run", required=True)
    parser.add_argument("--local", action="store_true", help="Run command on local mac via osascript")
    args = parser.parse_args()

    if args.local or args.host in ("local", "localhost"):
        rc = run_local_applescript(args.cmd)
    else:
        rc = run_ssh(args.host, args.cmd)
    sys.exit(rc)


if __name__ == "__main__":
    main()
