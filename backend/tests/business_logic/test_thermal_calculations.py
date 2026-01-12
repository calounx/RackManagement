"""
Business logic tests for thermal calculations.

Tests thermal zone assignment, heat distribution, cooling efficiency,
hot spot detection, and airflow conflict detection.
Total: ~20 tests
"""

import pytest
from sqlalchemy.orm import Session

from app.thermal import (
    get_thermal_zone,
    calculate_rack_heat_output,
    calculate_cooling_efficiency,
    identify_hot_spots,
    check_airflow_conflicts,
    get_thermal_recommendations
)
from app.models import (
    Rack, Device, DeviceSpecification, RackPosition,
    ThermalZone, AirflowPattern, SourceType
)


class TestThermalZoneAssignment:
    """Tests for thermal zone assignment logic."""

    def test_get_thermal_zone_bottom(self):
        """Test bottom zone assignment (U1-U14 in 42U rack)."""
        assert get_thermal_zone(1, 42) == ThermalZone.BOTTOM
        assert get_thermal_zone(7, 42) == ThermalZone.BOTTOM
        assert get_thermal_zone(14, 42) == ThermalZone.BOTTOM

    def test_get_thermal_zone_middle(self):
        """Test middle zone assignment (U15-U28 in 42U rack)."""
        assert get_thermal_zone(15, 42) == ThermalZone.MIDDLE
        assert get_thermal_zone(21, 42) == ThermalZone.MIDDLE
        assert get_thermal_zone(28, 42) == ThermalZone.MIDDLE

    def test_get_thermal_zone_top(self):
        """Test top zone assignment (U29-U42 in 42U rack)."""
        assert get_thermal_zone(29, 42) == ThermalZone.TOP
        assert get_thermal_zone(35, 42) == ThermalZone.TOP
        assert get_thermal_zone(42, 42) == ThermalZone.TOP

    def test_get_thermal_zone_different_rack_heights(self):
        """Test zone assignment works with different rack heights."""
        # 48U rack
        assert get_thermal_zone(1, 48) == ThermalZone.BOTTOM
        assert get_thermal_zone(16, 48) == ThermalZone.BOTTOM
        assert get_thermal_zone(17, 48) == ThermalZone.MIDDLE
        assert get_thermal_zone(33, 48) == ThermalZone.TOP

    def test_get_thermal_zone_small_rack(self):
        """Test zone assignment in small rack (12U)."""
        assert get_thermal_zone(1, 12) == ThermalZone.BOTTOM
        assert get_thermal_zone(4, 12) == ThermalZone.BOTTOM
        assert get_thermal_zone(5, 12) == ThermalZone.MIDDLE
        assert get_thermal_zone(9, 12) == ThermalZone.TOP


class TestHeatDistribution:
    """Tests for heat distribution calculations."""

    def test_calculate_rack_heat_empty_rack(self, db_session: Session):
        """Test heat calculation for empty rack."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        result = calculate_rack_heat_output(rack, db_session)

        assert result["total_heat_btu_hr"] == 0.0
        assert result["total_power_watts"] == 0.0
        assert result["device_count"] == 0

    def test_calculate_rack_heat_single_device(self, db_session: Session):
        """Test heat calculation with single device."""
        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0,
            heat_output_btu=341.2
        )
        db_session.add(spec)
        db_session.commit()

        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        device = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device)
        db_session.commit()

        position = RackPosition(
            device_id=device.id,
            rack_id=rack.id,
            start_u=10
        )
        db_session.add(position)
        db_session.commit()

        result = calculate_rack_heat_output(rack, db_session)

        assert result["total_heat_btu_hr"] == 341.2
        assert result["total_power_watts"] == 100.0
        assert result["device_count"] == 1

    def test_calculate_rack_heat_multiple_devices(self, db_session: Session):
        """Test heat calculation with multiple devices."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        # Create 3 devices with different power levels
        specs_and_positions = [
            (100.0, 5),   # Bottom zone
            (200.0, 20),  # Middle zone
            (300.0, 35),  # Top zone
        ]

        for power, u_pos in specs_and_positions:
            spec = DeviceSpecification(
                brand="Test", model=f"Device{power}W",
                height_u=1.0,
                power_watts=power
            )
            db_session.add(spec)
            db_session.commit()

            device = Device(
                custom_name=f"Device{power}W",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()

            position = RackPosition(
                device_id=device.id,
                rack_id=rack.id,
                start_u=u_pos
            )
            db_session.add(position)
            db_session.commit()

        result = calculate_rack_heat_output(rack, db_session)

        assert result["total_power_watts"] == 600.0
        assert result["total_heat_btu_hr"] == pytest.approx(600.0 * 3.412, rel=0.01)
        assert result["device_count"] == 3

    def test_heat_distribution_by_zone(self, db_session: Session):
        """Test heat is correctly distributed across thermal zones."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        # Add device in bottom zone
        spec1 = DeviceSpecification(
            brand="Test", model="Device1",
            height_u=1.0,
            power_watts=100.0,
            heat_output_btu=341.2
        )
        db_session.add(spec1)
        db_session.commit()

        device1 = Device(
            custom_name="Device1",
            specification_id=spec1.id,
            brand="Test", model="Device1"
        )
        db_session.add(device1)
        db_session.commit()

        pos1 = RackPosition(device_id=device1.id, rack_id=rack.id, start_u=5)
        db_session.add(pos1)
        db_session.commit()

        result = calculate_rack_heat_output(rack, db_session)

        # All heat should be in bottom zone
        assert result["bottom_zone_btu"] == 341.2
        assert result["middle_zone_btu"] == 0.0
        assert result["top_zone_btu"] == 0.0

    def test_auto_calculate_btu_from_watts(self, db_session: Session):
        """Test BTU is auto-calculated from watts when not specified."""
        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0,
            heat_output_btu=None  # Not specified
        )
        db_session.add(spec)
        db_session.commit()

        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        device = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device)
        db_session.commit()

        position = RackPosition(
            device_id=device.id,
            rack_id=rack.id,
            start_u=10
        )
        db_session.add(position)
        db_session.commit()

        result = calculate_rack_heat_output(rack, db_session)

        # 100W * 3.412 = 341.2 BTU
        assert result["total_heat_btu_hr"] == pytest.approx(341.2, rel=0.01)


class TestCoolingEfficiency:
    """Tests for cooling efficiency calculations."""

    def test_cooling_efficiency_no_load(self):
        """Test cooling efficiency with no heat load."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            cooling_capacity_btu=17000.0
        )

        result = calculate_cooling_efficiency(rack, 0.0)

        assert result["utilization_percent"] == 0.0
        assert result["remaining_capacity_btu_hr"] == 17000.0
        assert result["status"] == "optimal"

    def test_cooling_efficiency_optimal_load(self):
        """Test cooling efficiency at optimal load (< 70%)."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            cooling_capacity_btu=17000.0
        )

        # 10,000 BTU load = 58.8% utilization
        result = calculate_cooling_efficiency(rack, 10000.0)

        assert result["utilization_percent"] == pytest.approx(58.8, rel=0.1)
        assert result["remaining_capacity_btu_hr"] == 7000.0
        assert result["status"] == "optimal"

    def test_cooling_efficiency_acceptable_load(self):
        """Test cooling efficiency at acceptable load (70-85%)."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            cooling_capacity_btu=17000.0
        )

        # 13,000 BTU load = 76.5% utilization
        result = calculate_cooling_efficiency(rack, 13000.0)

        assert result["utilization_percent"] == pytest.approx(76.5, rel=0.1)
        assert result["status"] == "acceptable"

    def test_cooling_efficiency_warning_load(self):
        """Test cooling efficiency at warning load (85-100%)."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            cooling_capacity_btu=17000.0
        )

        # 15,000 BTU load = 88.2% utilization
        result = calculate_cooling_efficiency(rack, 15000.0)

        assert result["utilization_percent"] == pytest.approx(88.2, rel=0.1)
        assert result["status"] == "warning"

    def test_cooling_efficiency_critical_load(self):
        """Test cooling efficiency at critical load (> 100%)."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            cooling_capacity_btu=17000.0
        )

        # 18,000 BTU load = 105.9% utilization
        result = calculate_cooling_efficiency(rack, 18000.0)

        assert result["utilization_percent"] == pytest.approx(105.9, rel=0.1)
        assert result["status"] == "critical"
        assert result["remaining_capacity_btu_hr"] == 0.0

    def test_cooling_capacity_in_tons(self):
        """Test cooling capacity is correctly converted to tons."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            cooling_capacity_btu=12000.0  # 1 ton
        )

        result = calculate_cooling_efficiency(rack, 0.0)

        assert result["cooling_capacity_tons"] == 1.0
        assert result["remaining_capacity_tons"] == 1.0


class TestHotSpotDetection:
    """Tests for hot spot identification."""

    def test_identify_hot_spots_none(self, db_session: Session):
        """Test hot spot detection with low-power devices."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="LowPower",
            height_u=1.0,
            power_watts=50.0  # Low power, < 1000 BTU threshold
        )
        db_session.add(spec)
        db_session.commit()

        device = Device(
            custom_name="LowPower",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device)
        db_session.commit()

        position = RackPosition(
            device_id=device.id,
            rack_id=rack.id,
            start_u=10
        )
        db_session.add(position)
        db_session.commit()

        hot_spots = identify_hot_spots(rack, db_session, threshold_btu=1000.0)

        assert len(hot_spots) == 0

    def test_identify_hot_spots_single(self, db_session: Session):
        """Test hot spot detection with high-power device."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="HighPower",
            height_u=1.0,
            power_watts=500.0,  # 1706 BTU
            heat_output_btu=1706.0
        )
        db_session.add(spec)
        db_session.commit()

        device = Device(
            custom_name="Server1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device)
        db_session.commit()

        position = RackPosition(
            device_id=device.id,
            rack_id=rack.id,
            start_u=10
        )
        db_session.add(position)
        db_session.commit()

        hot_spots = identify_hot_spots(rack, db_session, threshold_btu=1000.0)

        assert len(hot_spots) == 1
        assert hot_spots[0]["device_name"] == "Server1"
        assert hot_spots[0]["heat_output_btu_hr"] == 1706.0

    def test_hot_spots_sorted_by_heat(self, db_session: Session):
        """Test hot spots are sorted by heat output (highest first)."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        power_levels = [300.0, 500.0, 200.0]

        for power in power_levels:
            spec = DeviceSpecification(
                brand="Test", model=f"Device{power}W",
                height_u=1.0,
                power_watts=power
            )
            db_session.add(spec)
            db_session.commit()

            device = Device(
                custom_name=f"Device{power}W",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()

            position = RackPosition(
                device_id=device.id,
                rack_id=rack.id,
                start_u=int(power)  # Arbitrary position
            )
            db_session.add(position)
            db_session.commit()

        hot_spots = identify_hot_spots(rack, db_session, threshold_btu=500.0)

        # Should be sorted: 500W, 300W, 200W
        assert len(hot_spots) == 3
        assert hot_spots[0]["device_name"] == "Device500.0W"
        assert hot_spots[1]["device_name"] == "Device300.0W"
        assert hot_spots[2]["device_name"] == "Device200.0W"


class TestAirflowConflicts:
    """Tests for airflow conflict detection."""

    def test_check_airflow_no_conflicts(self, db_session: Session):
        """Test no conflicts with same airflow direction."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        # Both devices have front-to-back airflow
        for i in range(2):
            spec = DeviceSpecification(
                brand="Test", model=f"Device{i}",
                height_u=1.0,
                power_watts=100.0,
                airflow_pattern=AirflowPattern.FRONT_TO_BACK
            )
            db_session.add(spec)
            db_session.commit()

            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()

            position = RackPosition(
                device_id=device.id,
                rack_id=rack.id,
                start_u=i * 10 + 1
            )
            db_session.add(position)
            db_session.commit()

        conflicts = check_airflow_conflicts(rack, db_session)

        assert len(conflicts) == 0

    def test_check_airflow_opposing_patterns(self, db_session: Session):
        """Test detection of opposing airflow patterns."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        # Device 1: front-to-back
        spec1 = DeviceSpecification(
            brand="Test", model="Device1",
            height_u=1.0,
            power_watts=100.0,
            airflow_pattern=AirflowPattern.FRONT_TO_BACK
        )
        db_session.add(spec1)
        db_session.commit()

        device1 = Device(
            custom_name="Device1",
            specification_id=spec1.id,
            brand="Test", model="Device1"
        )
        db_session.add(device1)
        db_session.commit()

        pos1 = RackPosition(device_id=device1.id, rack_id=rack.id, start_u=10)
        db_session.add(pos1)
        db_session.commit()

        # Device 2: back-to-front (adjacent)
        spec2 = DeviceSpecification(
            brand="Test", model="Device2",
            height_u=1.0,
            power_watts=100.0,
            airflow_pattern=AirflowPattern.BACK_TO_FRONT
        )
        db_session.add(spec2)
        db_session.commit()

        device2 = Device(
            custom_name="Device2",
            specification_id=spec2.id,
            brand="Test", model="Device2"
        )
        db_session.add(device2)
        db_session.commit()

        pos2 = RackPosition(device_id=device2.id, rack_id=rack.id, start_u=11)
        db_session.add(pos2)
        db_session.commit()

        conflicts = check_airflow_conflicts(rack, db_session)

        assert len(conflicts) == 1
        assert conflicts[0]["type"] == "opposing_airflow"
        assert conflicts[0]["severity"] == "high"


class TestThermalRecommendations:
    """Tests for thermal management recommendations."""

    def test_recommendations_optimal_config(self, db_session: Session):
        """Test recommendations for optimal thermal configuration."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            cooling_capacity_btu=17000.0
        )
        db_session.add(rack)
        db_session.commit()

        recommendations = get_thermal_recommendations(rack, db_session)

        # Should have positive message for optimal config
        assert any("optimal" in rec.lower() for rec in recommendations)

    def test_recommendations_high_cooling_utilization(self, db_session: Session):
        """Test recommendations when cooling is heavily utilized."""
        rack = Rack(
            name="Test",
            total_height_u=42,
            cooling_capacity_btu=1000.0  # Very low capacity
        )
        db_session.add(rack)
        db_session.commit()

        # Add high-power device
        spec = DeviceSpecification(
            brand="Test", model="HighPower",
            height_u=1.0,
            power_watts=300.0
        )
        db_session.add(spec)
        db_session.commit()

        device = Device(
            custom_name="Server",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device)
        db_session.commit()

        position = RackPosition(
            device_id=device.id,
            rack_id=rack.id,
            start_u=10
        )
        db_session.add(position)
        db_session.commit()

        recommendations = get_thermal_recommendations(rack, db_session)

        # Should recommend upgrading cooling
        assert any("cooling" in rec.lower() for rec in recommendations)
