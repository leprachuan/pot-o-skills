#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
LEARN_DIR="$ROOT/.learnings"
mkdir -p "$LEARN_DIR"

write_if_missing() {
  local path="$1"
  local content="$2"
  if [ ! -f "$path" ]; then
    printf '%s' "$content" > "$path"
    echo "created $path"
  else
    echo "exists   $path"
  fi
}

write_if_missing "$LEARN_DIR/LEARNINGS.md" "# Learnings

Corrections, insights, knowledge gaps, and best practices captured during work.

**Categories**: correction | insight | knowledge_gap | best_practice
**Areas**: frontend | backend | infra | tests | docs | config
**Statuses**: pending | in_progress | resolved | wont_fix | promoted | promoted_to_skill

---
"
write_if_missing "$LEARN_DIR/ERRORS.md" "# Errors

Unexpected command failures, runtime errors, and integration issues.

---
"
write_if_missing "$LEARN_DIR/FEATURE_REQUESTS.md" "# Feature Requests

Requested capabilities that do not exist yet or should be expanded.

---
"
