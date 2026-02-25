"""
PDF Extractor for DOD Chinese Military Companies List (Section 1260H)

This module extracts entity names from the Department of Defense list of
Chinese Military Companies operating in the United States.
"""

import PyPDF2
import re
from typing import List, Tuple


def extract_dod_entities(pdf_path: str) -> List[Tuple[str, str, str]]:
    """
    Extract entity names from DOD 1260H PDF.

    The PDF structure is typically:
    - Numbered list format (e.g., "1. Company Name")
    - May span multiple pages
    - May include Chinese characters and parenthetical information

    Args:
        pdf_path (str): Path to the DOD PDF file

    Returns:
        list: List of tuples [(name, entity_type, additional_info), ...]
    """
    entities = []

    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            full_text = ""

            # Extract text from all pages
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                full_text += text + "\n"

            # Parse the text to extract entity names
            entities = _parse_dod_text(full_text)

            print(f"✓ Extracted {len(entities)} entities from DOD 1260H PDF")

    except FileNotFoundError:
        print(f"✗ Error: PDF file not found at {pdf_path}")
    except Exception as e:
        print(f"✗ Error extracting PDF: {str(e)}")

    return entities


def _parse_dod_text(text: str) -> List[Tuple[str, str, str]]:
    """
    Parse extracted PDF text to identify entity names.

    The DOD Section 1260H list uses a plain format:
    - Each entity name is on its own line
    - Subsidiary/related entities are indented
    - Abbreviated names shown in parentheses
    - Separated by blank lines

    Args:
        text (str): Raw text extracted from PDF

    Returns:
        list: List of tuples [(name, entity_type, additional_info), ...]
    """
    entities = []

    # Split into lines
    lines = text.split('\n')

    # Skip patterns (header/footer/metadata)
    skip_patterns = [
        'entities identified as chinese military companies',
        'section 1260h',
        'william m.',
        'thornberry national defense',
        'authorization act',
        'public law',
        'page ',
        'unclassified',
        'footnote',
        'previously identified',
        'united states in accordance'
    ]

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip lines with skip patterns
        if any(skip.lower() in line.lower() for skip in skip_patterns):
            continue

        # Skip very short lines (likely noise)
        if len(line) < 5:
            continue

        # Skip lines that are just numbers or symbols
        if re.match(r'^[\d\s\-\*]+$', line):
            continue

        # This is likely an entity name
        entity_name = line.strip()

        # Clean the entity name
        entity_name = _clean_entity_name(entity_name)

        if entity_name and len(entity_name) > 2:
            # Extract additional info (Chinese characters, aliases)
            additional_info = _extract_additional_info(entity_name)

            entities.append((
                entity_name,
                'Company',  # DOD list is primarily companies
                additional_info
            ))

    # Deduplicate entities (in case of parsing errors)
    # Use a dict to preserve order while removing duplicates
    unique_entities = {}
    for name, entity_type, info in entities:
        # Use lowercase name as key for deduplication
        key = name.lower()
        if key not in unique_entities:
            unique_entities[key] = (name, entity_type, info)

    return list(unique_entities.values())


def _clean_entity_name(name: str) -> str:
    """
    Clean entity name by removing artifacts and normalizing.

    Args:
        name (str): Raw entity name

    Returns:
        str: Cleaned entity name
    """
    # Remove extra whitespace
    name = ' '.join(name.split())

    # Remove trailing punctuation that might be parsing artifacts
    name = name.rstrip('.,;:')

    return name


def _extract_additional_info(name: str) -> str:
    """
    Extract additional information from entity name.

    This includes:
    - Chinese characters (e.g., "华为")
    - Aliases in parentheses (e.g., "(a.k.a. Alternative Name)")
    - Country indicators

    Args:
        name (str): Entity name

    Returns:
        str: Additional information as JSON-like string
    """
    info_parts = []

    # Check for Chinese characters
    if re.search(r'[\u4e00-\u9fff]', name):
        info_parts.append("Contains Chinese characters")

    # Check for parenthetical information
    parenthetical = re.findall(r'\(([^)]+)\)', name)
    if parenthetical:
        info_parts.append(f"Aliases: {', '.join(parenthetical)}")

    return "; ".join(info_parts) if info_parts else ""


# For testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default path
        pdf_path = "../external sources/ENTITIES-IDENTIFIED-AS-CHINESE-MILITARY-COMPANIES-OPERATING-IN-THE-UNITED-STATES.pdf"

    print(f"Extracting entities from: {pdf_path}")
    print("=" * 80)

    entities = extract_dod_entities(pdf_path)

    print(f"\nTotal entities extracted: {len(entities)}\n")
    print("Sample entities:")
    for i, (name, entity_type, info) in enumerate(entities[:10], 1):
        print(f"{i}. {name}")
        if info:
            print(f"   Info: {info}")
