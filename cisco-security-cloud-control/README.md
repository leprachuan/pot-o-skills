# Cisco Security Cloud Control Skill

Comprehensive management of Cisco Security Cloud Control infrastructure including organization management, user administration, and advanced firewall management operations.

## Quick Start

### 1. Credentials Setup
Your `.env` file is already configured with API credentials and git-ignored for security.

```bash
CISCO_API_KEY_ID=your_key_id
CISCO_ACCESS_TOKEN=your_access_token
CISCO_REFRESH_TOKEN=your_refresh_token
```

### 2. Install Dependencies

**Python (Claude/Copilot):**
```bash
pip install requests python-dotenv pyjwt
```

**Node.js (Gemini):**
```bash
npm install axios dotenv jsonwebtoken
```

### 3. Basic Usage

**Organization Management:**
```python
from copilot.cisco_scc import CiscoSCCClient

client = CiscoSCCClient()
orgs = client.list_organizations()
print(orgs)
```

**Firewall Manager:**
```python
from copilot.cisco_scc_firewall import CiscoSCCFirewallManager

fw_client = CiscoSCCFirewallManager(region="us")

# Step 1: Get domain UUID (required for cdFMC operations)
domain = fw_client.get_cdfmc_domain()
domain_uid = domain['data']['id']  # Extract domain UUID

# Step 2: Use domain UUID for policy queries
policies = fw_client.get_cdfmc_access_policies(domain_uid)
print(policies)

# Step 3: List devices
devices = fw_client.list_devices()
print(devices)
```

**JavaScript:**
```javascript
const { CiscoSCCFirewallManager } = require('./gemini/cisco_scc_firewall');

const fw_client = new CiscoSCCFirewallManager("us");
const devices = await fw_client.listDevices();
console.log(devices);
```

## Organization Management

### Organizations
- ✅ List all organizations
- ✅ Create organization (managed/standalone)
- ✅ Get organization details
- ✅ Update organization
- ✅ Delete organization

### Users & Groups
- ✅ List organization users
- ✅ Add user to organization
- ✅ Remove user from organization
- ✅ Assign roles to users
- ✅ List admin groups

### Subscriptions
- ✅ List subscriptions
- ✅ Get subscription details
- ✅ Manage product subscriptions

### Roles
- ✅ List available roles
- ✅ Assign role to user
- ✅ Get role permissions

## Firewall Manager Operations

### Inventory Management
- ✅ List devices
- ✅ Get device details
- ✅ List device managers
- ✅ Get cloud-delivered FMC
- ✅ List cloud services

### Cloud-delivered FMC
- ✅ Get access policies
- ✅ Get specific access policy
- ✅ Get access rules for policies
- ✅ Manage network objects

### Policy & Configuration
- ✅ List firewall objects
- ✅ Get object details
- ✅ Deploy configurations to devices

### Monitoring & Tracking
- ✅ Get device health
- ✅ List asynchronous transactions
- ✅ Get transaction status
- ✅ View changelog
- ✅ Search across tenant

## Integrated Products

**Organization Level:**
- AI Defense
- Firewall Management
- Multicloud Defense
- Secure Access
- Secure Workload

**Firewall Manager:**
- Cloud-delivered Firewall Management Center (cdFMC)
- Device Management
- Policy Management
- Object Management

## Supported Regions

- **us** - United States (api.us.security.cisco.com)
- **eu** - Europe (api.eu.security.cisco.com)
- **apj** - Asia-Pacific Japan (api.apj.security.cisco.com)
- **au** - Australia (api.au.security.cisco.com)
- **in** - India (api.in.security.cisco.com)

## File Structure

```
cisco-security-cloud-control/
├── .env.example                # Credentials template
├── SKILL.md                    # Skill documentation
├── skill_metadata.json         # Metadata and parameters
├── README.md                   # This file
├── claude/
│   ├── cisco_scc.py           # Organization API
│   └── cisco_scc_firewall.py  # Firewall Manager API
├── copilot/
│   ├── cisco_scc.py           # Organization API
│   └── cisco_scc_firewall.py  # Firewall Manager API
├── gemini/
│   ├── cisco_scc.js           # Organization API
│   └── cisco_scc_firewall.js  # Firewall Manager API
├── scripts/                    # Helper scripts
├── templates/                  # API request templates
└── references/                 # API docs and guides
```

## Authentication

Uses OAuth 2.0 Bearer Token. Credentials managed via:
- `.env` file (copy from `.env.example`)
- Environment variables
- Automatic token refresh on expiry

## Error Handling

- ✅ Token expiry → Auto-refresh
- ✅ 401 errors → Re-authenticate
- ✅ 429 rate limits → Exponential backoff
- ✅ Network errors → Graceful fallback

## Security

✅ Use `.env.example` template (never commit real credentials)
✅ Store credentials in `.env` or environment variables
✅ No credential exposure in logs
✅ OAuth 2.0 standard authentication

## Support

- **Organization API Docs:** https://developer.cisco.com/docs/security-cloud-control/
- **Firewall Manager Docs:** https://developer.cisco.com/docs/cisco-security-cloud-control-firewall-manager/
- **Base URL (Org):** https://api.security.cisco.com/v1
- **Base URL (Firewall):** https://api.{region}.security.cisco.com/firewall/v1
- **Issues:** Check your API credentials in `.env`

