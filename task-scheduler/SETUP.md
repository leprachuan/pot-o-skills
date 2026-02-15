# Setup

## Dependencies

This skill requires **Wee-Orchestrator** (n8n-copilot-shim) to be installed:

- **Repository**: https://github.com/leprachuan/Wee-Orchestrator.git
- **Install location**: `/opt/n8n-copilot-shim/`
- **Purpose**: Provides agent_manager.py for executing LLM tasks with multiple runtimes (Claude, Copilot, Gemini)

Clone it with:
```bash
git clone https://github.com/leprachuan/Wee-Orchestrator.git /opt/n8n-copilot-shim
```

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
