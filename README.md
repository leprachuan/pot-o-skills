# Cisco Meraki Skill

Comprehensive REST API access to Cisco Meraki cloud networking platform for complete network management and monitoring.

**Status:** ✅ **Fully Functional** - All core APIs operational

## Quick Start

### 1. Setup API Key

```bash
# Copy template
cp .env.example .env

# Add your Meraki API key
# Get from: Dashboard → Organization → Administrators → API access
MERAKI_API_KEY=your_key_here
```

### 2. Install Dependencies

**Python:**
```bash
pip install requests python-dotenv
```

**Node.js:**
```bash
npm install axios dotenv
```

### 3. List Your Organizations

**Python:**
```python
from copilot.cisco_meraki import MerakiClient, format_as_markdown_table

client = MerakiClient()
orgs = client.list_organizations()

headers = ["#", "Name", "ID", "URL"]
key_mapping = {
    "#": "#",
    "Name": "name",
    "ID": "id",
    "URL": "url"
}

table = format_as_markdown_table(orgs, headers, key_mapping)
print(table)
```

**JavaScript:**
```javascript
const { MerakiClient, formatAsMarkdownTable } = require('./gemini/cisco_meraki');

const client = new MerakiClient();
const orgs = await client.listOrganizations();

const headers = ["#", "Name", "ID"];
const keyMapping = { "#": "#", "Name": "name", "ID": "id" };
const table = formatAsMarkdownTable(orgs, headers, keyMapping);
console.log(table);
```

## Core Workflows

### Get Organization Networks

```python
client = MerakiClient()

# List orgs
orgs = client.list_organizations()
org_id = orgs[0]['id']

# List networks in org
networks = client.list_networks(org_id)
for net in networks:
    print(f"Network: {net['name']} ({net['id']}, type: {net['type']})")
```

### Monitor Device Status

```python
client = MerakiClient()
network_id = "your_network_id"

# List all devices
devices = client.list_devices(network_id)

# Check status of each
for device in devices:
    status = client.get_device_status(network_id, device['serial'])
    print(f"{device['name']}: {status['status']}")
```

### Get Network Clients

```python
client = MerakiClient()
network_id = "your_network_id"

# List connected clients
clients = client.list_network_clients(network_id)

for client_info in clients:
    print(f"MAC: {client_info['mac']}, IP: {client_info['ip']}, OS: {client_info['os']}")
```

### Manage SSIDs

```python
client = MerakiClient()
network_id = "your_network_id"

# List SSIDs
ssids = client.list_ssids(network_id)

for ssid in ssids:
    if ssid['enabled']:
        print(f"SSID {ssid['number']}: {ssid['name']} ({ssid['securityType']})")
```

## Network Types

| Type | Description | Devices |
|---|---|---|
| **wireless** | WiFi networks | MR (access points) |
| **switch** | Wired networks | MS (switches) |
| **appliance** | Security appliances | MX (firewalls/gateways) |
| **phone** | Phone systems | MP (phones) |
| **camera** | Video surveillance | MV (cameras) |

## Device Types

| Code | Type | Examples |
|---|---|---|
| **MR** | Access Point | MR30H, MR42, MR44 |
| **MS** | Switch | MS120-24P, MS225-24X |
| **MX** | Security Appliance | MX250, MX450, Z3 |
| **Z** | Teleworker Gateway | Z1, Z3 |
| **MV** | Camera | MV2, MV52, MV72 |
| **MT** | Sensor | MT10, MT12 |

## Capabilities

### Organizations
- ✅ List organizations
- ✅ Get organization details
- ✅ Multi-org API access

### Networks
- ✅ List networks by organization
- ✅ Get network configuration
- ✅ Network tagging
- ✅ Time zone configuration

### Devices
- ✅ List all devices in network
- ✅ Get device details (model, firmware, serial)
- ✅ Check device status (online/offline/alerting)
- ✅ Device inventory and location
- ✅ Uplink information

### Wireless (SSID)
- ✅ List SSIDs
- ✅ Get SSID configuration
- ✅ Security settings (WPA2/WPA3)
- ✅ Band steering
- ✅ Client limits

### Switches
- ✅ List switch ports
- ✅ Get port status
- ✅ VLAN configuration
- ✅ Port forwarding
- ✅ PoE status

### Firewall
- ✅ List firewall rules
- ✅ Get firewall settings
- ✅ Access control lists
- ✅ Intrusion prevention

### Clients
- ✅ List connected clients
- ✅ Get client details
- ✅ Usage statistics
- ✅ Device history
- ✅ IP and MAC addresses

## File Structure

```
cisco-meraki/
├── .env                    # API credentials (git-ignored)
├── .env.example            # Template
├── .gitignore              # Protects secrets
├── SKILL.md                # Skill definition
├── README.md               # This file
├── skill_metadata.json     # Metadata
│
├── claude/
│   └── cisco_meraki.py     # Claude implementation
│
├── copilot/
│   └── cisco_meraki.py     # Copilot CLI implementation
│
├── gemini/
│   └── cisco_meraki.js     # Gemini/Node.js implementation
│
├── scripts/
│   └── examples/           # Usage examples
│
└── references/
    └── api_docs.md         # API reference
```

## Authentication

**API Key Location:**
Meraki Dashboard → Organization → Administrators → My Profile → API Access

**Key Format:**
- Length: 40 characters
- Format: Hexadecimal string
- Access: Organization-level permissions
- Expiration: Configurable by admin

**Token Type:** Bearer token in Authorization header
```
Authorization: Bearer your_api_key_here
```

## Rate Limiting

- **Limit:** 10 requests per second per API key
- **Burst:** Up to 100 requests per second
- **Reset:** Automatic after 1 second
- **Handling:** Implement exponential backoff

## Common Tasks

### Monitor All Networks

```python
client = MerakiClient()

# Get all orgs
orgs = client.list_organizations()

for org in orgs:
    print(f"\n=== Organization: {org['name']} ===")
    
    # Get networks
    nets = client.list_networks(org['id'])
    for net in nets:
        print(f"  Network: {net['name']}")
        
        # Get devices
        devices = client.list_devices(net['id'])
        print(f"    Devices: {len(devices)}")
```

### Check Device Uptime

```python
client = MerakiClient()
network_id = "your_network_id"

devices = client.list_devices(network_id)
for device in devices:
    status = client.get_device_status(network_id, device['serial'])
    print(f"{device['name']}: {status['status']} (Uptime: {status['lastReportedAt']})")
```

### List All Clients and IPs

```python
client = MerakiClient()
network_id = "your_network_id"

clients = client.list_network_clients(network_id)
print(f"Total clients: {len(clients)}\n")

for client_info in clients:
    print(f"IP: {client_info.get('ip', 'N/A'):15} MAC: {client_info['mac']} OS: {client_info.get('os', 'Unknown')}")
```

## Troubleshooting

**"401 Unauthorized":**
- Verify API key is correct
- Check key is still active in dashboard
- Confirm organization access

**"403 Forbidden":**
- User account may lack API access
- Enable API access in admin settings
- Verify organization permissions

**"404 Not Found":**
- Verify network/device IDs are correct
- Device may not exist in network
- Check organization access

**Rate Limit Errors:**
- Implement backoff/retry logic
- Reduce request frequency
- Batch requests where possible

## Support & Documentation

- **Official API**: https://developer.cisco.com/meraki/api-v1/
- **Dashboard**: https://dashboard.meraki.com
- **Status**: https://status.meraki.com
- **Community**: https://community.meraki.com

## License

MIT
