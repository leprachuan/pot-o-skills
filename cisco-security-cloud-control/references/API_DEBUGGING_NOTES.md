# Cisco SCC Firewall API - Debugging Notes

## Discovery Process

### OpenAPI Spec
- **URL:** https://pubhub.devnetcloud.com/media/cdo-api-documentation/docs/9b0e4c9a-48cb-3530-a00a-1f32fbf2438c/cisco_security_cloud_control_firewall_manager_api_1_17_0.yaml
- **Version:** 1.17.0
- **Saved locally:** `firewall_openapi_1_17_0.yaml`

### Verified Information from Spec

**Base URLs (Servers):**
```yaml
- https://api.us.security.cisco.com/firewall (US)
- https://api.eu.security.cisco.com/firewall (EU)  
- https://api.apj.security.cisco.com/firewall (APJ)
- https://api.au.security.cisco.com/firewall (AUS)
- https://api.in.security.cisco.com/firewall (IN)
```

**Key Endpoints from Spec:**
- `GET /v1/inventory/devices` - List devices
- `GET /v1/inventory/managers` - List device managers (with optional filter query)
- `POST /v1/inventory/managers/cdfmc` - Provision cdFMC
- `GET /v1/fmc/gateway/command` - Execute FMC commands

**Security:** Bearer Token (JWT) in Authorization header

### Current Issue - 400 Bad Request

**Symptom:** All firewall endpoints return 400 Bad Request, routing through:
```
/api/platform/scc-gateway/request/api/rest/v1/{endpoint}
```

**Token Status:**
- ✅ Valid for organization API (GET /v1/organizations works)
- ❌ Rejected for firewall API endpoints

**Examples tested:**
```bash
# Works
curl -H "Authorization: Bearer ${TOKEN}" \
  https://api.security.cisco.com/v1/organizations

# Returns 400
curl -H "Authorization: Bearer ${TOKEN}" \
  https://api.us.security.cisco.com/firewall/v1/inventory/devices

# Alternative domains also fail
https://edge.us.cdo.cisco.com/api/rest/v1/inventory/devices (401)
https://us.manage.security.cisco.com/api/rest/v1/inventory/devices (401)
```

## Possible Root Causes

1. **Token scope issue:**
   - Organization API token ≠ Firewall API token
   - May need separate token generation for firewall APIs
   - Token might need explicit firewall API scope

2. **API gateway restrictions:**
   - Gateway may require tenant/organization context header
   - May need to explicitly opt-in to firewall API access
   - Could be account-level API enablement required

3. **Missing request headers:**
   - Example URLs show `edge.us.cdo.cisco.com` but spec lists `api.us.security.cisco.com`
   - Possible mismatch between documented and actual endpoints
   - May require additional headers (X-CDO-Tenant, X-Org-ID, etc.)

4. **Account configuration:**
   - Firewall subscription active ✅ but API access not enabled
   - Firewall Manager UI access ≠ API access
   - May require explicit API enablement in tenant settings

## Recommended Next Steps

1. **Check Cisco SCC UI:**
   - Verify firewall API access is enabled
   - Check if there's an API enablement toggle
   - Review tenant settings for API restrictions

2. **Contact Cisco Support:**
   - Provide 400 error details and request IDs
   - Ask if firewall API requires separate token/credentials
   - Confirm API gateway routing is correct for your region

3. **Try different token:**
   - If organization/firewall tokens are separate, obtain firewall-specific token
   - Test if scope/audience needs to be different

4. **Test alternative endpoints:**
   - Try the CDO edge endpoints with proper authentication
   - Verify if manage domain requires different credentials

5. **Enable firewall API in UI:**
   - If there's an API enablement setting, explicitly enable it
   - This might provision the necessary gateway routes

## Implementation Status

**Skill Code:** ✅ Ready
- All methods implemented according to OpenAPI spec
- Endpoint structures correct per documentation
- Error handling in place

**Testing:** ❌ Blocked by 400 errors
- Cannot verify functionality without API access
- Once API access is enabled, skill should work immediately

## Files

- `firewall_openapi_1_17_0.yaml` - Full OpenAPI specification
- Implementation files:
  - `../claude/cisco_scc_firewall.py`
  - `../copilot/cisco_scc_firewall.py`
  - `../gemini/cisco_scc_firewall.js`
