# 🍀 pot-o-skills

A collection of production-ready API skills for **Wee-Orchestrator**, enabling multi-agent coordination across cloud networking, security, and infrastructure platforms. Works seamlessly with Claude, Gemini, and Copilot CLI runtimes.

## Overview

pot-o-skills provides comprehensive REST API access to enterprise platforms, enabling automation, monitoring, and management workflows across your infrastructure. Each skill is implemented across all three supported runtimes for maximum flexibility.

## Available Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| **[Cisco Meraki](./cisco-meraki/)** | Cloud networking, WiFi, switches, firewalls, device management | ✅ Production Ready |
| **[Cisco Security Cloud Control](./cisco-security-cloud-control/)** | Organization management, firewall policies, threat detection | ✅ Production Ready |

## Installation

### 1. Clone into Wee-Orchestrator

Clone this repository alongside your Wee-Orchestrator installation:

```bash
# Navigate to the orchestrator parent directory
cd /opt

# Clone pot-o-skills
git clone https://github.com/leprachuan/pot-o-skills.git

# Verify structure
ls -la
# n8n-copilot-shim/
# n8n-copilot-shim-dev/
# pot-o-skills/          ← newly cloned
```

### 2. Symlink Skills Into Place

Link individual skills into your Wee-Orchestrator's skill directory:

```bash
# For development
cd /opt/n8n-copilot-shim-dev/.github/skills
ln -s /opt/pot-o-skills/cisco-meraki
ln -s /opt/pot-o-skills/cisco-security-cloud-control

# For production (only when deploying)
cd /opt/n8n-copilot-shim/.github/skills
ln -s /opt/pot-o-skills/cisco-meraki
ln -s /opt/pot-o-skills/cisco-security-cloud-control
```

### 3. Configure Credentials

Each skill requires API credentials stored in `.env` files (git-ignored for security):

```bash
# Cisco Meraki
cd /opt/pot-o-skills/cisco-meraki
cp .env.example .env
# Edit .env and add your Meraki API key

# Cisco Security Cloud Control
cd /opt/pot-o-skills/cisco-security-cloud-control
cp .env.example .env
# Edit .env and add your SCC and cdFMC API tokens
```

## Skills

### 🌐 Cisco Meraki
**Network management, monitoring, and configuration across cloud-delivered networking infrastructure.**

Access the full documentation and examples in [`cisco-meraki/README.md`](./cisco-meraki/README.md)

**Key Features:**
- Organizations and networks
- Device management & status
- WiFi SSIDs and wireless configuration
- Switch ports and wired networking
- Firewall rules and security
- Connected clients and usage analytics

### 🔒 Cisco Security Cloud Control (SCC)
**Organization management, firewall policies, and threat defense at cloud scale.**

Access the full documentation and examples in [`cisco-security-cloud-control/README.md`](./cisco-security-cloud-control/README.md)

**Key Features:**
- Organization management
- User and role administration
- Subscription and license tracking
- Cloud Delivered Firewall Manager (cdFMC)
- Access control policies
- Threat defense rules

## Runtime Support

All skills work across three runtimes:

| Runtime | Language | Use Case |
|---------|----------|----------|
| **Claude** | Python | Full AI code generation & analysis |
| **Copilot CLI** | Python | Terminal workflows & automation |
| **Gemini** | JavaScript | Web-based integrations |

## Security

- ✅ All credentials stored in `.env` files (git-ignored)
- ✅ No hardcoded secrets in code
- ✅ API keys protected and never committed
- ✅ `.env.example` templates provided
- ✅ Main branch protected - all changes via pull requests

## Contributing

This repository is open to community contributions! To contribute:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/my-skill`)
3. **Implement your skill** across all three runtimes
4. **Add documentation** (SKILL.md, README.md)
5. **Submit a Pull Request** for review

All pull requests require:
- ✅ Approval from maintainer
- ✅ No exposed credentials
- ✅ Implementations for Python and JavaScript
- ✅ Comprehensive documentation

## Directory Structure

```
pot-o-skills/
├── README.md                              # This file
├── .gitignore                             # Protects .env files
├── .env.example                           # Template credentials
│
├── cisco-meraki/
│   ├── README.md                          # Skill documentation
│   ├── SKILL.md                           # Skill definition
│   ├── .env.example                       # Meraki API key template
│   ├── skill_metadata.json                # Capability metadata
│   ├── claude/                            # Claude Python implementation
│   ├── copilot/                           # Copilot CLI Python implementation
│   └── gemini/                            # Gemini JavaScript implementation
│
└── cisco-security-cloud-control/
    ├── README.md                          # Skill documentation
    ├── SKILL.md                           # Skill definition
    ├── .env.example                       # SCC & cdFMC token templates
    ├── skill_metadata.json                # Capability metadata
    ├── claude/                            # Claude Python implementation
    ├── copilot/                           # Copilot CLI Python implementation
    └── gemini/                            # Gemini JavaScript implementation
```

## License

MIT

---

**Questions?** Check individual skill READMEs for specific documentation, examples, and troubleshooting. For general issues, open a GitHub issue.
