"""
Web Scraper for FCC Covered List

This module scrapes the FCC Covered List from the official FCC website.
Source: https://www.fcc.gov/supplychain/coveredlist
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Tuple
import time


def extract_fcc_covered_list(url: str = "https://www.fcc.gov/supplychain/coveredlist") -> List[Tuple[str, str, str]]:
    """
    Scrape FCC Covered List from webpage.

    The FCC Covered List identifies equipment and services covered by
    Section 2 of the Secure Networks Act.

    Args:
        url (str): URL to the FCC Covered List webpage

    Returns:
        list: List of tuples [(name, entity_type, additional_info), ...]
    """
    entities = []

    try:
        print(f"Fetching FCC Covered List from: {url}")

        # Set headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

        # Fetch the webpage (increased timeout for slow government sites)
        response = requests.get(url, headers=headers, timeout=90)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')

        # Strategy 1: Look for tables (most likely format)
        entities_from_tables = _extract_from_tables(soup)
        if entities_from_tables:
            entities.extend(entities_from_tables)

        # Strategy 2: Look for lists (alternative format)
        if not entities:
            entities_from_lists = _extract_from_lists(soup)
            if entities_from_lists:
                entities.extend(entities_from_lists)

        # Strategy 3: Look for specific div/section patterns
        if not entities:
            entities_from_sections = _extract_from_sections(soup)
            if entities_from_sections:
                entities.extend(entities_from_sections)

        print(f"✓ Extracted {len(entities)} entities from FCC Covered List")

    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching webpage: {str(e)}")
    except Exception as e:
        print(f"✗ Error parsing webpage: {str(e)}")

    return entities


def _extract_from_tables(soup: BeautifulSoup) -> List[Tuple[str, str, str]]:
    """
    Extract entities from HTML tables.

    Special handling for FCC Covered List format where entity names
    are embedded in descriptions like "equipment produced by COMPANY NAME".

    Args:
        soup (BeautifulSoup): Parsed HTML

    Returns:
        list: List of entities
    """
    import re
    entities = []

    # Find all tables
    tables = soup.find_all('table')

    for table in tables:
        rows = table.find_all('tr')

        # Skip if table is too small (likely not data)
        if len(rows) < 2:
            continue

        # Try to identify header row
        headers = []
        header_row = rows[0]
        for th in header_row.find_all(['th', 'td']):
            headers.append(th.get_text(strip=True).lower())

        # Extract data rows
        for row in rows[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])

            if len(cells) >= 1:
                # Get the description (first column)
                description = cells[0].get_text(strip=True)

                # Get date (second column if available)
                date_added = ""
                if len(cells) >= 2:
                    date_added = cells[1].get_text(strip=True)

                # Extract entity name from description using regex patterns
                entity_name = None
                entity_type = "Equipment/Service"

                # Pattern 1: "produced by COMPANY NAME" or "provided by COMPANY NAME"
                pattern1 = r'(?:produced|provided|supplied)\s+by\s+([^,\.;]+?)(?:,|\.|;|including|to the extent|subject to)'
                match1 = re.search(pattern1, description, re.IGNORECASE)
                if match1:
                    entity_name = match1.group(1).strip()

                # Pattern 2: Look for "by COMPANY" pattern more broadly
                if not entity_name:
                    pattern2 = r'by\s+([A-Z][A-Za-z0-9\s\.\,\(\)]+?)(?:subject to|including|\.|,)'
                    match2 = re.search(pattern2, description)
                    if match2:
                        entity_name = match2.group(1).strip()

                # Clean up entity name
                if entity_name:
                    # Remove trailing "or", "and", etc.
                    entity_name = re.sub(r'\s+(or|and|any)$', '', entity_name, flags=re.IGNORECASE)

                    # Additional info is the full description
                    additional_info = f"Date Added: {date_added}. {description[:200]}"

                    entities.append((
                        entity_name,
                        entity_type,
                        additional_info
                    ))
                else:
                    # Fallback: If no pattern match, use first 50 chars as entity name
                    # (for rows that don't follow the "produced by X" pattern)
                    entity_name = description[:50].strip()
                    if len(entity_name) > 3:
                        entities.append((
                            entity_name,
                            entity_type,
                            f"Date Added: {date_added}. {description[:200]}"
                        ))

    return entities


def _extract_from_lists(soup: BeautifulSoup) -> List[Tuple[str, str, str]]:
    """
    Extract entities from HTML lists (ul, ol).

    Args:
        soup (BeautifulSoup): Parsed HTML

    Returns:
        list: List of entities
    """
    entities = []

    # Find all lists
    lists = soup.find_all(['ul', 'ol'])

    for lst in lists:
        items = lst.find_all('li')

        # Skip if list is too small
        if len(items) < 3:
            continue

        for item in items:
            text = item.get_text(strip=True)

            # Skip navigation/menu items (too short or contain common nav words)
            if len(text) < 3 or any(nav in text.lower() for nav in ['home', 'menu', 'search', 'contact']):
                continue

            # Entity name is the text
            entity_name = text

            entities.append((
                entity_name,
                "Equipment/Service",
                ""
            ))

    return entities


def _extract_from_sections(soup: BeautifulSoup) -> List[Tuple[str, str, str]]:
    """
    Extract entities from specific sections/divs with known patterns.

    Args:
        soup (BeautifulSoup): Parsed HTML

    Returns:
        list: List of entities
    """
    entities = []

    # Look for divs with specific classes or IDs that might contain the list
    possible_containers = soup.find_all(['div', 'section', 'article'])

    for container in possible_containers:
        # Check if this looks like it contains entity data
        text = container.get_text(strip=True)

        # Look for patterns like "Company Name - Description"
        # or lists separated by line breaks

        if len(text) < 100:  # Too short to be the main content
            continue

        # Try to find entity names within the container
        # This is a fallback strategy if tables/lists don't work

        # Look for strong/bold text which often indicates entity names
        bold_elements = container.find_all(['strong', 'b', 'h3', 'h4'])

        for element in bold_elements:
            entity_name = element.get_text(strip=True)

            if entity_name and len(entity_name) > 3:
                # Get context (next sibling or parent text)
                additional_info = ""
                if element.next_sibling:
                    additional_info = str(element.next_sibling).strip()[:200]

                entities.append((
                    entity_name,
                    "Equipment/Service",
                    additional_info
                ))

    return entities


# For testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.fcc.gov/supplychain/coveredlist"

    print(f"Scraping FCC Covered List from: {url}")
    print("=" * 80)

    entities = extract_fcc_covered_list(url)

    print(f"\nTotal entities extracted: {len(entities)}\n")
    print("Sample entities:")
    for i, (name, entity_type, info) in enumerate(entities[:10], 1):
        print(f"{i}. {name} ({entity_type})")
        if info:
            print(f"   Info: {info[:100]}...")
