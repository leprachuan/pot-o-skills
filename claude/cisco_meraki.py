import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def format_as_markdown_table(items, headers, key_mapping):
    """Convert list of dictionaries to markdown table format.
    
    Args:
        items: List of dictionaries to format
        headers: List of column header names
        key_mapping: Dict mapping header names to item keys (e.g., {'Name': 'name', 'ID': 'id'})
    
    Returns:
        String with markdown table
    """
    if not items:
        return "No items found."
    
    # Build header row
    table = "| " + " | ".join(headers) + " |\n"
    # Build separator row
    table += "|" + "|".join(["---"] * len(headers)) + "|\n"
    
    # Build data rows
    for idx, item in enumerate(items, 1):
        row_values = []
        for header in headers:
            key = key_mapping.get(header, header.lower())
            if key == "#":
                row_values.append(str(idx))
            else:
                value = item.get(key, "N/A")
                row_values.append(str(value))
        table += "| " + " | ".join(row_values) + " |\n"
    
    return table

class MerakiClient:
    def __init__(self, api_key=None):
        """Initialize Meraki API client.
        
        Args:
            api_key: Meraki API key (uses MERAKI_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv('MERAKI_API_KEY')
        
        if not self.api_key:
            raise ValueError("MERAKI_API_KEY required in .env or as parameter")
        
        self.base_url = "https://api.meraki.com/api/v1"
        self.session = requests.Session()
        self._setup_headers()
    
    def _setup_headers(self):
        """Setup authorization headers"""
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to Meraki API"""
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
            raise Exception(f"Meraki API request failed: {str(e)}")
    
    # =====================================================================
    # Organization Operations
    # =====================================================================
    
    def list_organizations(self):
        """List all organizations the API key has access to.
        
        Returns:
            List of organizations with id, name, url
        """
        return self._make_request("GET", "/organizations")
    
    def get_organization(self, org_id):
        """Get organization details.
        
        Args:
            org_id: Organization ID
        
        Returns:
            Organization details
        """
        return self._make_request("GET", f"/organizations/{org_id}")
    
    # =====================================================================
    # Networks Operations
    # =====================================================================
    
    def list_networks(self, org_id):
        """List all networks in an organization.
        
        Args:
            org_id: Organization ID
        
        Returns:
            List of networks with id, name, type, tags
        """
        return self._make_request("GET", f"/organizations/{org_id}/networks")
    
    def get_network(self, network_id):
        """Get network details.
        
        Args:
            network_id: Network ID
        
        Returns:
            Network details
        """
        return self._make_request("GET", f"/networks/{network_id}")
    
    # =====================================================================
    # Device Operations
    # =====================================================================
    
    def list_devices(self, network_id):
        """List all devices in a network.
        
        Args:
            network_id: Network ID
        
        Returns:
            List of devices with serial, model, name, status
        """
        return self._make_request("GET", f"/networks/{network_id}/devices")
    
    def get_device(self, network_id, serial):
        """Get device details.
        
        Args:
            network_id: Network ID
            serial: Device serial number
        
        Returns:
            Device details
        """
        return self._make_request("GET", f"/networks/{network_id}/devices/{serial}")
    
    def get_device_status(self, network_id, serial):
        """Get device status (online/offline/alerting).
        
        Args:
            network_id: Network ID
            serial: Device serial number
        
        Returns:
            Device status details
        """
        return self._make_request("GET", f"/networks/{network_id}/devices/{serial}/status")
    
    # =====================================================================
    # Wireless (SSID) Operations
    # =====================================================================
    
    def list_ssids(self, network_id):
        """List all SSIDs in a network.
        
        Args:
            network_id: Network ID
        
        Returns:
            List of SSIDs with number, name, enabled, security
        """
        return self._make_request("GET", f"/networks/{network_id}/wireless/ssids")
    
    def get_ssid(self, network_id, number):
        """Get SSID details.
        
        Args:
            network_id: Network ID
            number: SSID number (0-14)
        
        Returns:
            SSID configuration
        """
        return self._make_request("GET", f"/networks/{network_id}/wireless/ssids/{number}")
    
    # =====================================================================
    # Switch Operations
    # =====================================================================
    
    def list_switch_ports(self, network_id, serial):
        """List all ports on a switch device.
        
        Args:
            network_id: Network ID
            serial: Switch serial number
        
        Returns:
            List of switch ports with status, vlan, name
        """
        return self._make_request("GET", f"/networks/{network_id}/devices/{serial}/switch/ports")
    
    def get_switch_port(self, network_id, serial, port_id):
        """Get switch port details.
        
        Args:
            network_id: Network ID
            serial: Switch serial number
            port_id: Port number (1-based)
        
        Returns:
            Switch port details
        """
        return self._make_request("GET", f"/networks/{network_id}/devices/{serial}/switch/ports/{port_id}")
    
    # =====================================================================
    # Firewall Operations
    # =====================================================================
    
    def list_firewall_rules(self, network_id):
        """List firewall rules for a network.
        
        Args:
            network_id: Network ID
        
        Returns:
            List of firewall rules with policy, protocol, src/dst
        """
        return self._make_request("GET", f"/networks/{network_id}/firewallRules")
    
    def get_firewall_settings(self, network_id):
        """Get firewall settings.
        
        Args:
            network_id: Network ID
        
        Returns:
            Firewall configuration
        """
        return self._make_request("GET", f"/networks/{network_id}/firewallSettings")
    
    # =====================================================================
    # Client Operations
    # =====================================================================
    
    def list_network_clients(self, network_id, params=None):
        """List all clients connected to a network.
        
        Args:
            network_id: Network ID
            params: Query parameters (e.g., t0, t1 for time range)
        
        Returns:
            List of clients with mac, ip, os, usage
        """
        return self._make_request("GET", f"/networks/{network_id}/clients", params=params)
    
    def get_client(self, network_id, client_id):
        """Get client details.
        
        Args:
            network_id: Network ID
            client_id: Client MAC address or ID
        
        Returns:
            Client details with history, usage, devices
        """
        return self._make_request("GET", f"/networks/{network_id}/clients/{client_id}")
