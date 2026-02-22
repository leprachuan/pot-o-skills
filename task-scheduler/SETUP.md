# Setup

## 🖥️ Host Requirements

**CLI-Tools host only** (`/opt/` on Linux)

This skill can **ONLY** be executed on the CLI-Tools host. It is **NOT available** on:
- ❌ MacBook (`~/Documents/fosterbot-home/`)
- ❌ lepbuntu or other hosts

**Reason**: The skill requires systemd services, `/opt/` infrastructure, and Linux-based APScheduler that are only available on the CLI-Tools host.

---

## Dependencies

This skill requires **Wee-Orchestrator** to be installed:

- **Project Name**: Wee-Orchestrator (formerly n8n-copilot-shim)
- **Repository**: https://github.com/leprachuan/Wee-Orchestrator.git
- **Local Folder** (legacy name): `/opt/n8n-copilot-shim/`
- **Purpose**: Provides agent_manager.py for executing LLM tasks with multiple runtimes (Claude, Copilot, Gemini)

Clone it with:
```bash
git clone https://github.com/leprachuan/Wee-Orchestrator.git /opt/n8n-copilot-shim
```

> **Naming Note**: The project was renamed to **Wee-Orchestrator**, but the local folder is kept as `n8n-copilot-shim` for backwards compatibility.

## Installation Steps

1. cp .env.example .env
2. Edit .env with your settings
3. mkdir -p /opt/.task-scheduler/logs/
4. mkdir -p /opt/.task-scheduler/results/
5. pip install apscheduler
6. Ensure Wee-Orchestrator (n8n-copilot-shim) is installed at `/opt/n8n-copilot-shim/`

## Configuration

Configure the task scheduler via environment variables in `.env`:

| Variable | Default | Description |
| --- | --- | --- |
| `SCHEDULER_JOBS_FILE` | `/opt/.task-scheduler/jobs.json` | Path to jobs database |
| `SCHEDULER_LOGS_DIR` | `/opt/.task-scheduler/logs/` | Directory for job execution logs |
| `SCHEDULER_RESULTS_DIR` | `/opt/.task-scheduler/results/` | Directory for JSONL results |
| `SCHEDULER_DEFAULT_AGENT` | `orchestrator` | Default agent if not specified in job |
| `SCHEDULER_DEFAULT_RUNTIME` | `claude` | Default runtime if not specified in job |
| `SCHEDULER_RETRY_MAX` | `3` | Maximum retry attempts per job |

### Example .env

```bash
SCHEDULER_DEFAULT_AGENT=my-orchestrator
SCHEDULER_DEFAULT_RUNTIME=claude
SCHEDULER_JOBS_FILE=/var/lib/task-scheduler/jobs.json
SCHEDULER_LOGS_DIR=/var/log/task-scheduler/
```

## Running the Scheduler

The task scheduler runs as a systemd service:

```bash
sudo systemctl start task-scheduler-executor
sudo systemctl status task-scheduler-executor
```

See README.md for usage.
