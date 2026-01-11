#!/usr/bin/env python3
"""
Test script to verify migration logic with sample data

This script creates sample device specifications and runs the migration
to verify everything works correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from app.database import SessionLocal
from app.models import (
    DeviceSpecification,
    DeviceType,
    Brand,
    Model,
    WidthType,
    AirflowPattern,
    SourceType,
    ConfidenceLevel,
    MigrationStatus,
)


def create_sample_data():
    """Create sample device specifications for testing"""
    db = SessionLocal()

    print("Creating sample device specifications...")

    # Clear existing test data
    db.query(DeviceSpecification).filter(
        DeviceSpecification.source == SourceType.USER_CUSTOM
    ).delete()
    db.commit()

    # Sample specifications
    samples = [
        # Cisco Switches
        {
            "brand": "Cisco",
            "model": "Catalyst 9300",
            "variant": "48-port",
            "height_u": 1.0,
            "width_type": WidthType.NINETEEN_INCH,
            "depth_mm": 480.0,
            "weight_kg": 5.5,
            "power_watts": 150.0,
            "heat_output_btu": 512.0,
            "airflow_pattern": AirflowPattern.FRONT_TO_BACK,
            "typical_ports": {"gigabit_ethernet": 48, "sfp_plus": 4},
            "mounting_type": "4-post rack",
        },
        {
            "brand": "Cisco",
            "model": "Nexus 5500",
            "variant": None,
            "height_u": 2.0,
            "width_type": WidthType.NINETEEN_INCH,
            "depth_mm": 550.0,
            "weight_kg": 12.0,
            "power_watts": 400.0,
            "heat_output_btu": 1365.0,
            "airflow_pattern": AirflowPattern.BACK_TO_FRONT,
            "typical_ports": {"10g_ethernet": 48, "qsfp": 2},
            "mounting_type": "4-post rack",
        },
        # Dell Servers
        {
            "brand": "Dell",
            "model": "PowerEdge R740",
            "variant": "Xeon Gold",
            "height_u": 2.0,
            "width_type": WidthType.NINETEEN_INCH,
            "depth_mm": 730.0,
            "weight_kg": 28.0,
            "power_watts": 750.0,
            "heat_output_btu": 2559.0,
            "airflow_pattern": AirflowPattern.FRONT_TO_BACK,
            "typical_ports": {"gigabit_ethernet": 4, "usb": 5},
            "mounting_type": "4-post rack",
        },
        {
            "brand": "Dell",
            "model": "PowerEdge R640",
            "variant": None,
            "height_u": 1.0,
            "width_type": WidthType.NINETEEN_INCH,
            "depth_mm": 625.0,
            "weight_kg": 18.0,
            "power_watts": 495.0,
            "heat_output_btu": 1689.0,
            "airflow_pattern": AirflowPattern.FRONT_TO_BACK,
            "typical_ports": {"gigabit_ethernet": 4, "usb": 5},
            "mounting_type": "4-post rack",
        },
        # HP Switches
        {
            "brand": "HPE",
            "model": "Aruba 2930F",
            "variant": "24-port PoE+",
            "height_u": 1.0,
            "width_type": WidthType.NINETEEN_INCH,
            "depth_mm": 260.0,
            "weight_kg": 4.2,
            "power_watts": 370.0,
            "heat_output_btu": 1262.0,
            "airflow_pattern": AirflowPattern.SIDE_TO_SIDE,
            "typical_ports": {"gigabit_ethernet": 24, "sfp": 4},
            "mounting_type": "2-post rack",
        },
        # Fortinet Firewall
        {
            "brand": "Fortinet",
            "model": "FortiGate 100F",
            "variant": None,
            "height_u": 1.0,
            "width_type": WidthType.NINETEEN_INCH,
            "depth_mm": 220.0,
            "weight_kg": 2.5,
            "power_watts": 18.0,
            "heat_output_btu": 61.0,
            "airflow_pattern": AirflowPattern.FRONT_TO_BACK,
            "typical_ports": {"gigabit_ethernet": 10, "usb": 1},
            "mounting_type": "wall-mount",
        },
        # APC PDU
        {
            "brand": "APC",
            "model": "AP8868",
            "variant": "Switched Rack PDU",
            "height_u": 0.0,  # Zero-U device
            "width_type": None,
            "depth_mm": 45.0,
            "weight_kg": 3.2,
            "power_watts": None,  # PDU distributes power
            "heat_output_btu": None,
            "airflow_pattern": AirflowPattern.PASSIVE,
            "typical_ports": {"iec_c13": 24, "iec_c19": 6},
            "mounting_type": "vertical",
        },
        # Duplicate for testing (same brand, model, variant)
        {
            "brand": "cisco",  # Different case
            "model": "Catalyst 9300",
            "variant": "48-port",
            "height_u": 1.0,
            "width_type": WidthType.NINETEEN_INCH,
            "depth_mm": 480.0,
            "weight_kg": 5.5,
            "power_watts": 150.0,
            "heat_output_btu": 512.0,
            "airflow_pattern": AirflowPattern.FRONT_TO_BACK,
            "typical_ports": {"gigabit_ethernet": 48, "sfp_plus": 4},
            "mounting_type": "4-post rack",
        },
    ]

    for sample in samples:
        spec = DeviceSpecification(
            brand=sample["brand"],
            model=sample["model"],
            variant=sample.get("variant"),
            height_u=sample["height_u"],
            width_type=sample.get("width_type"),
            depth_mm=sample.get("depth_mm"),
            weight_kg=sample.get("weight_kg"),
            power_watts=sample.get("power_watts"),
            heat_output_btu=sample.get("heat_output_btu"),
            airflow_pattern=sample.get("airflow_pattern", AirflowPattern.FRONT_TO_BACK),
            typical_ports=sample.get("typical_ports"),
            mounting_type=sample.get("mounting_type"),
            source=SourceType.USER_CUSTOM,
            confidence=ConfidenceLevel.HIGH,
            fetched_at=datetime.utcnow(),
        )
        db.add(spec)

    db.commit()

    count = db.query(DeviceSpecification).count()
    print(f"Created {len(samples)} sample specifications")
    print(f"Total specifications in database: {count}")

    db.close()


def verify_migration():
    """Verify migration results"""
    db = SessionLocal()

    print("\nVerifying migration results...")

    # Count records
    specs = db.query(DeviceSpecification).count()
    brands = db.query(Brand).count()
    models = db.query(Model).count()
    migrated = db.query(DeviceSpecification).filter(
        DeviceSpecification.migration_status == MigrationStatus.COMPLETED
    ).count()

    print(f"\nRecord counts:")
    print(f"  Specifications: {specs}")
    print(f"  Brands: {brands}")
    print(f"  Models: {models}")
    print(f"  Migrated specs: {migrated}")

    # List brands
    print(f"\nBrands created:")
    for brand in db.query(Brand).all():
        model_count = db.query(Model).filter(Model.brand_id == brand.id).count()
        print(f"  - {brand.name} (slug: {brand.slug}, {model_count} models)")

    # Show device type distribution
    print(f"\nDevice type distribution:")
    for dt in db.query(DeviceType).all():
        model_count = db.query(Model).filter(Model.device_type_id == dt.id).count()
        if model_count > 0:
            print(f"  - {dt.name}: {model_count} models")

    # Check for failed migrations
    failed = db.query(DeviceSpecification).filter(
        DeviceSpecification.migration_status == MigrationStatus.FAILED
    ).all()

    if failed:
        print(f"\nWARNING: {len(failed)} failed migrations:")
        for spec in failed:
            print(f"  - ID {spec.id}: {spec.brand} {spec.model}")
    else:
        print(f"\n✓ All specifications migrated successfully!")

    # Sample model details
    print(f"\nSample models:")
    for model in db.query(Model).limit(3).all():
        print(f"  - {model.brand.name} {model.name}")
        print(f"    Type: {model.device_type.name}")
        print(f"    Variant: {model.variant or 'N/A'}")
        print(f"    Height: {model.height_u}U")
        print(f"    Power: {model.power_watts}W" if model.power_watts else "    Power: N/A")

    db.close()


def cleanup():
    """Clean up test data"""
    db = SessionLocal()

    print("\nCleaning up test data...")

    # Delete models (will cascade from specs)
    deleted_models = db.query(Model).delete()
    deleted_brands = db.query(Brand).delete()
    deleted_specs = db.query(DeviceSpecification).delete()

    db.commit()

    print(f"Deleted {deleted_specs} specifications")
    print(f"Deleted {deleted_brands} brands")
    print(f"Deleted {deleted_models} models")

    db.close()


def main():
    """Main test flow"""
    import argparse

    parser = argparse.ArgumentParser(description="Test migration script")
    parser.add_argument('action', choices=['setup', 'verify', 'cleanup'],
                       help='Action to perform')

    args = parser.parse_args()

    if args.action == 'setup':
        create_sample_data()
        print("\nTest data created. Now run:")
        print("  python3 scripts/migrate_specs_to_catalog.py --dry-run --verbose")
        print("  python3 scripts/migrate_specs_to_catalog.py --verbose --skip-duplicates")

    elif args.action == 'verify':
        verify_migration()

    elif args.action == 'cleanup':
        cleanup()


if __name__ == "__main__":
    main()
