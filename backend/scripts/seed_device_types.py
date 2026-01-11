#!/usr/bin/env python3
"""
Seed device types into the database
Phase 1 - Initial catalog setup
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import DeviceType
from datetime import datetime

# 9 predefined device types
DEVICE_TYPES = [
    {
        "name": "Server",
        "slug": "server",
        "icon": "🖥️",
        "description": "Rack-mounted servers, compute nodes, and blade servers",
        "color": "#3B82F6"  # blue
    },
    {
        "name": "Switch",
        "slug": "switch",
        "icon": "🔀",
        "description": "Network switches, including managed, unmanaged, and PoE switches",
        "color": "#10B981"  # green
    },
    {
        "name": "Router",
        "slug": "router",
        "icon": "📡",
        "description": "Network routers and gateways",
        "color": "#8B5CF6"  # purple
    },
    {
        "name": "Firewall",
        "slug": "firewall",
        "icon": "🛡️",
        "description": "Firewall appliances and security devices",
        "color": "#EF4444"  # red
    },
    {
        "name": "Storage",
        "slug": "storage",
        "icon": "💾",
        "description": "NAS, SAN, and storage arrays",
        "color": "#F59E0B"  # amber
    },
    {
        "name": "PDU",
        "slug": "pdu",
        "icon": "⚡",
        "description": "Power Distribution Units",
        "color": "#FCD34D"  # yellow
    },
    {
        "name": "UPS",
        "slug": "ups",
        "icon": "🔋",
        "description": "Uninterruptible Power Supplies",
        "color": "#84CC16"  # lime
    },
    {
        "name": "Patch Panel",
        "slug": "patch_panel",
        "icon": "🔌",
        "description": "Network patch panels and cable management",
        "color": "#06B6D4"  # cyan
    },
    {
        "name": "Other",
        "slug": "other",
        "icon": "📦",
        "description": "Other rack-mounted equipment",
        "color": "#6B7280"  # gray
    }
]


def seed_device_types():
    """Seed device types into database"""
    db = SessionLocal()
    try:
        # Check if device types already exist
        existing_count = db.query(DeviceType).count()
        if existing_count > 0:
            print(f"✓ Device types already seeded ({existing_count} types exist)")
            return

        # Insert device types
        for dt_data in DEVICE_TYPES:
            device_type = DeviceType(**dt_data)
            db.add(device_type)

        db.commit()
        print(f"✓ Successfully seeded {len(DEVICE_TYPES)} device types")

        # Print summary
        for dt in DEVICE_TYPES:
            print(f"  {dt['icon']} {dt['name']} ({dt['slug']})")

    except Exception as e:
        print(f"✗ Error seeding device types: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding device types...")
    seed_device_types()
    print("Done!")
