---
name: cisco-security-cloud-control
description: Manage Cisco Security Cloud Control and cdFMC resources - organizations, users, subscriptions, roles, and firewall policies
---

# Cisco Security Cloud Control Skill

Comprehensive REST API access to Cisco Security Cloud Control (SCC) for organization management and cloud-delivered Firewall Management Center (cdFMC) for firewall policy management.

**Status:** ✅ **Fully Functional** - Both SCC and cdFMC APIs operational

## Features

### Organization Management (SCC API) ✅
- Organization creation and management
- Subscription management  
- User and group management
- Role assignment and permissions
- Multi-product integration (Firewall, Defense, etc.)

### Firewall Policy Management (cdFMC API) ✅
- Domain UUID discovery
- Access control policy queries
- Access rule management
- Network and object management
- Policy configuration retrieval

### Device Management (SCC Firewall API)
- Device inventory queries
- Device manager listing
- Device health monitoring
- Deployment tracking

### Multi-Region Support ✅
- **US**: api.us.security.cisco.com
- **EU**: api.eu.security.cisco.com
- **APJ**: api.apj.security.cisco.com
- **Australia**: api.au.security.cisco.com
- **India**: api.in.security.cisco.com

## Setup

### 1. Credentials (.env)

```bash
# Organization/SCC API Token
CISCO_API_KEY_ID=your_key_id
CISCO_ACCESS_TOKEN=your_scc_api_token
CISCO_REFRESH_TOKEN=your_refresh_token

# cdFMC API Token (REQUIRED for firewall policies)
CISCO_CDFMC_ACCESS_TOKEN=your_cdfmc_api_token
```

**Important:** cdFMC requires a separate token from the organization API. Generate both:
1. SCC token in Security Cloud Control UI
2. cdFMC token in cdFMC API section (appears after cdFMC is provisioned)

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

**Get Access Control Policies (Python):**
```python
from copilot.cisco_scc_firewall import CiscoSCCFirewallManager

fw_client = CiscoSCCFirewallManager(region="us")

# Step 1: Get domain UUID (required for all cdFMC queries)
domain = fw_client.get_cdfmc_domain()
domain_uuid = domain['items'][0]['uuid']

# Step 2: Query access policies
policies = fw_client.get_cdfmc_access_policies(domain_uuid)

# Step 3: Display results
for policy in policies['items']:
    print(f"{policy['name']} (ID: {policy['id']})")
```

**Get Organizations (Python):**
```python
from copilot.cisco_scc import CiscoSCCClient

scc_client = CiscoSCCClient()
orgs = scc_client.list_organizations()

for org in orgs['organizations']:
    print(f"{org['name']} ({org['id']})")
```

## API Reference

### Organization API

| Method | Description |
| --- | --- |
| `list_organizations()` | List all organizations |
| `create_organization(name, type)` | Create new organization |
| `list_users(org_id)` | List users in organization |
| `add_user(org_id, email, role)` | Add user to organization |
| `list_subscriptions(org_id)` | List subscriptions |
| `list_roles()` | List available roles |

### Firewall Manager API

| Method | Description |
| --- | --- |
| `get_cdfmc_domain()` | Get domain UUID ⭐ **Call this first** |
| `get_cdfmc_access_policies(domain_uuid)` | List access policies |
| `get_cdfmc_access_policy(domain_uuid, policy_id)` | Get specific policy |
| `get_cdfmc_access_rules(domain_uuid, policy_id)` | Get policy rules |
| `get_cdfmc_network_objects(domain_uuid)` | List network objects |

### Device Manager API

| Method | Description |
| --- | --- |
| `list_devices()` | List firewall devices |
| `get_device(device_uid)` | Get device details |
| `list_managers()` | List FMC managers |

## Workflow: Get Access Policies

```
1. Initialize client
   ↓
2. Call get_cdfmc_domain()
   ↓
3. Extract domain UUID from response
   ↓
4. Call get_cdfmc_access_policies(domain_uuid)
   ↓
5. Process policy list
```

## Authentication

### Two Separate APIs, Two Tokens

**SCC API (Organization Management)**
- Base: `https://api.security.cisco.com/v1`
- Token: `CISCO_ACCESS_TOKEN`
- Methods: Organization, user, subscription management

**cdFMC API (Firewall Policies)**
- Base: `https://api.{region}.security.cisco.com/firewall`
- Token: `CISCO_CDFMC_ACCESS_TOKEN`
- Methods: Policy and object queries
- Paths: `/v1/cdfmc/api/fmc_platform/v1/...` and `/v1/cdfmc/api/fmc_config/v1/...`

**Automatic Token Switching:**
The implementation automatically uses the correct token for each endpoint type.

## Response Format

All APIs return JSON with pagination:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Resource Name",
      "type": "ResourceType"
    }
  ],
  "paging": {
    "offset": 0,
    "limit": 25,
    "count": 5,
    "pages": 1
  },
  "links": {
    "self": "https://..."
  }
}
```

## Error Codes

| Code | Meaning | Solution |
| --- | --- | --- |
| 401 | Unauthorized | Check token validity and expiration |
| 403 | Forbidden | Verify token permissions for endpoint |
| 404 | Not Found | Check domain UUID or resource ID |
| 429 | Rate Limited | Retry with backoff |
| 500 | Server Error | Contact Cisco support |

## Security

✅ Credentials stored in `.env` (git-ignored)
✅ Separate tokens for different API scopes
✅ Bearer authentication (OAuth 2.0)
✅ No credentials in logs
✅ HTTPS only

## Troubleshooting

**"400 Bad Request" on firewall endpoints:**
- Verify `CISCO_CDFMC_ACCESS_TOKEN` is set in `.env`
- Confirm token is valid and not expired
- Check that cdFMC is provisioned in your account

**"401 Unauthorized":**
- Verify token format (should be JWT)
- Check token hasn't expired
- Generate fresh token from SCC UI

**No policies returned:**
- Verify domain UUID is correct
- Confirm your account has access control policies configured
- Check policy permissions

## File Structure

```
cisco-security-cloud-control/
├── .env.example                # Template with all required variables
├── .gitignore                  # Protects .env and credentials
├── SKILL.md                    # This documentation
├── README.md                   # Detailed guide
├── skill_metadata.json         # Skill metadata
├── claude/
│   ├── cisco_scc.py
│   └── cisco_scc_firewall.py
├── copilot/
│   ├── cisco_scc.py
│   └── cisco_scc_firewall.py
├── gemini/
│   ├── cisco_scc.js
│   └── cisco_scc_firewall.js
└── references/
    ├── firewall_openapi_1_17_0.yaml
    ├── cdfmc_openapi_1_17_0.yaml
    ├── CDFMC_CLARIFICATION.md
    └── FIREWALL_API_NOTES.md
```

## Support

- **SCC API Docs**: https://developer.cisco.com/docs/security-cloud-control/
- **cdFMC API Docs**: https://developer.cisco.com/docs/cisco-cloud-delivered-firewall-management-center-cd-fmc-api/
- **OpenAPI Specs**: See `references/` folder
- **Issues**: Check credentials in `.env` and token expiration
