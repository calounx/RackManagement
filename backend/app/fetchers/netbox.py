"""
NetBox DCIM fetcher for device specifications.
Fetches device specifications from NetBox DCIM system instead of manufacturer websites.
"""
import logging
from typing import Optional, List

from .base import BaseSpecFetcher, DeviceSpec
from ..config import settings
from ..models import ConfidenceLevel
from ..integrations.netbox import NetBoxClient
from ..exceptions import DCIMConnectionError, DCIMAuthenticationError

logger = logging.getLogger(__name__)


class NetBoxFetcher(BaseSpecFetcher):
    """
    Fetcher that retrieves device specifications from NetBox DCIM.
    Uses NetBox as the authoritative source for device data.
    """

    def __init__(self, cache_manager=None, rate_limiter=None):
        """
        Initialize NetBox fetcher.

        Args:
            cache_manager: Cache manager for storing fetched specs
            rate_limiter: Rate limiter (not heavily needed for internal DCIM)

        Raises:
            ValueError: If NetBox integration is not enabled
        """
        super().__init__(cache_manager, rate_limiter)

        if not settings.NETBOX_ENABLED:
            raise ValueError("NetBox integration is not enabled. Set NETBOX_ENABLED=true.")

        try:
            self.client = NetBoxClient()
            logger.info("NetBox fetcher initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NetBox fetcher: {e}")
            raise

    @property
    def manufacturer_name(self) -> str:
        """Return manufacturer name (generic for NetBox)."""
        return "NetBox"

    async def fetch_spec(self, brand: str, model: str) -> Optional[DeviceSpec]:
        """
        Fetch device specification from NetBox.

        Args:
            brand: Device manufacturer/brand
            model: Device model

        Returns:
            DeviceSpec if found in NetBox, None otherwise

        Raises:
            DCIMConnectionError: If connection to NetBox fails
            DCIMAuthenticationError: If authentication fails
        """
        try:
            logger.info(f"Fetching spec from NetBox: {brand} {model}")

            # Fetch device type from NetBox
            device_type = await self.client.get_device_type(brand, model)

            if not device_type:
                logger.info(f"No device type found in NetBox for {brand} {model}")
                return None

            # Convert NetBox device type to DeviceSpec
            spec = DeviceSpec(
                brand=device_type.get("brand", brand),
                model=device_type.get("model", model),
                variant=None,
                height_u=device_type.get("height_u"),
                width_type="19\"",  # Standard rack width
                depth_mm=device_type.get("depth_mm"),
                weight_kg=device_type.get("weight_kg"),
                power_watts=device_type.get("power_watts"),
                heat_output_btu=device_type.get("heat_output_btu"),
                airflow_pattern=device_type.get("airflow_pattern"),
                max_operating_temp_c=device_type.get("max_operating_temp_c"),
                typical_ports=None,  # Can be extracted if needed
                mounting_type="rack",
                source_url=device_type.get("source_url"),
                confidence=ConfidenceLevel.HIGH  # NetBox is authoritative
            )

            logger.info(f"Successfully fetched spec from NetBox: {brand} {model}")
            return spec

        except DCIMAuthenticationError as e:
            logger.error(f"NetBox authentication failed: {e}")
            raise
        except DCIMConnectionError as e:
            logger.error(f"NetBox connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching from NetBox: {e}")
            return None

    async def search_product(self, brand: str, model: str) -> List[str]:
        """
        Generate NetBox device type URLs.

        Args:
            brand: Device brand
            model: Device model

        Returns:
            List with NetBox device type URL
        """
        if not settings.NETBOX_URL:
            return []

        # Generate search URL for NetBox device types
        base_url = settings.NETBOX_URL.rstrip('/')
        search_url = f"{base_url}/dcim/device-types/?q={brand}+{model}"

        return [search_url]

    def get_confidence_level(self, data_source: str = "netbox") -> ConfidenceLevel:
        """
        NetBox data is considered HIGH confidence (authoritative source).

        Args:
            data_source: Source of data (always NetBox for this fetcher)

        Returns:
            ConfidenceLevel.HIGH (NetBox is the source of truth)
        """
        return ConfidenceLevel.HIGH

    async def close(self):
        """Close HTTP client connections."""
        # NetBox client uses async context managers, no need to close
        await super().close()
