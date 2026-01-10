"""
Fetcher factory for selecting the appropriate manufacturer-specific fetcher.
Provides automatic fetcher selection based on brand name.
"""
import logging
from typing import Optional, Dict, Type

from .base import BaseSpecFetcher
from .cisco import CiscoFetcher
from .ubiquiti import UbiquitiFetcher
from .generic import GenericFetcher

logger = logging.getLogger(__name__)

# Lazy imports for manufacturer fetchers to avoid circular dependencies
_fetcher_cache: Dict[str, Type[BaseSpecFetcher]] = {}


def _load_fetcher_class(module_name: str, class_name: str) -> Optional[Type[BaseSpecFetcher]]:
    """Dynamically load a fetcher class."""
    try:
        import importlib
        module = importlib.import_module(f"app.fetchers.{module_name}")
        return getattr(module, class_name)
    except Exception as e:
        logger.warning(f"Failed to load {module_name}.{class_name}: {e}")
        return None


class SpecFetcherFactory:
    """
    Factory for creating manufacturer-specific spec fetchers.

    Automatically selects the appropriate fetcher based on brand name.
    Falls back to generic fetcher if no specific implementation exists.
    """

    # Manufacturer to fetcher mapping
    _FETCHER_MAP = {
        # Network Equipment
        "cisco": ("cisco", "CiscoFetcher"),
        "ubiquiti": ("ubiquiti", "UbiquitiFetcher"),
        "unifi": ("ubiquiti", "UbiquitiFetcher"),  # Ubiquiti brand alias

        # NAS and Storage
        "synology": ("synology", "SynologyFetcher"),

        # Servers and Compute
        "dell": ("dell", "DellFetcher"),
        "hp": ("hp", "HPFetcher"),
        "hpe": ("hp", "HPFetcher"),
        "hewlett packard": ("hp", "HPFetcher"),
        "hewlett-packard": ("hp", "HPFetcher"),

        # Consumer/Prosumer Networking
        "asus": ("asus", "ASUSFetcher"),
        "apple": ("apple", "AppleFetcher"),

        # Add more manufacturers here as fetchers are implemented
    }

    def __init__(self, cache_manager=None, rate_limiter=None):
        """
        Initialize factory with optional cache and rate limiter.

        Args:
            cache_manager: Cache manager for storing fetched specs
            rate_limiter: Rate limiter to prevent overwhelming manufacturer sites
        """
        self.cache_manager = cache_manager
        self.rate_limiter = rate_limiter
        self._fetchers: Dict[str, BaseSpecFetcher] = {}

    def get_fetcher(self, brand: str) -> BaseSpecFetcher:
        """
        Get the appropriate fetcher for a brand.

        Args:
            brand: Device brand/manufacturer name

        Returns:
            Manufacturer-specific fetcher or generic fetcher if no match
        """
        # Normalize brand name
        brand_key = brand.lower().strip()

        # Check if we've already instantiated this fetcher
        if brand_key in self._fetchers:
            return self._fetchers[brand_key]

        # Look up fetcher in map
        if brand_key in self._FETCHER_MAP:
            module_name, class_name = self._FETCHER_MAP[brand_key]

            # Load fetcher class
            if class_name not in _fetcher_cache:
                fetcher_class = _load_fetcher_class(module_name, class_name)
                if fetcher_class:
                    _fetcher_cache[class_name] = fetcher_class

            if class_name in _fetcher_cache:
                # Instantiate fetcher
                fetcher_class = _fetcher_cache[class_name]
                fetcher = fetcher_class(
                    cache_manager=self.cache_manager,
                    rate_limiter=self.rate_limiter
                )
                self._fetchers[brand_key] = fetcher
                logger.info(f"Using {class_name} for brand '{brand}'")
                return fetcher

        # Fall back to generic fetcher
        logger.info(f"No specific fetcher for '{brand}', using GenericFetcher")
        if "generic" not in self._fetchers:
            self._fetchers["generic"] = GenericFetcher(
                cache_manager=self.cache_manager,
                rate_limiter=self.rate_limiter
            )

        return self._fetchers["generic"]

    def get_supported_manufacturers(self) -> list[str]:
        """
        Get list of supported manufacturers.

        Returns:
            List of manufacturer names with dedicated fetchers
        """
        # Get unique manufacturers (accounting for aliases)
        manufacturers = set()
        for brand_key in self._FETCHER_MAP.keys():
            # Capitalize first letter of each word
            manufacturers.add(brand_key.title())

        return sorted(list(manufacturers))

    def has_specific_fetcher(self, brand: str) -> bool:
        """
        Check if a specific fetcher exists for the brand.

        Args:
            brand: Device brand/manufacturer name

        Returns:
            True if specific fetcher exists, False if would use generic
        """
        brand_key = brand.lower().strip()
        return brand_key in self._FETCHER_MAP

    async def close_all(self):
        """Close all instantiated fetchers."""
        for fetcher in self._fetchers.values():
            await fetcher.close()

        self._fetchers.clear()
        logger.info("All fetchers closed")


# Singleton factory instance (optional, for convenience)
_default_factory: Optional[SpecFetcherFactory] = None


def get_default_factory() -> SpecFetcherFactory:
    """
    Get the default singleton factory instance.

    Returns:
        Default SpecFetcherFactory instance
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = SpecFetcherFactory()
    return _default_factory


def reset_default_factory():
    """Reset the default factory (useful for testing)."""
    global _default_factory
    if _default_factory:
        import asyncio
        asyncio.create_task(_default_factory.close_all())
    _default_factory = None
