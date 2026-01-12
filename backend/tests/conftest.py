"""
Pytest Configuration and Shared Fixtures for Integration Tests

This module provides:
- Test database setup with automatic cleanup
- FastAPI TestClient configuration
- Shared fixtures for common test data
- Database session management
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import (
    DeviceType, Brand, Model, DeviceSpecification,
    Device, Rack, RackPosition, Connection,
    SourceType, ConfidenceLevel, AccessFrequency,
    AirflowPattern, CableType, RoutingPath
)


# Use in-memory SQLite for tests (fast and isolated)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with special config for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Ensure same connection for in-memory DB
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.

    Database is created before each test and all tables are dropped after.
    This ensures complete test isolation.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a TestClient with overridden database dependency.

    All API calls made through this client will use the test database.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


# ============================================================================
# Catalog Fixtures - Device Types, Brands, Models
# ============================================================================

@pytest.fixture
def device_type_switch(db_session: Session) -> DeviceType:
    """Create a Switch device type."""
    device_type = DeviceType(
        name="Switch",
        slug="switch",
        icon="🔀",
        description="Network switches",
        color="#4CAF50"
    )
    db_session.add(device_type)
    db_session.commit()
    db_session.refresh(device_type)
    return device_type


@pytest.fixture
def device_type_server(db_session: Session) -> DeviceType:
    """Create a Server device type."""
    device_type = DeviceType(
        name="Server",
        slug="server",
        icon="🖥️",
        description="Servers",
        color="#2196F3"
    )
    db_session.add(device_type)
    db_session.commit()
    db_session.refresh(device_type)
    return device_type


@pytest.fixture
def device_type_firewall(db_session: Session) -> DeviceType:
    """Create a Firewall device type."""
    device_type = DeviceType(
        name="Firewall",
        slug="firewall",
        icon="🔥",
        description="Firewalls and security appliances",
        color="#FF5722"
    )
    db_session.add(device_type)
    db_session.commit()
    db_session.refresh(device_type)
    return device_type


@pytest.fixture
def brand_cisco(db_session: Session) -> Brand:
    """Create a Cisco brand."""
    brand = Brand(
        name="Cisco Systems",
        slug="cisco-systems",
        website="https://www.cisco.com",
        support_url="https://www.cisco.com/c/en/us/support/index.html",
        logo_url="https://www.cisco.com/logo.png",
        description="American multinational technology company",
        founded_year=1984,
        headquarters="San Jose, California"
    )
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def brand_dell(db_session: Session) -> Brand:
    """Create a Dell brand."""
    brand = Brand(
        name="Dell Technologies",
        slug="dell-technologies",
        website="https://www.dell.com",
        description="American technology company",
        founded_year=1984,
        headquarters="Round Rock, Texas"
    )
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def model_catalyst_9300(db_session: Session, brand_cisco: Brand, device_type_switch: DeviceType) -> Model:
    """Create a Cisco Catalyst 9300 model."""
    model = Model(
        brand_id=brand_cisco.id,
        device_type_id=device_type_switch.id,
        name="Catalyst 9300",
        variant="48-port",
        description="Enterprise-class switch",
        height_u=1.0,
        width_type='19"',
        depth_mm=445.0,
        weight_kg=7.3,
        power_watts=215.0,
        heat_output_btu=733.0,
        airflow_pattern="front_to_back",
        max_operating_temp_c=45.0,
        typical_ports={"gigabit_ethernet": 48, "sfp+": 4},
        mounting_type="2-post",
        source="manual",
        confidence="high"
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model


@pytest.fixture
def model_poweredge_r740(db_session: Session, brand_dell: Brand, device_type_server: DeviceType) -> Model:
    """Create a Dell PowerEdge R740 model."""
    model = Model(
        brand_id=brand_dell.id,
        device_type_id=device_type_server.id,
        name="PowerEdge R740",
        description="2U rack server",
        height_u=2.0,
        width_type='19"',
        depth_mm=730.0,
        weight_kg=28.8,
        power_watts=750.0,
        heat_output_btu=2559.0,
        airflow_pattern="front_to_back",
        max_operating_temp_c=35.0,
        typical_ports={"gigabit_ethernet": 4, "usb": 2},
        mounting_type="4-post",
        source="manual",
        confidence="high"
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model


# ============================================================================
# Legacy Specification Fixtures
# ============================================================================

@pytest.fixture
def spec_switch(db_session: Session) -> DeviceSpecification:
    """Create a switch specification (legacy)."""
    spec = DeviceSpecification(
        brand="Cisco",
        model="Catalyst 2960",
        height_u=1.0,
        power_watts=120.0,
        heat_output_btu=409.0,
        airflow_pattern=AirflowPattern.FRONT_TO_BACK,
        typical_ports={"gigabit_ethernet": 24, "sfp": 2},
        source=SourceType.USER_CUSTOM,
        confidence=ConfidenceLevel.HIGH
    )
    db_session.add(spec)
    db_session.commit()
    db_session.refresh(spec)
    return spec


@pytest.fixture
def spec_server(db_session: Session) -> DeviceSpecification:
    """Create a server specification (legacy)."""
    spec = DeviceSpecification(
        brand="Dell",
        model="PowerEdge R640",
        height_u=1.0,
        power_watts=500.0,
        heat_output_btu=1706.0,
        airflow_pattern=AirflowPattern.FRONT_TO_BACK,
        source=SourceType.USER_CUSTOM,
        confidence=ConfidenceLevel.HIGH
    )
    db_session.add(spec)
    db_session.commit()
    db_session.refresh(spec)
    return spec


@pytest.fixture
def spec_firewall(db_session: Session) -> DeviceSpecification:
    """Create a firewall specification (legacy)."""
    spec = DeviceSpecification(
        brand="Palo Alto",
        model="PA-3020",
        height_u=1.0,
        power_watts=280.0,
        heat_output_btu=955.0,
        airflow_pattern=AirflowPattern.FRONT_TO_BACK,
        source=SourceType.USER_CUSTOM,
        confidence=ConfidenceLevel.MEDIUM
    )
    db_session.add(spec)
    db_session.commit()
    db_session.refresh(spec)
    return spec


# ============================================================================
# Device Fixtures
# ============================================================================

@pytest.fixture
def device_switch(db_session: Session, spec_switch: DeviceSpecification) -> Device:
    """Create a switch device."""
    device = Device(
        custom_name="Core Switch 1",
        specification_id=spec_switch.id,
        brand=spec_switch.brand,
        model=spec_switch.model,
        access_frequency=AccessFrequency.HIGH,
        notes="Main distribution switch"
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def device_server(db_session: Session, spec_server: DeviceSpecification) -> Device:
    """Create a server device."""
    device = Device(
        custom_name="Web Server 1",
        specification_id=spec_server.id,
        brand=spec_server.brand,
        model=spec_server.model,
        access_frequency=AccessFrequency.MEDIUM
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def device_from_model(db_session: Session, model_catalyst_9300: Model) -> Device:
    """Create a device from catalog model."""
    device = Device(
        custom_name="Access Switch 1",
        specification_id=None,  # Using catalog model instead
        model_id=model_catalyst_9300.id,
        brand=model_catalyst_9300.brand.name,
        model=model_catalyst_9300.name,
        access_frequency=AccessFrequency.MEDIUM
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


# ============================================================================
# Rack Fixtures
# ============================================================================

@pytest.fixture
def rack_standard(db_session: Session) -> Rack:
    """Create a standard 42U rack."""
    rack = Rack(
        name="Rack A1",
        location="Data Center 1",
        total_height_u=42,
        max_weight_kg=500.0,
        max_power_watts=5000.0,
        cooling_capacity_btu=17000.0,
        ambient_temp_c=22.0,
        max_inlet_temp_c=27.0
    )
    db_session.add(rack)
    db_session.commit()
    db_session.refresh(rack)
    return rack


@pytest.fixture
def rack_with_devices(db_session: Session, rack_standard: Rack, device_switch: Device, device_server: Device) -> Rack:
    """Create a rack with positioned devices."""
    # Add switch at bottom
    pos1 = RackPosition(
        device_id=device_switch.id,
        rack_id=rack_standard.id,
        start_u=1,
        locked=False
    )
    # Add server in middle
    pos2 = RackPosition(
        device_id=device_server.id,
        rack_id=rack_standard.id,
        start_u=20,
        locked=False
    )
    db_session.add_all([pos1, pos2])
    db_session.commit()
    db_session.refresh(rack_standard)
    return rack_standard


# ============================================================================
# Connection Fixtures
# ============================================================================

@pytest.fixture
def connection_switch_to_server(db_session: Session, device_switch: Device, device_server: Device) -> Connection:
    """Create a connection between switch and server."""
    connection = Connection(
        from_device_id=device_switch.id,
        to_device_id=device_server.id,
        from_port="Gi0/1",
        to_port="eth0",
        cable_type=CableType.CAT6,
        routing_path=RoutingPath.DIRECT
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)
    return connection
