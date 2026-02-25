#!/usr/bin/env python3
"""
External Sources Data Loader

This script loads entities from external sources into the local database:
1. DOD Section 1260H - Chinese Military Companies (PDF)
2. FCC Covered List - Equipment/Services (Web)

Usage:
  python load_external_sources.py --all          # Load all sources
  python load_external_sources.py --dod          # Load DOD PDF only
  python load_external_sources.py --fcc          # Load FCC URL only
  python load_external_sources.py --refresh      # Clear and reload all
"""

import argparse
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    init_db,
    insert_local_entity,
    get_local_entity_count,
    clear_local_entities_by_source
)
from extractors import extract_dod_entities, extract_fcc_covered_list


# Source configuration
SOURCES_CONFIG = {
    'dod': {
        'name': 'DOD Section 1260H',
        'identifier': 'DOD_1260H',
        'pdf_path': 'external sources/ENTITIES-IDENTIFIED-AS-CHINESE-MILITARY-COMPANIES-OPERATING-IN-THE-UNITED-STATES.pdf',
        'url': 'https://media.defense.gov/2025/Jan/07/2003625471/-1/-1/1/ENTITIES-IDENTIFIED-AS-CHINESE-MILITARY-COMPANIES-OPERATING-IN-THE-UNITED-STATES.PDF'
    },
    'fcc': {
        'name': 'FCC Covered List',
        'identifier': 'FCC_COVERED',
        'url': 'https://www.fcc.gov/supplychain/coveredlist'
    }
}


def load_dod_list(refresh=False):
    """
    Load DOD Chinese Military Companies list from PDF.

    Args:
        refresh (bool): If True, clear existing entries before loading
    """
    config = SOURCES_CONFIG['dod']
    print(f"\n{'=' * 80}")
    print(f"Loading: {config['name']}")
    print(f"{'=' * 80}")

    # Clear existing if refresh requested
    if refresh:
        deleted = clear_local_entities_by_source(config['identifier'])
        print(f"✓ Cleared {deleted} existing entities")

    # Check if PDF exists
    pdf_path = config['pdf_path']
    if not os.path.exists(pdf_path):
        print(f"✗ Error: PDF file not found at '{pdf_path}'")
        print(f"  Please ensure the file exists in the 'external sources' directory")
        return 0

    # Extract entities from PDF
    print(f"Extracting entities from PDF...")
    entities = extract_dod_entities(pdf_path)

    if not entities:
        print(f"✗ No entities extracted from PDF")
        return 0

    # Insert into database
    print(f"Inserting {len(entities)} entities into database...")
    inserted_count = 0

    for name, entity_type, additional_info in entities:
        try:
            insert_local_entity(
                name=name,
                entity_type=entity_type,
                source_list=config['identifier'],
                source_url=config['url'],
                additional_info=additional_info
            )
            inserted_count += 1
        except Exception as e:
            print(f"  Warning: Failed to insert '{name}': {str(e)}")

    print(f"✓ Successfully loaded {inserted_count} entities from {config['name']}")
    return inserted_count


def load_fcc_list(refresh=False):
    """
    Load FCC Covered List from web.

    Args:
        refresh (bool): If True, clear existing entries before loading
    """
    config = SOURCES_CONFIG['fcc']
    print(f"\n{'=' * 80}")
    print(f"Loading: {config['name']}")
    print(f"{'=' * 80}")

    # Clear existing if refresh requested
    if refresh:
        deleted = clear_local_entities_by_source(config['identifier'])
        print(f"✓ Cleared {deleted} existing entities")

    # Extract entities from web
    print(f"Scraping entities from {config['url']}...")
    entities = extract_fcc_covered_list(config['url'])

    if not entities:
        print(f"✗ No entities extracted from webpage")
        print(f"  This may be due to:")
        print(f"    - Network connectivity issues")
        print(f"    - Website structure changes")
        print(f"    - Firewall/security restrictions")
        return 0

    # Insert into database
    print(f"Inserting {len(entities)} entities into database...")
    inserted_count = 0

    for name, entity_type, additional_info in entities:
        try:
            insert_local_entity(
                name=name,
                entity_type=entity_type,
                source_list=config['identifier'],
                source_url=config['url'],
                additional_info=additional_info
            )
            inserted_count += 1
        except Exception as e:
            print(f"  Warning: Failed to insert '{name}': {str(e)}")

    print(f"✓ Successfully loaded {inserted_count} entities from {config['name']}")
    return inserted_count


def print_summary():
    """Print summary of loaded entities."""
    print(f"\n{'=' * 80}")
    print("DATABASE SUMMARY")
    print(f"{'=' * 80}")

    counts = get_local_entity_count()

    for source_id, config in SOURCES_CONFIG.items():
        identifier = config['identifier']
        count = counts.get(identifier, 0)
        print(f"{config['name']}: {count} entities")

    print(f"\nTotal: {counts.get('TOTAL', 0)} entities")
    print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    parser = argparse.ArgumentParser(
        description='Load external sources into local database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python load_external_sources.py --all          # Load all sources
  python load_external_sources.py --dod          # Load DOD PDF only
  python load_external_sources.py --fcc          # Load FCC URL only
  python load_external_sources.py --refresh      # Clear and reload all
        """
    )

    parser.add_argument('--all', action='store_true',
                        help='Load all external sources')
    parser.add_argument('--dod', action='store_true',
                        help='Load DOD Section 1260H only')
    parser.add_argument('--fcc', action='store_true',
                        help='Load FCC Covered List only')
    parser.add_argument('--refresh', action='store_true',
                        help='Clear existing data before loading (use with --all, --dod, or --fcc)')

    args = parser.parse_args()

    # If no arguments, show help
    if not (args.all or args.dod or args.fcc):
        parser.print_help()
        sys.exit(1)

    # Initialize database
    print("Initializing database...")
    init_db()
    print("✓ Database initialized")

    # Load sources based on arguments
    total_loaded = 0

    if args.all or args.dod:
        total_loaded += load_dod_list(refresh=args.refresh)

    if args.all or args.fcc:
        total_loaded += load_fcc_list(refresh=args.refresh)

    # Print summary
    print_summary()

    print(f"\n{'=' * 80}")
    print(f"✓ Data loading complete: {total_loaded} total entities loaded")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
