"""
ASUS-specific device specification fetcher.
Fetches specs from ASUS support pages and datasheets for networking equipment.
"""
import logging
from typing import Optional, List
import re
from bs4 import BeautifulSoup

from .base import BaseSpecFetcher, DeviceSpec
from ..models import ConfidenceLevel
from ..parsers.base import PDFParser, HTMLParser
from ..exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class ASUSFetcher(BaseSpecFetcher):
    """Fetcher for ASUS network equipment specifications."""

    @property
    def manufacturer_name(self) -> str:
        return "ASUS"

    async def search_product(self, brand: str, model: str) -> List[str]:
        """
        Search for ASUS product pages.

        ASUS product URLs typically follow patterns:
        - https://www.asus.com/networking/routers/{model}/
        - https://www.asus.com/networking/switches/{model}/
        - https://www.asus.com/networking/servers/{model}/
        - https://www.asus.com/support/download/
        """
        urls = []

        # Clean model number (remove spaces, normalize case)
        clean_model = model.replace(" ", "-").lower()

        # Common ASUS networking product categories
        categories = ["routers", "switches", "servers", "wireless"]

        # Try main product pages
        for category in categories:
            url = f"https://www.asus.com/networking/{category}/{clean_model}/"
            urls.append(url)

        # Try product pages without trailing slash
        for category in categories:
            url = f"https://www.asus.com/networking/{category}/{clean_model}"
            urls.append(url)

        # ASUS support/specification pages
        urls.append(f"https://www.asus.com/support/download-center/")
        urls.append(f"https://www.asus.com/support/")

        # Direct search for datasheet
        urls.append(f"https://www.asus.com/support/search-result/?searchKey={model}+datasheet")

        return urls

    async def fetch_spec(self, brand: str, model: str) -> Optional[DeviceSpec]:
        """
        Fetch ASUS device specification.

        Strategy:
        1. Try to find product support page
        2. Download datasheet PDF if available
        3. Parse PDF for specifications
        4. Fall back to HTML parsing if PDF unavailable
        """
        try:
            # Search for product pages
            urls = await self.search_product(brand, model)

            for url in urls:
                try:
                    response = await self.client.get(url)

                    if response.status_code == 200:
                        # Parse HTML to find datasheet link or specs
                        soup = BeautifulSoup(response.content, 'lxml')

                        # Look for datasheet PDF link
                        pdf_links = soup.find_all('a', href=re.compile(r'.*\.pdf$', re.IGNORECASE))
                        datasheet_links = [
                            link for link in pdf_links
                            if 'datasheet' in link.get('href', '').lower() or
                               'specification' in link.get('href', '').lower() or
                               'manual' in link.get('href', '').lower()
                        ]

                        if datasheet_links:
                            pdf_url = datasheet_links[0].get('href')
                            if not pdf_url.startswith('http'):
                                # Handle relative URLs
                                if pdf_url.startswith('/'):
                                    pdf_url = f"https://www.asus.com{pdf_url}"
                                else:
                                    pdf_url = f"https://www.asus.com/{pdf_url}"

                            # Download and parse PDF
                            spec = await self._fetch_from_pdf(pdf_url, brand, model)
                            if spec:
                                return spec

                        # If no PDF found, try parsing HTML directly
                        spec = await self._fetch_from_html(response.content, url, brand, model)
                        if spec:
                            return spec

                except Exception as e:
                    logger.warning(f"Failed to fetch from {url}: {e}")
                    continue

            logger.warning(f"No ASUS specs found for {brand} {model}")
            return None

        except Exception as e:
            logger.error(f"Error fetching ASUS spec for {brand} {model}: {e}")
            raise ExternalServiceError(
                service="ASUS",
                message=f"Failed to fetch specification: {str(e)}"
            )

    async def _fetch_from_pdf(self, pdf_url: str, brand: str, model: str) -> Optional[DeviceSpec]:
        """Download and parse PDF datasheet."""
        try:
            response = await self.client.get(pdf_url)
            if response.status_code != 200:
                return None

            # Parse PDF
            parser = PDFParser()
            specs_data = await parser.parse(response.content, "application/pdf")

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
                logger.warning(f"ASUS PDF spec validation failed: {issues}")
                spec.confidence = ConfidenceLevel.MEDIUM

            return spec

        except Exception as e:
            logger.error(f"Failed to parse ASUS PDF {pdf_url}: {e}")
            return None

    async def _fetch_from_html(self, html_content: bytes, url: str, brand: str, model: str) -> Optional[DeviceSpec]:
        """Parse HTML specification page."""
        try:
            parser = HTMLParser()
            specs_data = await parser.parse(html_content, "text/html")

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
                logger.warning(f"ASUS HTML spec validation failed: {issues}")
                spec.confidence = ConfidenceLevel.LOW

            return spec

        except Exception as e:
            logger.error(f"Failed to parse ASUS HTML: {e}")
            return None

    def get_confidence_level(self, data_source: str) -> ConfidenceLevel:
        """Determine confidence level based on data source."""
        if "pdf" in data_source.lower() or "datasheet" in data_source.lower():
            return ConfidenceLevel.HIGH
        elif "spec" in data_source.lower() or "official" in data_source.lower():
            return ConfidenceLevel.HIGH
        elif "html" in data_source.lower():
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
