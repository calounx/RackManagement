"""
Base abstract class for manufacturer-specific device specification fetchers.
Defines common interface and shared functionality for all fetchers.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import logging
import httpx
from app.config import settings
from app.models import ConfidenceLevel
from app.exceptions import ExternalServiceError, TimeoutError as HomeRackTimeoutError

logger = logging.getLogger(__name__)


class DeviceSpec:
    """
    Data class for device specifications fetched from external sources.
    """

    def __init__(
        self,
        brand: str,
        model: str,
        variant: Optional[str] = None,
        height_u: Optional[float] = None,
        width_type: Optional[str] = None,
        depth_mm: Optional[float] = None,
        weight_kg: Optional[float] = None,
        power_watts: Optional[float] = None,
        heat_output_btu: Optional[float] = None,
        airflow_pattern: Optional[str] = None,
        max_operating_temp_c: Optional[float] = None,
        typical_ports: Optional[Dict[str, int]] = None,
        mounting_type: Optional[str] = None,
        source_url: Optional[str] = None,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        **kwargs
    ):
        self.brand = brand
        self.model = model
        self.variant = variant
        self.height_u = height_u
        self.width_type = width_type
        self.depth_mm = depth_mm
        self.weight_kg = weight_kg
        self.power_watts = power_watts
        self.heat_output_btu = heat_output_btu
        self.airflow_pattern = airflow_pattern
        self.max_operating_temp_c = max_operating_temp_c
        self.typical_ports = typical_ports
        self.mounting_type = mounting_type
        self.source_url = source_url
        self.confidence = confidence
        self.extra_data = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "brand": self.brand,
            "model": self.model,
            "variant": self.variant,
            "height_u": self.height_u,
            "width_type": self.width_type,
            "depth_mm": self.depth_mm,
            "weight_kg": self.weight_kg,
            "power_watts": self.power_watts,
            "heat_output_btu": self.heat_output_btu,
            "airflow_pattern": self.airflow_pattern,
            "max_operating_temp_c": self.max_operating_temp_c,
            "typical_ports": self.typical_ports,
            "mounting_type": self.mounting_type,
            "source_url": self.source_url,
            "confidence": self.confidence,
            **self.extra_data
        }


class BaseSpecFetcher(ABC):
    """
    Abstract base class for device specification fetchers.

    Each manufacturer implementation should subclass this and implement
    the required abstract methods.
    """

    def __init__(self, cache_manager=None, rate_limiter=None):
        """
        Initialize fetcher with optional cache and rate limiter.

        Args:
            cache_manager: Cache manager instance for storing fetched specs
            rate_limiter: Rate limiter instance to prevent overwhelming manufacturer sites
        """
        self.cache_manager = cache_manager
        self.rate_limiter = rate_limiter
        self.timeout = settings.SPEC_FETCH_TIMEOUT
        self.user_agent = settings.SPEC_FETCH_USER_AGENT

        # HTTP client with reasonable defaults
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={"User-Agent": self.user_agent},
            follow_redirects=True
        )

    async def close(self):
        """Close HTTP client connections."""
        await self.client.aclose()

    @property
    @abstractmethod
    def manufacturer_name(self) -> str:
        """Return the manufacturer name this fetcher handles."""
        pass

    @abstractmethod
    async def fetch_spec(self, brand: str, model: str) -> Optional[DeviceSpec]:
        """
        Fetch device specification from manufacturer website.

        Args:
            brand: Device brand/manufacturer
            model: Device model number

        Returns:
            DeviceSpec object if found, None otherwise

        Raises:
            ExternalServiceError: If fetching fails
            TimeoutError: If request times out
        """
        pass

    @abstractmethod
    async def search_product(self, brand: str, model: str) -> List[str]:
        """
        Search for product URLs matching the brand/model.

        Args:
            brand: Device brand/manufacturer
            model: Device model number

        Returns:
            List of potential product page URLs
        """
        pass

    @abstractmethod
    def get_confidence_level(self, data_source: str) -> ConfidenceLevel:
        """
        Determine confidence level based on data source quality.

        Args:
            data_source: Source of the data (e.g., "pdf_datasheet", "html_spec_page")

        Returns:
            ConfidenceLevel enum value
        """
        pass

    async def _rate_limit(self):
        """Apply rate limiting if rate limiter is configured."""
        if self.rate_limiter:
            await self.rate_limiter.acquire(self.manufacturer_name.lower())

    async def _get_cached(self, brand: str, model: str) -> Optional[DeviceSpec]:
        """Get cached specification if available."""
        if self.cache_manager:
            return await self.cache_manager.get_cached_spec(brand, model)
        return None

    async def _cache_spec(self, brand: str, model: str, spec: DeviceSpec, success: bool = True):
        """Cache specification for future requests."""
        if self.cache_manager:
            await self.cache_manager.cache_spec(brand, model, spec.to_dict(), success)

    async def fetch_with_cache(self, brand: str, model: str) -> Optional[DeviceSpec]:
        """
        Fetch spec with caching and rate limiting.

        This is the main entry point for fetching specs. It handles:
        - Checking cache first
        - Rate limiting
        - Fetching from source
        - Caching results

        Args:
            brand: Device brand/manufacturer
            model: Device model number

        Returns:
            DeviceSpec if found, None otherwise
        """
        # Check cache first
        cached = await self._get_cached(brand, model)
        if cached:
            logger.info(f"Cache hit for {brand} {model}")
            return cached

        logger.info(f"Cache miss for {brand} {model}, fetching from source")

        # Apply rate limiting
        await self._rate_limit()

        # Fetch from source
        try:
            spec = await self.fetch_spec(brand, model)

            if spec:
                # Cache successful fetch
                await self._cache_spec(brand, model, spec, success=True)
                logger.info(f"Successfully fetched and cached {brand} {model}")
                return spec
            else:
                # Cache negative result to avoid repeated failed fetches
                await self._cache_spec(brand, model, None, success=False)
                logger.warning(f"No spec found for {brand} {model}")
                return None

        except Exception as e:
            logger.error(f"Error fetching spec for {brand} {model}: {str(e)}")
            # Don't cache errors - allow retry
            raise

    def _validate_spec(self, spec: DeviceSpec) -> tuple[bool, List[str]]:
        """
        Validate fetched specification data.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Required fields check
        if not spec.height_u:
            issues.append("Missing height")

        # Range validation
        if spec.height_u and (spec.height_u < 0.25 or spec.height_u > 50):
            issues.append(f"Invalid height: {spec.height_u}U (expected 0.25-50)")

        if spec.depth_mm and (spec.depth_mm < 100 or spec.depth_mm > 1500):
            issues.append(f"Invalid depth: {spec.depth_mm}mm (expected 100-1500)")

        if spec.weight_kg and (spec.weight_kg < 0.1 or spec.weight_kg > 500):
            issues.append(f"Invalid weight: {spec.weight_kg}kg (expected 0.1-500)")

        if spec.power_watts and (spec.power_watts < 0 or spec.power_watts > 10000):
            issues.append(f"Invalid power: {spec.power_watts}W (expected 0-10000)")

        # Consistency checks
        if spec.depth_mm and spec.depth_mm > 1200:
            issues.append(f"Depth {spec.depth_mm}mm exceeds typical rack limit (1200mm)")

        if spec.power_watts and spec.power_watts > 5000:
            issues.append(f"Unusually high power consumption: {spec.power_watts}W")

        is_valid = len(issues) < 3  # Allow some issues but not too many
        return is_valid, issues
