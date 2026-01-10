"""
Database initialization script
Creates all tables and optionally seeds with sample data
"""
from app.database import Base, engine
from app.models import (
    DeviceSpecification,
    Device,
    Rack,
    RackPosition,
    Connection,
    WidthType,
    SourceType,
    ConfidenceLevel
)
from sqlalchemy.orm import Session


def init_database():
    """Initialize database schema"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def seed_sample_data():
    """Seed database with sample device specifications"""
    print("\nSeeding sample data...")

    with Session(engine) as session:
        # Sample device specifications
        specs = [
            DeviceSpecification(
                brand="Cisco",
                model="Catalyst 2960-48TT-L",
                height_u=1,
                width_type=WidthType.NINETEEN_INCH,
                depth_mm=445,
                weight_kg=4.1,
                power_watts=25,
                heat_output_btu=85,
                typical_ports={"gigabit_ethernet": 48, "sfp": 2, "console": 1},
                mounting_type="4-post",
                source=SourceType.MANUFACTURER_SPEC,
                confidence=ConfidenceLevel.HIGH
            ),
            DeviceSpecification(
                brand="Ubiquiti",
                model="USW-Pro-48",
                height_u=1,
                width_type=WidthType.NINETEEN_INCH,
                depth_mm=350,
                weight_kg=3.8,
                power_watts=45,
                heat_output_btu=153,
                typical_ports={"gigabit_ethernet": 48, "sfp_plus": 4},
                mounting_type="2-post",
                source=SourceType.MANUFACTURER_SPEC,
                confidence=ConfidenceLevel.HIGH
            ),
            DeviceSpecification(
                brand="Juniper",
                model="EX4300-48T",
                height_u=1,
                width_type=WidthType.NINETEEN_INCH,
                depth_mm=438,
                weight_kg=7.7,
                power_watts=110,
                heat_output_btu=375,
                typical_ports={"gigabit_ethernet": 48, "qsfp_plus": 4},
                mounting_type="4-post",
                source=SourceType.MANUFACTURER_SPEC,
                confidence=ConfidenceLevel.HIGH
            ),
        ]

        session.add_all(specs)
        session.commit()
        print(f"✓ Added {len(specs)} sample device specifications")

        # Create a sample rack
        rack = Rack(
            name="Main Rack",
            location="Server Room A",
            total_height_u=42,
            width_inches=WidthType.NINETEEN_INCH,
            depth_mm=700,
            max_weight_kg=500,
            max_power_watts=5000
        )
        session.add(rack)
        session.commit()
        print("✓ Created sample rack")


if __name__ == "__main__":
    print("=" * 50)
    print("HomeRack Database Initialization")
    print("=" * 50)

    init_database()

    # Ask if user wants sample data
    response = input("\nSeed with sample data? (y/n): ")
    if response.lower() == 'y':
        seed_sample_data()

    print("\n" + "=" * 50)
    print("✓ Initialization complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Start the backend: uvicorn app.main:app --reload")
    print("2. Visit API docs: http://localhost:8000/docs")
    print("3. Start the frontend: cd ../frontend && npm run dev")
