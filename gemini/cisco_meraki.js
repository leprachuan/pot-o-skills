const axios = require('axios');
require('dotenv').config();

function formatAsMarkdownTable(items, headers, keyMapping) {
  /**
   * Convert list of objects to markdown table format.
   */
  if (!items || items.length === 0) {
    return "No items found.";
  }
  
  let table = "| " + headers.join(" | ") + " |\n";
  table += "|" + headers.map(() => "---").join("|") + "|\n";
  
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

class MerakiClient {
  constructor(apiKey = null) {
    /**
     * Initialize Meraki API client.
     * @param {string} apiKey - Meraki API key (uses MERAKI_API_KEY env var if not provided)
     */
    this.apiKey = apiKey || process.env.MERAKI_API_KEY;
    
    if (!this.apiKey) {
      throw new Error("MERAKI_API_KEY required in .env or as parameter");
    }
    
    this.baseUrl = "https://api.meraki.com/api/v1";
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: this.getHeaders(),
      timeout: 30000
    });
  }

  getHeaders() {
    return {
      "Authorization": `Bearer ${this.apiKey}`,
      "Content-Type": "application/json",
      "Accept": "application/json"
    };
  }

  async makeRequest(method, endpoint, data = null, params = null) {
    try {
      const response = await this.client({
        method,
        url: endpoint,
        data,
        params,
        headers: this.getHeaders()
      });
      return response.data;
    } catch (error) {
      throw new Error(`Meraki API request failed: ${error.message}`);
    }
  }

  // =====================================================================
  // Organization Operations
  // =====================================================================

  async listOrganizations() {
    /**
     * List all organizations the API key has access to.
     * @returns {Promise<Array>} List of organizations
     */
    return await this.makeRequest("GET", "/organizations");
  }

  async getOrganization(orgId) {
    /**
     * Get organization details.
     * @param {string} orgId - Organization ID
     * @returns {Promise<Object>} Organization details
     */
    return await this.makeRequest("GET", `/organizations/${orgId}`);
  }

  // =====================================================================
  // Networks Operations
  // =====================================================================

  async listNetworks(orgId) {
    /**
     * List all networks in an organization.
     * @param {string} orgId - Organization ID
     * @returns {Promise<Array>} List of networks
     */
    return await this.makeRequest("GET", `/organizations/${orgId}/networks`);
  }

  async getNetwork(networkId) {
    /**
     * Get network details.
     * @param {string} networkId - Network ID
     * @returns {Promise<Object>} Network details
     */
    return await this.makeRequest("GET", `/networks/${networkId}`);
  }

  // =====================================================================
  // Device Operations
  // =====================================================================

  async listDevices(networkId) {
    /**
     * List all devices in a network.
     * @param {string} networkId - Network ID
     * @returns {Promise<Array>} List of devices
     */
    return await this.makeRequest("GET", `/networks/${networkId}/devices`);
  }

  async getDevice(networkId, serial) {
    /**
     * Get device details.
     * @param {string} networkId - Network ID
     * @param {string} serial - Device serial number
     * @returns {Promise<Object>} Device details
     */
    return await this.makeRequest("GET", `/networks/${networkId}/devices/${serial}`);
  }

  async getDeviceStatus(networkId, serial) {
    /**
     * Get device status (online/offline/alerting).
     * @param {string} networkId - Network ID
     * @param {string} serial - Device serial number
     * @returns {Promise<Object>} Device status
     */
    return await this.makeRequest("GET", `/networks/${networkId}/devices/${serial}/status`);
  }

  // =====================================================================
  // Wireless (SSID) Operations
  // =====================================================================

  async listSSIDs(networkId) {
    /**
     * List all SSIDs in a network.
     * @param {string} networkId - Network ID
     * @returns {Promise<Array>} List of SSIDs
     */
    return await this.makeRequest("GET", `/networks/${networkId}/wireless/ssids`);
  }

  async getSSID(networkId, number) {
    /**
     * Get SSID details.
     * @param {string} networkId - Network ID
     * @param {number} number - SSID number (0-14)
     * @returns {Promise<Object>} SSID configuration
     */
    return await this.makeRequest("GET", `/networks/${networkId}/wireless/ssids/${number}`);
  }

  // =====================================================================
  // Switch Operations
  // =====================================================================

  async listSwitchPorts(networkId, serial) {
    /**
     * List all ports on a switch device.
     * @param {string} networkId - Network ID
     * @param {string} serial - Switch serial number
     * @returns {Promise<Array>} List of switch ports
     */
    return await this.makeRequest("GET", `/networks/${networkId}/devices/${serial}/switch/ports`);
  }

  async getSwitchPort(networkId, serial, portId) {
    /**
     * Get switch port details.
     * @param {string} networkId - Network ID
     * @param {string} serial - Switch serial number
     * @param {number} portId - Port number (1-based)
     * @returns {Promise<Object>} Switch port details
     */
    return await this.makeRequest("GET", `/networks/${networkId}/devices/${serial}/switch/ports/${portId}`);
  }

  // =====================================================================
  // Firewall Operations
  // =====================================================================

  async listFirewallRules(networkId) {
    /**
     * List firewall rules for a network.
     * @param {string} networkId - Network ID
     * @returns {Promise<Array>} List of firewall rules
     */
    return await this.makeRequest("GET", `/networks/${networkId}/firewallRules`);
  }

  async getFirewallSettings(networkId) {
    /**
     * Get firewall settings.
     * @param {string} networkId - Network ID
     * @returns {Promise<Object>} Firewall configuration
     */
    return await this.makeRequest("GET", `/networks/${networkId}/firewallSettings`);
  }

  // =====================================================================
  // Client Operations
  // =====================================================================

  async listNetworkClients(networkId, params = null) {
    /**
     * List all clients connected to a network.
     * @param {string} networkId - Network ID
     * @param {Object} params - Query parameters (e.g., t0, t1)
     * @returns {Promise<Array>} List of clients
     */
    return await this.makeRequest("GET", `/networks/${networkId}/clients`, null, params);
  }

  async getClient(networkId, clientId) {
    /**
     * Get client details.
     * @param {string} networkId - Network ID
     * @param {string} clientId - Client MAC address or ID
     * @returns {Promise<Object>} Client details
     */
    return await this.makeRequest("GET", `/networks/${networkId}/clients/${clientId}`);
  }
}

module.exports = { MerakiClient, formatAsMarkdownTable };
