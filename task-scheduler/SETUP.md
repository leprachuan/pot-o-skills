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

## Running the Scheduler

The task scheduler runs as a systemd service:

```bash
sudo systemctl start task-scheduler-executor
sudo systemctl status task-scheduler-executor
```

See README.md for usage.
