"""Proxmox skill implementation for Claude.

Provides API and SSH/CLI access to a Proxmox VE cluster.
Configuration is loaded from .env in the skill root directory.

Community helper scripts: https://github.com/community-scripts/ProxmoxVE
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# Load .env from skill root
_SKILL_ROOT = Path(__file__).parent.parent.parent
_ENV_FILE = _SKILL_ROOT / ".env"


def _load_env():
    env = {}
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    # Override with actual environment vars
    for k in list(env.keys()):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


class ProxmoxSkill:
    """Proxmox VE cluster management via API and SSH."""

    def __init__(self):
        cfg = _load_env()
        self.primary = cfg.get("PROXMOX_PRIMARY", "192.168.1.44")
        self.port = int(cfg.get("PROXMOX_API_PORT", "8006"))
        self.ssh_user = cfg.get("PROXMOX_SSH_USER", "root")
        self.ssh_key = cfg.get("PROXMOX_SSH_KEY", "/home/flipkey/.ssh/id_ed25519")
        self.token_id = cfg.get("PROXMOX_API_TOKEN_ID", "")
        self.token_secret = cfg.get("PROXMOX_API_TOKEN_SECRET", "")
        self.helper_repo = cfg.get(
            "PROXMOX_HELPER_SCRIPTS_REPO", "community-scripts/ProxmoxVE"
        )

        # Build node map: name -> IP
        nodes_raw = cfg.get("PROXMOX_NODES", self.primary)
        names_raw = cfg.get("PROXMOX_NODE_NAMES", "")
        ips = [n.strip() for n in nodes_raw.split(",") if n.strip()]
        names = [n.strip() for n in names_raw.split(",") if n.strip()]
        self.node_map: dict[str, str] = {}  # name -> ip
        self.ip_map: dict[str, str] = {}    # ip -> name
        for i, ip in enumerate(ips):
            name = names[i] if i < len(names) else ip
            self.node_map[name] = ip
            self.ip_map[ip] = name

        # Auto-provision API token if secret is missing
        if not self.token_secret:
            result = self._provision_api_token(silent=True)
            if result.get("success"):
                self.token_secret = result["token_secret"]
                self.token_id = result["token_id"]

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _resolve_node(self, node: str | None) -> tuple[str, str]:
        """Return (name, ip) for the given node identifier."""
        if not node:
            ip = self.primary
            name = self.ip_map.get(ip, ip)
            return name, ip
        if node in self.node_map:
            return node, self.node_map[node]
        if node in self.ip_map:
            return self.ip_map[node], node
        # Treat as IP directly
        return self.ip_map.get(node, node), node

    def _api(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict | None = None,
        node_ip: str | None = None,
    ) -> dict:
        """Make a Proxmox API call. Returns parsed JSON response."""
        host = node_ip or self.primary
        url = f"https://{host}:{self.port}/api2/json{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.token_id and self.token_secret:
            headers["Authorization"] = f"PVEAPIToken={self.token_id}={self.token_secret}"

        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        # Disable SSL verification (Proxmox uses self-signed certs by default)
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode(errors="replace")
            return {"error": f"HTTP {e.code}: {body_text}"}
        except Exception as e:
            return {"error": str(e)}

    def _ssh(self, node_ip: str, command: str) -> dict:
        """Run a command on a Proxmox node via SSH."""
        ssh_cmd = [
            "ssh",
            "-i", self.ssh_key,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes",
            f"{self.ssh_user}@{node_ip}",
            command,
        ]
        try:
            result = subprocess.run(
                ssh_cmd, capture_output=True, text=True, timeout=120
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "SSH command timed out after 120s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _all_nodes(self) -> list[tuple[str, str]]:
        """Return list of (name, ip) for all configured nodes."""
        return list(self.node_map.items())

    def _write_env_value(self, key: str, value: str) -> None:
        """Update or append a key=value line in the .env file."""
        if not _ENV_FILE.exists():
            _ENV_FILE.write_text(f"{key}={value}\n")
            return
        lines = _ENV_FILE.read_text().splitlines()
        found = False
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(f"{key}=") or stripped == key:
                new_lines.append(f"{key}={value}")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"{key}={value}")
        _ENV_FILE.write_text("\n".join(new_lines) + "\n")

    def _provision_api_token(self, silent: bool = False) -> dict:
        """Create a Proxmox API token via SSH if one doesn't exist in .env.

        Uses `pveum user token add` on the primary node. The generated secret
        is written back to .env automatically.

        Args:
            silent: If True, suppress SSH errors (used during __init__).
        """
        # Parse token_id to extract user@realm and token name
        raw_id = self.token_id or "root@pam!ai-agent"
        if "!" in raw_id:
            user_realm, token_name = raw_id.split("!", 1)
        else:
            user_realm, token_name = "root@pam", raw_id or "ai-agent"

        # Check if token already exists on the node
        check_cmd = (
            f"pveum user token list {user_realm} --output-format json 2>/dev/null"
        )
        check = self._ssh(self.primary, check_cmd)
        if check.get("success") and check.get("output"):
            try:
                existing = json.loads(check["output"])
                for t in existing:
                    if t.get("tokenid") == token_name:
                        return {
                            "success": False,
                            "already_exists": True,
                            "message": (
                                f"Token '{token_name}' already exists for {user_realm}. "
                                "To get the secret, delete it and re-run setup_api_token, "
                                "or set PROXMOX_API_TOKEN_SECRET in .env manually."
                            ),
                            "token_id": f"{user_realm}!{token_name}",
                        }
            except (json.JSONDecodeError, TypeError):
                pass

        # Create the token (--privsep 0 = no privilege separation = full access)
        create_cmd = (
            f"pveum user token add {user_realm} {token_name} "
            f"--privsep 0 --output-format json"
        )
        result = self._ssh(self.primary, create_cmd)

        if not result.get("success"):
            if silent:
                return {"success": False, "error": result.get("error", result.get("stderr", "SSH failed"))}
            return {
                "success": False,
                "error": result.get("error", result.get("stderr", "SSH command failed")),
                "node": self.primary,
                "command": create_cmd,
            }

        try:
            data = json.loads(result["output"])
        except (json.JSONDecodeError, ValueError):
            return {
                "success": False,
                "error": "Could not parse pveum output",
                "raw_output": result.get("output", ""),
            }

        secret = data.get("value", "")
        full_token_id = data.get("full-tokenid", f"{user_realm}!{token_name}")

        if not secret:
            return {
                "success": False,
                "error": "pveum returned no secret value",
                "raw": data,
            }

        # Persist to .env
        self._write_env_value("PROXMOX_API_TOKEN_ID", full_token_id)
        self._write_env_value("PROXMOX_API_TOKEN_SECRET", secret)

        return {
            "success": True,
            "token_id": full_token_id,
            "token_secret": secret,
            "node": self.primary,
            "message": (
                f"API token '{full_token_id}' created and saved to .env. "
                "Future API calls will use this token automatically."
            ),
        }

    def setup_api_token(self) -> dict:
        """Public action: create a Proxmox API token via SSH if none exists.

        Safe to call at any time — if a token secret is already configured
        it reports that and skips creation. If the token exists on the node
        but isn't in .env, it reports that too (Proxmox only shows the secret
        at creation time).
        """
        if self.token_secret:
            return {
                "success": True,
                "already_configured": True,
                "message": f"API token already configured: {self.token_id}",
                "token_id": self.token_id,
            }
        return self._provision_api_token(silent=False)

    # -------------------------------------------------------------------------
    # Cluster / Node actions
    # -------------------------------------------------------------------------

    def list_nodes(self) -> dict:
        """List all cluster nodes with status."""
        resp = self._api("/nodes")
        if "error" in resp:
            # Fallback: SSH to primary and run pvesh
            result = self._ssh(self.primary, "pvesh get /nodes --output-format json")
            if result["success"]:
                try:
                    data = json.loads(result["output"])
                    return {"success": True, "nodes": data, "method": "ssh"}
                except Exception:
                    pass
            return {"success": False, "error": resp["error"]}

        nodes = resp.get("data", [])
        # Enrich with our IP map
        for node in nodes:
            name = node.get("node", "")
            node["ip"] = self.node_map.get(name, "unknown")
        return {"success": True, "nodes": nodes, "method": "api"}

    def node_status(self, node: str | None = None) -> dict:
        """Get detailed status for a node."""
        name, ip = self._resolve_node(node)
        resp = self._api(f"/nodes/{name}/status", node_ip=ip)
        if "error" in resp:
            result = self._ssh(ip, f"pvesh get /nodes/{name}/status --output-format json")
            if result["success"]:
                try:
                    data = json.loads(result["output"])
                    return {"success": True, "status": data, "node": name, "ip": ip, "method": "ssh"}
                except Exception:
                    pass
            return {"success": False, "error": resp["error"]}
        return {"success": True, "status": resp.get("data", {}), "node": name, "ip": ip, "method": "api"}

    # -------------------------------------------------------------------------
    # VM actions
    # -------------------------------------------------------------------------

    def list_vms(self, node: str | None = None) -> dict:
        """List VMs on a specific node, or all nodes if node is None."""
        results = []
        nodes = [self._resolve_node(node)] if node else self._all_nodes()
        for name, ip in nodes:
            resp = self._api(f"/nodes/{name}/qemu", node_ip=ip)
            if "error" in resp:
                r = self._ssh(ip, "qm list")
                vms = [{"node": name, "raw": r.get("output", ""), "method": "ssh"}]
            else:
                vms = resp.get("data", [])
                for vm in vms:
                    vm["node"] = name
                    vm["node_ip"] = ip
            results.extend(vms)
        return {"success": True, "vms": results}

    def _vm_action(self, action: str, vmid: int, node: str | None) -> dict:
        name, ip = self._resolve_node(node)
        resp = self._api(f"/nodes/{name}/qemu/{vmid}/status/{action}", method="POST", node_ip=ip)
        if "error" in resp:
            r = self._ssh(ip, f"qm {action} {vmid}")
            return {**r, "node": name, "vmid": vmid, "action": action, "method": "ssh"}
        return {"success": True, "result": resp.get("data"), "node": name, "vmid": vmid, "action": action, "method": "api"}

    def start_vm(self, vmid: int, node: str | None = None) -> dict:
        return self._vm_action("start", vmid, node)

    def stop_vm(self, vmid: int, node: str | None = None) -> dict:
        return self._vm_action("stop", vmid, node)

    def restart_vm(self, vmid: int, node: str | None = None) -> dict:
        return self._vm_action("reboot", vmid, node)

    # -------------------------------------------------------------------------
    # LXC Container actions
    # -------------------------------------------------------------------------

    def list_containers(self, node: str | None = None) -> dict:
        """List LXC containers on a specific node, or all nodes."""
        results = []
        nodes = [self._resolve_node(node)] if node else self._all_nodes()
        for name, ip in nodes:
            resp = self._api(f"/nodes/{name}/lxc", node_ip=ip)
            if "error" in resp:
                r = self._ssh(ip, "pct list")
                cts = [{"node": name, "raw": r.get("output", ""), "method": "ssh"}]
            else:
                cts = resp.get("data", [])
                for ct in cts:
                    ct["node"] = name
                    ct["node_ip"] = ip
            results.extend(cts)
        return {"success": True, "containers": results}

    def _ct_action(self, action: str, vmid: int, node: str | None) -> dict:
        name, ip = self._resolve_node(node)
        resp = self._api(f"/nodes/{name}/lxc/{vmid}/status/{action}", method="POST", node_ip=ip)
        if "error" in resp:
            cmd_map = {"start": "start", "stop": "stop", "reboot": "restart"}
            cli_action = cmd_map.get(action, action)
            r = self._ssh(ip, f"pct {cli_action} {vmid}")
            return {**r, "node": name, "vmid": vmid, "action": action, "method": "ssh"}
        return {"success": True, "result": resp.get("data"), "node": name, "vmid": vmid, "action": action, "method": "api"}

    def start_container(self, vmid: int, node: str | None = None) -> dict:
        return self._ct_action("start", vmid, node)

    def stop_container(self, vmid: int, node: str | None = None) -> dict:
        return self._ct_action("stop", vmid, node)

    def restart_container(self, vmid: int, node: str | None = None) -> dict:
        return self._ct_action("reboot", vmid, node)

    # -------------------------------------------------------------------------
    # SSH / CLI
    # -------------------------------------------------------------------------

    def ssh_command(self, command: str, node: str | None = None) -> dict:
        """Run an arbitrary command on a Proxmox node via SSH."""
        name, ip = self._resolve_node(node)
        result = self._ssh(ip, command)
        result["node"] = name
        result["ip"] = ip
        result["command"] = command
        return result

    # -------------------------------------------------------------------------
    # Raw API
    # -------------------------------------------------------------------------

    def api_call(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict | None = None,
        node: str | None = None,
    ) -> dict:
        """Make a raw Proxmox API call."""
        _, ip = self._resolve_node(node)
        resp = self._api(endpoint, method=method, data=data, node_ip=ip)
        if "error" in resp:
            return {"success": False, "error": resp["error"]}
        return {"success": True, "result": resp.get("data", resp)}

    # -------------------------------------------------------------------------
    # Community Helper Scripts (community-scripts/ProxmoxVE)
    # -------------------------------------------------------------------------

    def search_helper_scripts(self, query: str = "") -> dict:
        """List known community helper scripts, optionally filtered by query."""
        # Curated list of popular scripts from community-scripts/ProxmoxVE
        scripts = [
            # LXC Containers
            {"name": "homeassistant", "type": "ct", "description": "Home Assistant OS"},
            {"name": "homeassistant-core", "type": "ct", "description": "Home Assistant Core"},
            {"name": "docker", "type": "ct", "description": "Docker LXC"},
            {"name": "pihole", "type": "ct", "description": "Pi-hole DNS ad-blocker"},
            {"name": "nginx-proxy-manager", "type": "ct", "description": "Nginx Proxy Manager"},
            {"name": "portainer", "type": "ct", "description": "Portainer container management"},
            {"name": "jellyfin", "type": "ct", "description": "Jellyfin media server"},
            {"name": "plex", "type": "ct", "description": "Plex media server"},
            {"name": "nextcloud", "type": "ct", "description": "Nextcloud file sharing"},
            {"name": "vaultwarden", "type": "ct", "description": "Vaultwarden (Bitwarden) password manager"},
            {"name": "grafana", "type": "ct", "description": "Grafana dashboards"},
            {"name": "prometheus", "type": "ct", "description": "Prometheus monitoring"},
            {"name": "influxdb", "type": "ct", "description": "InfluxDB time series database"},
            {"name": "mosquitto", "type": "ct", "description": "Mosquitto MQTT broker"},
            {"name": "zigbee2mqtt", "type": "ct", "description": "Zigbee2MQTT bridge"},
            {"name": "node-red", "type": "ct", "description": "Node-RED flow automation"},
            {"name": "uptime-kuma", "type": "ct", "description": "Uptime Kuma monitoring"},
            {"name": "adguard", "type": "ct", "description": "AdGuard Home DNS"},
            {"name": "technitium-dns", "type": "ct", "description": "Technitium DNS server"},
            {"name": "postgresql", "type": "ct", "description": "PostgreSQL database"},
            {"name": "mariadb", "type": "ct", "description": "MariaDB database"},
            {"name": "redis", "type": "ct", "description": "Redis in-memory store"},
            {"name": "gitea", "type": "ct", "description": "Gitea self-hosted git"},
            {"name": "gitlab", "type": "ct", "description": "GitLab CE"},
            {"name": "wireguard", "type": "ct", "description": "WireGuard VPN"},
            {"name": "tailscale", "type": "ct", "description": "Tailscale VPN"},
            {"name": "frigate", "type": "ct", "description": "Frigate NVR"},
            {"name": "ollama", "type": "ct", "description": "Ollama LLM runner"},
            {"name": "n8n", "type": "ct", "description": "N8N workflow automation"},
            {"name": "traefik", "type": "ct", "description": "Traefik reverse proxy"},
            {"name": "cloudflared", "type": "ct", "description": "Cloudflare tunnel"},
            {"name": "ubuntu", "type": "ct", "description": "Ubuntu LXC container"},
            {"name": "debian", "type": "ct", "description": "Debian LXC container"},
            {"name": "alpine", "type": "ct", "description": "Alpine Linux LXC container"},
            # VMs
            {"name": "haos", "type": "vm", "description": "Home Assistant OS VM"},
            {"name": "ubuntu-vm", "type": "vm", "description": "Ubuntu VM"},
            {"name": "debian-vm", "type": "vm", "description": "Debian VM"},
            {"name": "windows11", "type": "vm", "description": "Windows 11 VM"},
            # Tools
            {"name": "pve-scripts-local", "type": "ct", "description": "PVEScripts-Local menu manager"},
        ]

        if query:
            q = query.lower()
            scripts = [
                s for s in scripts
                if q in s["name"].lower() or q in s["description"].lower()
            ]

        base_url = f"https://raw.githubusercontent.com/{self.helper_repo}/main"
        for s in scripts:
            s["install_command"] = (
                f'bash -c "$(curl -fsSL {base_url}/{s["type"]}/{s["name"]}.sh)"'
            )

        return {
            "success": True,
            "scripts": scripts,
            "count": len(scripts),
            "repo": f"https://github.com/{self.helper_repo}",
            "website": "https://community-scripts.github.io/ProxmoxVE/",
        }

    def run_helper_script(
        self,
        script_name: str,
        script_type: str = "ct",
        node: str | None = None,
    ) -> dict:
        """Run a community helper script on a Proxmox node via SSH.

        The script runs interactively on the node using the standard one-liner
        from community-scripts/ProxmoxVE. Requires the node to have curl and
        internet access.

        Args:
            script_name: Script identifier (e.g. 'homeassistant', 'docker', 'pihole')
            script_type: 'ct' for LXC, 'vm' for VM, 'tools' or 'misc'
            node: Target node (defaults to primary)
        """
        name, ip = self._resolve_node(node)
        base_url = f"https://raw.githubusercontent.com/{self.helper_repo}/main"
        script_url = f"{base_url}/{script_type}/{script_name}.sh"
        command = f'bash -c "$(curl -fsSL {script_url})"'

        return {
            "success": True,
            "node": name,
            "ip": ip,
            "script": script_name,
            "type": script_type,
            "script_url": script_url,
            "command": command,
            "instructions": (
                f"To install '{script_name}' on {name} ({ip}), run this command "
                f"in the Proxmox shell or via SSH:\n\n{command}\n\n"
                f"Or SSH directly:\n"
                f"ssh {self.ssh_user}@{ip}\n"
                f"Then paste the command above."
            ),
            "ssh_ready_command": (
                f"ssh -i {self.ssh_key} {self.ssh_user}@{ip} "
                f"'bash -c \"$(curl -fsSL {script_url})\"'"
            ),
            "note": (
                "Community scripts run interactively with prompts. "
                "For unattended use, SSH to the node and run the command manually. "
                "Script source: https://github.com/" + self.helper_repo
            ),
        }

    def ssh_run_helper_script(
        self,
        script_name: str,
        script_type: str = "ct",
        node: str | None = None,
        extra_env: dict | None = None,
    ) -> dict:
        """Attempt to run a helper script non-interactively via SSH.

        Note: Most community scripts require interactive input. This works best
        for simple scripts or when APP_PORT/APP_PASS env vars are pre-set.
        """
        name, ip = self._resolve_node(node)
        base_url = f"https://raw.githubusercontent.com/{self.helper_repo}/main"
        script_url = f"{base_url}/{script_type}/{script_name}.sh"

        env_prefix = ""
        if extra_env:
            env_prefix = " ".join(f'{k}="{v}"' for k, v in extra_env.items()) + " "

        command = f'{env_prefix}bash -c "$(curl -fsSL {script_url})"'
        result = self._ssh(ip, command)
        result["node"] = name
        result["ip"] = ip
        result["script"] = script_name
        result["script_url"] = script_url
        return result

    # -------------------------------------------------------------------------
    # Create LXC / VM (via API)
    # -------------------------------------------------------------------------

    def create_lxc(
        self,
        vmid: int,
        hostname: str,
        ostemplate: str,
        node: str | None = None,
        cores: int = 1,
        memory: int = 512,
        swap: int = 512,
        disk: str = "local-lvm:8",
        ip: str = "dhcp",
        gateway: str = "192.168.1.1",
        bridge: str = "vmbr1",
        password: str | None = None,
        start: bool = True,
        **kwargs,
    ) -> dict:
        """Create an LXC container via the Proxmox API."""
        name, node_ip = self._resolve_node(node)
        net0 = f"name=eth0,bridge={bridge}"
        if ip != "dhcp":
            net0 += f",ip={ip}/21,gw={gateway},type=veth"
        else:
            net0 += ",ip=dhcp"

        payload = {
            "vmid": vmid,
            "hostname": hostname,
            "ostemplate": ostemplate,
            "cores": cores,
            "memory": memory,
            "swap": swap,
            "rootfs": disk,
            "net0": net0,
            "unprivileged": 1,
            "start": 1 if start else 0,
        }
        if password:
            payload["password"] = password
        payload.update(kwargs)

        resp = self._api(f"/nodes/{name}/lxc", method="POST", data=payload, node_ip=node_ip)
        if "error" in resp:
            return {"success": False, "error": resp["error"], "node": name, "vmid": vmid}
        return {
            "success": True,
            "result": resp.get("data"),
            "node": name,
            "vmid": vmid,
            "hostname": hostname,
            "message": f"LXC {vmid} ({hostname}) created on {name}",
        }

    def create_vm(
        self,
        vmid: int,
        name: str,
        node: str | None = None,
        cores: int = 2,
        memory: int = 2048,
        disk: str = "local-lvm:32",
        iso: str | None = None,
        start: bool = False,
        **kwargs,
    ) -> dict:
        """Create a VM via the Proxmox API."""
        node_name, node_ip = self._resolve_node(node)
        payload = {
            "vmid": vmid,
            "name": name,
            "cores": cores,
            "memory": memory,
            "scsi0": disk,
            "net0": "virtio,bridge=vmbr0",
            "ostype": "l26",
        }
        if iso:
            payload["cdrom"] = iso
        payload.update(kwargs)

        resp = self._api(f"/nodes/{node_name}/qemu", method="POST", data=payload, node_ip=node_ip)
        if "error" in resp:
            return {"success": False, "error": resp["error"], "node": node_name, "vmid": vmid}
        return {
            "success": True,
            "result": resp.get("data"),
            "node": node_name,
            "vmid": vmid,
            "name": name,
            "message": f"VM {vmid} ({name}) created on {node_name}",
        }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Proxmox skill CLI")
    parser.add_argument("action", help="Action to perform")
    parser.add_argument("--node", help="Target node name or IP")
    parser.add_argument("--vmid", type=int, help="VM or container ID")
    parser.add_argument("--command", help="SSH command to run")
    parser.add_argument("--endpoint", help="API endpoint")
    parser.add_argument("--method", default="GET", help="HTTP method")
    parser.add_argument("--script", help="Helper script name")
    parser.add_argument("--script-type", default="ct", help="Script type: ct or vm")
    parser.add_argument("--query", default="", help="Search query for scripts")
    parser.add_argument("--data", help="JSON data for API call")
    args = parser.parse_args()

    skill = ProxmoxSkill()

    if args.action == "list_nodes":
        result = skill.list_nodes()
    elif args.action == "node_status":
        result = skill.node_status(args.node)
    elif args.action == "list_vms":
        result = skill.list_vms(args.node)
    elif args.action == "list_containers":
        result = skill.list_containers(args.node)
    elif args.action == "start_vm":
        result = skill.start_vm(args.vmid, args.node)
    elif args.action == "stop_vm":
        result = skill.stop_vm(args.vmid, args.node)
    elif args.action == "restart_vm":
        result = skill.restart_vm(args.vmid, args.node)
    elif args.action == "start_container":
        result = skill.start_container(args.vmid, args.node)
    elif args.action == "stop_container":
        result = skill.stop_container(args.vmid, args.node)
    elif args.action == "restart_container":
        result = skill.restart_container(args.vmid, args.node)
    elif args.action == "ssh_command":
        result = skill.ssh_command(args.command, args.node)
    elif args.action == "api_call":
        data = json.loads(args.data) if args.data else None
        result = skill.api_call(args.endpoint, args.method, data, args.node)
    elif args.action == "search_helper_scripts":
        result = skill.search_helper_scripts(args.query)
    elif args.action == "run_helper_script":
        result = skill.run_helper_script(args.script, args.script_type, args.node)
    elif args.action == "setup_api_token":
        result = skill.setup_api_token()
    else:
        result = {"error": f"Unknown action: {args.action}"}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
