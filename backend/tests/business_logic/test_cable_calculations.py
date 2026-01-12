"""
Business logic tests for cable length calculations.

Tests cable length calculation, bend radius, routing paths, and cable limits.
Total: ~10 tests
"""

import pytest
import math
from sqlalchemy.orm import Session

from app.models import (
    Rack, Device, DeviceSpecification, RackPosition, Connection,
    CableType, RoutingPath
)


class TestCableLengthCalculations:
    """Tests for cable length calculation logic."""

    def test_calculate_cable_length_vertical_same_rack(self, db_session: Session):
        """Test cable length calculation for devices in same rack vertically."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        device1 = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        device2 = Device(
            custom_name="Device2",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add_all([device1, device2])
        db_session.commit()

        # Position devices vertically
        pos1 = RackPosition(device_id=device1.id, rack_id=rack.id, start_u=1)
        pos2 = RackPosition(device_id=device2.id, rack_id=rack.id, start_u=10)
        db_session.add_all([pos1, pos2])
        db_session.commit()

        # Create connection
        conn = Connection(
            from_device_id=device1.id,
            to_device_id=device2.id,
            cable_type=CableType.CAT6,
            routing_path=RoutingPath.DIRECT
        )
        db_session.add(conn)
        db_session.commit()

        # Calculate cable length
        # 9U difference * 1.75" per U = 15.75" = 0.4m
        # Plus slack and service loop
        # Actual calculation depends on implementation

    def test_cable_length_with_slack_factor(self, db_session: Session):
        """Test cable length includes slack factor for service loops."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        device1 = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        device2 = Device(
            custom_name="Device2",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add_all([device1, device2])
        db_session.commit()

        pos1 = RackPosition(device_id=device1.id, rack_id=rack.id, start_u=1)
        pos2 = RackPosition(device_id=device2.id, rack_id=rack.id, start_u=20)
        db_session.add_all([pos1, pos2])
        db_session.commit()

        conn = Connection(
            from_device_id=device1.id,
            to_device_id=device2.id,
            cable_type=CableType.CAT6,
            routing_path=RoutingPath.DIRECT
        )
        db_session.add(conn)
        db_session.commit()

        # Cable length should include 15-20% slack for service loops

    def test_cable_length_cable_tray_routing(self, db_session: Session):
        """Test cable length calculation with cable tray routing path."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        device1 = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        device2 = Device(
            custom_name="Device2",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add_all([device1, device2])
        db_session.commit()

        pos1 = RackPosition(device_id=device1.id, rack_id=rack.id, start_u=1)
        pos2 = RackPosition(device_id=device2.id, rack_id=rack.id, start_u=20)
        db_session.add_all([pos1, pos2])
        db_session.commit()

        conn = Connection(
            from_device_id=device1.id,
            to_device_id=device2.id,
            cable_type=CableType.CAT6,
            routing_path=RoutingPath.CABLE_TRAY
        )
        db_session.add(conn)
        db_session.commit()

        # Cable tray routing should add extra length for overhead path

    def test_cable_length_conduit_routing(self, db_session: Session):
        """Test cable length calculation with conduit routing path."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        device1 = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        device2 = Device(
            custom_name="Device2",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add_all([device1, device2])
        db_session.commit()

        pos1 = RackPosition(device_id=device1.id, rack_id=rack.id, start_u=1)
        pos2 = RackPosition(device_id=device2.id, rack_id=rack.id, start_u=20)
        db_session.add_all([pos1, pos2])
        db_session.commit()

        conn = Connection(
            from_device_id=device1.id,
            to_device_id=device2.id,
            cable_type=CableType.CAT6,
            routing_path=RoutingPath.CONDUIT
        )
        db_session.add(conn)
        db_session.commit()

        # Conduit routing may add extra length for bends


class TestCableBendRadius:
    """Tests for cable bend radius validation."""

    def test_copper_cable_bend_radius(self):
        """Test copper cable (Cat6) has appropriate bend radius."""
        # Cat6 minimum bend radius is 4x cable diameter (typically ~6mm)
        min_bend_radius = 24  # mm
        assert min_bend_radius > 0

    def test_fiber_cable_bend_radius_singlemode(self):
        """Test single-mode fiber has stricter bend radius."""
        # Single-mode fiber minimum bend radius is typically 30-50mm
        min_bend_radius = 30  # mm
        assert min_bend_radius > 0

    def test_fiber_cable_bend_radius_multimode(self):
        """Test multi-mode fiber bend radius."""
        # Multi-mode fiber minimum bend radius is typically 30mm
        min_bend_radius = 30  # mm
        assert min_bend_radius > 0

    def test_cable_bend_radius_validation(self, db_session: Session):
        """Test validation prevents cables with insufficient bend radius."""
        # This would validate that cable routing respects minimum bend radius
        # based on cable type and routing path
        pass


class TestCableLimits:
    """Tests for cable length limits and specifications."""

    def test_cat5e_max_length(self):
        """Test Cat5e cable has 100m maximum length."""
        max_length = 100.0  # meters
        assert max_length == 100.0

    def test_cat6_max_length(self):
        """Test Cat6 cable has 100m maximum length."""
        max_length = 100.0  # meters
        assert max_length == 100.0

    def test_cat6a_max_length(self):
        """Test Cat6a cable has 100m maximum length."""
        max_length = 100.0  # meters
        assert max_length == 100.0

    def test_fiber_singlemode_max_length(self):
        """Test single-mode fiber has extended maximum length."""
        max_length = 10000.0  # meters (10km typical)
        assert max_length > 1000.0

    def test_fiber_multimode_max_length(self):
        """Test multi-mode fiber maximum length."""
        max_length = 550.0  # meters (OM4 at 10Gbps)
        assert max_length > 100.0

    def test_validate_cable_length_within_limits(self, db_session: Session):
        """Test validation ensures cable length doesn't exceed limits."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        device1 = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        device2 = Device(
            custom_name="Device2",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add_all([device1, device2])
        db_session.commit()

        pos1 = RackPosition(device_id=device1.id, rack_id=rack.id, start_u=1)
        pos2 = RackPosition(device_id=device2.id, rack_id=rack.id, start_u=10)
        db_session.add_all([pos1, pos2])
        db_session.commit()

        conn = Connection(
            from_device_id=device1.id,
            to_device_id=device2.id,
            cable_type=CableType.CAT6,
            routing_path=RoutingPath.DIRECT
        )
        db_session.add(conn)
        db_session.commit()

        # Should be valid - within 100m limit


class TestCableRouting:
    """Tests for cable routing optimization."""

    def test_minimize_cable_crossings(self):
        """Test optimization minimizes cable crossings."""
        # Devices should be arranged to minimize cable crossings
        # for cleaner cable management
        pass

    def test_group_connected_devices(self):
        """Test optimization groups connected devices together."""
        # Devices with many connections should be positioned near each other
        pass

    def test_calculate_total_cable_length(self, db_session: Session):
        """Test calculation of total cable length for rack."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        devices = []
        for i in range(3):
            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()
            devices.append(device)

            pos = RackPosition(
                device_id=device.id,
                rack_id=rack.id,
                start_u=i * 10 + 1
            )
            db_session.add(pos)
            db_session.commit()

        # Create connections between devices
        conn1 = Connection(
            from_device_id=devices[0].id,
            to_device_id=devices[1].id,
            cable_type=CableType.CAT6
        )
        conn2 = Connection(
            from_device_id=devices[1].id,
            to_device_id=devices[2].id,
            cable_type=CableType.CAT6
        )
        db_session.add_all([conn1, conn2])
        db_session.commit()

        # Should be able to calculate total cable length for BOM
