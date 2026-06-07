---
name: github-kanban-board
description: Interactive GitHub issues kanban board with agent assignments, due dates, and glassmorphism theming. Fully configurable for any GitHub repository.
keywords: [github, kanban, board, issues, todo, management, agent, scheduling, ui]
---

# GitHub Kanban Board

An interactive, configurable kanban board for managing GitHub issues. Display issues in a beautiful 3-column layout (To Do → In Progress → Done) with intelligent filtering by agent assignments and due dates.

## Features

✨ **3-Column Kanban Layout**
- Organize issues by status (Todo/In Progress/Done)
- Drag & drop cards between columns to sync with GitHub
- Real-time issue updates

🏷️ **Smart Label Parsing**
- **Agent Labels**: `agent:devops`, `agent:research` → Filter by team member
- **Due Date Labels**: `due:2026-06-15` → Color-coded urgency (red=overdue, gold=soon, green=future)
- **Priority Labels**: `priority:high`, `priority:critical` → Highlighted
- **Status Labels**: `status:todo`, `status:in-progress`, `status:done` → Auto-synced

🎨 **Professional Design**
- Glassmorphism dark theme with emerald and gold accents
- Responsive layout works on desktop and tablet
- Smooth animations and transitions
- High-contrast, accessible text

🔧 **Fully Configurable**
- Any GitHub repository (public or private)
- Custom port and host binding
- Configurable agent list for filtering
- Environment variable overrides for CI/CD

## Quick Start

### 1. Clone or Copy the Skill

```bash
git clone https://github.com/your-org/pot-o-skills.git
cd pot-o-skills/.github/skills/github-kanban-board
```

### 2. Edit Configuration

Edit `config.json` with your GitHub repository:

```json
{
  "repository": "your-username/your-repo",
  "port": 8888,
  "host": "0.0.0.0",
  "default_agents": ["devops", "research", "frontend", "backend"]
}
```

### 3. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Start the Server

```bash
GITHUB_TOKEN=$(gh auth token) python3 scripts/kanban_server.py
```

Open your browser: **http://localhost:8888**

## Configuration

### Via config.json (Recommended)

Edit `config.json` to customize:

```json
{
  "repository": "owner/repo",           // GitHub repo (required)
  "port": 8888,                         // Server port
  "host": "0.0.0.0",                    // Bind to all interfaces (or 127.0.0.1 for localhost)
  "default_agents": [],                 // List of agents for filter dropdown
  "enable_status_sync": true            // Sync status changes back to GitHub
}
```

### Via Environment Variables (CI/CD)

Environment variables override `config.json`:

```bash
# Switch repository dynamically
KANBAN_REPO=org/different-repo python3 scripts/kanban_server.py

# Change port
KANBAN_PORT=9999 python3 scripts/kanban_server.py

# Bind to specific host
KANBAN_HOST=127.0.0.1 python3 scripts/kanban_server.py

# GitHub authentication (required)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx python3 scripts/kanban_server.py
```

### Authentication

The board requires a GitHub personal access token:

```bash
# Using gh CLI (recommended)
GITHUB_TOKEN=$(gh auth token) python3 scripts/kanban_server.py

# Or set manually
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
python3 scripts/kanban_server.py
```

**Permissions Required:**
- `repo` (for private repos) OR
- `public_repo` (for public repos only)

## Label Format for Your Issues

Add these labels to your GitHub issues to use all features:

### Agent Assignment
```
agent:devops
agent:research
agent:frontend
agent:backend
```

### Due Dates (YYYY-MM-DD format)
```
due:2026-06-15
due:2026-12-31
```

### Priority
```
priority:critical
priority:high
priority:medium
priority:low
```

### Status (auto-managed by drag & drop)
```
status:todo
status:in-progress
status:done
```

### Example Issue Labels
```
agent:devops due:2026-06-20 priority:high
```

The board will automatically:
- Assign issues to the "In Progress" column if they have the `status:in-progress` label
- Color-code due dates: 🔴 red (overdue), 🟡 gold (within 3 days), 🟢 green (future)
- Filter agents from the dropdown for quick navigation

## Network Access

### Local Development
```
http://localhost:8888
```

### Network Access (with `host: "0.0.0.0"`)
```
http://<your-machine-ip>:8888
```

### Tailscale Network
If your machine is on Tailscale:
```
http://<tailscale-ip>:8888
```

## Deployment

### Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN python3 -m venv venv
RUN . venv/bin/activate && pip install -r requirements.txt

EXPOSE 8888

CMD ["bash", "-c", "source venv/bin/activate && python3 scripts/kanban_server.py"]
```

Build and run:

```bash
docker build -t github-kanban-board .
docker run -e GITHUB_TOKEN=$GITHUB_TOKEN -p 8888:8888 github-kanban-board
```

### Systemd Service (Linux)

Create `/etc/systemd/system/github-kanban.service`:

```ini
[Unit]
Description=GitHub Kanban Board
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/github-kanban-board
Environment="GITHUB_TOKEN=your-token-here"
ExecStart=/opt/github-kanban-board/venv/bin/python3 /opt/github-kanban-board/scripts/kanban_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable github-kanban
sudo systemctl start github-kanban
```

## Troubleshooting

### Issues not loading (404 error)

1. Verify repository name is correct: `owner/repo`
2. Verify access: `gh repo view owner/repo`
3. Check GitHub token has proper permissions

### Server not accessible over network

- Ensure `host: "0.0.0.0"` in config.json
- Check firewall allows port 8888
- Verify with `netstat -tlnp | grep 8888`

### Token errors

```bash
# Test token validity
gh auth token

# Re-authenticate
gh auth logout
gh auth login
```

### Port already in use

```bash
# Find process on port 8888
lsof -i :8888

# Change port in config.json or via env var
KANBAN_PORT=9999 python3 scripts/kanban_server.py
```

## Architecture

```
config.json (configuration)
    ↓
Environment Variables (override)
    ↓
kanban_server.py (Flask backend)
    ├── Fetches GitHub issues via PyGithub
    ├── Parses labels for agent/due-date
    └── Serves REST API at /api/issues
        
index.html (Frontend)
    ├── Glassmorphism design
    ├── 3-column kanban layout
    ├── Drag & drop support
    └── Real-time filtering
```

## API Endpoints

### GET /api/issues

Fetch all open issues grouped by status.

```json
{
  "success": true,
  "columns": {
    "todo": [...],
    "in-progress": [...],
    "done": [...]
  },
  "agents": ["devops", "research"],
  "total": 42
}
```

### POST /api/issues/{issue_num}/status

Update issue status (syncs to GitHub via label).

```json
{
  "status": "in-progress"
}
```

### GET /api/config

Get server configuration.

```json
{
  "repo": "owner/repo",
  "port": 8888,
  "host": "0.0.0.0",
  "default_agents": []
}
```

## Development

### Local Testing

```bash
source venv/bin/activate
GITHUB_TOKEN=$(gh auth token) python3 scripts/kanban_server.py
```

Visit: http://localhost:8888

### Code Structure

```
github-kanban-board/
├── SKILL.md                    # This documentation
├── config.json                 # Configuration template
├── requirements.txt            # Python dependencies
├── scripts/
│   └── kanban_server.py       # Flask backend + CLI
└── assets/
    └── index.html             # Frontend (HTML/CSS/JS)
```

### Making Changes

1. Edit Python: `scripts/kanban_server.py`
2. Edit Frontend: `assets/index.html`
3. Reload browser (CSS/JS) or restart server (Python)

## No Sensitive Data

This skill contains **no hardcoded sensitive information**:
- ✅ GitHub token is environment variable only
- ✅ No API keys in code
- ✅ No credentials in config.json
- ✅ Safe for public repositories

## License

Open source - use and modify freely. Attribution appreciated.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify your config.json is correct
3. Test GitHub access: `gh repo view owner/repo`
4. Review logs: `tail -50 /tmp/kanban.log`

---

**Ready to use!** Fork/clone pot-o-skills and customize for your needs.
