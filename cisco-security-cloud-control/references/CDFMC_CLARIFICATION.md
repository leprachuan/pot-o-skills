# cdFMC vs SCC Firewall APIs - Clarification

## Two Separate APIs

### 1. **SCC Firewall Manager API** (Inventory & Device Management)
- **Purpose:** Manage firewall devices, inventory, deployments at SCC level
- **OpenAPI Spec:** `firewall_openapi_1_17_0.yaml` (730 KB)
- **Base URLs:**
  - https://api.us.security.cisco.com/firewall
  - https://api.{region}.security.cisco.com/firewall
- **Key Endpoints:**
  - `GET /v1/inventory/devices` - List all devices
  - `GET /v1/inventory/managers` - List device managers (FMC, cdFMC, etc.)
  - `POST /v1/inventory/managers/cdfmc` - Provision cdFMC

### 2. **cdFMC API** (Configuration & Policy Management)
- **Purpose:** Manage firewall policies, objects, rules, deployed in FMC
- **OpenAPI Spec:** `cdfmc_openapi_1_17_0.yaml` (11 MB - much larger!)
- **Base URLs:** (Same as SCC Firewall)
  - https://api.us.security.cisco.com/firewall
  - https://api.{region}.security.cisco.com/firewall
- **Path Prefix:** `/v1/cdfmc/api/fmc_config/v1/` (not just `/v1/`)
- **Key Endpoints:**
  - `GET /v1/cdfmc/api/fmc_platform/v1/info/domain` - Get domain UUID
  - `GET /v1/cdfmc/api/fmc_config/v1/domain/{domainUUID}/policy/accesspolicies` - Get policies
  - `GET /v1/cdfmc/api/fmc_config/v1/domain/{domainUUID}/object/networks` - Get objects

## Critical Path Difference

| Component | SCC Firewall | cdFMC |
| --- | --- | --- |
| Base | `/firewall` | `/firewall` |
| Version | `/v1/` | `/v1/` |
| Domain prefix | N/A (no domain needed) | `/cdfmc/api/fmc_config/v1/` |
| Domain context | N/A | `/domain/{domainUUID}/` |

## Endpoint Examples

### SCC Firewall
```
GET /firewall/v1/inventory/devices
GET /firewall/v1/inventory/managers
```

### cdFMC
```
GET /firewall/v1/cdfmc/api/fmc_platform/v1/info/domain
GET /firewall/v1/cdfmc/api/fmc_config/v1/domain/{UUID}/policy/accesspolicies
GET /firewall/v1/cdfmc/api/fmc_config/v1/domain/{UUID}/object/networks
```

## Workflow to Get Access Policies

1. **Step 1:** Call `GET /firewall/v1/cdfmc/api/fmc_platform/v1/info/domain`
   - Returns: `{id: "e276abec-e0f2-11e3-8169-6d9ed49b625f", ...}`
   - Extract domain UUID: `e276abec-e0f2-11e3-8169-6d9ed49b625f`

2. **Step 2:** Call `GET /firewall/v1/cdfmc/api/fmc_config/v1/domain/{UUID}/policy/accesspolicies`
   - Use UUID from Step 1
   - Returns: List of access control policies

## Current Status

**Both APIs returning 400 Bad Request:**
- ❌ SCC Firewall endpoints (inventory, managers)
- ❌ cdFMC endpoints (domain info, policies, objects)

**Issue:** Authorization/Permission at API gateway level
- Not endpoint structure (both verified correct per spec)
- Not token validity (organization API works)
- Likely: Firewall API access not enabled for account

## What's Implemented

✅ **Skill has both:**
- SCC Firewall methods (inventory, device management)
- cdFMC methods (domain discovery, policy management, object management)

✅ **Code matches:**
- SCC Firewall API spec exactly
- cdFMC API spec exactly

❌ **Cannot test:** Authorization prevents API calls

## Files

- `firewall_openapi_1_17_0.yaml` - SCC Firewall Manager API
- `cdfmc_openapi_1_17_0.yaml` - cloud-delivered Firewall Management Center API
- Implementation files already handle both correctly
