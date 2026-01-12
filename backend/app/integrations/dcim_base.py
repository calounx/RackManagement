"""
Abstract base class for DCIM system integrations.
Provides a common interface for different DCIM systems (NetBox, RackTables, etc.)
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class BaseDCIMClient(ABC):
    """Abstract base class for DCIM system integrations."""

    @abstractmethod
    async def get_device_type(self, manufacturer: str, model: str) -> Optional[Dict[str, Any]]:
        """
        Fetch device specification from DCIM.

        Args:
            manufacturer: Device manufacturer/brand name
            model: Device model name

        Returns:
            Dictionary with device type information or None if not found
        """
        pass

    @abstractmethod
    async def get_rack(self, rack_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch rack details from DCIM.

        Args:
            rack_name: Name of the rack to fetch

        Returns:
            Dictionary with rack information or None if not found
        """
        pass

    @abstractmethod
    async def list_devices_in_rack(self, rack_id: str) -> List[Dict[str, Any]]:
        """
        List all devices positioned in a rack.

        Args:
            rack_id: ID of the rack in the DCIM system

        Returns:
            List of device dictionaries
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verify connection to DCIM system.

        Returns:
            True if connection successful, False otherwise
        """
        pass
