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

### Critical: Getting Domain UUID

**All cdFMC operations require a domain UUID.** Fetch it first using:

```bash
curl -L --request GET \
--url https://api.us.security.cisco.com/firewall/v1/cdfmc/api/fmc_platform/v1/info/domain \
--header 'Accept: application/json'
```

**Python/JS Usage:**
```python
fw_client = CiscoSCCFirewallManager(region="us")
domain_response = fw_client.get_cdfmc_domain()
# Extract domain UUID from response to use in policy/object queries
```

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
1. **Domain endpoint:** `/cdfmc/api/fmc_platform/v1/info/domain` - Get UUID first ⭐
2. **cdFMC policy pattern:** `/cdfmc/api/fmc_config/v1/domain/{domainUUID}/policy/accesspolicies`
3. **Device path pattern:** `/inventory/devices/{deviceType}/{deviceUid}/{resource}`
4. **Device types:** `asas`, `ftds`, etc. (ASA Security, FTD, etc.)
5. **Domain UUID:** Required for cdFMC queries - extracted from get_cdfmc_domain()

### Workflow
1. Call `get_cdfmc_domain()` to fetch domain UUID
2. Extract UUID from response
3. Use UUID in subsequent cdFMC policy/object calls
4. For device operations, use device type and UID directly

### Testing Status
- Endpoints return 400 Bad Request when tested (account may not have Firewall Manager subscription or devices provisioned)
- Endpoint structures verified correct via user-provided curl examples
- Implementations ready for testing once account has subscriptions/devices

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

1. **get_cdfmc_domain() is critical** - Must call this first to get domain UUID for all cdFMC operations
2. **Domain UUID extraction** - Response contains domain UUID needed for policy/object queries
3. **Gateway routing** - API routes through SCC gateway layer (expected behavior)
4. **Regional endpoints** - Each region has its own base URL for firewall operations
5. **400 errors expected** - If account lacks Firewall Manager subscription or has no devices provisioned
6. **Firewall implementations complete** - All methods implemented, awaiting subscription/device testing

## References

- [Cisco Security Cloud Control API](https://developer.cisco.com/docs/security-cloud-control/)
- [Firewall Manager API Docs](https://developer.cisco.com/docs/cisco-security-cloud-control-firewall-manager/)
