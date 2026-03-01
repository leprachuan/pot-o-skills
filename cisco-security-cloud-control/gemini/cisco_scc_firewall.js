const axios = require('axios');
require('dotenv').config();

function formatAsMarkdownTable(items, headers, keyMapping) {
  /**
   * Convert list of objects to markdown table format.
   * 
   * @param {Array} items - List of objects to format
   * @param {Array} headers - List of column header names
   * @param {Object} keyMapping - Maps header names to item keys
   * @returns {String} Markdown table
   */
  if (!items || items.length === 0) {
    return "No items found.";
  }
  
  // Build header row
  let table = "| " + headers.join(" | ") + " |\n";
  // Build separator row
  table += "|" + headers.map(() => "---").join("|") + "|\n";
  
  // Build data rows
  items.forEach((item, idx) => {
    const rowValues = headers.map((header) => {
      const key = keyMapping[header] || header.toLowerCase();
      if (key === "#") {
        return String(idx + 1);
      }
      return String(item[key] || "N/A");
    });
    table += "| " + rowValues.join(" | ") + " |\n";
  });
  
  return table;
}

class CiscoSCCFirewallManager {
  constructor(region = "us") {
    this.apiKeyId = process.env.CISCO_API_KEY_ID;
    this.accessToken = process.env.CISCO_ACCESS_TOKEN;
    this.cdfmcToken = process.env.CISCO_CDFMC_ACCESS_TOKEN;
    
    if (!this.apiKeyId || !this.accessToken) {
      throw new Error("CISCO_API_KEY_ID and CISCO_ACCESS_TOKEN required in .env");
    }
    
    this.region = region;
    this.baseUrl = `https://api.${region}.security.cisco.com/firewall/v1`;
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: this.getHeaders(),
      timeout: 30000
    });
  }

  getHeaders(useCdfmcToken = false) {
    const token = useCdfmcToken && this.cdfmcToken ? this.cdfmcToken : this.accessToken;
    return {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
      "Accept": "application/json"
    };
  }

  async makeRequest(method, endpoint, data = null, params = null, useCdfmcToken = false) {
    try {
      const response = await this.client({
        method,
        url: endpoint,
        data,
        params,
        headers: this.getHeaders(useCdfmcToken)
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

  async getCDFMCDomain() {
    // Get cloud-delivered FMC domain UUID
    // This endpoint retrieves the domain UUID needed for all cdFMC operations
    // Must be called first to get domain UUID for other policy/object queries
    //
    // Returns domain object with UUID used in:
    // - /cdfmc/api/fmc_config/v1/domain/{domainUUID}/policy/accesspolicies
    // - /cdfmc/api/fmc_config/v1/domain/{domainUUID}/object/networks
    // - etc.
    //
    // Endpoint: /cdfmc/api/fmc_platform/v1/info/domain
    return this.makeRequest("GET", "/cdfmc/api/fmc_platform/v1/info/domain", null, null, true);
  }
  

  async listServices(limit = 50, offset = 0) {
    return this.makeRequest("GET", "/inventory/services", null, { limit, offset });
  }

  // Cloud-delivered FMC Operations
  async getCDFMCAccessPolicies(domainUid, limit = 50, offset = 0) {
    // Get all access policies from cdFMC
    // Args:
    //   domainUid: Domain UUID obtained from getCDFMCDomain()
    //   limit: Results per page (default 50)
    //   offset: Pagination offset (default 0)
    // Endpoint: /cdfmc/api/fmc_config/v1/domain/{domainUUID}/policy/accesspolicies
    const endpoint = `/cdfmc/api/fmc_config/v1/domain/${domainUid}/policy/accesspolicies`;
    return this.makeRequest("GET", endpoint, null, { limit, offset }, true);
  }

  async getCDFMCAccessPolicy(domainUid, policyId) {
    const endpoint = `/cdfmc/api/fmc_config/v1/domain/${domainUid}/policy/accesspolicies/${policyId}`;
    return this.makeRequest("GET", endpoint, null, null, true);
  }

  async getCDFMCAccessRules(domainUid, policyId, expanded = false) {
    const endpoint = `/cdfmc/api/fmc_config/v1/domain/${domainUid}/policy/accesspolicies/${policyId}/accessrules`;
    const params = { expanded: expanded ? "true" : "false" };
    return this.makeRequest("GET", endpoint, null, params, true);
  }

  async getCDFMCNetworkObjects(domainUid, limit = 50, offset = 0) {
    const endpoint = `/cdfmc/api/fmc_config/v1/domain/${domainUid}/object/networks`;
    return this.makeRequest("GET", endpoint, null, { limit, offset }, true);
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
