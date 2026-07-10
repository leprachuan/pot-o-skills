mac-control skill

This skill provides helpers to control macOS machines (SSH, AppleScript), read Apple Notes, control browsers, and run automations on registered Macs.

Runtimes:
- copilot: CLI helper scripts (copilot/mac_control.py)
- claude: natural-language mapping to actions
- gemini: natural-language mapping to actions

Security:
Do NOT store passwords or private keys in the repo. Use SSH keys or a secrets manager and restrict access to registered hosts.

Examples:
- Run a remote command:
  python3 copilot/mac_control.py --host user@mac.example.com --cmd 'ls -la'
- Run a local AppleScript:
  python3 copilot/mac_control.py --host local --cmd 'tell application "Finder" to open home' --local
