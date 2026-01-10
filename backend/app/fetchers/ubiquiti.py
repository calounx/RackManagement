"""
Ubiquiti-specific device specification fetcher.
Fetches specs from ui.com product pages.
"""
import logging
from typing import Optional, List
import json
from bs4 import BeautifulSoup

from .base import BaseSpecFetcher, DeviceSpec
from ..models import ConfidenceLevel
from ..parsers.base import HTMLParser
from ..exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class UbiquitiFetcher(BaseSpecFetcher):
    """Fetcher for Ubiquiti network equipment specifications."""

    @property
    def manufacturer_name(self) -> str:
        return "Ubiquiti"

    async def search_product(self, brand: str, model: str) -> List[str]:
        """
        Search for Ubiquiti product pages.

        Ubiquiti URLs:
        - https://ui.com/switching/comparison?product={model}
        - https://store.ui.com/collections/unifi-network-switching/{model}
        """
        urls = []

        # Clean model number
        clean_model = model.replace(" ", "-").lower()

        # Product comparison page (best for structured data)
        urls.append(f"https://ui.com/switching/comparison?product={clean_model}")

        # Store page
        urls.append(f"https://store.ui.com/products/{clean_model}")

        # Alternative: search by model in main products page
        urls.append(f"https://ui.com/switching")

        return urls

    async def fetch_spec(self, brand: str, model: str) -> Optional[DeviceSpec]:
        """
        Fetch Ubiquiti device specification.

        Ubiquiti has well-structured HTML pages with JSON-LD data.
        Strategy:
        1. Try comparison page (has structured product data)
        2. Parse JSON-LD structured data
        3. Fall back to HTML table parsing
        """
        try:
            urls = await self.search_product(brand, model)

            for url in urls:
                try:
                    response = await self.client.get(url)

                    if response.status_code == 200:
                        # Try parsing structured data first
                        spec = await self._fetch_from_structured_data(response.content, url, brand, model)
                        if spec:
                            return spec

                        # Fall back to HTML parsing
                        spec = await self._fetch_from_html(response.content, url, brand, model)
                        if spec:
                            return spec

                except Exception as e:
                    logger.warning(f"Failed to fetch from {url}: {e}")
                    continue

            logger.warning(f"No Ubiquiti specs found for {brand} {model}")
            return None

        except Exception as e:
            logger.error(f"Error fetching Ubiquiti spec for {brand} {model}: {e}")
            raise ExternalServiceError(
                service="Ubiquiti",
                message=f"Failed to fetch specification: {str(e)}"
            )

    async def _fetch_from_structured_data(self, html_content: bytes, url: str, brand: str, model: str) -> Optional[DeviceSpec]:
        """Extract specs from JSON-LD structured data."""
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # Find JSON-LD script tags
            scripts = soup.find_all('script', type='application/ld+json')

            for script in scripts:
                try:
                    data = json.loads(script.string)

                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        # Extract product specs
                        specs_data = self._parse_product_json(data)

                        if specs_data:
                            spec = DeviceSpec(
                                brand=brand,
                                model=model,
                                source_url=url,
                                confidence=ConfidenceLevel.HIGH,  # Structured data is reliable
                                **specs_data
                            )

                            is_valid, issues = self._validate_spec(spec)
                            if is_valid:
                                return spec

                except Exception as e:
                    logger.warning(f"Failed to parse JSON-LD: {e}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Failed to parse Ubiquiti structured data: {e}")
            return None

    def _parse_product_json(self, data: dict) -> dict:
        """Parse Product schema JSON-LD."""
        specs = {}

        # Basic info
        if 'name' in data:
            specs['model'] = data['name']

        # Look for additionalProperty or offers details
        if 'additionalProperty' in data:
            for prop in data['additionalProperty']:
                name = prop.get('name', '').lower()
                value = prop.get('value')

                if 'height' in name or 'rack' in name:
                    specs['height_u'] = self._parse_rack_units(str(value))
                elif 'depth' in name:
                    specs['depth_mm'] = self._parse_depth(str(value))
                elif 'weight' in name:
                    specs['weight_kg'] = self._parse_weight(str(value))
                elif 'power' in name or 'wattage' in name:
                    specs['power_watts'] = self._parse_power(str(value))

        return specs

    async def _fetch_from_html(self, html_content: bytes, url: str, brand: str, model: str) -> Optional[DeviceSpec]:
        """Parse HTML specification tables."""
        try:
            parser = HTMLParser()
            specs_data = await parser.parse(html_content, "text/html")

            if not specs_data:
                return None

            spec = DeviceSpec(
                brand=brand,
                model=model,
                source_url=url,
                confidence=ConfidenceLevel.HIGH,  # Ubiquiti HTML is structured
                **specs_data
            )

            is_valid, issues = self._validate_spec(spec)
            if not is_valid:
                logger.warning(f"Ubiquiti HTML spec validation failed: {issues}")
                spec.confidence = ConfidenceLevel.MEDIUM

            return spec

        except Exception as e:
            logger.error(f"Failed to parse Ubiquiti HTML: {e}")
            return None

    def get_confidence_level(self, data_source: str) -> ConfidenceLevel:
        """Ubiquiti has consistently high-quality structured data."""
        if "json" in data_source.lower() or "structured" in data_source.lower():
            return ConfidenceLevel.HIGH
        elif "html" in data_source.lower():
            return ConfidenceLevel.HIGH  # Ubiquiti HTML is also well-structured
        else:
            return ConfidenceLevel.MEDIUM

    def _parse_rack_units(self, value: str) -> Optional[float]:
        """Parse rack units from string."""
        import re
        match = re.search(r'(\d+\.?\d*)', value)
        return float(match.group(1)) if match else None

    def _parse_depth(self, value: str) -> Optional[float]:
        """Parse depth in millimeters."""
        import re
        parser = HTMLParser()
        return parser._parse_depth(value)

    def _parse_weight(self, value: str) -> Optional[float]:
        """Parse weight in kilograms."""
        parser = HTMLParser()
        return parser._parse_weight(value)

    def _parse_power(self, value: str) -> Optional[float]:
        """Parse power in watts."""
        parser = HTMLParser()
        return parser._parse_power(value)
