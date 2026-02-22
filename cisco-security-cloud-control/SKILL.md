---
name: cisco-security-cloud-control
description: Manage Cisco Security Cloud Control resources - organizations, users, subscriptions, roles, and firewall management
---

# Cisco Security Cloud Control Skill

Comprehensive REST API access to Cisco Security Cloud Control for security management and firewall operations.

## Features

### Organization Management
- **Organization Management**: Create and manage standalone/managed organizations
- **Subscription Management**: Manage software subscriptions across organizations
- **User & Group Management**: Add/remove users and admin groups
- **Role Management**: Assign and manage user roles and permissions

### Firewall Manager (NEW!)
- **Inventory Management**: Manage devices, services, and device managers
- **Cloud-delivered FMC**: Access and manage cloud-delivered Firewall Management Center
- **Policy Management**: Create, read, and manage access policies and rules
- **Object Management**: Manage firewall policy objects (networks, services, etc.)
- **Deployment**: Deploy changes to devices at scale
- **Monitoring**: Track device health, transactions, and changes
- **Search**: Perform complex searches across the entire tenant
- **Changelog**: View detailed history of all changes

### Multi-Region Support
- **US Region**: api.us.security.cisco.com
- **EU Region**: api.eu.security.cisco.com
- **APJ Region**: api.apj.security.cisco.com
- **Australia Region**: api.au.security.cisco.com
- **India Region**: api.in.security.cisco.com

## Setup

1. **Credentials in .env:**
   ```bash
   CISCO_API_KEY_ID=your_key_id
   CISCO_ACCESS_TOKEN=your_access_token
   CISCO_REFRESH_TOKEN=your_refresh_token
   ```

2. **Dependencies:**
   - Python: `requests`, `python-dotenv`
   - Node.js: `axios`, `dotenv`

## Quick Reference

### Organization Operations
- List organizations
- Create organization (managed/standalone)
- Get organization details
- Update organization
- Delete organization

### Firewall Manager Operations
- List devices in inventory
- Get cloud-delivered FMC manager
- List and manage access policies
- Manage network objects
- Deploy configurations
- Track transactions
- Search across tenant
- View changelog

## Authentication

Uses OAuth 2.0 Bearer Token authentication. Token automatically included in Authorization header.

## Base URLs

### Organization API
```
https://api.security.cisco.com/v1
```

### Firewall Manager API (Regional)
```
https://api.{region}.security.cisco.com/firewall/v1
```

Supported regions: us, eu, apj, au, in

## Error Handling

- Token expiry → Automatic refresh using refresh token
- 401 Unauthorized → Re-authenticate
- Rate limiting (429) → Exponential backoff retry
- Missing credentials → Graceful error message

## API Response Format

Standard REST JSON responses:
```json
{
  "success": true,
  "data": { /* resource data */ },
  "message": "Operation successful"
}
```

## Security

- Credentials stored in `.env` (git-ignored)
- Bearer token in Authorization header
- No credentials logged or exposed
- Token refresh handled automatically

