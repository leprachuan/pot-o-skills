---
name: cisco-meraki
description: Manage Cisco Meraki cloud networking - organizations, networks, devices, wireless, switches, firewall, and clients
---

# Cisco Meraki Skill

Complete REST API access to Cisco Meraki cloud networking platform for managing networks, devices, SSIDs, switches, and security policies.

**Status:** ✅ **Fully Functional** - All core APIs operational

## Features

### Organization Management ✅
- List organizations
- Get organization details
- Access control per organization

### Network Management ✅
- List networks in organization
- Get network details
- Network configuration
- Multi-site management

### Device Management ✅
- List devices by network
- Get device details (model, firmware, status)
- Device online/offline status monitoring
- Device inventory tracking

### Wireless (SSID) Management ✅
- List SSIDs in network
- Get SSID configuration
- Security settings (WPA2/WPA3)
- Access point management

### Switch Management ✅
- List switch ports
- Get port status and configuration
- VLAN management
- PoE status

### Firewall Management ✅
- List firewall rules
- Get firewall settings
- Access control lists
- Intrusion detection

### Client Management ✅
- List connected clients
- Get client details
- Client usage and history
- Device type detection

## Setup

### 1. API Key (.env)

```bash
# Get API key from Meraki Dashboard
# Meraki Dashboard → Organization → Administrators → My profile → API access
MERAKI_API_KEY=your_meraki_api_key_here
```

### 2. Dependencies

**Python (Claude/Copilot):**
```bash
pip install requests python-dotenv
```

**Node.js (Gemini):**
```bash
npm install axios dotenv
```

### 3. Basic Usage

**List Organizations (Python):**
```python
from copilot.cisco_meraki import MerakiClient

client = MerakiClient()
orgs = client.list_organizations()

for org in orgs:
    print(f"{org['name']} (ID: {org['id']})")
```

**List Networks (Python):**
```python
from copilot.cisco_meraki import MerakiClient

client = MerakiClient()
org_id = "your_org_id"

networks = client.list_networks(org_id)
for net in networks:
    print(f"{net['name']} - Type: {net['type']}")
```

**List Devices (Python):**
```python
from copilot.cisco_meraki import MerakiClient

client = MerakiClient()
network_id = "your_network_id"

devices = client.list_devices(network_id)
for device in devices:
    print(f"{device['model']} ({device['serial']}) - {device['name']}")
```

**JavaScript (Gemini):**
```javascript
const { MerakiClient } = require('./gemini/cisco_meraki');

const client = new MerakiClient();

// List organizations
const orgs = await client.listOrganizations();
orgs.forEach(org => {
  console.log(`${org.name} (${org.id})`);
});
```

## API Reference

### Organization API

| Method | Description |
| --- | --- |
| `list_organizations()` | List all accessible organizations |
| `get_organization(org_id)` | Get organization details |

### Networks API

| Method | Description |
| --- | --- |
| `list_networks(org_id)` | List networks in organization |
| `get_network(network_id)` | Get network configuration |

### Devices API

| Method | Description |
| --- | --- |
| `list_devices(network_id)` | List all devices in network |
| `get_device(network_id, serial)` | Get device details |
| `get_device_status(network_id, serial)` | Get device status |

### Wireless API

| Method | Description |
| --- | --- |
| `list_ssids(network_id)` | List SSIDs in network |
| `get_ssid(network_id, number)` | Get SSID configuration |

### Switch API

| Method | Description |
| --- | --- |
| `list_switch_ports(network_id, serial)` | List switch ports |
| `get_switch_port(network_id, serial, port_id)` | Get port details |

### Firewall API

| Method | Description |
| --- | --- |
| `list_firewall_rules(network_id)` | List firewall rules |
| `get_firewall_settings(network_id)` | Get firewall configuration |

### Clients API

| Method | Description |
| --- | --- |
| `list_network_clients(network_id, params)` | List connected clients |
| `get_client(network_id, client_id)` | Get client details |

## Device Types

- **MR** - Wireless access points (WiFi)
- **MS** - Managed switches (wired)
- **MX** - Security appliances (firewall/gateway)
- **Z** - Teleworker gateways
- **MV** - Security cameras
- **MT** - Environmental sensors

## Supported Networks

- Wireless networks (WiFi)
- Switched networks (wired)
- Security appliance networks
- Hybrid networks (wired + wireless)

## Response Format

All APIs return JSON with consistent structure:

```json
{
  "id": "unique-identifier",
  "name": "Resource Name",
  "type": "ResourceType",
  "status": "active|offline",
  "url": "https://..."
}
```

## Error Codes

| Code | Meaning |
| --- | --- |
| 401 | Unauthorized (invalid API key) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not found (resource doesn't exist) |
| 429 | Rate limited (too many requests) |
| 500 | Server error |

## Security

✅ API key stored in `.env` (git-ignored)
✅ HTTPS only
✅ OAuth 2.0 Bearer token
✅ No credentials in logs
✅ Per-organization isolation

## Support

- **API Documentation**: https://developer.cisco.com/meraki/api-v1/
- **Meraki Dashboard**: https://dashboard.meraki.com
- **Status Page**: https://status.meraki.com
