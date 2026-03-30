# Wee Orchestrator Integration

This skill is designed for local use inside Wee Orchestrator repos and agent workspaces.

## Recommended Placement of `.learnings/`

Create `.learnings/` in the repo you are actively changing:

- `/opt/n8n-copilot-shim/.learnings/` for production-repo analysis
- `/opt/n8n-copilot-shim-dev/.learnings/` for dev implementation work
- `/opt/wee-dev/.learnings/` for wee-dev queue or repo-specific lessons
- `/opt/wee-qa/.learnings/` for QA-specific findings
- `/opt/skills/<skill-name>/.learnings/` while building a skill

## Hook Strategy

### Claude-style local hooks

If the runtime supports hook commands, point them at this skill's helper scripts.

Example project-local hook config:

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "/opt/skills/self-improving-agent/scripts/activator.sh"
      }]
    }],
    "PostToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "/opt/skills/self-improving-agent/scripts/error-detector.sh"
      }]
    }]
  }
}
```

### Copilot CLI

Copilot CLI does not provide the same hook path here. Use one of these instead:

1. Add a short self-improvement reminder to the relevant `AGENTS.md`
2. Review `.learnings/` before major work
3. Promote stable lessons to repo memory or Total Recall

## Promotion Guidance for Wee

Promote lessons when they meet at least one of these:

- repeated across multiple tasks
- likely to affect future agents
- tied to repo-specific conventions
- important enough to belong in standing instructions

Common destinations:

- `/opt/AGENTS.md`
- `/opt/CLAUDE.md`
- repo-local `AGENTS.md`
- `.github/copilot-instructions.md`
- Total Recall category `agent_lessons`
