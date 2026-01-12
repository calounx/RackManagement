#!/usr/bin/env python3
"""
List and explore the device catalog (brands and models)

Usage:
    python list_catalog.py                      # List all brands with model counts
    python list_catalog.py --brands             # List all brands with details
    python list_catalog.py --models             # List all models
    python list_catalog.py --brand cisco        # List models for specific brand
    python list_catalog.py --type switch        # List models for specific device type
    python list_catalog.py --stats              # Show detailed statistics
"""
import sys
import argparse
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Brand, Model, DeviceType


def list_brands(db, detailed=False):
    """List all brands"""
    brands = db.query(Brand).order_by(Brand.name).all()

    print(f"\n{'='*70}")
    print(f"BRANDS ({len(brands)} total)")
    print(f"{'='*70}\n")

    for brand in brands:
        model_count = db.query(Model).filter(Model.brand_id == brand.id).count()

        if detailed:
            print(f"{brand.name}")
            print(f"  Slug: {brand.slug}")
            print(f"  Website: {brand.website}")
            print(f"  Founded: {brand.founded_year}")
            print(f"  Headquarters: {brand.headquarters}")
            print(f"  Models: {model_count}")
            if brand.description:
                print(f"  Description: {brand.description[:80]}...")
            print()
        else:
            print(f"  {brand.name:40} {model_count:3} models")


def list_models(db, brand_slug=None, device_type_slug=None):
    """List models, optionally filtered"""
    query = db.query(Model)

    # Apply filters
    if brand_slug:
        brand = db.query(Brand).filter(Brand.slug == brand_slug).first()
        if not brand:
            print(f"ERROR: Brand '{brand_slug}' not found")
            return
        query = query.filter(Model.brand_id == brand.id)

    if device_type_slug:
        device_type = db.query(DeviceType).filter(DeviceType.slug == device_type_slug).first()
        if not device_type:
            print(f"ERROR: Device type '{device_type_slug}' not found")
            return
        query = query.filter(Model.device_type_id == device_type.id)

    # Get models with related data
    models = query.all()

    # Build title
    title_parts = ["MODELS"]
    if brand_slug:
        title_parts.append(f"Brand: {brand_slug}")
    if device_type_slug:
        title_parts.append(f"Type: {device_type_slug}")
    title_parts.append(f"({len(models)} total)")
    title = " - ".join(title_parts)

    print(f"\n{'='*70}")
    print(title)
    print(f"{'='*70}\n")

    if not models:
        print("No models found")
        return

    # Print models
    for model in models:
        brand = db.query(Brand).filter(Brand.id == model.brand_id).first()
        device_type = db.query(DeviceType).filter(DeviceType.id == model.device_type_id).first()

        variant_str = f" ({model.variant})" if model.variant else ""
        print(f"{brand.name} {model.name}{variant_str}")
        print(f"  Type: {device_type.icon} {device_type.name}")
        print(f"  Size: {model.height_u}U, {model.depth_mm}mm deep, {model.weight_kg}kg")
        print(f"  Power: {model.power_watts}W, {model.heat_output_btu} BTU/hr")
        print(f"  Airflow: {model.airflow_pattern}")

        if model.typical_ports:
            ports_str = ", ".join([f"{v}x {k}" for k, v in model.typical_ports.items()])
            print(f"  Ports: {ports_str}")

        if model.description:
            print(f"  Description: {model.description}")

        print()


def show_statistics(db):
    """Show detailed statistics"""
    brands = db.query(Brand).all()
    models = db.query(Model).all()
    device_types = db.query(DeviceType).all()

    print(f"\n{'='*70}")
    print("CATALOG STATISTICS")
    print(f"{'='*70}\n")

    # Overall counts
    print(f"Total Brands: {len(brands)}")
    print(f"Total Models: {len(models)}")
    print(f"Total Device Types: {len(device_types)}\n")

    # Models by brand
    print("Models per Brand:")
    brand_counts = defaultdict(int)
    for model in models:
        brand = db.query(Brand).filter(Brand.id == model.brand_id).first()
        brand_counts[brand.name] += 1

    for brand_name in sorted(brand_counts.keys()):
        print(f"  {brand_name:40} {brand_counts[brand_name]:3} models")
    print()

    # Models by device type
    print("Models per Device Type:")
    type_counts = defaultdict(int)
    for model in models:
        device_type = db.query(DeviceType).filter(DeviceType.id == model.device_type_id).first()
        type_counts[f"{device_type.icon} {device_type.name}"] += 1

    for type_name in sorted(type_counts.keys()):
        print(f"  {type_name:40} {type_counts[type_name]:3} models")
    print()

    # Size statistics
    heights = [m.height_u for m in models if m.height_u]
    if heights:
        print("Height Distribution (U):")
        print(f"  Min: {min(heights)}U")
        print(f"  Max: {max(heights)}U")
        print(f"  Average: {sum(heights)/len(heights):.1f}U")
        print()

    # Power statistics
    powers = [m.power_watts for m in models if m.power_watts and m.power_watts > 0]
    if powers:
        print("Power Consumption (W):")
        print(f"  Min: {min(powers)}W")
        print(f"  Max: {max(powers)}W")
        print(f"  Average: {sum(powers)/len(powers):.0f}W")
        print(f"  Total: {sum(powers):.0f}W")
        print()

    # Confidence levels
    confidence_counts = defaultdict(int)
    for model in models:
        if model.confidence:
            confidence_counts[model.confidence] += 1

    if confidence_counts:
        print("Data Confidence:")
        for level in ["high", "medium", "low"]:
            count = confidence_counts.get(level, 0)
            if count > 0:
                print(f"  {level.capitalize():10} {count:3} models")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="List and explore the device catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python list_catalog.py                      # List all brands with model counts
  python list_catalog.py --brands             # List all brands with details
  python list_catalog.py --models             # List all models
  python list_catalog.py --brand cisco        # List models for specific brand
  python list_catalog.py --type switch        # List models for specific device type
  python list_catalog.py --stats              # Show detailed statistics
        """
    )
    parser.add_argument("--brands", action="store_true", help="List all brands with details")
    parser.add_argument("--models", action="store_true", help="List all models")
    parser.add_argument("--brand", type=str, help="Filter models by brand slug")
    parser.add_argument("--type", type=str, help="Filter models by device type slug")
    parser.add_argument("--stats", action="store_true", help="Show detailed statistics")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.stats:
            show_statistics(db)
        elif args.models or args.brand or args.type:
            list_models(db, brand_slug=args.brand, device_type_slug=args.type)
        elif args.brands:
            list_brands(db, detailed=True)
        else:
            # Default: list brands with counts
            list_brands(db, detailed=False)

    finally:
        db.close()


if __name__ == "__main__":
    main()
