const axios = require('axios');
require('dotenv').config();

class CiscoSCCClient {
  constructor() {
    this.apiKeyId = process.env.CISCO_API_KEY_ID;
    this.accessToken = process.env.CISCO_ACCESS_TOKEN;
    this.refreshToken = process.env.CISCO_REFRESH_TOKEN;
    
    if (!this.apiKeyId || !this.accessToken) {
      throw new Error("CISCO_API_KEY_ID and CISCO_ACCESS_TOKEN required in .env");
    }
    
    this.baseUrl = "https://api.security.cisco.com/v1";
    this.orgId = "d1dbb9db-29f4-4547-9de5-3b436015f0f0";
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        "Authorization": `Bearer ${this.accessToken}`,
        "Content-Type": "application/json"
      },
      timeout: 30000
    });
  }

  async makeRequest(method, endpoint, data = null, params = null) {
    try {
      const config = { params };
      const response = await this.client({
        method,
        url: endpoint,
        data,
        ...config
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

  // Organization Operations
  async listOrganizations() {
    return this.makeRequest("GET", "/organizations");
  }

  async getOrganization(orgId) {
    return this.makeRequest("GET", `/organizations/${orgId}`);
  }

  async createOrganization(name, orgType = "managed", description = null) {
    const payload = {
      name,
      type: orgType
    };
    if (description) {
      payload.description = description;
    }
    return this.makeRequest("POST", "/organizations", payload);
  }

  async updateOrganization(orgId, updates) {
    return this.makeRequest("PUT", `/organizations/${orgId}`, updates);
  }

  async deleteOrganization(orgId) {
    return this.makeRequest("DELETE", `/organizations/${orgId}`);
  }

  // Admin Groups
  async listAdminGroups(orgId) {
    return this.makeRequest("GET", `/organizations/${orgId}/adminGroups`);
  }

  // User Management
  async listUsers(orgId) {
    return this.makeRequest("GET", `/organizations/${orgId}/users`);
  }

  async addUser(orgId, email, role = "user") {
    const payload = { email, role };
    return this.makeRequest("POST", `/organizations/${orgId}/users`, payload);
  }

  async removeUser(orgId, userId) {
    return this.makeRequest("DELETE", `/organizations/${orgId}/users/${userId}`);
  }

  async assignRole(orgId, userId, roleId) {
    const payload = { role_id: roleId };
    return this.makeRequest("PUT", `/organizations/${orgId}/users/${userId}/role`, payload);
  }

  // Subscription Management
  async listSubscriptions(orgId) {
    return this.makeRequest("GET", `/organizations/${orgId}/subscriptions`);
  }

  async getSubscription(orgId, subscriptionId) {
    return this.makeRequest("GET", `/organizations/${orgId}/subscriptions/${subscriptionId}`);
  }

  // Role Management
  async listRoles(orgId) {
    return this.makeRequest("GET", `/organizations/${orgId}/roles`);
  }

  async getRole(orgId, roleId) {
    return this.makeRequest("GET", `/organizations/${orgId}/roles/${roleId}`);
  }
}

module.exports = { CiscoSCCClient };
