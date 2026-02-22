import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class CiscoSCCClient:
    def __init__(self):
        self.api_key_id = os.getenv('CISCO_API_KEY_ID')
        self.access_token = os.getenv('CISCO_ACCESS_TOKEN')
        self.refresh_token = os.getenv('CISCO_REFRESH_TOKEN')
        
        if not all([self.api_key_id, self.access_token]):
            raise ValueError("CISCO_API_KEY_ID and CISCO_ACCESS_TOKEN required in .env")
        
        self.base_url = "https://api.sxo.cisco.com/platform/api/v1"
        self.session = requests.Session()
        self._setup_headers()
    
    def _setup_headers(self):
        """Setup authorization headers"""
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to Cisco SCC API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params, timeout=30)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, params=params, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.text else {"status": "success"}
        
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "url": url,
                "method": method,
                "status_code": getattr(e.response, 'status_code', None)
            }
    
    # Organization Operations
    def list_organizations(self):
        """List all organizations"""
        return self._make_request("GET", "/orgs")
    
    def get_organization(self, org_id):
        """Get organization details"""
        return self._make_request("GET", f"/orgs/{org_id}")
    
    def create_organization(self, name, org_type="managed", description=None):
        """Create new organization"""
        payload = {
            "name": name,
            "type": org_type
        }
        if description:
            payload["description"] = description
        
        return self._make_request("POST", "/orgs", data=payload)
    
    def update_organization(self, org_id, **kwargs):
        """Update organization"""
        return self._make_request("PUT", f"/orgs/{org_id}", data=kwargs)
    
    def delete_organization(self, org_id):
        """Delete organization"""
        return self._make_request("DELETE", f"/orgs/{org_id}")
    
    # User Management
    def list_users(self, org_id):
        """List users in organization"""
        return self._make_request("GET", f"/orgs/{org_id}/users")
    
    def add_user(self, org_id, email, role="user"):
        """Add user to organization"""
        payload = {
            "email": email,
            "role": role
        }
        return self._make_request("POST", f"/orgs/{org_id}/users", data=payload)
    
    def remove_user(self, org_id, user_id):
        """Remove user from organization"""
        return self._make_request("DELETE", f"/orgs/{org_id}/users/{user_id}")
    
    def assign_role(self, org_id, user_id, role_id):
        """Assign role to user"""
        payload = {"role_id": role_id}
        return self._make_request("PUT", f"/orgs/{org_id}/users/{user_id}/role", data=payload)
    
    # Subscription Management
    def list_subscriptions(self, org_id):
        """List subscriptions for organization"""
        return self._make_request("GET", f"/orgs/{org_id}/subscriptions")
    
    def get_subscription(self, org_id, subscription_id):
        """Get subscription details"""
        return self._make_request("GET", f"/orgs/{org_id}/subscriptions/{subscription_id}")
    
    # Role Management
    def list_roles(self, org_id):
        """List available roles in organization"""
        return self._make_request("GET", f"/orgs/{org_id}/roles")
    
    def get_role(self, org_id, role_id):
        """Get role details and permissions"""
        return self._make_request("GET", f"/orgs/{org_id}/roles/{role_id}")

if __name__ == "__main__":
    import sys
    
    client = CiscoSCCClient()
    
    if len(sys.argv) < 2:
        print("Usage: python cisco_scc.py <action> [org_id] [user_id] [role_id]")
        print("Actions: list_organizations, list_users, list_subscriptions, etc.")
        sys.exit(1)
    
    action = sys.argv[1]
    org_id = sys.argv[2] if len(sys.argv) > 2 else None
    user_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Route to appropriate method
    if action == "list_organizations":
        result = client.list_organizations()
    elif action == "list_users" and org_id:
        result = client.list_users(org_id)
    elif action == "list_subscriptions" and org_id:
        result = client.list_subscriptions(org_id)
    elif action == "list_roles" and org_id:
        result = client.list_roles(org_id)
    else:
        result = {"error": f"Unknown action: {action}"}
    
    print(json.dumps(result, indent=2))
