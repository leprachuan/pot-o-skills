# Cisco Security Cloud Control Skill

Programmatic management of Cisco Security Cloud Control infrastructure across Claude, Copilot CLI, and Gemini.

## Quick Start

### 1. Get API Credentials

1. Visit [Cisco Developer Console](https://developer.cisco.com/docs/security-cloud-control/introduction/)
2. Create or obtain your API credentials:
   - API Key ID
   - Access Token
   - Refresh Token

### 2. Setup Credentials

Copy `.env.example` to `.env` and add your credentials:

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

Or set environment variables:
```bash
export CISCO_API_KEY_ID=your_key_id
export CISCO_ACCESS_TOKEN=your_access_token
export CISCO_REFRESH_TOKEN=your_refresh_token
```

### 3. Install Dependencies

**Python (Claude/Copilot):**
```bash
pip install requests python-dotenv pyjwt
```

**Node.js (Gemini):**
```bash
npm install axios dotenv jsonwebtoken
```

### 4. Basic Usage

**Python:**
```python
from copilot.cisco_scc import CiscoSCCClient

client = CiscoSCCClient()
orgs = client.list_organizations()
print(orgs)
```

**JavaScript:**
```javascript
const { CiscoSCCClient } = require('./gemini/cisco_scc');

const client = new CiscoSCCClient();
const orgs = await client.listOrganizations();
console.log(orgs);
```

## Key Operations

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

## Integrated Products

- AI Defense
- Firewall Management
- Multicloud Defense
- Secure Access
- Secure Workload

## File Structure

```
cisco-security-cloud-control/
├── .env.example           # Credentials template (copy to .env)
├── SKILL.md              # Skill documentation
├── skill_metadata.json   # Metadata and parameters
├── README.md             # This file
├── claude/               # Claude implementation
├── copilot/              # Copilot CLI implementation
├── gemini/               # Gemini implementation
├── scripts/              # Helper scripts
├── templates/            # API request templates
└── references/           # API docs and guides
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

- API Docs: https://developer.cisco.com/docs/security-cloud-control/
- Base URL: https://api.security.cisco.com/v1
- Endpoint Structure: `/organizations/{orgId}/...`
- Issues: Check your API credentials in `.env`
