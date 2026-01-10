"""
Dell-specific device specification fetcher.
Fetches specs from Dell support pages and QuickSpecs PDFs.
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


class DellFetcher(BaseSpecFetcher):
    """Fetcher for Dell server and networking equipment specifications."""

    @property
    def manufacturer_name(self) -> str:
        return "Dell"

    async def search_product(self, brand: str, model: str) -> List[str]:
        """
        Search for Dell product pages.

        Dell product URLs:
        - https://www.dell.com/support/home/en-us/product-support/product/{model}/docs
        - https://www.dell.com/support/home/en-us/product-support/product/{model}/specs
        - https://www.dell.com/en-us/business/products/servers/{model}
        """
        urls = []

        # Clean model number (remove spaces)
        clean_model = model.replace(" ", "-").lower()

        # Dell support documentation page
        urls.append(f"https://www.dell.com/support/home/en-us/product-support/product/{clean_model}/docs")

        # Dell support specifications page
        urls.append(f"https://www.dell.com/support/home/en-us/product-support/product/{clean_model}/specs")

        # Dell business product page
        urls.append(f"https://www.dell.com/en-us/business/products/servers/{clean_model}")

        # Alternative: Dell EMC support (for EMC products)
        urls.append(f"https://www.dellemc.com/support/home/en-us/product-support/product/{clean_model}/docs")

        # Search for QuickSpecs PDF
        urls.append(f"https://www.dell.com/support/home/en-us/product-support/product/{clean_model}/quickspecs")

        return urls

    async def fetch_spec(self, brand: str, model: str) -> Optional[DeviceSpec]:
        """
        Fetch Dell device specification.

        Strategy:
        1. Try to find QuickSpecs PDF (most reliable)
        2. Download and parse QuickSpecs PDF
        3. Fall back to HTML specifications page
        4. Try support pages for additional data
        """
        try:
            urls = await self.search_product(brand, model)

            for url in urls:
                try:
                    response = await self.client.get(url)

                    if response.status_code == 200:
                        # Check if this is a PDF
                        content_type = response.headers.get('content-type', '')
                        if 'pdf' in content_type.lower():
                            # Parse PDF
                            spec = await self._fetch_from_pdf(url, response.content, brand, model)
                            if spec:
                                return spec
                        else:
                            # Parse HTML - look for QuickSpecs PDF link first
                            soup = BeautifulSoup(response.content, 'lxml')

                            # Look for QuickSpecs PDF link
                            pdf_links = soup.find_all('a', href=re.compile(r'.*\.pdf$', re.IGNORECASE))
                            quickspecs_links = [
                                link for link in pdf_links
                                if 'quickspec' in link.get('href', '').lower() or
                                   'datasheet' in link.get('href', '').lower()
                            ]

                            if quickspecs_links:
                                pdf_url = quickspecs_links[0].get('href')
                                if not pdf_url.startswith('http'):
                                    if pdf_url.startswith('/'):
                                        pdf_url = f"https://www.dell.com{pdf_url}"
                                    else:
                                        pdf_url = f"https://www.dell.com/support/home/en-us/product-support/{pdf_url}"

                                # Download and parse PDF
                                spec = await self._fetch_from_pdf(pdf_url, None, brand, model, download=True)
                                if spec:
                                    return spec

                            # If no PDF found, try parsing HTML directly
                            spec = await self._fetch_from_html(response.content, url, brand, model)
                            if spec:
                                return spec

                except Exception as e:
                    logger.warning(f"Failed to fetch from {url}: {e}")
                    continue

            logger.warning(f"No Dell specs found for {brand} {model}")
            return None

        except Exception as e:
            logger.error(f"Error fetching Dell spec for {brand} {model}: {e}")
            raise ExternalServiceError(
                service="Dell",
                message=f"Failed to fetch specification: {str(e)}"
            )

    async def _fetch_from_pdf(self, pdf_url: str, content: Optional[bytes], brand: str, model: str, download: bool = False) -> Optional[DeviceSpec]:
        """Download and parse QuickSpecs PDF or other datasheet."""
        try:
            # Download if needed
            if download or content is None:
                response = await self.client.get(pdf_url)
                if response.status_code != 200:
                    return None
                content = response.content

            # Parse PDF
            parser = PDFParser()
            specs_data = await parser.parse(content, "application/pdf")

            if not specs_data:
                return None

            # Create DeviceSpec
            spec = DeviceSpec(
                brand=brand,
                model=model,
                source_url=pdf_url,
                confidence=ConfidenceLevel.HIGH,  # QuickSpecs PDFs are high quality
                **specs_data
            )

            # Validate
            is_valid, issues = self._validate_spec(spec)
            if not is_valid:
                logger.warning(f"Dell PDF spec validation failed: {issues}")
                spec.confidence = ConfidenceLevel.MEDIUM

            return spec

        except Exception as e:
            logger.error(f"Failed to parse Dell PDF {pdf_url}: {e}")
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
                logger.warning(f"Dell HTML spec validation failed: {issues}")
                spec.confidence = ConfidenceLevel.LOW

            return spec

        except Exception as e:
            logger.error(f"Failed to parse Dell HTML: {e}")
            return None

    def get_confidence_level(self, data_source: str) -> ConfidenceLevel:
        """Determine confidence level based on data source."""
        source_lower = data_source.lower()
        if "quickspec" in source_lower or "pdf" in source_lower or "datasheet" in source_lower:
            return ConfidenceLevel.HIGH
        elif "html" in source_lower or "spec" in source_lower:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
