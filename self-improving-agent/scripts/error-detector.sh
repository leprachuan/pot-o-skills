#!/usr/bin/env bash
set -euo pipefail
OUTPUT="${CLAUDE_TOOL_OUTPUT:-}"

case "$OUTPUT" in
  *"error:"*|*"Error:"*|*"failed"*|*"FAILED"*|*"command not found"*|*"No such file"*|*"Permission denied"*|*"Traceback"*|*"Exception"*|*"exit code"*)
    cat <<'EOF'
<self-improving-agent-error>
A tool error was detected. If the failure was non-obvious, recurring, or required debugging, add a concise entry to .learnings/ERRORS.md.
</self-improving-agent-error>
EOF
    ;;
esac
