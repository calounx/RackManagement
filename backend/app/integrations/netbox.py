"""
NetBox DCIM integration client.
Provides methods to fetch device specifications and rack layouts from NetBox.
"""
import httpx
import logging
from typing import List, Optional, Dict, Any

from ..config import settings
from ..exceptions import DCIMConnectionError, DCIMAuthenticationError, DCIMNotFoundError
from .dcim_base import BaseDCIMClient

logger = logging.getLogger(__name__)


class NetBoxClient(BaseDCIMClient):
    """NetBox DCIM integration client."""

    def __init__(self):
        if not settings.NETBOX_ENABLED:
            raise ValueError("NetBox integration is not enabled. Set NETBOX_ENABLED=true in environment.")

        if not settings.NETBOX_URL:
            raise ValueError("NETBOX_URL is required when NetBox integration is enabled.")

        if not settings.NETBOX_TOKEN:
            raise ValueError("NETBOX_TOKEN is required when NetBox integration is enabled.")

        self.base_url = settings.NETBOX_URL.rstrip('/')
        self.token = settings.NETBOX_TOKEN
        self.timeout = settings.NETBOX_TIMEOUT
        self.verify_ssl = settings.NETBOX_VERIFY_SSL

        self.headers = {
            "Authorization": f"Token {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to NetBox API with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (e.g., "/api/dcim/device-types/")
            **kwargs: Additional arguments for httpx request

        Returns:
            Response JSON data

        Raises:
            DCIMAuthenticationError: If authentication fails
            DCIMNotFoundError: If resource not found
            DCIMConnectionError: For other connection errors
        """
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
            try:
                logger.debug(f"NetBox API request: {method} {url}")
                response = await client.request(method, url, headers=self.headers, **kwargs)

                if response.status_code == 401:
                    raise DCIMAuthenticationError("NetBox authentication failed. Check NETBOX_TOKEN.")
                elif response.status_code == 404:
                    raise DCIMNotFoundError(f"NetBox resource not found: {endpoint}")
                elif response.status_code >= 400:
                    error_detail = response.text[:200]  # Limit error message length
                    raise DCIMConnectionError(f"NetBox API error {response.status_code}: {error_detail}")

                return response.json()

            except httpx.TimeoutException:
                raise DCIMConnectionError(f"NetBox request timeout after {self.timeout}s")
            except httpx.RequestError as e:
                raise DCIMConnectionError(f"NetBox connection error: {str(e)}")

    async def get_device_type(self, manufacturer: str, model: str) -> Optional[Dict[str, Any]]:
        """
        Fetch device type from NetBox.

        Endpoint: GET /api/dcim/device-types/?manufacturer={}&model={}

        Args:
            manufacturer: Manufacturer name
            model: Model name

        Returns:
            Device type dictionary with specifications or None if not found
        """
        try:
            params = {
                "manufacturer": manufacturer,
                "model": model
            }

            response = await self._request("GET", "/api/dcim/device-types/", params=params)
            results = response.get("results", [])

            if not results:
                logger.info(f"No device type found for {manufacturer} {model}")
                return None

            device_type = results[0]  # Return first match
            logger.info(f"Found device type: {manufacturer} {model}")

            # Map NetBox device type to HomeRack format
            return self._map_device_type(device_type)

        except (DCIMAuthenticationError, DCIMConnectionError) as e:
            logger.error(f"Failed to fetch device type from NetBox: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching device type: {e}")
            return None

    def _map_device_type(self, netbox_device_type: Dict) -> Dict[str, Any]:
        """
        Map NetBox device type schema to HomeRack DeviceSpec format.

        Args:
            netbox_device_type: Raw device type data from NetBox

        Returns:
            Mapped device specification dictionary
        """
        manufacturer_data = netbox_device_type.get("manufacturer", {})
        manufacturer_name = manufacturer_data.get("name", "Unknown") if isinstance(manufacturer_data, dict) else str(manufacturer_data)

        return {
            "id": netbox_device_type.get("id"),
            "brand": manufacturer_name,
            "model": netbox_device_type.get("model", "Unknown"),
            "height_u": float(netbox_device_type.get("u_height", 1)),
            "depth_mm": self._extract_depth(netbox_device_type),
            "weight_kg": self._extract_weight(netbox_device_type),
            "power_watts": self._extract_power(netbox_device_type),
            "heat_output_btu": self._calculate_heat_output(self._extract_power(netbox_device_type)),
            "source": "netbox",
            "confidence": "high",
            "source_url": f"{self.base_url}/dcim/device-types/{netbox_device_type.get('id')}/"
        }

    def _extract_depth(self, device_type: Dict) -> Optional[float]:
        """Extract depth in millimeters from NetBox device type."""
        # NetBox stores depth in millimeters in custom fields or comments
        depth = device_type.get("depth_mm")
        if depth:
            return float(depth)

        # Try custom fields
        custom_fields = device_type.get("custom_fields", {})
        if "depth_mm" in custom_fields:
            return float(custom_fields["depth_mm"])

        return None

    def _extract_weight(self, device_type: Dict) -> Optional[float]:
        """Extract weight in kilograms from NetBox device type."""
        weight = device_type.get("weight")
        if weight:
            # NetBox stores weight in grams
            return float(weight) / 1000.0

        # Try custom fields
        custom_fields = device_type.get("custom_fields", {})
        if "weight_kg" in custom_fields:
            return float(custom_fields["weight_kg"])

        return None

    def _extract_power(self, device_type: Dict) -> Optional[float]:
        """Extract power consumption in watts from NetBox device type."""
        # Check for power port data
        power_ports = device_type.get("power_ports", [])
        if power_ports:
            total_power = sum(port.get("allocated_draw", 0) for port in power_ports)
            if total_power > 0:
                return float(total_power)

        # Try custom fields
        custom_fields = device_type.get("custom_fields", {})
        if "power_watts" in custom_fields:
            return float(custom_fields["power_watts"])

        return None

    def _calculate_heat_output(self, power_watts: Optional[float]) -> Optional[float]:
        """Calculate heat output in BTU/hr from power consumption."""
        if power_watts:
            # 1 watt = 3.412 BTU/hr
            return power_watts * 3.412
        return None

    async def get_rack(self, rack_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch rack from NetBox.

        Endpoint: GET /api/dcim/racks/?name={}

        Args:
            rack_name: Name of the rack

        Returns:
            Rack dictionary with specifications or None if not found
        """
        try:
            params = {"name": rack_name}
            response = await self._request("GET", "/api/dcim/racks/", params=params)
            results = response.get("results", [])

            if not results:
                logger.info(f"No rack found with name: {rack_name}")
                return None

            rack = results[0]  # Return first match
            logger.info(f"Found rack: {rack_name}")

            return self._map_rack(rack)

        except (DCIMAuthenticationError, DCIMConnectionError) as e:
            logger.error(f"Failed to fetch rack from NetBox: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching rack: {e}")
            return None

    def _map_rack(self, netbox_rack: Dict) -> Dict[str, Any]:
        """
        Map NetBox rack schema to HomeRack Rack format.

        Args:
            netbox_rack: Raw rack data from NetBox

        Returns:
            Mapped rack dictionary
        """
        site_data = netbox_rack.get("site", {})
        site_name = site_data.get("name", "Unknown") if isinstance(site_data, dict) else str(site_data)

        location_data = netbox_rack.get("location", {})
        location_name = location_data.get("name", "") if isinstance(location_data, dict) else str(location_data)

        full_location = f"{site_name}" + (f" / {location_name}" if location_name else "")

        return {
            "id": netbox_rack.get("id"),
            "name": netbox_rack.get("name"),
            "location": full_location,
            "total_height_u": int(netbox_rack.get("u_height", 42)),
            "width_inches": netbox_rack.get("width", 19),  # NetBox uses rack width enum
            "depth_mm": self._extract_rack_depth(netbox_rack),
            "max_power_watts": self._extract_rack_power(netbox_rack),
            "max_weight_kg": self._extract_rack_weight(netbox_rack),
            "cooling_type": self._extract_cooling_type(netbox_rack),
            "cooling_capacity_btu": self._extract_cooling_capacity(netbox_rack)
        }

    def _extract_rack_depth(self, rack: Dict) -> Optional[float]:
        """Extract rack depth from NetBox."""
        custom_fields = rack.get("custom_fields", {})
        return custom_fields.get("depth_mm", 1000)  # Default to 1000mm

    def _extract_rack_power(self, rack: Dict) -> Optional[float]:
        """Extract rack max power from NetBox."""
        custom_fields = rack.get("custom_fields", {})
        return custom_fields.get("max_power_watts", 5000)  # Default to 5000W

    def _extract_rack_weight(self, rack: Dict) -> Optional[float]:
        """Extract rack max weight from NetBox."""
        custom_fields = rack.get("custom_fields", {})
        return custom_fields.get("max_weight_kg", 500)  # Default to 500kg

    def _extract_cooling_type(self, rack: Dict) -> Optional[str]:
        """Extract cooling type from NetBox."""
        custom_fields = rack.get("custom_fields", {})
        return custom_fields.get("cooling_type", "Room cooling")

    def _extract_cooling_capacity(self, rack: Dict) -> Optional[float]:
        """Extract cooling capacity from NetBox."""
        custom_fields = rack.get("custom_fields", {})
        return custom_fields.get("cooling_capacity_btu", 10000)  # Default to 10000 BTU/hr

    async def list_devices_in_rack(self, rack_id: str) -> List[Dict[str, Any]]:
        """
        List devices in a NetBox rack.

        Endpoint: GET /api/dcim/devices/?rack_id={}

        Args:
            rack_id: NetBox rack ID

        Returns:
            List of device dictionaries
        """
        try:
            params = {"rack_id": rack_id}
            response = await self._request("GET", "/api/dcim/devices/", params=params)

            devices = []
            for device_data in response.get("results", []):
                mapped_device = self._map_device(device_data)
                devices.append(mapped_device)

            logger.info(f"Found {len(devices)} devices in rack {rack_id}")
            return devices

        except (DCIMAuthenticationError, DCIMConnectionError) as e:
            logger.error(f"Failed to list devices from NetBox: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing devices: {e}")
            return []

    def _map_device(self, netbox_device: Dict) -> Dict[str, Any]:
        """
        Map NetBox device schema to HomeRack Device format.

        Args:
            netbox_device: Raw device data from NetBox

        Returns:
            Mapped device dictionary
        """
        device_type = netbox_device.get("device_type", {})
        manufacturer = device_type.get("manufacturer", {}) if isinstance(device_type, dict) else {}

        return {
            "id": netbox_device.get("id"),
            "name": netbox_device.get("name"),
            "brand": manufacturer.get("name", "Unknown") if isinstance(manufacturer, dict) else str(manufacturer),
            "model": device_type.get("model", "Unknown") if isinstance(device_type, dict) else str(device_type),
            "serial": netbox_device.get("serial"),
            "position": netbox_device.get("position"),  # U position in rack
            "face": netbox_device.get("face")  # Front or rear
        }

    async def health_check(self) -> bool:
        """
        Verify NetBox connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            await self._request("GET", "/api/")
            logger.info("NetBox health check successful")
            return True
        except Exception as e:
            logger.error(f"NetBox health check failed: {e}")
            return False
