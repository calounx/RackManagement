"""
Base abstract classes for parsing device specifications from various formats.
Supports HTML, PDF, and structured data extraction.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """
    Abstract base class for specification parsers.

    Parsers extract device specifications from various formats
    (HTML pages, PDF datasheets, structured data, etc.)
    """

    @abstractmethod
    async def parse(self, content: bytes, content_type: str) -> Dict[str, Any]:
        """
        Parse content and extract device specifications.

        Args:
            content: Raw content bytes (HTML, PDF, etc.)
            content_type: MIME type of content

        Returns:
            Dictionary of extracted specifications
        """
        pass

    @abstractmethod
    def extract_measurements(self, text: str) -> Dict[str, float]:
        """
        Extract physical measurements from text.

        Args:
            text: Text containing measurements

        Returns:
            Dictionary of measurements (height_u, depth_mm, weight_kg, etc.)
        """
        pass

    @abstractmethod
    def normalize_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert measurement from one unit to another.

        Args:
            value: Measurement value
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            Converted value
        """
        pass


class HTMLParser(BaseParser):
    """Parser for HTML specification pages."""

    async def parse(self, content: bytes, content_type: str = "text/html") -> Dict[str, Any]:
        """
        Parse HTML content to extract specifications.

        Uses BeautifulSoup to parse structured HTML and extract
        specification tables, definition lists, and structured data.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, 'lxml')
        specs = {}

        # Extract structured data (JSON-LD, microdata)
        structured = self._extract_structured_data(soup)
        if structured:
            specs.update(structured)

        # Extract specification tables
        tables = self._extract_spec_tables(soup)
        if tables:
            specs.update(tables)

        # Extract definition lists
        dl_specs = self._extract_dl_lists(soup)
        if dl_specs:
            specs.update(dl_specs)

        return specs

    def _extract_structured_data(self, soup) -> Dict[str, Any]:
        """Extract JSON-LD or microdata structured data."""
        specs = {}

        # Look for JSON-LD
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                import json
                data = json.loads(script.string)
                # Extract relevant product data
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    specs.update(self._parse_product_jsonld(data))
            except Exception as e:
                logger.warning(f"Failed to parse JSON-LD: {e}")

        return specs

    def _parse_product_jsonld(self, data: Dict) -> Dict[str, Any]:
        """Parse Product schema JSON-LD data."""
        specs = {}

        # Extract basic info
        if 'name' in data:
            specs['model'] = data['name']

        # Extract detailed properties
        if 'additionalProperty' in data:
            for prop in data['additionalProperty']:
                name = prop.get('name', '').lower()
                value = prop.get('value')

                if 'height' in name or 'rack unit' in name:
                    specs['height_u'] = self._parse_rack_units(str(value))
                elif 'depth' in name:
                    specs['depth_mm'] = self._parse_depth(str(value))
                elif 'weight' in name:
                    specs['weight_kg'] = self._parse_weight(str(value))
                elif 'power' in name:
                    specs['power_watts'] = self._parse_power(str(value))

        return specs

    def _extract_spec_tables(self, soup) -> Dict[str, Any]:
        """Extract specifications from HTML tables."""
        specs = {}

        # Look for tables with specification-like headers
        tables = soup.find_all('table')
        for table in tables:
            # Check if table looks like a spec table
            table_text = table.get_text().lower()
            if any(keyword in table_text for keyword in ['specification', 'technical', 'physical']):
                specs.update(self._parse_spec_table(table))

        return specs

    def _parse_spec_table(self, table) -> Dict[str, Any]:
        """Parse a specification table into key-value pairs."""
        specs = {}

        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key = cells[0].get_text().strip().lower()
                value = cells[1].get_text().strip()

                if 'height' in key or 'rack unit' in key:
                    specs['height_u'] = self._parse_rack_units(value)
                elif 'depth' in key:
                    specs['depth_mm'] = self._parse_depth(value)
                elif 'weight' in key:
                    specs['weight_kg'] = self._parse_weight(value)
                elif 'power' in key:
                    specs['power_watts'] = self._parse_power(value)

        return specs

    def _extract_dl_lists(self, soup) -> Dict[str, Any]:
        """Extract specifications from definition lists (<dl>)."""
        specs = {}

        dl_elements = soup.find_all('dl')
        for dl in dl_elements:
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')

            for dt, dd in zip(dts, dds):
                key = dt.get_text().strip().lower()
                value = dd.get_text().strip()

                if 'height' in key:
                    specs['height_u'] = self._parse_rack_units(value)
                elif 'depth' in key:
                    specs['depth_mm'] = self._parse_depth(value)
                elif 'weight' in key:
                    specs['weight_kg'] = self._parse_weight(value)
                elif 'power' in key:
                    specs['power_watts'] = self._parse_power(value)

        return specs

    def extract_measurements(self, text: str) -> Dict[str, float]:
        """Extract measurements from free text using regex patterns."""
        import re
        measurements = {}

        # Rack units: "1U", "2 RU", "1.75 inches"
        ru_pattern = r'(\d+\.?\d*)\s*(?:[Uu]|[Rr][Uu]|rack\s*units?)'
        ru_match = re.search(ru_pattern, text, re.IGNORECASE)
        if ru_match:
            measurements['height_u'] = float(ru_match.group(1))

        # Depth: "445mm", "17.5 inches"
        depth_mm_pattern = r'(\d+\.?\d*)\s*mm'
        depth_match = re.search(depth_mm_pattern, text, re.IGNORECASE)
        if depth_match:
            measurements['depth_mm'] = float(depth_match.group(1))

        # Weight: "4.1 kg", "9 lbs"
        weight_kg_pattern = r'(\d+\.?\d*)\s*kg'
        weight_match = re.search(weight_kg_pattern, text, re.IGNORECASE)
        if weight_match:
            measurements['weight_kg'] = float(weight_match.group(1))

        # Power: "25W", "25 watts"
        power_pattern = r'(\d+\.?\d*)\s*(?:[Ww]atts?|[Ww])'
        power_match = re.search(power_pattern, text, re.IGNORECASE)
        if power_match:
            measurements['power_watts'] = float(power_match.group(1))

        return measurements

    def normalize_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert between units."""
        conversions = {
            ('inches', 'mm'): 25.4,
            ('mm', 'inches'): 1 / 25.4,
            ('lbs', 'kg'): 0.453592,
            ('kg', 'lbs'): 1 / 0.453592,
            ('watts', 'btu'): 3.412,
            ('btu', 'watts'): 1 / 3.412,
        }

        key = (from_unit.lower(), to_unit.lower())
        if key in conversions:
            return value * conversions[key]
        else:
            logger.warning(f"Unknown conversion: {from_unit} to {to_unit}")
            return value

    # Helper parsing methods
    def _parse_rack_units(self, value: str) -> Optional[float]:
        """Parse rack units from various formats."""
        import re
        match = re.search(r'(\d+\.?\d*)', value)
        return float(match.group(1)) if match else None

    def _parse_depth(self, value: str) -> Optional[float]:
        """Parse depth in millimeters."""
        import re
        # Look for mm first
        match = re.search(r'(\d+\.?\d*)\s*mm', value, re.IGNORECASE)
        if match:
            return float(match.group(1))

        # Look for inches
        match = re.search(r'(\d+\.?\d*)\s*(?:inches|in\.?|")', value, re.IGNORECASE)
        if match:
            return self.normalize_units(float(match.group(1)), 'inches', 'mm')

        return None

    def _parse_weight(self, value: str) -> Optional[float]:
        """Parse weight in kilograms."""
        import re
        # Look for kg first
        match = re.search(r'(\d+\.?\d*)\s*kg', value, re.IGNORECASE)
        if match:
            return float(match.group(1))

        # Look for lbs
        match = re.search(r'(\d+\.?\d*)\s*(?:lbs?|pounds?)', value, re.IGNORECASE)
        if match:
            return self.normalize_units(float(match.group(1)), 'lbs', 'kg')

        return None

    def _parse_power(self, value: str) -> Optional[float]:
        """Parse power in watts."""
        import re
        match = re.search(r'(\d+\.?\d*)\s*[Ww]', value)
        return float(match.group(1)) if match else None


class PDFParser(BaseParser):
    """Parser for PDF datasheets."""

    async def parse(self, content: bytes, content_type: str = "application/pdf") -> Dict[str, Any]:
        """
        Parse PDF content to extract specifications.

        Uses pdfplumber for table extraction and PyMuPDF for text extraction.
        """
        import pdfplumber
        import io

        specs = {}

        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                # Extract tables from all pages
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        table_specs = self._parse_pdf_table(table)
                        specs.update(table_specs)

                    # Also extract text for regex parsing
                    text = page.extract_text()
                    if text:
                        text_specs = self.extract_measurements(text)
                        specs.update(text_specs)

        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")

        return specs

    def _parse_pdf_table(self, table: List[List[str]]) -> Dict[str, Any]:
        """Parse a PDF table into specifications."""
        specs = {}

        for row in table:
            if len(row) >= 2 and row[0] and row[1]:
                key = str(row[0]).strip().lower()
                value = str(row[1]).strip()

                if 'height' in key or 'rack unit' in key:
                    parsed = self._parse_rack_units(value)
                    if parsed:
                        specs['height_u'] = parsed
                elif 'depth' in key:
                    parsed = self._parse_depth(value)
                    if parsed:
                        specs['depth_mm'] = parsed
                elif 'weight' in key:
                    parsed = self._parse_weight(value)
                    if parsed:
                        specs['weight_kg'] = parsed
                elif 'power' in key:
                    parsed = self._parse_power(value)
                    if parsed:
                        specs['power_watts'] = parsed

        return specs

    def extract_measurements(self, text: str) -> Dict[str, float]:
        """Use HTML parser's measurement extraction (same logic)."""
        html_parser = HTMLParser()
        return html_parser.extract_measurements(text)

    def normalize_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """Use HTML parser's unit conversion (same logic)."""
        html_parser = HTMLParser()
        return html_parser.normalize_units(value, from_unit, to_unit)

    # Reuse HTML parser helper methods
    def _parse_rack_units(self, value: str) -> Optional[float]:
        return HTMLParser()._parse_rack_units(value)

    def _parse_depth(self, value: str) -> Optional[float]:
        return HTMLParser()._parse_depth(value)

    def _parse_weight(self, value: str) -> Optional[float]:
        return HTMLParser()._parse_weight(value)

    def _parse_power(self, value: str) -> Optional[float]:
        return HTMLParser()._parse_power(value)
