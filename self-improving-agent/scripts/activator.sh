#!/usr/bin/env bash
set -euo pipefail
cat <<'EOF'
<self-improving-agent-reminder>
After this task, check whether you learned something worth keeping:
- a non-obvious fix
- a repeated failure pattern
- a project-specific convention
- a missing feature request
If yes, record it in .learnings/ and promote stable lessons into standing guidance.
</self-improving-agent-reminder>
EOF
