---
name: self-improving-agent
description: Capture corrections, errors, feature requests, and recurring best practices in a local `.learnings/` workspace so future agent runs can avoid repeating mistakes. Use when a command fails, a user corrects the agent, a missing capability is requested, a better repeatable approach is discovered, or before major work to review prior lessons.
---

# Self-Improving Agent

Use this skill to keep a lightweight local learning loop for Wee Orchestrator work and related repos.

## Quick Start

Initialize a learning workspace in the current project root:

```bash
./scripts/init_learnings.sh
```

That creates:

```text
.learnings/
├── LEARNINGS.md
├── ERRORS.md
└── FEATURE_REQUESTS.md
```

Do not overwrite existing files. Keep entries short, specific, and sanitized.

## Wee Orchestrator Adaptation

This skill is adapted for Wee Orchestrator rather than OpenClaw.

- Use `.learnings/` in the repo or agent workspace you are actively changing.
- For Wee Orchestrator dev work, prefer `/opt/n8n-copilot-shim-dev/.learnings/` on the dev host.
- For local agent repos like `/opt/wee-dev`, `/opt/wee-qa`, or `/opt/skills/<skill-name>`, keep `.learnings/` inside that repo.
- Do not store secrets, tokens, raw environment files, or full logs. Store summaries or redacted excerpts.

## When to Log

| Situation | Destination |
|---|---|
| Unexpected command or tool failure | `.learnings/ERRORS.md` |
| User correction or outdated assumption | `.learnings/LEARNINGS.md` |
| Missing capability request | `.learnings/FEATURE_REQUESTS.md` |
| Better recurring implementation pattern | `.learnings/LEARNINGS.md` |
| Repeated bug pattern from multiple tasks | Update existing learning and increase recurrence metadata |

## Before Major Work

Before a substantial task, scan local learnings:

```bash
grep -n "^## \[" .learnings/*.md 2>/dev/null
```

If you are working in a familiar area, also search by topic:

```bash
grep -Rni "auth\|scheduler\|queue\|frontend" .learnings/ 2>/dev/null
```

## Promotion Targets

When a learning is stable and broadly useful, promote it out of `.learnings/`:

- Project conventions → `CLAUDE.md`
- Agent workflow guidance → `AGENTS.md`
- Copilot-specific reminders → `.github/copilot-instructions.md`
- Cross-session durable lessons → Total Recall `agent_lessons`
- Repository-wide implementation facts → repo memory/store-memory workflow

For Wee Orchestrator specifically, the most common promotion targets are `/opt/AGENTS.md`, `/opt/CLAUDE.md`, and the relevant repo-local `AGENTS.md`.

## Entry Guidelines

Use IDs like `LRN-YYYYMMDD-001`, `ERR-YYYYMMDD-001`, and `FEAT-YYYYMMDD-001`.

Always include:

- timestamp
- priority
- status
- area
- concise summary
- concrete suggested action
- related files when known

Prefer updating an existing entry over duplicating it. Link related items with `See Also`.

## Status Values

Use these statuses consistently:

- `pending`
- `in_progress`
- `resolved`
- `wont_fix`
- `promoted`
- `promoted_to_skill`

## Hook / Reminder Support

This skill includes small helper scripts:

- `scripts/activator.sh` — reminder at prompt start
- `scripts/error-detector.sh` — reminder after shell/tool failures

For Claude-style environments with hooks, see `references/wee-orchestrator-integration.md`.
For Copilot CLI, add a short reminder to `AGENTS.md` or `copilot-instructions.md` instead of relying on hooks.

## Resources

- `references/examples.md` — example entries for each log type
- `references/wee-orchestrator-integration.md` — setup guidance for local agent repos
- `references/upstream.md` — upstream source references and adaptation notes
- `assets/` — starter templates for `.learnings/` files
