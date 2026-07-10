# Cisco Security Cloud Control Skill

Comprehensive management of Cisco Security Cloud Control (SCC) and cloud-delivered Firewall Management Center (cdFMC) infrastructure.

**Status:** ✅ **Fully Functional** - All APIs working

## Quick Start

### 1. Credentials Setup

Your `.env` file requires credentials for two separate APIs:

```bash
# Organization/SCC API (for org/user/subscription management)
CISCO_API_KEY_ID=your_key_id
CISCO_ACCESS_TOKEN=your_scc_api_token
CISCO_REFRESH_TOKEN=your_refresh_token

# cdFMC API Token (for firewall policy management) - REQUIRED
CISCO_CDFMC_ACCESS_TOKEN=your_cdfmc_api_token
```

**⚠️ Important:** cdFMC requires a **separate token** from the organization API.
- SCC token: Generated in SCC UI Administration → API Credentials
- cdFMC token: Generated in cdFMC API section after cdFMC provisioning

### 2. Install Dependencies

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

# Step 1: Get domain UUID (required for all cdFMC operations)
domain = fw_client.get_cdfmc_domain()
domain_uuid = domain['items'][0]['uuid']

# Step 2: Get access control policies
policies = fw_client.get_cdfmc_access_policies(domain_uuid)

# Step 3: Display results
print(f"Found {policies['paging']['count']} access control policies:")
for policy in policies['items']:
    print(f"  - {policy['name']} (ID: {policy['id']})")
```

**Get Organizations (Python):**
```python
from copilot.cisco_scc import CiscoSCCClient

scc_client = CiscoSCCClient()
orgs = scc_client.list_organizations()

print(f"Organizations:")
for org in orgs['organizations']:
    print(f"  - {org['name']} ({org['id']})")
```

**JavaScript (Gemini):**
```javascript
const { CiscoSCCFirewallManager } = require('./gemini/cisco_scc_firewall');

const fw_client = new CiscoSCCFirewallManager("us");

// Get domain UUID
const domain = await fw_client.getCDFMCDomain();
const domainUuid = domain.items[0].uuid;

// Get access policies
const policies = await fw_client.getCDFMCAccessPolicies(domainUuid);
console.log(`Found ${policies.paging.count} policies`);
policies.items.forEach(policy => {
  console.log(`  - ${policy.name} (${policy.id})`);
});
```

## Organization Management

### Available Operations
- ✅ List organizations
- ✅ Create organization (managed/standalone)
- ✅ Get organization details
- ✅ Update organization
- ✅ Delete organization
- ✅ List users
- ✅ Add/remove users
- ✅ Assign roles to users
- ✅ List admin groups
- ✅ List subscriptions
- ✅ Get subscription details

### Subscriptions Managed
- AI Defense
- Firewall Management
- Multicloud Defense
- Secure Access
- Secure Workload

## Firewall Manager Operations

### cdFMC API Operations ✅
- ✅ Domain UUID discovery (required first step)
- ✅ Access control policy queries
- ✅ Access rule management
- ✅ Network object management
- ✅ Policy configuration retrieval

### Device Management (SCC Firewall API)
- Device inventory listing
- Device details retrieval
- Device manager queries
- Device health monitoring

## Supported Regions

| Region | Base URL |
| --- | --- |
| **US** | api.us.security.cisco.com |
| **EU** | api.eu.security.cisco.com |
| **APJ** | api.apj.security.cisco.com |
| **Australia** | api.au.security.cisco.com |
| **India** | api.in.security.cisco.com |

## API Structure

### Two Separate APIs

**SCC API (Organization Management)**
- Base: `https://api.security.cisco.com/v1`
- Token: `CISCO_ACCESS_TOKEN`
- Manages: Orgs, users, subscriptions, roles

**cdFMC API (Firewall Policies)**
- Base: `https://api.{region}.security.cisco.com/firewall`
- Token: `CISCO_CDFMC_ACCESS_TOKEN` (separate!)
- Manages: Policies, rules, objects, domains

### Automatic Token Switching
The implementation automatically uses the correct token for each endpoint type. You don't need to manage this manually.

## Response Format

All APIs return paginated JSON responses:

```json
{
  "items": [
    {
      "id": "unique-id",
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
    "self": "https://api.security.cisco.com/..."
  }
}
```

## Workflow: Get Your Access Policies

```
1. Create CiscoSCCFirewallManager instance
   ↓
2. Call get_cdfmc_domain()
   ↓ Returns: { items: [{ uuid: "...", name: "Global", ... }] }
   ↓
3. Extract domain UUID from response
   ↓
4. Call get_cdfmc_access_policies(domain_uuid)
   ↓ Returns: { items: [{ id: "...", name: "PolicyName" }, ...] }
   ↓
5. Process policies
```

## File Structure

```
cisco-security-cloud-control/
├── .env.example                # Credentials template (fill and rename to .env)
├── .gitignore                  # Protects .env from git
├── SKILL.md                    # Skill definition
├── README.md                   # This file
├── skill_metadata.json         # Skill metadata for registration
│
├── claude/
│   ├── cisco_scc.py           # SCC organization API
│   └── cisco_scc_firewall.py  # cdFMC firewall API
│
├── copilot/
│   ├── cisco_scc.py           # SCC organization API
│   └── cisco_scc_firewall.py  # cdFMC firewall API
│
├── gemini/
│   ├── cisco_scc.js           # SCC organization API
│   └── cisco_scc_firewall.js  # cdFMC firewall API
│
└── references/
    ├── firewall_openapi_1_17_0.yaml    # SCC Firewall API spec
    ├── cdfmc_openapi_1_17_0.yaml       # cdFMC API spec
    ├── CDFMC_CLARIFICATION.md          # API differences explained
    ├── FIREWALL_API_NOTES.md           # Endpoint documentation
    └── API_DEBUGGING_NOTES.md          # Troubleshooting guide
```

## Troubleshooting

### "401 Unauthorized" on cdFMC endpoints
- **Cause:** Invalid or expired cdFMC token
- **Solution:** Generate fresh `CISCO_CDFMC_ACCESS_TOKEN` from SCC UI

### "400 Bad Request" on firewall endpoints
- **Cause:** Token not set or cdFMC not provisioned
- **Solution:** Verify `CISCO_CDFMC_ACCESS_TOKEN` in .env and cdFMC is provisioned

### No policies returned
- **Cause:** Wrong domain UUID or no policies configured
- **Solution:** Verify domain UUID and check cdFMC has policies

### Token expired
- **Cause:** Token older than max lifetime
- **Solution:** Generate fresh token from SCC UI

## Security

✅ `.env` is git-ignored (never commit credentials)
✅ Two separate tokens for different API scopes
✅ OAuth 2.0 Bearer token authentication
✅ HTTPS only
✅ No credentials logged
✅ Sensitive data protected

## Documentation

- **SCC API Docs:** https://developer.cisco.com/docs/security-cloud-control/
- **cdFMC API Docs:** https://developer.cisco.com/docs/cisco-cloud-delivered-firewall-management-center-cd-fmc-api/
- **OpenAPI Specs:** See `references/` folder for complete API specifications
- **Skill Docs:** See `SKILL.md` for detailed feature documentation

## API Endpoints

### Organization API
```
GET /v1/organizations - List organizations
POST /v1/organizations - Create organization
GET /v1/organizations/{orgId} - Get organization
GET /v1/organizations/{orgId}/users - List users
POST /v1/organizations/{orgId}/users - Add user
GET /v1/organizations/{orgId}/subscriptions - List subscriptions
```

### cdFMC API
```
GET /v1/cdfmc/api/fmc_platform/v1/info/domain - Get domain UUID ⭐
GET /v1/cdfmc/api/fmc_config/v1/domain/{UUID}/policy/accesspolicies - Get policies
GET /v1/cdfmc/api/fmc_config/v1/domain/{UUID}/policy/accesspolicies/{ID} - Get policy
GET /v1/cdfmc/api/fmc_config/v1/domain/{UUID}/object/networks - Get objects
```

## Examples: Your Current Account

**Organization:**
- Name: cisco-flipkey
- ID: 1690ffc9-b3cd-4aaa-bc04-7245bf5567bb

**Domain (cdFMC):**
- Name: Global
- UUID: e276abec-e0f2-11e3-8169-6d9ed49b625f

**Access Control Policies (5):**
1. Dad-Policy
2. Default Access Control Policy
3. FoserTestPolicy
4. ISP_FW_POLICY
5. test

## Support & Issues

For issues:
1. Check `.env` has all required credentials
2. Verify tokens haven't expired
3. Review OpenAPI specs in `references/`
4. Check troubleshooting section above
5. Contact Cisco support if persisting

## Understanding cdFMC & FTD Concepts

For deeper understanding of cdFMC and Threat Defense concepts, refer to Cisco's official documentation:

**Cisco Secure Firewall - Threat Defense 10.0.0 Documentation:**
https://www.cisco.com/c/en/us/td/docs/security/secure-firewall/landing-page/threat-defense/threatdefense-10-0-0-docs.html

This documentation covers:
- Access Control policies and rules
- Objects and object groups
- Network configuration
- Device management
- Policy deployment
- Threat defense features
