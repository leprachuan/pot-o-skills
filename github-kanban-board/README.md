# GitHub Kanban Board

A beautiful, interactive kanban board for managing GitHub issues with smart label parsing and glassmorphism design.

![GitHub Kanban Board](https://img.shields.io/badge/python-3.12+-blue)
![MIT License](https://img.shields.io/badge/license-MIT-green)

## 🎯 What This Does

- 📊 Displays GitHub issues in a 3-column kanban board (To Do → In Progress → Done)
- 🏷️ Parses labels for agent assignments and due dates
- 🎨 Beautiful dark theme with emerald accents
- 🔄 Drag & drop to update issue status
- 🎛️ Filter issues by agent assignment
- 🌍 Accessible over local network or Tailscale

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- GitHub account with a repository
- `gh` CLI (for authentication)

### Installation

```bash
# Clone the skill
git clone https://github.com/your-org/pot-o-skills.git
cd pot-o-skills/.github/skills/github-kanban-board

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure for your repository
cp config.json.example config.json
vim config.json  # Edit with your repo name
```

### Run

```bash
GITHUB_TOKEN=$(gh auth token) python3 scripts/kanban_server.py
```

Open: **http://localhost:8888**

## ⚙️ Configuration

Edit `config.json`:

```json
{
  "repository": "your-username/your-repo",
  "port": 8888,
  "host": "0.0.0.0",
  "default_agents": ["frontend", "backend", "devops"]
}
```

## 🏷️ GitHub Issue Labels

To use all features, add these labels to your issues:

```
agent:frontend      # Assigned to frontend team
due:2026-06-15      # Due date (YYYY-MM-DD)
priority:high       # Priority level
status:in-progress  # Current status (auto-synced)
```

## 🔐 Security

- ✅ **No hardcoded credentials**
- ✅ **No sensitive data in repo**
- ✅ **GitHub token via environment variable only**
- ✅ **Safe for public use**

## 📖 Full Documentation

See [SKILL.md](SKILL.md) for comprehensive documentation including:
- Detailed configuration options
- Deployment guides (Docker, systemd)
- API reference
- Troubleshooting

## 💡 Example Use Cases

- **Sprint Planning**: Track sprint tasks with due dates
- **Team Coordination**: Assign issues to team members via labels
- **Public Projects**: Beautiful issue board for community projects
- **Personal Projects**: Simple todo board for your repos

## 🛠️ Development

```bash
# Start in dev mode
python3 scripts/kanban_server.py

# Changes to Python require restart
# Changes to HTML/CSS are live-reloaded

# Run tests
pytest tests/
```

## 📋 Architecture

```
Frontend (index.html)
    ↓ (REST API)
Backend (kanban_server.py)
    ↓ (PyGithub)
GitHub API
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Test locally
4. Submit a PR

## 📄 License

MIT License - Use freely, attribute if possible.

## 🙋 Support

- **Documentation**: See [SKILL.md](SKILL.md)
- **Issues**: GitHub issues in pot-o-skills
- **Setup Help**: See Troubleshooting in SKILL.md

---

**Ready to track your GitHub issues beautifully?** Get started now:

```bash
GITHUB_TOKEN=$(gh auth token) python3 scripts/kanban_server.py
```

Open http://localhost:8888 ✨
