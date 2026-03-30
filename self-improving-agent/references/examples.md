# Entry Examples

These are concise example entries for local `.learnings/` files.

## Learning Example

```markdown
## [LRN-20260330-001] best_practice

**Logged**: 2026-03-30T00:00:00Z
**Priority**: high
**Status**: pending
**Area**: backend

### Summary
Background task dispatch must use the orchestrator API for user-visible work.

### Details
A task was launched internally and did not appear in the Tasks tab. The correct path for user-visible background work is the orchestrator background task API.

### Suggested Action
Use the orchestrator API for user-facing background runs and reserve internal delegation for invisible sub-agent routing.

### Metadata
- Source: user_feedback
- Related Files: /opt/AGENTS.md, /opt/n8n-copilot-shim/agent_manager.py
- Tags: background-tasks, orchestration

---
```

## Error Example

```markdown
## [ERR-20260330-001] pytest

**Logged**: 2026-03-30T00:10:00Z
**Priority**: medium
**Status**: pending
**Area**: tests

### Summary
Pytest failed because the dev environment was not synced after a dependency change.

### Error
```text
ModuleNotFoundError: No module named 'yaml'
```

### Context
- Command: `python3 -m pytest tests/ -q`
- Environment: dev host
- Related step: dependency update was made but the environment was not refreshed

### Suggested Fix
Reinstall dependencies before rerunning tests and document the dependency requirement.

### Metadata
- Reproducible: yes
- Related Files: requirements.txt

---
```

## Feature Request Example

```markdown
## [FEAT-20260330-001] max-concurrent-ui

**Logged**: 2026-03-30T00:20:00Z
**Priority**: medium
**Status**: pending
**Area**: frontend

### Requested Capability
Expose `max_concurrent` in the agent settings panel.

### User Context
The backend already supports per-agent concurrency limits, but the WebUI does not expose the field for editing.

### Complexity Estimate
simple

### Suggested Implementation
Add a numeric settings field wired to the existing agents-config save path and validate values are integers >= 1.

### Metadata
- Frequency: recurring
- Related Features: agents-config, settings panel

---
```
