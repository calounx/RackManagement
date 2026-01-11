"""
Wikipedia-specific parser for extracting structured data from Wikipedia infoboxes.
Used by WikipediaFetcher to parse HTML content.
"""
import logging
from typing import Dict, Any, Optional
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WikipediaParser:
    """Parser for Wikipedia infobox and article data."""

    def parse_infobox(self, html: str) -> Dict[str, Any]:
        """
        Extract infobox data from Wikipedia HTML.

        Args:
            html: Wikipedia page HTML content

        Returns:
            Dictionary of parsed infobox data
        """
        soup = BeautifulSoup(html, 'lxml')
        infobox_data = {}

        # Find infobox table (multiple class patterns)
        infobox = soup.find("table", class_=re.compile(r"infobox", re.I))
        if not infobox:
            return infobox_data

        # Parse rows
        rows = infobox.find_all("tr")
        for row in rows:
            header = row.find("th")
            data = row.find("td")

            if header and data:
                key = header.get_text(strip=True).lower()
                value = self._clean_text(data.get_text(strip=True))
                infobox_data[key] = value

        return infobox_data

    def extract_first_paragraph(self, html: str) -> Optional[str]:
        """
        Extract the first meaningful paragraph as description.

        Args:
            html: Wikipedia page HTML content

        Returns:
            First paragraph text (cleaned, max 500 chars)
        """
        soup = BeautifulSoup(html, 'lxml')

        # Find paragraphs after infobox
        paragraphs = soup.find_all("p", limit=10)

        for p in paragraphs:
            text = p.get_text(strip=True)

            # Skip empty or very short paragraphs
            if len(text) < 50:
                continue

            # Clean up references [1], [2], etc.
            text = re.sub(r'\[\d+\]', '', text)
            text = re.sub(r'\[citation needed\]', '', text, flags=re.I)

            # Limit to 500 characters
            if len(text) > 500:
                text = text[:497] + "..."

            return text

        return None

    def extract_founded_year(self, infobox_data: Dict[str, str]) -> Optional[int]:
        """
        Extract founded year from infobox data.

        Args:
            infobox_data: Parsed infobox dictionary

        Returns:
            Founded year as integer, or None
        """
        # Common keys for founded information
        founded_keys = [
            "founded", "foundation", "established",
            "founded date", "establishment", "inception"
        ]

        for key in founded_keys:
            for infobox_key, value in infobox_data.items():
                if key in infobox_key:
                    year = self._extract_year(value)
                    if year:
                        return year

        return None

    def extract_headquarters(self, infobox_data: Dict[str, str]) -> Optional[str]:
        """
        Extract headquarters location from infobox data.

        Args:
            infobox_data: Parsed infobox dictionary

        Returns:
            Headquarters location string, or None
        """
        hq_keys = ["headquarters", "location", "hq", "headquarter"]

        for key in hq_keys:
            for infobox_key, value in infobox_data.items():
                if key in infobox_key and value:
                    # Clean up the location
                    location = self._clean_location(value)
                    if location:
                        return location[:200]  # Limit length

        return None

    def extract_website(self, infobox_data: Dict[str, str]) -> Optional[str]:
        """
        Extract official website URL from infobox data.

        Args:
            infobox_data: Parsed infobox dictionary

        Returns:
            Website URL, or None
        """
        website_keys = ["website", "url", "homepage", "official website"]

        for key in website_keys:
            for infobox_key, value in infobox_data.items():
                if key in infobox_key and value:
                    url = self._clean_url(value)
                    if url:
                        return url[:500]  # Limit length

        return None

    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing citations, extra whitespace, etc.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove citations [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        # Remove citation needed tags
        text = re.sub(r'\[citation needed\]', '', text, flags=re.I)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_year(self, text: str) -> Optional[int]:
        """
        Extract 4-digit year from text.

        Args:
            text: Text potentially containing a year

        Returns:
            Year as integer, or None
        """
        # Look for 4-digit year
        match = re.search(r'(\d{4})', text)
        if match:
            year = int(match.group(1))
            # Sanity check: reasonable year range
            if 1800 <= year <= 2100:
                return year

        return None

    def _clean_location(self, location: str) -> Optional[str]:
        """
        Clean location string (remove coordinates, references, etc.).

        Args:
            location: Raw location string

        Returns:
            Cleaned location string, or None
        """
        # Remove references [1], [2]
        location = re.sub(r'\[.*?\]', '', location)
        # Remove parentheses content (often coordinates)
        location = re.sub(r'\(.*?\)', '', location)
        # Remove extra whitespace
        location = re.sub(r'\s+', ' ', location)
        location = location.strip()

        if len(location) > 0:
            return location

        return None

    def _clean_url(self, url: str) -> Optional[str]:
        """
        Clean and validate URL string.

        Args:
            url: Raw URL string

        Returns:
            Cleaned URL, or None
        """
        # Remove whitespace
        url = url.strip()

        # If it already starts with http/https, return it
        if url.startswith("http://") or url.startswith("https://"):
            return url

        # If it looks like a domain, add https://
        if "." in url and " " not in url:
            return f"https://{url}"

        return None
