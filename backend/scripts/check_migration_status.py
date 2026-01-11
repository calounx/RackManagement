#!/usr/bin/env python3
"""
Quick migration status checker

This script checks the current migration status of device specifications
and provides a summary of the catalog structure.

Usage:
    python3 scripts/check_migration_status.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import (
    DeviceSpecification,
    DeviceType,
    Brand,
    Model,
    MigrationStatus,
)
from sqlalchemy import func


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print('='*70)


def check_migration_status():
    """Check and display migration status"""
    db = SessionLocal()

    try:
        print_section("CATALOG STATUS")

        # Basic counts
        spec_count = db.query(DeviceSpecification).count()
        brand_count = db.query(Brand).count()
        model_count = db.query(Model).count()
        device_type_count = db.query(DeviceType).count()

        print(f"\nRecord Counts:")
        print(f"  Device Specifications: {spec_count}")
        print(f"  Brands: {brand_count}")
        print(f"  Models: {model_count}")
        print(f"  Device Types: {device_type_count}")

        # Migration status breakdown
        if spec_count > 0:
            print_section("MIGRATION STATUS")

            pending = db.query(DeviceSpecification).filter(
                (DeviceSpecification.migration_status == None) |
                (DeviceSpecification.migration_status == MigrationStatus.PENDING)
            ).count()

            in_progress = db.query(DeviceSpecification).filter(
                DeviceSpecification.migration_status == MigrationStatus.IN_PROGRESS
            ).count()

            completed = db.query(DeviceSpecification).filter(
                DeviceSpecification.migration_status == MigrationStatus.COMPLETED
            ).count()

            failed = db.query(DeviceSpecification).filter(
                DeviceSpecification.migration_status == MigrationStatus.FAILED
            ).count()

            print(f"\nSpecification Migration Status:")
            print(f"  Pending:     {pending:4d} ({pending/spec_count*100:5.1f}%)")
            print(f"  In Progress: {in_progress:4d} ({in_progress/spec_count*100:5.1f}%)")
            print(f"  Completed:   {completed:4d} ({completed/spec_count*100:5.1f}%)")
            print(f"  Failed:      {failed:4d} ({failed/spec_count*100:5.1f}%)")

            if completed == spec_count:
                print("\n  ✓ All specifications have been migrated!")
            elif pending == spec_count:
                print("\n  ⚠ No specifications have been migrated yet")
            elif failed > 0:
                print(f"\n  ⚠ {failed} specifications failed to migrate")
            else:
                print(f"\n  → {pending} specifications remaining to migrate")

            # Show failed specs if any
            if failed > 0:
                print("\n  Failed Specifications:")
                failed_specs = db.query(DeviceSpecification).filter(
                    DeviceSpecification.migration_status == MigrationStatus.FAILED
                ).limit(5).all()

                for spec in failed_specs:
                    print(f"    - ID {spec.id}: {spec.brand} {spec.model}")

                if failed > 5:
                    print(f"    ... and {failed - 5} more")

        # Brand statistics
        if brand_count > 0:
            print_section("BRAND CATALOG")

            print(f"\nTop Brands by Model Count:")
            brand_stats = db.query(
                Brand.name,
                Brand.slug,
                func.count(Model.id).label('model_count')
            ).join(Model).group_by(Brand.id).order_by(
                func.count(Model.id).desc()
            ).limit(10).all()

            for brand_name, slug, count in brand_stats:
                print(f"  {brand_name:20s} ({slug:20s}): {count:3d} models")

            if brand_count > 10:
                print(f"\n  ... and {brand_count - 10} more brands")

        # Device type distribution
        if model_count > 0:
            print_section("DEVICE TYPE DISTRIBUTION")

            print(f"\nModels by Device Type:")
            type_stats = db.query(
                DeviceType.name,
                DeviceType.slug,
                func.count(Model.id).label('model_count')
            ).join(Model).group_by(DeviceType.id).order_by(
                func.count(Model.id).desc()
            ).all()

            total_typed = sum(count for _, _, count in type_stats)

            for type_name, slug, count in type_stats:
                pct = count / total_typed * 100 if total_typed > 0 else 0
                bar = '█' * int(pct / 2)  # Scale to 50 chars max
                print(f"  {type_name:15s}: {count:3d} ({pct:5.1f}%) {bar}")

        # Model statistics
        if model_count > 0:
            print_section("MODEL STATISTICS")

            # Height distribution
            avg_height = db.query(func.avg(Model.height_u)).scalar()
            min_height = db.query(func.min(Model.height_u)).scalar()
            max_height = db.query(func.max(Model.height_u)).scalar()

            print(f"\nRack Unit (U) Distribution:")
            print(f"  Average: {avg_height:.2f}U")
            print(f"  Minimum: {min_height:.1f}U")
            print(f"  Maximum: {max_height:.1f}U")

            # Power distribution
            models_with_power = db.query(Model).filter(
                Model.power_watts != None
            ).count()

            if models_with_power > 0:
                avg_power = db.query(func.avg(Model.power_watts)).filter(
                    Model.power_watts != None
                ).scalar()
                min_power = db.query(func.min(Model.power_watts)).filter(
                    Model.power_watts != None
                ).scalar()
                max_power = db.query(func.max(Model.power_watts)).filter(
                    Model.power_watts != None
                ).scalar()

                print(f"\nPower Consumption (for {models_with_power} models with data):")
                print(f"  Average: {avg_power:.1f}W")
                print(f"  Minimum: {min_power:.1f}W")
                print(f"  Maximum: {max_power:.1f}W")

        # Data quality metrics
        if model_count > 0:
            print_section("DATA QUALITY METRICS")

            # Count models with various data points
            with_depth = db.query(Model).filter(Model.depth_mm != None).count()
            with_weight = db.query(Model).filter(Model.weight_kg != None).count()
            with_power = db.query(Model).filter(Model.power_watts != None).count()
            with_ports = db.query(Model).filter(Model.typical_ports != None).count()
            with_datasheet = db.query(Model).filter(Model.datasheet_url != None).count()

            print(f"\nData Completeness:")
            print(f"  Depth data:      {with_depth:4d} / {model_count} ({with_depth/model_count*100:5.1f}%)")
            print(f"  Weight data:     {with_weight:4d} / {model_count} ({with_weight/model_count*100:5.1f}%)")
            print(f"  Power data:      {with_power:4d} / {model_count} ({with_power/model_count*100:5.1f}%)")
            print(f"  Port data:       {with_ports:4d} / {model_count} ({with_ports/model_count*100:5.1f}%)")
            print(f"  Datasheet URLs:  {with_datasheet:4d} / {model_count} ({with_datasheet/model_count*100:5.1f}%)")

            # Confidence distribution
            print(f"\nConfidence Levels:")
            high_conf = db.query(Model).filter(Model.confidence == 'high').count()
            med_conf = db.query(Model).filter(Model.confidence == 'medium').count()
            low_conf = db.query(Model).filter(Model.confidence == 'low').count()
            no_conf = db.query(Model).filter(Model.confidence == None).count()

            if high_conf + med_conf + low_conf + no_conf > 0:
                print(f"  High:            {high_conf:4d} ({high_conf/model_count*100:5.1f}%)")
                print(f"  Medium:          {med_conf:4d} ({med_conf/model_count*100:5.1f}%)")
                print(f"  Low:             {low_conf:4d} ({low_conf/model_count*100:5.1f}%)")
                print(f"  Unknown:         {no_conf:4d} ({no_conf/model_count*100:5.1f}%)")

        print("\n" + "="*70 + "\n")

    except Exception as e:
        print(f"\nError checking migration status: {e}")
        return 1

    finally:
        db.close()

    return 0


def main():
    """Main entry point"""
    return check_migration_status()


if __name__ == "__main__":
    sys.exit(main())
