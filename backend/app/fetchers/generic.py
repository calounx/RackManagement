"""
Generic fallback device specification fetcher.
Uses web search and heuristic parsing when manufacturer-specific fetcher unavailable.
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


class GenericFetcher(BaseSpecFetcher):
    """
    Generic fallback fetcher for any manufacturer.

    Uses heuristic search and parsing strategies:
    1. Search for "{brand} {model} specifications" or "datasheet"
    2. Try common documentation URL patterns
    3. Download and parse PDFs
    4. Parse HTML tables
    5. Mark with LOW confidence for manual review
    """

    @property
    def manufacturer_name(self) -> str:
        return "Generic"

    async def search_product(self, brand: str, model: str) -> List[str]:
        """
        Generate potential product documentation URLs.

        Uses common patterns across manufacturers.
        """
        urls = []

        clean_model = model.replace(" ", "-").lower()
        clean_brand = brand.replace(" ", "-").lower()

        # Common URL patterns
        patterns = [
            f"https://www.{clean_brand}.com/products/{clean_model}",
            f"https://www.{clean_brand}.com/support/{clean_model}",
            f"https://{clean_brand}.com/{clean_model}",
            f"https://support.{clean_brand}.com/{clean_model}",
            f"https://www.{clean_brand}.com/en-us/products/{clean_model}",
        ]

        urls.extend(patterns)

        return urls

    async def fetch_spec(self, brand: str, model: str) -> Optional[DeviceSpec]:
        """
        Fetch device specification using generic strategies.

        Strategy:
        1. Try common URL patterns
        2. Look for specification PDFs
        3. Parse HTML specification tables
        4. All results marked LOW confidence for review
        """
        try:
            urls = await self.search_product(brand, model)

            # Try each potential URL
            for url in urls:
                try:
                    response = await self.client.get(url)

                    if response.status_code == 200:
                        # Look for PDF links
                        soup = BeautifulSoup(response.content, 'lxml')

                        # Find specification PDFs
                        pdf_links = soup.find_all('a', href=re.compile(r'.*\.pdf$'))
                        spec_pdfs = [
                            link for link in pdf_links
                            if any(keyword in link.get('href', '').lower()
                                   for keyword in ['spec', 'datasheet', 'data_sheet', 'quickspecs'])
                        ]

                        if spec_pdfs:
                            pdf_url = spec_pdfs[0].get('href')
                            if not pdf_url.startswith('http'):
                                # Construct absolute URL
                                from urllib.parse import urljoin
                                pdf_url = urljoin(url, pdf_url)

                            spec = await self._fetch_from_pdf(pdf_url, brand, model)
                            if spec:
                                return spec

                        # Try parsing HTML directly
                        spec = await self._fetch_from_html(response.content, url, brand, model)
                        if spec:
                            return spec

                except Exception as e:
                    logger.debug(f"Generic fetch failed for {url}: {e}")
                    continue

            logger.warning(f"No generic specs found for {brand} {model}")
            return None

        except Exception as e:
            logger.error(f"Error in generic fetch for {brand} {model}: {e}")
            raise ExternalServiceError(
                service="Generic",
                message=f"Failed to fetch specification: {str(e)}"
            )

    async def _fetch_from_pdf(self, pdf_url: str, brand: str, model: str) -> Optional[DeviceSpec]:
        """Download and parse PDF using generic strategies."""
        try:
            response = await self.client.get(pdf_url)
            if response.status_code != 200:
                return None

            # Check PDF size limit
            content_length = int(response.headers.get('content-length', 0))
            max_size = self.client.timeout.connect * 1024 * 1024  # Use timeout as proxy for max MB

            if content_length > max_size:
                logger.warning(f"PDF too large ({content_length} bytes): {pdf_url}")
                return None

            # Parse PDF
            parser = PDFParser()
            specs_data = await parser.parse(response.content, "application/pdf")

            if not specs_data or len(specs_data) < 2:
                logger.warning(f"Insufficient data from generic PDF: {pdf_url}")
                return None

            # Create DeviceSpec with LOW confidence
            spec = DeviceSpec(
                brand=brand,
                model=model,
                source_url=pdf_url,
                confidence=ConfidenceLevel.LOW,  # Generic parsing is unreliable
                **specs_data
            )

            # Validate
            is_valid, issues = self._validate_spec(spec)
            if not is_valid:
                logger.warning(f"Generic PDF spec validation failed: {issues}")
                return None  # Don't return invalid specs

            return spec

        except Exception as e:
            logger.error(f"Failed to parse generic PDF {pdf_url}: {e}")
            return None

    async def _fetch_from_html(self, html_content: bytes, url: str, brand: str, model: str) -> Optional[DeviceSpec]:
        """Parse HTML using generic strategies."""
        try:
            parser = HTMLParser()
            specs_data = await parser.parse(html_content, "text/html")

            if not specs_data or len(specs_data) < 2:
                logger.warning(f"Insufficient data from generic HTML: {url}")
                return None

            # Create DeviceSpec with LOW confidence
            spec = DeviceSpec(
                brand=brand,
                model=model,
                source_url=url,
                confidence=ConfidenceLevel.LOW,  # Generic parsing needs review
                **specs_data
            )

            # Validate
            is_valid, issues = self._validate_spec(spec)
            if not is_valid:
                logger.warning(f"Generic HTML spec validation failed: {issues}")
                return None  # Don't return invalid specs

            return spec

        except Exception as e:
            logger.error(f"Failed to parse generic HTML: {e}")
            return None

    def get_confidence_level(self, data_source: str) -> ConfidenceLevel:
        """Generic fetcher always returns LOW confidence."""
        return ConfidenceLevel.LOW


class SearchBasedFetcher(GenericFetcher):
    """
    Extended generic fetcher that uses search engines.

    Future enhancement: Integrate with Google Custom Search API
    or DuckDuckGo to find product pages dynamically.
    """

    async def search_product(self, brand: str, model: str) -> List[str]:
        """
        Use web search to find product pages.

        TODO: Implement search engine integration
        - Google Custom Search API
        - DuckDuckGo API
        - Bing Search API

        Search query examples:
        - "{brand} {model} specifications datasheet"
        - "{brand} {model} rack mount specifications"
        - "{brand} {model} technical specifications pdf"
        """
        # For now, fall back to parent implementation
        urls = await super().search_product(brand, model)

        # Placeholder for future search integration
        logger.info(f"Search-based fetching not yet implemented for {brand} {model}")

        return urls
