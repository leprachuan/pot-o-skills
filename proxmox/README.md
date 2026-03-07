# Proxmox Skill

Manage Proxmox VE clusters via REST API and SSH/CLI. Supports VM and LXC container management, node status, raw API calls, and one-click deployment of community helper scripts.

**Cluster**: lepproxmox1
**Community Scripts**: [community-scripts/ProxmoxVE](https://github.com/community-scripts/ProxmoxVE)

## Setup

1. Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

2. Edit `.env`:

```env
PROXMOX_NODES=192.168.1.44,192.168.1.46,192.168.1.47,192.168.1.41,192.168.1.42
PROXMOX_NODE_NAMES=proxmox4,proxmox5,proxmox7,proxmox10,proxmox11
PROXMOX_PRIMARY=192.168.1.44
PROXMOX_SSH_USER=root
PROXMOX_SSH_KEY=/home/flipkey/.ssh/id_ed25519
PROXMOX_API_TOKEN_ID=root@pam!ai-agent
PROXMOX_API_TOKEN_SECRET=your-secret-here
```

3. Create an API token in the Proxmox UI:
   - Datacenter → Permissions → API Tokens → Add
   - User: `root@pam`, Token ID: any name you like (e.g. `ai-agent`, `homelab-bot`)
   - Uncheck "Privilege Separation" for full access
   - Copy the secret into `.env`

## Cluster Nodes

| Node | IP | CPU | RAM |
|------|-----|-----|-----|
| proxmox4 | 192.168.1.44 | Intel i5-12600H | 62Gi |
| proxmox5 | 192.168.1.46 | Intel i5-7400 | 31Gi |
| proxmox7 | 192.168.1.47 | AMD Ryzen 5 5500U | 62Gi |
| proxmox10 | 192.168.1.41 | Intel i5-12600H | 62Gi |
| proxmox11 | 192.168.1.42 | Intel i9-13900H | 62Gi |

## Supported Actions

| Action | Description |
|--------|-------------|
| `list_nodes` | List all cluster nodes with status |
| `node_status` | Detailed CPU/RAM/storage for a node |
| `list_vms` | List VMs (one node or all) |
| `list_containers` | List LXC containers (one node or all) |
| `start_vm` | Start a VM by ID |
| `stop_vm` | Stop a VM by ID |
| `restart_vm` | Reboot a VM by ID |
| `start_container` | Start an LXC container |
| `stop_container` | Stop an LXC container |
| `restart_container` | Reboot an LXC container |
| `ssh_command` | Run any CLI command on a node via SSH |
| `api_call` | Make a raw Proxmox REST API call |
| `search_helper_scripts` | Find community helper scripts |
| `run_helper_script` | Get install command for a helper script |
| `create_lxc` | Create an LXC container via API |
| `create_vm` | Create a VM via API |

## API vs SSH Fallback

All actions try the Proxmox REST API first (requires API token in `.env`). If the API call fails (e.g. no token configured), most actions fall back automatically to SSH using the configured key.

## Community Helper Scripts

The skill integrates with [community-scripts/ProxmoxVE](https://github.com/community-scripts/ProxmoxVE), the community continuation of the popular tteck Proxmox helper scripts.

**Search for scripts:**
```
"search proxmox helper scripts for docker"
"find proxmox helper script homeassistant"
```

**Install a script:**
```
"run the docker helper script on proxmox4"
"install pihole on proxmox11 using the helper script"
```

The `run_helper_script` action returns the exact SSH command and instructions. Because most scripts run interactively (they prompt for settings), the skill provides the ready-to-run SSH command rather than running blindly.

For truly non-interactive installs, use `ssh_run_helper_script` with `extra_env` vars.

### Popular Scripts

| Script | Type | Description |
|--------|------|-------------|
| `homeassistant` | ct | Home Assistant OS |
| `docker` | ct | Docker LXC |
| `pihole` | ct | Pi-hole DNS |
| `nginx-proxy-manager` | ct | NPM reverse proxy |
| `portainer` | ct | Container management UI |
| `jellyfin` | ct | Media server |
| `vaultwarden` | ct | Password manager |
| `grafana` | ct | Dashboards |
| `prometheus` | ct | Monitoring |
| `ollama` | ct | LLM runner |
| `n8n` | ct | Workflow automation |
| `ubuntu` | ct | Ubuntu LXC |
| `haos` | vm | Home Assistant OS VM |

Full list: https://community-scripts.github.io/ProxmoxVE/

## Example Usage (Claude)

```python
from proxmox_skill import ProxmoxSkill

skill = ProxmoxSkill()

# List all nodes
skill.list_nodes()

# List all containers across cluster
skill.list_containers()

# Start container 200 on proxmox4
skill.start_container(200, node="proxmox4")

# Run SSH command on proxmox11
skill.ssh_command("pct list", node="proxmox11")

# Search for helper scripts
skill.search_helper_scripts("home assistant")

# Get install instructions for docker on proxmox4
skill.run_helper_script("docker", "ct", node="proxmox4")

# Raw API call
skill.api_call("/cluster/status")
```

## CLI Usage

```bash
python3 claude/implementation/proxmox_skill.py list_nodes
python3 claude/implementation/proxmox_skill.py list_containers --node proxmox4
python3 claude/implementation/proxmox_skill.py start_container --vmid 200 --node proxmox4
python3 claude/implementation/proxmox_skill.py ssh_command --command "pct list" --node proxmox11
python3 claude/implementation/proxmox_skill.py search_helper_scripts --query docker
python3 claude/implementation/proxmox_skill.py run_helper_script --script docker --script-type ct --node proxmox4
python3 claude/implementation/proxmox_skill.py api_call --endpoint /cluster/status
```
