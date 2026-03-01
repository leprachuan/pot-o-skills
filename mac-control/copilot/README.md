copilot runtime for mac-control

This folder contains CLI helpers used by the copilot runtime.

Usage:
- python3 mac_control.py --host user@mac.example.com --cmd 'ls -la'
- python3 mac_control.py --host local --cmd 'tell application "Finder" to open home' --local

Security: use SSH keys and a secure agent; do not store passwords in code.
