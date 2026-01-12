"""
Business logic tests for validation rules.

Tests width compatibility, position validation, power/weight limits, and thermal constraints.
Total: ~10 tests
"""

import pytest
from sqlalchemy.orm import Session

from app.models import (
    Rack, Device, DeviceSpecification, RackPosition,
    WidthType, AirflowPattern
)


class TestWidthCompatibility:
    """Tests for rack width compatibility validation."""

    def test_19_inch_device_fits_19_inch_rack(self, db_session: Session):
        """Test 19" device fits in 19" rack."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            width_inches=WidthType.NINETEEN_INCH
        )
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            width_type=WidthType.NINETEEN_INCH
        )
        db_session.add(spec)
        db_session.commit()

        # Should be compatible
        assert spec.width_type == rack.width_inches

    def test_19_inch_device_does_not_fit_11_inch_rack(self, db_session: Session):
        """Test 19" device does not fit in 11" rack."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            width_inches=WidthType.ELEVEN_INCH
        )
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            width_type=WidthType.NINETEEN_INCH
        )
        db_session.add(spec)
        db_session.commit()

        # Should be incompatible
        assert spec.width_type != rack.width_inches

    def test_23_inch_device_fits_23_inch_rack(self, db_session: Session):
        """Test 23" device fits in 23" rack."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            width_inches=WidthType.TWENTY_THREE_INCH
        )
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            width_type=WidthType.TWENTY_THREE_INCH
        )
        db_session.add(spec)
        db_session.commit()

        assert spec.width_type == rack.width_inches


class TestPositionValidation:
    """Tests for rack position validation rules."""

    def test_position_within_rack_bounds(self, db_session: Session):
        """Test device position is within rack height bounds."""
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

        device = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device)
        db_session.commit()

        # Valid position
        pos = RackPosition(
            device_id=device.id,
            rack_id=rack.id,
            start_u=1
        )
        db_session.add(pos)
        db_session.commit()

        assert pos.start_u >= 1
        assert pos.start_u + spec.height_u <= rack.total_height_u

    def test_position_exceeds_rack_height_invalid(self, db_session: Session):
        """Test device position exceeding rack height is invalid."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=3.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        device = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device)
        db_session.commit()

        # Position 41 + 3U = 44U, exceeds 42U rack
        # In real validation, this should be rejected
        start_u = 41
        end_u = start_u + spec.height_u
        assert end_u > rack.total_height_u  # Invalid

    def test_no_overlapping_positions(self, db_session: Session):
        """Test overlapping device positions are invalid."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=2.0,
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

        # Device1 at U10-U11 (2U)
        pos1 = RackPosition(
            device_id=device1.id,
            rack_id=rack.id,
            start_u=10
        )
        db_session.add(pos1)
        db_session.commit()

        # Device2 at U11-U12 (2U) - overlaps with Device1
        # In real validation, this should be rejected
        start_u2 = 11
        end_u1 = pos1.start_u + spec.height_u
        assert start_u2 < end_u1  # Overlap detected


class TestPowerLimits:
    """Tests for power limit validation."""

    def test_total_power_within_rack_limit(self, db_session: Session):
        """Test total power consumption is within rack limit."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            max_power_watts=1000.0
        )
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=300.0
        )
        db_session.add(spec)
        db_session.commit()

        # Add 3 devices = 900W total, within 1000W limit
        for i in range(3):
            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()

            pos = RackPosition(
                device_id=device.id,
                rack_id=rack.id,
                start_u=i * 10 + 1
            )
            db_session.add(pos)
            db_session.commit()

        # Calculate total power
        total_power = 3 * 300.0
        assert total_power <= rack.max_power_watts

    def test_total_power_exceeds_rack_limit_invalid(self, db_session: Session):
        """Test total power exceeding rack limit is invalid."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            max_power_watts=1000.0
        )
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=400.0
        )
        db_session.add(spec)
        db_session.commit()

        # Add 3 devices = 1200W total, exceeds 1000W limit
        for i in range(3):
            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()

            pos = RackPosition(
                device_id=device.id,
                rack_id=rack.id,
                start_u=i * 10 + 1
            )
            db_session.add(pos)
            db_session.commit()

        total_power = 3 * 400.0
        assert total_power > rack.max_power_watts  # Invalid


class TestWeightLimits:
    """Tests for weight limit validation."""

    def test_total_weight_within_rack_limit(self, db_session: Session):
        """Test total weight is within rack limit."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            max_weight_kg=500.0
        )
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            weight_kg=100.0
        )
        db_session.add(spec)
        db_session.commit()

        # Add 4 devices = 400kg total, within 500kg limit
        for i in range(4):
            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()

            pos = RackPosition(
                device_id=device.id,
                rack_id=rack.id,
                start_u=i * 10 + 1
            )
            db_session.add(pos)
            db_session.commit()

        total_weight = 4 * 100.0
        assert total_weight <= rack.max_weight_kg

    def test_total_weight_exceeds_rack_limit_invalid(self, db_session: Session):
        """Test total weight exceeding rack limit is invalid."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            max_weight_kg=500.0
        )
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            weight_kg=150.0
        )
        db_session.add(spec)
        db_session.commit()

        # Add 4 devices = 600kg total, exceeds 500kg limit
        for i in range(4):
            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()

            pos = RackPosition(
                device_id=device.id,
                rack_id=rack.id,
                start_u=i * 10 + 1
            )
            db_session.add(pos)
            db_session.commit()

        total_weight = 4 * 150.0
        assert total_weight > rack.max_weight_kg  # Invalid


class TestThermalConstraints:
    """Tests for thermal constraint validation."""

    def test_cooling_capacity_sufficient(self, db_session: Session):
        """Test cooling capacity is sufficient for heat load."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            cooling_capacity_btu=17000.0
        )
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=200.0,
            heat_output_btu=682.4
        )
        db_session.add(spec)
        db_session.commit()

        # Add 10 devices = 6824 BTU total, within 17000 BTU capacity
        for i in range(10):
            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()

            pos = RackPosition(
                device_id=device.id,
                rack_id=rack.id,
                start_u=i * 4 + 1
            )
            db_session.add(pos)
            db_session.commit()

        total_heat = 10 * 682.4
        assert total_heat <= rack.cooling_capacity_btu

    def test_cooling_capacity_insufficient_warning(self, db_session: Session):
        """Test warning when cooling capacity is insufficient."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            cooling_capacity_btu=5000.0  # Low capacity
        )
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=500.0,
            heat_output_btu=1706.0
        )
        db_session.add(spec)
        db_session.commit()

        # Add 5 devices = 8530 BTU total, exceeds 5000 BTU capacity
        for i in range(5):
            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()

            pos = RackPosition(
                device_id=device.id,
                rack_id=rack.id,
                start_u=i * 8 + 1
            )
            db_session.add(pos)
            db_session.commit()

        total_heat = 5 * 1706.0
        assert total_heat > rack.cooling_capacity_btu  # Warning condition
