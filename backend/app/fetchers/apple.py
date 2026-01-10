"""
Apple-specific device specification fetcher.
Fetches specs from Apple support pages and tech specs for Mac Studio, Mac Mini Server, and Xserve legacy products.
"""
import logging
from typing import Optional, List
import re
from bs4 import BeautifulSoup

from .base import BaseSpecFetcher, DeviceSpec
from ..models import ConfidenceLevel
from ..parsers.base import HTMLParser
from ..exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class AppleFetcher(BaseSpecFetcher):
    """Fetcher for Apple network and server equipment specifications."""

    # Mapping of Apple product names to support KB article numbers and URLs
    APPLE_PRODUCTS = {
        "Mac Mini Server": {
            "kb_numbers": ["SP632", "SP644", "SP734"],  # Various Mac Mini Server generations
            "support_urls": [
                "https://support.apple.com/kb/SP632",
                "https://support.apple.com/kb/SP644",
                "https://support.apple.com/kb/SP734",
            ]
        },
        "Mac Studio": {
            "support_urls": [
                "https://www.apple.com/mac-studio/specs/",
                "https://support.apple.com/en-us/HT208139",
            ]
        },
        "Xserve": {
            "kb_numbers": ["SP468"],
            "support_urls": [
                "https://support.apple.com/kb/SP468",
            ]
        },
    }

    @property
    def manufacturer_name(self) -> str:
        return "Apple"

    async def search_product(self, brand: str, model: str) -> List[str]:
        """
        Search for Apple product pages.

        Apple product URLs typically follow patterns:
        - https://support.apple.com/kb/SP### (technical specs)
        - https://www.apple.com/{product}/specs/ (product specs)
        """
        urls = []

        # Clean model name
        clean_model = model.strip().lower()

        # Check if model matches known Apple products
        for product_name, product_info in self.APPLE_PRODUCTS.items():
            if product_name.lower() in clean_model or clean_model in product_name.lower():
                # Add known URLs for this product
                if "support_urls" in product_info:
                    urls.extend(product_info["support_urls"])

        # Generate generic patterns for Apple support and product pages
        # Mac Studio format
        urls.append("https://www.apple.com/mac-studio/specs/")

        # Mac Mini Server format
        urls.append("https://support.apple.com/kb/SP644")  # Mac Mini Server
        urls.append("https://support.apple.com/kb/SP632")  # Earlier Mac Mini Server

        # Xserve legacy
        urls.append("https://support.apple.com/kb/SP468")

        # Apple support page search pattern
        urls.append(f"https://support.apple.com/search?q={model.replace(' ', '+')}+specifications")

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    async def fetch_spec(self, brand: str, model: str) -> Optional[DeviceSpec]:
        """
        Fetch Apple device specification.

        Strategy:
        1. Search for Apple support/product spec pages
        2. Parse HTML to extract technical specifications
        3. Look for physical dimensions, power consumption, and thermal specs
        4. Validate and return with appropriate confidence level
        """
        try:
            # Search for product pages
            urls = await self.search_product(brand, model)

            for url in urls:
                try:
                    response = await self.client.get(url)

                    if response.status_code == 200:
                        # Try parsing the HTML spec page
                        spec = await self._fetch_from_html(response.content, url, brand, model)
                        if spec:
                            return spec

                except Exception as e:
                    logger.warning(f"Failed to fetch from {url}: {e}")
                    continue

            logger.warning(f"No Apple specs found for {brand} {model}")
            return None

        except Exception as e:
            logger.error(f"Error fetching Apple spec for {brand} {model}: {e}")
            raise ExternalServiceError(
                service="Apple",
                message=f"Failed to fetch specification: {str(e)}"
            )

    async def _fetch_from_html(self, html_content: bytes, url: str, brand: str, model: str) -> Optional[DeviceSpec]:
        """Parse Apple HTML specification page."""
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # Try custom Apple-specific parsing first
            specs_data = self._parse_apple_specs(soup, url)

            if not specs_data:
                # Fall back to generic HTML parser
                parser = HTMLParser()
                specs_data = await parser.parse(html_content, "text/html")

            if not specs_data:
                return None

            spec = DeviceSpec(
                brand=brand,
                model=model,
                source_url=url,
                confidence=ConfidenceLevel.HIGH,  # Apple official pages are reliable
                **specs_data
            )

            # Validate
            is_valid, issues = self._validate_spec(spec)
            if not is_valid:
                logger.warning(f"Apple spec validation failed: {issues}")
                spec.confidence = ConfidenceLevel.MEDIUM

            return spec

        except Exception as e:
            logger.error(f"Failed to parse Apple HTML: {e}")
            return None

    def _parse_apple_specs(self, soup: BeautifulSoup, url: str) -> dict:
        """
        Parse Apple-specific specification pages.

        Apple pages have consistent formatting with tech specs sections,
        definition lists, and specification tables.
        """
        specs = {}

        # Look for specification sections with common Apple patterns
        # Apple typically uses <dt> (definition term) and <dd> (definition data) patterns
        self._parse_apple_definition_lists(soup, specs)

        # Also check for specification tables
        self._parse_apple_spec_tables(soup, specs)

        # Look for divs with spec classes
        self._parse_apple_spec_divs(soup, specs)

        # Extract from structured content
        self._parse_apple_structured_content(soup, specs)

        return specs

    def _parse_apple_definition_lists(self, soup: BeautifulSoup, specs: dict) -> None:
        """Extract specs from Apple's definition list format."""
        dl_elements = soup.find_all(['dl', 'div'], class_=re.compile(r'spec|technical|definition', re.I))

        for element in dl_elements:
            dts = element.find_all('dt')
            dds = element.find_all('dd')

            for dt, dd in zip(dts, dds):
                key = dt.get_text().strip().lower()
                value = dd.get_text().strip()

                self._parse_apple_spec_pair(key, value, specs)

    def _parse_apple_spec_tables(self, soup: BeautifulSoup, specs: dict) -> None:
        """Extract specs from Apple specification tables."""
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text().strip().lower()
                    value = cells[1].get_text().strip()

                    self._parse_apple_spec_pair(key, value, specs)

    def _parse_apple_spec_divs(self, soup: BeautifulSoup, specs: dict) -> None:
        """Extract specs from div-based structured content."""
        # Look for divs containing specification pairs
        spec_containers = soup.find_all('div', class_=re.compile(r'spec|technical|feature', re.I))

        for container in spec_containers:
            # Try to find key-value pairs within the container
            text = container.get_text()
            lines = text.split('\n')

            for i in range(0, len(lines) - 1, 2):
                key = lines[i].strip().lower()
                value = lines[i + 1].strip() if i + 1 < len(lines) else ""

                if key and value:
                    self._parse_apple_spec_pair(key, value, specs)

    def _parse_apple_structured_content(self, soup: BeautifulSoup, specs: dict) -> None:
        """Extract specs from Apple's standard content structure."""
        # Look for sections with specific spec information
        sections = soup.find_all(['section', 'article'])

        for section in sections:
            text = section.get_text()

            # Look for specific patterns Apple uses
            patterns = {
                'height_u': [
                    r'(\d+\.?\d*)\s*u(?:\s+|$)',
                    r'rack\s+height[:\s]+(\d+\.?\d*)\s*u',
                ],
                'depth_mm': [
                    r'(\d+\.?\d*)\s*mm\s+deep',
                    r'depth[:\s]+(\d+\.?\d*)\s*mm',
                ],
                'weight_kg': [
                    r'(\d+\.?\d*)\s*kg\s+weight',
                    r'weight[:\s]+(\d+\.?\d*)\s*kg',
                ],
                'power_watts': [
                    r'(\d+\.?\d*)\s*[Ww]\s+(?:power|consumption)',
                    r'power[:\s]+(\d+\.?\d*)\s*[Ww]',
                ],
                'max_operating_temp_c': [
                    r'operating\s+temperature[:\s]+.*?(\d+).?c',
                    r'max\s+temp[:\s]+(\d+).?c',
                ]
            }

            for spec_key, patterns_list in patterns.items():
                if spec_key not in specs:
                    for pattern in patterns_list:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            value = float(match.group(1))
                            specs[spec_key] = value
                            break

    def _parse_apple_spec_pair(self, key: str, value: str, specs: dict) -> None:
        """
        Parse individual spec key-value pairs common in Apple documentation.
        """
        parser = HTMLParser()

        if 'height' in key or 'rack' in key or 'u' in value.lower():
            parsed = parser._parse_rack_units(value)
            if parsed and 'height_u' not in specs:
                specs['height_u'] = parsed

        elif 'depth' in key:
            parsed = parser._parse_depth(value)
            if parsed and 'depth_mm' not in specs:
                specs['depth_mm'] = parsed

        elif 'weight' in key:
            parsed = parser._parse_weight(value)
            if parsed and 'weight_kg' not in specs:
                specs['weight_kg'] = parsed

        elif 'power' in key or 'wattage' in key or 'consumption' in key:
            parsed = parser._parse_power(value)
            if parsed and 'power_watts' not in specs:
                specs['power_watts'] = parsed

        elif 'temperature' in key or 'thermal' in key or 'heat' in key:
            # Parse operating temperature
            temp_match = re.search(r'(\d+\.?\d*)\s*(?:°)?[Cc]', value)
            if temp_match and 'max_operating_temp_c' not in specs:
                specs['max_operating_temp_c'] = float(temp_match.group(1))

        elif 'port' in key or 'network' in key or 'ethernet' in key:
            # Parse port information
            port_match = re.search(r'(\d+)\s*(?:x\s*)?(?:gigabit\s+)?ethernet', value, re.IGNORECASE)
            if port_match:
                port_count = int(port_match.group(1))
                if 'typical_ports' not in specs:
                    specs['typical_ports'] = {}
                specs['typical_ports']['ethernet'] = port_count

        elif 'fan' in key or 'airflow' in key:
            # Capture airflow information
            if 'typical_ports' not in specs:
                specs['typical_ports'] = {}
            if value:
                specs['typical_ports']['cooling'] = value

    def get_confidence_level(self, data_source: str) -> ConfidenceLevel:
        """Determine confidence level based on data source."""
        if "support.apple.com" in data_source.lower() or "apple.com" in data_source.lower():
            return ConfidenceLevel.HIGH  # Official Apple pages are authoritative
        elif "html" in data_source.lower():
            return ConfidenceLevel.MEDIUM  # HTML pages can vary in structure
        else:
            return ConfidenceLevel.LOW
