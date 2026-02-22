gemini runtime notes for mac-control

Same approach as the claude runtime: translate natural language to an action plan, then invoke the copilot helper to execute.

Suggested flow:
1. Parse user intent and extract target host and operation
2. Confirm potentially destructive actions with the user
3. Sanitize inputs and invoke copilot/mac_control.py

Security: require explicit confirmation for destructive operations and gate access to authorized hosts only.
