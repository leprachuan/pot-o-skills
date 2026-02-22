claude runtime notes for mac-control

This runtime maps natural language requests into concrete actions executed by the copilot runtime.

Examples of intents:
- "Read my Notes titled 'Groceries'" → map to a script that fetches Apple Notes content
- "Open Safari and go to example.com" → run AppleScript or remote command to control browser

Implementation notes:
- Claude runtime should validate and sanitize commands, then call the copilot/mac_control.py helper on the target host.
- Do not embed credentials; use an agent or SSH keys and a secure connector.
