#!/usr/bin/env python3
"""
Phase 2 Data Migration Script: device_specifications → brands + models

This script migrates data from the legacy device_specifications table to the new
normalized brands and models structure while maintaining data integrity and
backward compatibility.

Usage:
    python scripts/migrate_specs_to_catalog.py [options]

Options:
    --dry-run          Preview changes without committing to database
    --verbose          Enable detailed logging
    --batch-size N     Process N specifications at a time (default: 100)
    --skip-duplicates  Skip duplicate entries instead of raising errors
"""

import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import re
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal, engine
from app.models import (
    DeviceSpecification,
    DeviceType,
    Brand,
    Model,
    MigrationStatus,
    WidthType,
    AirflowPattern,
    SourceType,
    ConfidenceLevel,
)


# ============================================================================
# Utility Functions
# ============================================================================

def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug format.

    Args:
        text: Input text to slugify

    Returns:
        Slugified text (lowercase, alphanumeric + hyphens)
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)

    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r'[^a-z0-9-]', '', text)

    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)

    # Strip hyphens from start and end
    text = text.strip('-')

    return text


def infer_device_type(brand: str, model: str, db: Session) -> int:
    """
    Infer device type ID from brand and model name.

    Args:
        brand: Device brand name
        model: Device model name
        db: Database session

    Returns:
        Device type ID
    """
    # Cache device types to avoid repeated queries
    if not hasattr(infer_device_type, '_cache'):
        infer_device_type._cache = {}
        for dt in db.query(DeviceType).all():
            infer_device_type._cache[dt.slug] = dt.id

    cache = infer_device_type._cache
    combined = f"{brand} {model}".lower()

    # Check for keywords and product lines in order of specificity
    # Format: (keyword/pattern, device_type_slug)
    patterns = [
        # Switches - specific product lines first
        ('catalyst', 'switch'),      # Cisco Catalyst
        ('nexus', 'switch'),         # Cisco Nexus
        ('powerconnect', 'switch'),  # Dell PowerConnect
        ('aruba', 'switch'),         # HPE Aruba
        ('procurve', 'switch'),      # HP ProCurve
        ('switch', 'switch'),        # Generic

        # Routers
        ('asr', 'router'),           # Cisco ASR
        ('isr', 'router'),           # Cisco ISR
        ('router', 'router'),        # Generic

        # Firewalls
        ('fortigate', 'firewall'),   # Fortinet FortiGate
        ('palo alto', 'firewall'),   # Palo Alto
        ('asa', 'firewall'),         # Cisco ASA
        ('firewall', 'firewall'),    # Generic
        ('firepower', 'firewall'),   # Cisco Firepower

        # Servers
        ('poweredge', 'server'),     # Dell PowerEdge
        ('proliant', 'server'),      # HPE ProLiant
        ('primergy', 'server'),      # Fujitsu Primergy
        ('thinkserver', 'server'),   # Lenovo ThinkServer
        ('server', 'server'),        # Generic

        # Storage
        ('powerstore', 'storage'),   # Dell PowerStore
        ('powervault', 'storage'),   # Dell PowerVault
        ('nimble', 'storage'),       # HPE Nimble
        ('compellent', 'storage'),   # Dell Compellent
        ('storage', 'storage'),      # Generic
        ('san', 'storage'),          # Storage Area Network
        ('nas', 'storage'),          # Network Attached Storage

        # PDUs
        ('pdu', 'pdu'),
        ('power distribution', 'pdu'),
        ('rack pdu', 'pdu'),

        # UPS
        ('ups', 'ups'),
        ('uninterruptible', 'ups'),
        ('smart-ups', 'ups'),        # APC Smart-UPS

        # Patch Panels
        ('patch panel', 'patch_panel'),
        ('patch', 'patch_panel'),
    ]

    for pattern, slug in patterns:
        if pattern in combined:
            return cache.get(slug, cache['other'])

    # Default to 'other'
    return cache['other']


# ============================================================================
# Migration Functions
# ============================================================================

class MigrationStats:
    """Track migration statistics"""

    def __init__(self):
        self.specs_total = 0
        self.specs_processed = 0
        self.specs_migrated = 0
        self.specs_skipped = 0
        self.specs_failed = 0
        self.brands_created = 0
        self.brands_reused = 0
        self.models_created = 0
        self.models_duplicates = 0
        self.errors: List[Tuple[int, str]] = []
        self.start_time = datetime.utcnow()

    def add_error(self, spec_id: int, error_msg: str):
        """Add an error to the error list"""
        self.errors.append((spec_id, error_msg))
        self.specs_failed += 1

    def print_summary(self):
        """Print migration summary"""
        duration = (datetime.utcnow() - self.start_time).total_seconds()

        print("\n" + "="*70)
        print("MIGRATION SUMMARY")
        print("="*70)
        print(f"Duration: {duration:.2f} seconds")
        print(f"\nSpecifications:")
        print(f"  Total found:     {self.specs_total}")
        print(f"  Processed:       {self.specs_processed}")
        print(f"  Migrated:        {self.specs_migrated}")
        print(f"  Skipped:         {self.specs_skipped}")
        print(f"  Failed:          {self.specs_failed}")
        print(f"\nBrands:")
        print(f"  Created:         {self.brands_created}")
        print(f"  Reused:          {self.brands_reused}")
        print(f"\nModels:")
        print(f"  Created:         {self.models_created}")
        print(f"  Duplicates:      {self.models_duplicates}")

        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for spec_id, error_msg in self.errors[:10]:  # Show first 10
                print(f"  Spec ID {spec_id}: {error_msg}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")

        print("="*70 + "\n")


def find_or_create_brand(
    brand_name: str,
    db: Session,
    stats: MigrationStats,
    dry_run: bool = False
) -> Optional[Brand]:
    """
    Find existing brand or create a new one.

    Args:
        brand_name: Brand name to find or create
        db: Database session
        stats: Migration statistics object
        dry_run: If True, don't commit changes

    Returns:
        Brand object or None if dry_run
    """
    if not brand_name or not brand_name.strip():
        raise ValueError("Brand name cannot be empty")

    brand_name = brand_name.strip()
    slug = slugify(brand_name)

    # Try to find existing brand (case-insensitive)
    existing = db.query(Brand).filter(
        Brand.name.ilike(brand_name)
    ).first()

    if existing:
        stats.brands_reused += 1
        return existing

    # Create new brand
    if dry_run:
        logging.info(f"  [DRY-RUN] Would create brand: {brand_name} (slug: {slug})")
        stats.brands_created += 1
        return None

    brand = Brand(
        name=brand_name,
        slug=slug,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(brand)
    db.flush()  # Get the ID without committing

    stats.brands_created += 1
    logging.info(f"  Created brand: {brand_name} (ID: {brand.id})")

    return brand


def migrate_specification(
    spec: DeviceSpecification,
    db: Session,
    stats: MigrationStats,
    dry_run: bool = False,
    skip_duplicates: bool = False
) -> bool:
    """
    Migrate a single device specification to the new catalog structure.

    Args:
        spec: DeviceSpecification to migrate
        db: Database session
        stats: Migration statistics object
        dry_run: If True, don't commit changes
        skip_duplicates: If True, skip duplicates instead of failing

    Returns:
        True if migration successful, False otherwise
    """
    try:
        # Check if already migrated
        if spec.migration_status == MigrationStatus.COMPLETED:
            logging.debug(f"  Spec ID {spec.id} already migrated, skipping")
            stats.specs_skipped += 1
            return True

        # Validate required fields
        if not spec.brand or not spec.model:
            raise ValueError("Brand and model are required")

        # Find or create brand
        brand = find_or_create_brand(spec.brand, db, stats, dry_run)
        brand_id = brand.id if brand else None

        # Infer device type
        device_type_id = infer_device_type(spec.brand, spec.model, db)

        # Check for existing model (duplicate)
        if not dry_run:
            existing_model = db.query(Model).filter(
                Model.brand_id == brand_id,
                Model.name == spec.model,
                Model.variant == spec.variant
            ).first()

            if existing_model:
                if skip_duplicates:
                    logging.warning(
                        f"  Duplicate model found: {spec.brand} {spec.model} "
                        f"(variant: {spec.variant}), skipping"
                    )
                    stats.models_duplicates += 1
                    stats.specs_skipped += 1

                    # Update spec with existing model
                    spec.migrated_to_model_id = existing_model.id
                    spec.migration_status = MigrationStatus.COMPLETED
                    db.flush()

                    return True
                else:
                    raise IntegrityError(
                        "Duplicate model",
                        None,
                        None
                    )

        # Convert enum values to strings for Model
        width_type_str = spec.width_type.value if spec.width_type else None
        airflow_str = spec.airflow_pattern.value if spec.airflow_pattern else None
        source_str = spec.source.value if spec.source else None
        confidence_str = spec.confidence.value if spec.confidence else None

        if dry_run:
            logging.info(
                f"  [DRY-RUN] Would create model: {spec.brand} {spec.model} "
                f"(variant: {spec.variant}, type_id: {device_type_id})"
            )
            stats.models_created += 1
            stats.specs_migrated += 1
            return True

        # Create new Model
        model = Model(
            brand_id=brand_id,
            device_type_id=device_type_id,
            name=spec.model,
            variant=spec.variant,
            height_u=spec.height_u,
            width_type=width_type_str,
            depth_mm=spec.depth_mm,
            weight_kg=spec.weight_kg,
            power_watts=spec.power_watts,
            heat_output_btu=spec.heat_output_btu,
            airflow_pattern=airflow_str,
            max_operating_temp_c=spec.max_operating_temp_c,
            typical_ports=spec.typical_ports,
            mounting_type=spec.mounting_type,
            datasheet_url=spec.source_url,
            source=source_str,
            confidence=confidence_str,
            fetched_at=spec.fetched_at,
            last_updated=spec.last_updated or datetime.utcnow()
        )

        db.add(model)
        db.flush()  # Get the ID without committing

        # Update specification with migration info
        spec.migrated_to_model_id = model.id
        spec.migration_status = MigrationStatus.COMPLETED
        db.flush()

        stats.models_created += 1
        stats.specs_migrated += 1

        logging.info(
            f"  Migrated: {spec.brand} {spec.model} → Model ID {model.id} "
            f"(Device Type: {device_type_id})"
        )

        return True

    except Exception as e:
        error_msg = str(e)
        logging.error(f"  Failed to migrate spec ID {spec.id}: {error_msg}")
        stats.add_error(spec.id, error_msg)

        if not dry_run:
            spec.migration_status = MigrationStatus.FAILED
            db.flush()

        return False


def run_migration(
    batch_size: int = 100,
    dry_run: bool = False,
    skip_duplicates: bool = False
) -> MigrationStats:
    """
    Run the full migration process.

    Args:
        batch_size: Number of specs to process per batch
        dry_run: If True, don't commit changes
        skip_duplicates: If True, skip duplicates instead of failing

    Returns:
        Migration statistics object
    """
    stats = MigrationStats()
    db = SessionLocal()

    try:
        # Get total count
        stats.specs_total = db.query(DeviceSpecification).count()

        if stats.specs_total == 0:
            logging.warning("No device specifications found to migrate")
            return stats

        logging.info(f"Found {stats.specs_total} device specifications to migrate")

        if dry_run:
            logging.info("DRY-RUN MODE: No changes will be committed")

        # Process in batches
        offset = 0
        while offset < stats.specs_total:
            # Get batch
            specs = db.query(DeviceSpecification)\
                .offset(offset)\
                .limit(batch_size)\
                .all()

            if not specs:
                break

            logging.info(
                f"\nProcessing batch {offset // batch_size + 1} "
                f"({offset + 1}-{min(offset + len(specs), stats.specs_total)} "
                f"of {stats.specs_total})"
            )

            # Process each spec in batch
            for spec in specs:
                stats.specs_processed += 1
                migrate_specification(spec, db, stats, dry_run, skip_duplicates)

            # Commit batch
            if not dry_run:
                db.commit()
                logging.info(f"  Committed batch {offset // batch_size + 1}")

            offset += len(specs)

        if not dry_run:
            db.commit()

        logging.info("\nMigration completed successfully")

    except Exception as e:
        logging.error(f"Migration failed: {e}")
        if not dry_run:
            db.rollback()
        raise

    finally:
        db.close()

    return stats


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for migration script"""
    parser = argparse.ArgumentParser(
        description="Migrate device_specifications to brands + models structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview migration without making changes
  python scripts/migrate_specs_to_catalog.py --dry-run --verbose

  # Run migration with default settings
  python scripts/migrate_specs_to_catalog.py

  # Run migration with smaller batch size and skip duplicates
  python scripts/migrate_specs_to_catalog.py --batch-size 50 --skip-duplicates

  # Run migration with detailed logging
  python scripts/migrate_specs_to_catalog.py --verbose
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without committing to database'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable detailed logging'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of specifications to process per batch (default: 100)'
    )

    parser.add_argument(
        '--skip-duplicates',
        action='store_true',
        help='Skip duplicate entries instead of raising errors'
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Display configuration
    print("\n" + "="*70)
    print("DEVICE SPECIFICATION MIGRATION")
    print("="*70)
    print(f"Batch size:        {args.batch_size}")
    print(f"Dry run:           {args.dry_run}")
    print(f"Verbose:           {args.verbose}")
    print(f"Skip duplicates:   {args.skip_duplicates}")
    print("="*70 + "\n")

    # Confirm if not dry-run
    if not args.dry_run:
        response = input("This will modify the database. Continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled")
            return 0

    # Run migration
    try:
        stats = run_migration(
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            skip_duplicates=args.skip_duplicates
        )

        # Print summary
        stats.print_summary()

        # Exit code based on results
        if stats.specs_failed > 0:
            return 1

        return 0

    except Exception as e:
        logging.error(f"Migration failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
