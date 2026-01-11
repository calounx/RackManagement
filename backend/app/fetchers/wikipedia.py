"""
Wikipedia-specific fetcher for brand information.
Fetches brand data from Wikipedia using MediaWiki API.
"""
import logging
from typing import Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup
import re

from ..models import ConfidenceLevel

logger = logging.getLogger(__name__)


class BrandInfo:
    """Data class for brand information fetched from Wikipedia."""

    def __init__(
        self,
        name: str,
        slug: str,
        website: Optional[str] = None,
        description: Optional[str] = None,
        founded_year: Optional[int] = None,
        headquarters: Optional[str] = None,
        logo_url: Optional[str] = None,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        source: str = "wikipedia"
    ):
        self.name = name
        self.slug = slug
        self.website = website
        self.description = description
        self.founded_year = founded_year
        self.headquarters = headquarters
        self.logo_url = logo_url
        self.confidence = confidence
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "name": self.name,
            "slug": self.slug,
            "website": self.website,
            "description": self.description,
            "founded_year": self.founded_year,
            "headquarters": self.headquarters,
            "logo_url": self.logo_url,
            "fetch_confidence": self.confidence,
            "fetch_source": self.source
        }


class WikipediaFetcher:
    """Fetches brand information from Wikipedia using MediaWiki API."""

    BASE_URL = "https://en.wikipedia.org/w/api.php"
    TIMEOUT = 30.0

    def __init__(self):
        """Initialize Wikipedia fetcher with HTTP client."""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.TIMEOUT),
            headers={"User-Agent": "HomeRack/1.0 (Device Catalog Management)"},
            follow_redirects=True
        )

    async def close(self):
        """Close HTTP client connections."""
        await self.client.aclose()

    async def fetch_brand_info(self, brand_name: str) -> Optional[BrandInfo]:
        """
        Fetch brand information from Wikipedia.

        Args:
            brand_name: Brand name to search for

        Returns:
            BrandInfo object if found, None otherwise
        """
        try:
            # Step 1: Search for the page
            page_title = await self._search_page(brand_name)
            if not page_title:
                logger.warning(f"No Wikipedia page found for brand: {brand_name}")
                return None

            # Step 2: Get page content with infobox
            page_data = await self._fetch_page_content(page_title)
            if not page_data:
                logger.warning(f"Failed to fetch page content for: {page_title}")
                return None

            # Step 3: Parse infobox and extract data
            brand_info = await self._parse_page_data(page_data, brand_name)
            if not brand_info:
                logger.warning(f"Failed to parse brand data for: {page_title}")
                return None

            logger.info(f"Successfully fetched Wikipedia data for: {brand_name}")
            return brand_info

        except Exception as e:
            logger.error(f"Error fetching Wikipedia data for {brand_name}: {e}")
            return None

    async def _search_page(self, brand_name: str) -> Optional[str]:
        """
        Search for Wikipedia page matching brand name.

        Args:
            brand_name: Brand name to search

        Returns:
            Page title if found, None otherwise
        """
        try:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": brand_name,
                "format": "json",
                "srlimit": 5
            }

            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            search_results = data.get("query", {}).get("search", [])
            if not search_results:
                return None

            # Return the first result's title
            return search_results[0]["title"]

        except Exception as e:
            logger.error(f"Error searching Wikipedia for {brand_name}: {e}")
            return None

    async def _fetch_page_content(self, page_title: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full page content including infobox.

        Args:
            page_title: Wikipedia page title

        Returns:
            Dictionary with page data
        """
        try:
            params = {
                "action": "parse",
                "page": page_title,
                "prop": "text|images",
                "format": "json",
                "redirects": 1
            }

            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if "parse" not in data:
                return None

            return {
                "title": data["parse"]["title"],
                "html": data["parse"]["text"]["*"],
                "images": data["parse"].get("images", [])
            }

        except Exception as e:
            logger.error(f"Error fetching page content for {page_title}: {e}")
            return None

    async def _parse_page_data(self, page_data: Dict[str, Any], original_name: str) -> Optional[BrandInfo]:
        """
        Parse Wikipedia page data to extract brand information.

        Args:
            page_data: Dictionary with page HTML and metadata
            original_name: Original brand name from user input

        Returns:
            BrandInfo object
        """
        try:
            html = page_data["html"]
            soup = BeautifulSoup(html, 'lxml')

            # Extract infobox data
            infobox = self._extract_infobox(soup)

            # Extract description (first paragraph)
            description = self._extract_description(soup)

            # Extract specific fields from infobox
            founded_year = self._extract_founded_year(infobox)
            headquarters = self._extract_headquarters(infobox)
            website = self._extract_website(infobox)

            # Try to get logo from images
            logo_url = await self._extract_logo_url(page_data.get("images", []))

            # Create slug from original name
            slug = self._create_slug(original_name)

            brand_info = BrandInfo(
                name=original_name,
                slug=slug,
                website=website,
                description=description,
                founded_year=founded_year,
                headquarters=headquarters,
                logo_url=logo_url,
                confidence=ConfidenceLevel.MEDIUM,
                source="wikipedia"
            )

            return brand_info

        except Exception as e:
            logger.error(f"Error parsing page data: {e}")
            return None

    def _extract_infobox(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract infobox data from Wikipedia page.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Dictionary of infobox key-value pairs
        """
        infobox_data = {}

        # Find infobox table
        infobox = soup.find("table", class_=re.compile(r"infobox", re.I))
        if not infobox:
            return infobox_data

        # Parse rows
        rows = infobox.find_all("tr")
        for row in rows:
            # Look for header (th) and data (td) pairs
            header = row.find("th")
            data = row.find("td")

            if header and data:
                key = header.get_text(strip=True).lower()
                value = data.get_text(strip=True)
                infobox_data[key] = value

        return infobox_data

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract first paragraph as description.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Description text (first paragraph, max 500 chars)
        """
        # Find the first paragraph after the infobox
        paragraphs = soup.find_all("p", limit=10)

        for p in paragraphs:
            text = p.get_text(strip=True)

            # Skip empty paragraphs or very short ones
            if len(text) < 50:
                continue

            # Clean up references like [1], [2]
            text = re.sub(r'\[\d+\]', '', text)

            # Limit to 500 characters
            if len(text) > 500:
                text = text[:497] + "..."

            return text

        return None

    def _extract_founded_year(self, infobox: Dict[str, str]) -> Optional[int]:
        """
        Extract founded year from infobox.

        Args:
            infobox: Dictionary of infobox data

        Returns:
            Founded year as integer, or None
        """
        # Common keys for founded year
        keys = ["founded", "foundation", "established", "founded date"]

        for key in keys:
            for infobox_key, value in infobox.items():
                if key in infobox_key:
                    # Extract 4-digit year
                    match = re.search(r'(\d{4})', value)
                    if match:
                        year = int(match.group(1))
                        # Sanity check: year between 1800 and current year + 1
                        if 1800 <= year <= 2100:
                            return year

        return None

    def _extract_headquarters(self, infobox: Dict[str, str]) -> Optional[str]:
        """
        Extract headquarters location from infobox.

        Args:
            infobox: Dictionary of infobox data

        Returns:
            Headquarters location string, or None
        """
        # Common keys for headquarters
        keys = ["headquarters", "location", "hq"]

        for key in keys:
            for infobox_key, value in infobox.items():
                if key in infobox_key and value:
                    # Clean up the value (remove coordinates, etc.)
                    value = re.sub(r'\[.*?\]', '', value)  # Remove references
                    value = re.sub(r'\(.*?\)', '', value)  # Remove parentheses
                    value = value.strip()
                    if len(value) > 0:
                        return value[:200]  # Limit length

        return None

    def _extract_website(self, infobox: Dict[str, str]) -> Optional[str]:
        """
        Extract official website URL from infobox.

        Args:
            infobox: Dictionary of infobox data

        Returns:
            Website URL string, or None
        """
        # Common keys for website
        keys = ["website", "url", "homepage"]

        for key in keys:
            for infobox_key, value in infobox.items():
                if key in infobox_key and value:
                    # Clean URL (remove whitespace, etc.)
                    value = value.strip()

                    # Ensure it's a valid URL
                    if value.startswith("http"):
                        return value[:500]  # Limit length

                    # Add https if missing
                    if "." in value and not value.startswith("http"):
                        return f"https://{value}"[:500]

        return None

    async def _extract_logo_url(self, images: list) -> Optional[str]:
        """
        Extract logo URL from Wikipedia images.

        Args:
            images: List of image filenames from Wikipedia API

        Returns:
            Logo URL, or None
        """
        # Look for logo in images list
        for image in images:
            image_lower = image.lower()
            if "logo" in image_lower and (image_lower.endswith(".png") or
                                          image_lower.endswith(".svg") or
                                          image_lower.endswith(".jpg")):
                # Construct Wikimedia Commons URL
                # Note: This is a simplified approach. For production, you'd want to
                # use the imageinfo API to get the actual file URL
                filename = image.replace(" ", "_")
                return f"https://en.wikipedia.org/wiki/File:{filename}"

        return None

    def _create_slug(self, name: str) -> str:
        """
        Create URL-friendly slug from brand name.

        Args:
            name: Brand name

        Returns:
            Slugified name
        """
        # Convert to lowercase
        slug = name.lower()

        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)

        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        return slug
