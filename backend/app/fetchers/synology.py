"""
Synology-specific device specification fetcher.
Fetches specs from Synology product pages and datasheets.
Handles both NAS devices and network equipment.
"""
import logging
from typing import Optional, List, Dict, Any
import re
import json
from bs4 import BeautifulSoup

from .base import BaseSpecFetcher, DeviceSpec
from ..models import ConfidenceLevel
from ..parsers.base import PDFParser, HTMLParser
from ..exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class SynologyFetcher(BaseSpecFetcher):
    """Fetcher for Synology NAS and network equipment specifications."""

    @property
    def manufacturer_name(self) -> str:
        return "Synology"

    async def search_product(self, brand: str, model: str) -> List[str]:
        """
        Search for Synology product pages.

        Synology product URLs typically follow patterns:
        - https://www.synology.com/en-us/products/{model}
        - https://www.synology.com/en-us/products/{series}/{model}
        - https://www.synology.com/en-us/support/download-center

        Synology NAS series include: DiskStation, RackStation, FlashStation
        Network equipment: MoCA, Switch, etc.
        """
        urls = []

        # Clean model number (remove spaces, lowercase)
        clean_model = model.replace(" ", "-").lower()

        # Direct product page URLs
        # Try standard product page format
        urls.append(f"https://www.synology.com/en-us/products/{clean_model}")

        # Try with different region (US is common, but try others)
        urls.append(f"https://www.synology.com/en-global/products/{clean_model}")

        # Common Synology series for NAS
        nas_series = [
            "diskstation",
            "rackstation",
            "flashstation",
            "j-series",
            "d-series",
            "plus-series"
        ]

        for series in nas_series:
            urls.append(f"https://www.synology.com/en-us/products/{series}/{clean_model}")

        # Network/Switch products
        network_series = [
            "network",
            "switch",
            "moca"
        ]

        for series in network_series:
            urls.append(f"https://www.synology.com/en-us/products/{series}/{clean_model}")

        # Specification sheet search
        urls.append(f"https://www.synology.com/en-us/support/download-center?product={clean_model}")

        # Direct datasheet search
        urls.append(f"https://www.synology.com/en-us/support/download-center?model={model}")

        return urls

    async def fetch_spec(self, brand: str, model: str) -> Optional[DeviceSpec]:
        """
        Fetch Synology device specification.

        Strategy:
        1. Try to find product specification page
        2. Look for specification tables and structured data
        3. Download datasheet PDF if available
        4. Parse HTML specification sections
        5. Extract from structured data (JSON-LD)
        """
        try:
            # Search for product pages
            urls = await self.search_product(brand, model)

            for url in urls:
                try:
                    response = await self.client.get(url)

                    if response.status_code == 200:
                        # Try PDF datasheet first
                        spec = await self._fetch_from_pdf_in_page(response.content, url, brand, model)
                        if spec:
                            return spec

                        # Try structured data
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

            logger.warning(f"No Synology specs found for {brand} {model}")
            return None

        except Exception as e:
            logger.error(f"Error fetching Synology spec for {brand} {model}: {e}")
            raise ExternalServiceError(
                service="Synology",
                message=f"Failed to fetch specification: {str(e)}"
            )

    async def _fetch_from_pdf_in_page(self, html_content: bytes, url: str, brand: str, model: str) -> Optional[DeviceSpec]:
        """Look for PDF datasheet link in HTML and download it."""
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # Look for PDF links in the page
            pdf_links = soup.find_all('a', href=re.compile(r'.*\.pdf$', re.IGNORECASE))

            # Filter for datasheet/specification PDFs
            datasheet_links = [
                link for link in pdf_links
                if any(keyword in link.get('href', '').lower() for keyword in
                       ['datasheet', 'spec', 'specification', 'quick', 'install'])
            ]

            if datasheet_links:
                pdf_url = datasheet_links[0].get('href')

                # Handle relative URLs
                if not pdf_url.startswith('http'):
                    if pdf_url.startswith('/'):
                        pdf_url = f"https://www.synology.com{pdf_url}"
                    else:
                        base_url = '/'.join(url.split('/')[:3])
                        pdf_url = f"{base_url}/{pdf_url}"

                logger.info(f"Found Synology PDF datasheet: {pdf_url}")

                # Download and parse PDF
                try:
                    pdf_response = await self.client.get(pdf_url)
                    if pdf_response.status_code == 200:
                        spec = await self._fetch_from_pdf(pdf_response.content, brand, model, pdf_url)
                        if spec:
                            return spec
                except Exception as e:
                    logger.warning(f"Failed to download PDF from {pdf_url}: {e}")

            return None

        except Exception as e:
            logger.error(f"Failed to process PDF in page: {e}")
            return None

    async def _fetch_from_pdf(self, pdf_content: bytes, brand: str, model: str, pdf_url: str) -> Optional[DeviceSpec]:
        """Download and parse PDF datasheet."""
        try:
            # Parse PDF
            parser = PDFParser()
            specs_data = await parser.parse(pdf_content, "application/pdf")

            if not specs_data:
                return None

            # Create DeviceSpec
            spec = DeviceSpec(
                brand=brand,
                model=model,
                source_url=pdf_url,
                confidence=ConfidenceLevel.HIGH,  # PDF datasheets are high quality
                **specs_data
            )

            # Validate
            is_valid, issues = self._validate_spec(spec)
            if not is_valid:
                logger.warning(f"Synology PDF spec validation failed: {issues}")
                spec.confidence = ConfidenceLevel.MEDIUM

            return spec

        except Exception as e:
            logger.error(f"Failed to parse Synology PDF: {e}")
            return None

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
            logger.error(f"Failed to parse Synology structured data: {e}")
            return None

    def _parse_product_json(self, data: dict) -> dict:
        """Parse Product schema JSON-LD from Synology."""
        specs = {}

        # Basic info
        if 'name' in data:
            specs['model'] = data['name']

        # Look for additionalProperty or offers details
        if 'additionalProperty' in data:
            for prop in data['additionalProperty']:
                name = prop.get('name', '').lower()
                value = prop.get('value')

                if not value:
                    continue

                if 'height' in name or 'rack' in name or 'u' in name:
                    specs['height_u'] = self._parse_rack_units(str(value))
                elif 'depth' in name:
                    specs['depth_mm'] = self._parse_depth(str(value))
                elif 'weight' in name:
                    specs['weight_kg'] = self._parse_weight(str(value))
                elif 'power' in name or 'wattage' in name:
                    specs['power_watts'] = self._parse_power(str(value))
                elif 'thermal' in name or 'heat' in name:
                    specs['heat_output_btu'] = self._parse_heat_output(str(value))
                elif 'airflow' in name or 'cooling' in name:
                    specs['airflow_pattern'] = str(value)

        return specs

    async def _fetch_from_html(self, html_content: bytes, url: str, brand: str, model: str) -> Optional[DeviceSpec]:
        """Parse HTML specification page."""
        try:
            parser = HTMLParser()
            specs_data = await parser.parse(html_content, "text/html")

            # If HTML parser found nothing, try Synology-specific parsing
            if not specs_data:
                specs_data = await self._parse_synology_html_sections(html_content)

            if not specs_data:
                return None

            spec = DeviceSpec(
                brand=brand,
                model=model,
                source_url=url,
                confidence=ConfidenceLevel.MEDIUM,  # HTML less reliable than PDF
                **specs_data
            )

            # Validate
            is_valid, issues = self._validate_spec(spec)
            if not is_valid:
                logger.warning(f"Synology HTML spec validation failed: {issues}")
                spec.confidence = ConfidenceLevel.LOW

            return spec

        except Exception as e:
            logger.error(f"Failed to parse Synology HTML: {e}")
            return None

    async def _parse_synology_html_sections(self, html_content: bytes) -> Optional[Dict[str, Any]]:
        """Parse Synology-specific HTML structure."""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            specs = {}

            # Synology often uses specific class names for specifications
            spec_keywords = [
                'specifications',
                'specs',
                'technical-specifications',
                'technical_spec'
            ]

            # Look for sections with specification content
            for keyword in spec_keywords:
                # By class
                sections = soup.find_all(class_=re.compile(keyword, re.IGNORECASE))
                for section in sections:
                    section_specs = self._extract_specs_from_section(section)
                    specs.update(section_specs)

                # By ID
                section = soup.find(id=re.compile(keyword, re.IGNORECASE))
                if section:
                    section_specs = self._extract_specs_from_section(section)
                    specs.update(section_specs)

            # Look for specification tables
            tables = soup.find_all('table')
            for table in tables:
                table_specs = self._extract_specs_from_table(table)
                specs.update(table_specs)

            return specs if specs else None

        except Exception as e:
            logger.error(f"Failed to parse Synology HTML sections: {e}")
            return None

    def _extract_specs_from_section(self, section) -> Dict[str, Any]:
        """Extract specifications from a section element."""
        specs = {}

        # Look for dl (definition list) elements
        dls = section.find_all('dl')
        for dl in dls:
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')

            for dt, dd in zip(dts, dds):
                key = dt.get_text().strip().lower()
                value = dd.get_text().strip()

                specs.update(self._parse_spec_pair(key, value))

        # Look for label/div pairs
        labels = section.find_all(['label', 'strong', 'b'], class_=re.compile('label|spec-key', re.IGNORECASE))
        for label in labels:
            parent = label.parent
            if parent:
                key = label.get_text().strip().lower()
                # Try to find value in sibling or parent's span
                value_elem = parent.find(['span', 'div', 'p'])
                if value_elem:
                    value = value_elem.get_text().strip()
                    specs.update(self._parse_spec_pair(key, value))

        return specs

    def _extract_specs_from_table(self, table) -> Dict[str, Any]:
        """Extract specifications from a table element."""
        specs = {}

        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key = cells[0].get_text().strip().lower()
                value = cells[1].get_text().strip()

                specs.update(self._parse_spec_pair(key, value))

        return specs

    def _parse_spec_pair(self, key: str, value: str) -> Dict[str, Any]:
        """Parse a specification key-value pair."""
        specs = {}

        if 'height' in key or 'rack' in key or 'unit' in key or 'u)' in key:
            parsed = self._parse_rack_units(value)
            if parsed:
                specs['height_u'] = parsed
        elif 'depth' in key:
            parsed = self._parse_depth(value)
            if parsed:
                specs['depth_mm'] = parsed
        elif 'weight' in key or 'mass' in key:
            parsed = self._parse_weight(value)
            if parsed:
                specs['weight_kg'] = parsed
        elif 'power' in key or 'wattage' in key or 'consumption' in key:
            parsed = self._parse_power(value)
            if parsed:
                specs['power_watts'] = parsed
        elif 'thermal' in key or 'heat' in key:
            parsed = self._parse_heat_output(value)
            if parsed:
                specs['heat_output_btu'] = parsed
        elif 'operating' in key and 'temperature' in key:
            parsed = self._parse_temperature(value)
            if parsed:
                specs['max_operating_temp_c'] = parsed
        elif 'airflow' in key or 'cooling' in key:
            specs['airflow_pattern'] = value
        elif 'network' in key or 'port' in key or 'ethernet' in key or 'gigabit' in key:
            # Extract port information
            ports = self._parse_ports(key, value)
            if ports:
                specs.setdefault('typical_ports', {}).update(ports)
        elif 'mounting' in key:
            specs['mounting_type'] = value

        return specs

    def _parse_ports(self, key: str, value: str) -> Optional[Dict[str, int]]:
        """Parse network port information."""
        ports = {}

        # Extract numbers from port descriptions
        # e.g., "4x Gigabit Ethernet" -> {"gigabit_ethernet": 4}

        # Gigabit Ethernet
        match = re.search(r'(\d+)\s*x?\s*gigabit\s*ethernet', value, re.IGNORECASE)
        if match:
            ports['gigabit_ethernet'] = int(match.group(1))

        # 10G Ethernet
        match = re.search(r'(\d+)\s*x?\s*10g\s*ethernet', value, re.IGNORECASE)
        if match:
            ports['ten_gigabit_ethernet'] = int(match.group(1))

        # SFP ports
        match = re.search(r'(\d+)\s*x?\s*sfp', value, re.IGNORECASE)
        if match:
            ports['sfp'] = int(match.group(1))

        # USB ports
        match = re.search(r'(\d+)\s*x?\s*usb', value, re.IGNORECASE)
        if match:
            ports['usb'] = int(match.group(1))

        # HDMI
        match = re.search(r'(\d+)\s*x?\s*hdmi', value, re.IGNORECASE)
        if match:
            ports['hdmi'] = int(match.group(1))

        return ports if ports else None

    def get_confidence_level(self, data_source: str) -> ConfidenceLevel:
        """Determine confidence level based on data source."""
        if "pdf" in data_source.lower() or "datasheet" in data_source.lower():
            return ConfidenceLevel.HIGH
        elif "json" in data_source.lower() or "structured" in data_source.lower():
            return ConfidenceLevel.HIGH
        elif "html" in data_source.lower():
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    # Helper parsing methods
    def _parse_rack_units(self, value: str) -> Optional[float]:
        """Parse rack units from various formats."""
        match = re.search(r'(\d+\.?\d*)', value)
        return float(match.group(1)) if match else None

    def _parse_depth(self, value: str) -> Optional[float]:
        """Parse depth in millimeters."""
        # Look for mm first
        match = re.search(r'(\d+\.?\d*)\s*mm', value, re.IGNORECASE)
        if match:
            return float(match.group(1))

        # Look for inches
        match = re.search(r'(\d+\.?\d*)\s*(?:inches|in\.?|")', value, re.IGNORECASE)
        if match:
            parser = HTMLParser()
            return parser.normalize_units(float(match.group(1)), 'inches', 'mm')

        return None

    def _parse_weight(self, value: str) -> Optional[float]:
        """Parse weight in kilograms."""
        # Look for kg first
        match = re.search(r'(\d+\.?\d*)\s*kg', value, re.IGNORECASE)
        if match:
            return float(match.group(1))

        # Look for lbs
        match = re.search(r'(\d+\.?\d*)\s*(?:lbs?|pounds?)', value, re.IGNORECASE)
        if match:
            parser = HTMLParser()
            return parser.normalize_units(float(match.group(1)), 'lbs', 'kg')

        return None

    def _parse_power(self, value: str) -> Optional[float]:
        """Parse power in watts."""
        match = re.search(r'(\d+\.?\d*)\s*[Ww]', value)
        return float(match.group(1)) if match else None

    def _parse_heat_output(self, value: str) -> Optional[float]:
        """Parse heat output in BTU."""
        # Look for BTU
        match = re.search(r'(\d+\.?\d*)\s*(?:btu|BTU)', value, re.IGNORECASE)
        if match:
            return float(match.group(1))

        # If it's in watts, convert to BTU
        match = re.search(r'(\d+\.?\d*)\s*[Ww]', value)
        if match:
            parser = HTMLParser()
            watts = float(match.group(1))
            return parser.normalize_units(watts, 'watts', 'btu')

        return None

    def _parse_temperature(self, value: str) -> Optional[float]:
        """Parse temperature in Celsius."""
        # Look for Celsius
        match = re.search(r'(\d+\.?\d*)\s*(?:c|°c|celsius)', value, re.IGNORECASE)
        if match:
            return float(match.group(1))

        # Look for Fahrenheit and convert
        match = re.search(r'(\d+\.?\d*)\s*(?:f|°f|fahrenheit)', value, re.IGNORECASE)
        if match:
            fahrenheit = float(match.group(1))
            # Convert F to C: (F - 32) * 5/9
            return (fahrenheit - 32) * 5 / 9

        return None
