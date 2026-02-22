const axios = require('axios');
require('dotenv').config();

class CiscoSCCFirewallManager {
  constructor(region = "us") {
    this.apiKeyId = process.env.CISCO_API_KEY_ID;
    this.accessToken = process.env.CISCO_ACCESS_TOKEN;
    
    if (!this.apiKeyId || !this.accessToken) {
      throw new Error("CISCO_API_KEY_ID and CISCO_ACCESS_TOKEN required in .env");
    }
    
    this.region = region;
    this.baseUrl = `https://api.${region}.security.cisco.com/firewall/v1`;
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        "Authorization": `Bearer ${this.accessToken}`,
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      timeout: 30000
    });
  }

  async makeRequest(method, endpoint, data = null, params = null) {
    try {
      const response = await this.client({
        method,
        url: endpoint,
        data,
        params
      });
      return response.data;
    } catch (error) {
      return {
        error: error.message,
        url: endpoint,
        method,
        statusCode: error.response?.status
      };
    }
  }

  // Inventory Management
  async listDevices(limit = 50, offset = 0) {
    // Note: Returns 400 if no devices provisioned or requires additional org permissions
    return this.makeRequest("GET", "/inventory/devices", null, { limit, offset });
  }

  async getDevice(deviceUid) {
    return this.makeRequest("GET", `/inventory/devices/${deviceUid}`);
  }

  async listManagers(query = null, limit = 50, offset = 0) {
    const params = { limit, offset };
    if (query) params.q = query;
    return this.makeRequest("GET", "/inventory/managers", null, params);
  }

  async getCDFMCManager() {
    // Returns domain UUID and other FMC details needed for policy queries
    // Endpoint structure: /cdfmc/api/fmc_config/v1/domain/{domainUUID}/...
    return this.makeRequest("GET", "/inventory/managers", null, { q: "deviceType:CDFMC" });
  }

  async listServices(limit = 50, offset = 0) {
    return this.makeRequest("GET", "/inventory/services", null, { limit, offset });
  }

  // Cloud-delivered FMC Operations
  async getCDFMCAccessPolicies(domainUid, limit = 50, offset = 0) {
    // Get all access policies from cdFMC
    // Args:
    //   domainUid: Domain UUID obtained from getCDFMCManager()
    //   limit: Results per page (default 50)
    //   offset: Pagination offset (default 0)
    // Endpoint: /cdfmc/api/fmc_config/v1/domain/{domainUUID}/policy/accesspolicies
    // Note: 400 error if domainUUID invalid or org lacks Firewall Manager subscription
    const endpoint = `/cdfmc/api/fmc_config/v1/domain/${domainUid}/policy/accesspolicies`;
    return this.makeRequest("GET", endpoint, null, { limit, offset });
  }

  async getCDFMCAccessPolicy(domainUid, policyId) {
    const endpoint = `/cdfmc/api/fmc_config/v1/domain/${domainUid}/policy/accesspolicies/${policyId}`;
    return this.makeRequest("GET", endpoint);
  }

  async getCDFMCAccessRules(domainUid, policyId, expanded = false) {
    const endpoint = `/cdfmc/api/fmc_config/v1/domain/${domainUid}/policy/accesspolicies/${policyId}/accessrules`;
    const params = { expanded: expanded ? "true" : "false" };
    return this.makeRequest("GET", endpoint, null, params);
  }

  async getCDFMCNetworkObjects(domainUid, limit = 50, offset = 0) {
    const endpoint = `/cdfmc/api/fmc_config/v1/domain/${domainUid}/object/networks`;
    return this.makeRequest("GET", endpoint, null, { limit, offset });
  }

  // Object Management
  async listObjects(objectType = null, limit = 50, offset = 0) {
    const params = { limit, offset };
    if (objectType) params.type = objectType;
    return this.makeRequest("GET", "/objects", null, params);
  }

  async getObject(objectUid) {
    return this.makeRequest("GET", `/objects/${objectUid}`);
  }

  // Deployment/Changes
  async deployConfig(deviceUid, configData) {
    return this.makeRequest("POST", `/inventory/devices/${deviceUid}/deploy`, configData);
  }

  // Monitoring
  async getDeviceHealth(deviceUid) {
    return this.makeRequest("GET", `/inventory/devices/${deviceUid}/health`);
  }

  async listTransactions(limit = 50, offset = 0) {
    return this.makeRequest("GET", "/transactions", null, { limit, offset });
  }

  async getTransaction(transactionId) {
    return this.makeRequest("GET", `/transactions/${transactionId}`);
  }

  // Search
  async search(query, resourceType = null) {
    const params = { q: query };
    if (resourceType) params.type = resourceType;
    return this.makeRequest("GET", "/search", null, params);
  }

  // Changelog
  async getChangelog(limit = 50, offset = 0) {
    return this.makeRequest("GET", "/changelog", null, { limit, offset });
  }
}

module.exports = { CiscoSCCFirewallManager };
