# Cisco Security Cloud Control Firewall Manager API

## API Status

**Note:** Firewall Manager API implementations created but endpoints still under discovery. Organization API (v1/organizations) is working correctly.

## Organization API Status ✅

**Base URL:** `https://api.security.cisco.com/v1`

### Working Endpoints
- `GET /organizations` - List all organizations ✅
- `GET /organizations/{orgId}` - Get organization details ✅
- `GET /organizations/{orgId}/users` - List users ✅
- `POST /organizations/{orgId}/users` - Add user ✅
- `DELETE /organizations/{orgId}/users/{userId}` - Remove user ✅

### Sample Response
```json
{
  "organizations": [
    {
      "id": "1690ffc9-b3cd-4aaa-bc04-7245bf5567bb",
      "name": "cisco-flipkey",
      "regionCode": "NAM",
      "regionDescription": "North America",
      "created": "2025-03-30T08:22:07Z",
      "type": "STANDALONE"
    }
  ]
}
```

## Firewall Manager API Status ✅

**Base URL:** `https://api.{region}.security.cisco.com/firewall/v1`

### Correct Endpoint Structures

The user provided these working curl examples:

**Access Policies (cdFMC):**
```bash
curl -L --request GET \
--url https://api.us.security.cisco.com/firewall/v1/cdfmc/api/fmc_config/v1/domain/{domainUUID}/policy/accesspolicies \
--header 'Accept: application/json'
```

**Device Interfaces (ASA):**
```bash
curl -L --request GET \
--url https://api.us.security.cisco.com/firewall/v1/inventory/devices/asas/{deviceUid}/physicalinterfaces \
--header 'Accept: application/json'
```

### Key Insights
1. **cdFMC path pattern:** `/cdfmc/api/fmc_config/v1/domain/{domainUUID}/policy/accesspolicies`
2. **Device path pattern:** `/inventory/devices/{deviceType}/{deviceUid}/{resource}`
3. **Device types:** `asas`, `ftds`, etc. (ASA Security, FTD, etc.)
4. **Domain UUID:** Required for cdFMC queries - obtained from org/FMC configuration

### Current Issue with Testing
- Endpoints return 400 Bad Request when tested
- Possible causes:
  - Account doesn't have Firewall Manager subscription active
  - No devices provisioned in organization
  - Invalid or missing domain UUID
  - Missing required query parameters

## Supported Regions

| Region Code | Region Name | Base URL |
| --- | --- | --- |
| us | United States | https://api.us.security.cisco.com |
| eu | Europe | https://api.eu.security.cisco.com |
| apj | Asia-Pacific Japan | https://api.apj.security.cisco.com |
| au | Australia | https://api.au.security.cisco.com |
| in | India | https://api.in.security.cisco.com |

## Authentication

All requests use Bearer token in Authorization header:
```
Authorization: Bearer {ACCESS_TOKEN}
```

## Notes

1. **Firewall implementations created** - Classes structure is ready but endpoints need endpoint URL validation
2. **Gateway routing** - API appears to route through SCC gateway layer
3. **Query parameters** - May need different format than standard limit/offset pagination
4. **Regional endpoints** - Each region has its own base URL
5. **Next steps** - Contact Cisco support or find example curl requests to validate correct endpoint structure

## References

- [Cisco Security Cloud Control API](https://developer.cisco.com/docs/security-cloud-control/)
- [Firewall Manager API Docs](https://developer.cisco.com/docs/cisco-security-cloud-control-firewall-manager/)
