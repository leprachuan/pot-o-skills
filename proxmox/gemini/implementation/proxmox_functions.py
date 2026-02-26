"""Proxmox skill function definitions for Gemini runtime.

Wraps the shared ProxmoxSkill class as Gemini-compatible function declarations.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "claude" / "implementation"))
from proxmox_skill import ProxmoxSkill

_skill = ProxmoxSkill()


# ---------------------------------------------------------------------------
# Function declarations (Gemini tool format)
# ---------------------------------------------------------------------------

FUNCTION_DECLARATIONS = [
    {
        "name": "proxmox_list_nodes",
        "description": "List all Proxmox cluster nodes with their status",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "proxmox_node_status",
        "description": "Get detailed CPU, memory, and storage status for a Proxmox node",
        "parameters": {
            "type": "object",
            "properties": {
                "node": {"type": "string", "description": "Node name or IP (e.g. proxmox4 or 192.168.1.44)"}
            },
        },
    },
    {
        "name": "proxmox_list_vms",
        "description": "List all VMs on a node or across the whole cluster",
        "parameters": {
            "type": "object",
            "properties": {
                "node": {"type": "string", "description": "Node name or IP. Omit for all nodes."}
            },
        },
    },
    {
        "name": "proxmox_list_containers",
        "description": "List all LXC containers on a node or across the whole cluster",
        "parameters": {
            "type": "object",
            "properties": {
                "node": {"type": "string", "description": "Node name or IP. Omit for all nodes."}
            },
        },
    },
    {
        "name": "proxmox_start_vm",
        "description": "Start a VM by ID",
        "parameters": {
            "type": "object",
            "properties": {
                "vmid": {"type": "integer", "description": "VM ID"},
                "node": {"type": "string", "description": "Node name or IP"},
            },
            "required": ["vmid"],
        },
    },
    {
        "name": "proxmox_stop_vm",
        "description": "Stop a VM by ID",
        "parameters": {
            "type": "object",
            "properties": {
                "vmid": {"type": "integer", "description": "VM ID"},
                "node": {"type": "string", "description": "Node name or IP"},
            },
            "required": ["vmid"],
        },
    },
    {
        "name": "proxmox_start_container",
        "description": "Start an LXC container by ID",
        "parameters": {
            "type": "object",
            "properties": {
                "vmid": {"type": "integer", "description": "Container ID"},
                "node": {"type": "string", "description": "Node name or IP"},
            },
            "required": ["vmid"],
        },
    },
    {
        "name": "proxmox_stop_container",
        "description": "Stop an LXC container by ID",
        "parameters": {
            "type": "object",
            "properties": {
                "vmid": {"type": "integer", "description": "Container ID"},
                "node": {"type": "string", "description": "Node name or IP"},
            },
            "required": ["vmid"],
        },
    },
    {
        "name": "proxmox_ssh_command",
        "description": "Run an arbitrary CLI command on a Proxmox node via SSH",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run (e.g. 'pct list', 'qm status 100')"},
                "node": {"type": "string", "description": "Node name or IP"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "proxmox_api_call",
        "description": "Make a raw Proxmox REST API call",
        "parameters": {
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "API path (e.g. '/nodes/proxmox4/status')"},
                "method": {"type": "string", "description": "HTTP method: GET, POST, PUT, DELETE", "enum": ["GET", "POST", "PUT", "DELETE"]},
                "data": {"type": "string", "description": "JSON-encoded body for POST/PUT"},
                "node": {"type": "string", "description": "Node IP to call API against"},
            },
            "required": ["endpoint"],
        },
    },
    {
        "name": "proxmox_search_helper_scripts",
        "description": "Search available community helper scripts from community-scripts/ProxmoxVE",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term (e.g. 'docker', 'home assistant')"}
            },
        },
    },
    {
        "name": "proxmox_run_helper_script",
        "description": "Get install instructions and command for a community helper script on a Proxmox node",
        "parameters": {
            "type": "object",
            "properties": {
                "script_name": {"type": "string", "description": "Script name (e.g. 'homeassistant', 'docker', 'pihole')"},
                "script_type": {"type": "string", "description": "Script type: ct (LXC) or vm", "enum": ["ct", "vm", "tools", "misc"]},
                "node": {"type": "string", "description": "Target node name or IP"},
            },
            "required": ["script_name"],
        },
    },
    {
        "name": "proxmox_setup_api_token",
        "description": (
            "Create a Proxmox API token via SSH if one doesn't exist in .env. "
            "Safe to call at any time — skips creation if a token is already configured. "
            "Automatically saves the generated token secret to .env."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
]


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def dispatch(function_name: str, args: dict) -> dict:
    """Dispatch a Gemini function call to the ProxmoxSkill."""
    fn_map = {
        "proxmox_list_nodes": lambda a: _skill.list_nodes(),
        "proxmox_node_status": lambda a: _skill.node_status(a.get("node")),
        "proxmox_list_vms": lambda a: _skill.list_vms(a.get("node")),
        "proxmox_list_containers": lambda a: _skill.list_containers(a.get("node")),
        "proxmox_start_vm": lambda a: _skill.start_vm(a["vmid"], a.get("node")),
        "proxmox_stop_vm": lambda a: _skill.stop_vm(a["vmid"], a.get("node")),
        "proxmox_start_container": lambda a: _skill.start_container(a["vmid"], a.get("node")),
        "proxmox_stop_container": lambda a: _skill.stop_container(a["vmid"], a.get("node")),
        "proxmox_ssh_command": lambda a: _skill.ssh_command(a["command"], a.get("node")),
        "proxmox_api_call": lambda a: _skill.api_call(
            a["endpoint"],
            a.get("method", "GET"),
            json.loads(a["data"]) if a.get("data") else None,
            a.get("node"),
        ),
        "proxmox_search_helper_scripts": lambda a: _skill.search_helper_scripts(a.get("query", "")),
        "proxmox_run_helper_script": lambda a: _skill.run_helper_script(
            a["script_name"], a.get("script_type", "ct"), a.get("node")
        ),
        "proxmox_setup_api_token": lambda a: _skill.setup_api_token(),
    }
    fn = fn_map.get(function_name)
    if not fn:
        return {"error": f"Unknown function: {function_name}"}
    return fn(args)
