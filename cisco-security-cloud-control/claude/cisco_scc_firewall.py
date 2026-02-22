import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CiscoSCCFirewallManager:
    def __init__(self, region="us"):
        self.api_key_id = os.getenv('CISCO_API_KEY_ID')
        self.access_token = os.getenv('CISCO_ACCESS_TOKEN')
        
        if not all([self.api_key_id, self.access_token]):
            raise ValueError("CISCO_API_KEY_ID and CISCO_ACCESS_TOKEN required in .env")
        
        # Support multi-region deployment
        self.region = region
        self.base_url = f"https://api.{region}.security.cisco.com/firewall/v1"
        self.session = requests.Session()
        self._setup_headers()
    
    def _setup_headers(self):
        """Setup authorization headers"""
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to Cisco SCC Firewall API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params, timeout=30)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, json=data, params=params, timeout=30)
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
    
    # Inventory Management
    def list_devices(self, limit=50, offset=0):
        """List all devices in inventory
        
        Note: Returns 400 if no devices provisioned or requires additional org permissions
        """
        return self._make_request("GET", "/inventory/devices", 
                                params={"limit": limit, "offset": offset})
    
    def get_device(self, device_uid):
        """Get device details"""
        return self._make_request("GET", f"/inventory/devices/{device_uid}")
    
    def list_managers(self, query=None, limit=50, offset=0):
        """List device managers (FMC, etc.)"""
        params = {"limit": limit, "offset": offset}
        if query:
            params["q"] = query
        return self._make_request("GET", "/inventory/managers", params=params)
    
    def get_cdfmc_domain(self):
        """Get cloud-delivered FMC domain UUID
        
        This endpoint retrieves the domain UUID needed for all cdFMC operations.
        Must be called first to get domain UUID for other policy/object queries.
        
        Returns domain object with UUID used in:
        - /cdfmc/api/fmc_config/v1/domain/{domainUUID}/policy/accesspolicies
        - /cdfmc/api/fmc_config/v1/domain/{domainUUID}/object/networks
        - etc.
        
        Endpoint: /cdfmc/api/fmc_platform/v1/info/domain
        """
        endpoint = "/cdfmc/api/fmc_platform/v1/info/domain"
        return self._make_request("GET", endpoint)
    
    
    def list_services(self, limit=50, offset=0):
        """List cloud services"""
        return self._make_request("GET", "/inventory/services", 
                                params={"limit": limit, "offset": offset})
    
    # Cloud-delivered FMC Operations
    def get_cdfmc_access_policies(self, domain_uid, limit=50, offset=0):
        """Get all access policies from cdFMC
        
        Args:
            domain_uid: Domain UUID obtained from get_cdfmc_manager()
            limit: Results per page (default 50)
            offset: Pagination offset (default 0)
            
        Endpoint: /cdfmc/api/fmc_config/v1/domain/{domainUUID}/policy/accesspolicies
        Note: 400 error if domainUUID invalid or org lacks Firewall Manager subscription
        """
        endpoint = f"/cdfmc/api/fmc_config/v1/domain/{domain_uid}/policy/accesspolicies"
        return self._make_request("GET", endpoint, 
                                params={"limit": limit, "offset": offset})
    
    def get_cdfmc_access_policy(self, domain_uid, policy_id):
        """Get specific access policy from cdFMC"""
        endpoint = f"/cdfmc/api/fmc_config/v1/domain/{domain_uid}/policy/accesspolicies/{policy_id}"
        return self._make_request("GET", endpoint)
    
    def get_cdfmc_access_rules(self, domain_uid, policy_id, expanded=False):
        """Get access rules for a policy in cdFMC"""
        endpoint = f"/cdfmc/api/fmc_config/v1/domain/{domain_uid}/policy/accesspolicies/{policy_id}/accessrules"
        params = {"expanded": "true" if expanded else "false"}
        return self._make_request("GET", endpoint, params=params)
    
    def get_cdfmc_network_objects(self, domain_uid, limit=50, offset=0):
        """Get network objects from cdFMC"""
        endpoint = f"/cdfmc/api/fmc_config/v1/domain/{domain_uid}/object/networks"
        return self._make_request("GET", endpoint, 
                                params={"limit": limit, "offset": offset})
    
    # Object Management
    def list_objects(self, object_type=None, limit=50, offset=0):
        """List firewall policy objects"""
        params = {"limit": limit, "offset": offset}
        if object_type:
            params["type"] = object_type
        return self._make_request("GET", "/objects", params=params)
    
    def get_object(self, object_uid):
        """Get object details"""
        return self._make_request("GET", f"/objects/{object_uid}")
    
    # Deployment/Changes
    def deploy_config(self, device_uid, config_data):
        """Deploy configuration to device"""
        return self._make_request("POST", f"/inventory/devices/{device_uid}/deploy", 
                                data=config_data)
    
    # Monitoring
    def get_device_health(self, device_uid):
        """Get device health status"""
        return self._make_request("GET", f"/inventory/devices/{device_uid}/health")
    
    def list_transactions(self, limit=50, offset=0):
        """List asynchronous transactions"""
        return self._make_request("GET", "/transactions", 
                                params={"limit": limit, "offset": offset})
    
    def get_transaction(self, transaction_id):
        """Get transaction status"""
        return self._make_request("GET", f"/transactions/{transaction_id}")
    
    # Search
    def search(self, query, resource_type=None):
        """Search across Security Cloud Control"""
        params = {"q": query}
        if resource_type:
            params["type"] = resource_type
        return self._make_request("GET", "/search", params=params)
    
    # Changelog
    def get_changelog(self, limit=50, offset=0):
        """Get changelog of recent changes"""
        return self._make_request("GET", "/changelog", 
                                params={"limit": limit, "offset": offset})

__all__ = ['CiscoSCCFirewallManager']
