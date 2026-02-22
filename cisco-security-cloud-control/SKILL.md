---
name: cisco-security-cloud-control
description: Manage Cisco Security Cloud Control resources - organizations, users, subscriptions, and roles
---

# Cisco Security Cloud Control Skill

Programmatic access to Cisco Security Cloud Control API for managing security infrastructure.

## Features

- **Organization Management**: Create and manage standalone/managed organizations
- **Subscription Management**: Manage software subscriptions across organizations
- **User & Group Management**: Add/remove users and admin groups
- **Role Management**: Assign and manage user roles and permissions
- **Multi-Product Support**: Integrate with AI Defense, Firewall Management, Multicloud Defense, Secure Access, Secure Workload

## Setup

1. **Credentials in .env:**
   ```bash
   CISCO_API_KEY_ID=your_key_id
   CISCO_ACCESS_TOKEN=your_access_token
   CISCO_REFRESH_TOKEN=your_refresh_token
   ```

2. **Dependencies:**
   - Python: `requests`, `python-dotenv`, `jwt`
   - Node.js: `axios`, `dotenv`, `jsonwebtoken`

## Quick Reference

### Organization Operations
- List organizations
- Create organization (managed/standalone)
- Get organization details
- Update organization
- Delete organization

### User Management
- Add user to organization
- Remove user from organization
- List organization users
- Assign role to user
- Update user permissions

### Subscription Management
- List subscriptions
- Get subscription details
- Activate/deactivate subscriptions

### Role Management
- List available roles
- Assign roles to users/groups
- Get role permissions

## Authentication

Uses OAuth 2.0 Bearer Token authentication. Token automatically included in Authorization header.

## Base URL

```
https://api.sse.cisco.com/platform/api/v1
```

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
