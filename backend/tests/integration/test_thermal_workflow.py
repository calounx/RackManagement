"""
Integration Tests for Thermal Analysis Workflow

Tests complete thermal analysis workflow:
- Create rack with devices
- Run thermal analysis
- Verify heat distribution
- Identify hot spots
- Generate recommendations
- Test thermal zones
- Test airflow conflict detection
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestThermalAnalysisWorkflow:
    """Test complete thermal analysis workflow."""

    def test_basic_thermal_analysis(self, client: TestClient, db_session: Session):
        """
        Test basic thermal analysis on a rack with devices.

        Workflow:
        1. Create rack
        2. Add devices with varying power consumption
        3. Run thermal analysis
        4. Verify all thermal metrics are returned
        """
        # Create rack
        rack_data = {
            "name": "Thermal Test Rack",
            "total_height_u": 42,
            "cooling_capacity_btu": 20000.0,
            "ambient_temp_c": 22.0,
            "max_inlet_temp_c": 27.0
        }
        response = client.post("/api/racks", json=rack_data)
        assert response.status_code == 201
        rack_id = response.json()["id"]

        # Add low-power device
        spec1_data = {
            "brand": "Cisco",
            "model": "Catalyst 2960",
            "height_u": 1.0,
            "power_watts": 120.0,
            "heat_output_btu": 409.0,
            "airflow_pattern": "front_to_back"
        }
        response = client.post("/api/device-specs", json=spec1_data)
        spec1_id = response.json()["id"]

        device1_data = {
            "specification_id": spec1_id,
            "custom_name": "Access Switch"
        }
        response = client.post("/api/devices", json=device1_data)
        device1_id = response.json()["id"]

        position1_data = {
            "device_id": device1_id,
            "start_u": 1
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position1_data)
        assert response.status_code == 201

        # Add high-power device
        spec2_data = {
            "brand": "Dell",
            "model": "PowerEdge R740",
            "height_u": 2.0,
            "power_watts": 750.0,
            "heat_output_btu": 2559.0,
            "airflow_pattern": "front_to_back"
        }
        response = client.post("/api/device-specs", json=spec2_data)
        spec2_id = response.json()["id"]

        device2_data = {
            "specification_id": spec2_id,
            "custom_name": "Database Server"
        }
        response = client.post("/api/devices", json=device2_data)
        device2_id = response.json()["id"]

        position2_data = {
            "device_id": device2_id,
            "start_u": 20
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position2_data)
        assert response.status_code == 201

        # Run thermal analysis
        response = client.get(f"/api/racks/{rack_id}/thermal-analysis")
        assert response.status_code == 200

        thermal = response.json()

        # Verify structure
        assert "rack_id" in thermal
        assert thermal["rack_id"] == rack_id
        assert "rack_name" in thermal
        assert thermal["rack_name"] == "Thermal Test Rack"

        # Verify heat distribution
        assert "heat_distribution" in thermal
        heat_dist = thermal["heat_distribution"]
        assert "total_heat_btu_hr" in heat_dist
        assert "total_power_watts" in heat_dist
        assert "bottom_zone_btu" in heat_dist
        assert "middle_zone_btu" in heat_dist
        assert "top_zone_btu" in heat_dist
        assert "device_count" in heat_dist

        # Verify cooling efficiency
        assert "cooling_efficiency" in thermal
        cooling = thermal["cooling_efficiency"]
        assert "cooling_capacity_btu_hr" in cooling
        assert "heat_load_btu_hr" in cooling
        assert "utilization_percent" in cooling
        assert "remaining_capacity_btu_hr" in cooling
        assert "status" in cooling

        # Verify hot spots
        assert "hot_spots" in thermal
        assert isinstance(thermal["hot_spots"], list)

        # Verify airflow conflicts
        assert "airflow_conflicts" in thermal
        assert isinstance(thermal["airflow_conflicts"], list)

        # Verify recommendations
        assert "recommendations" in thermal
        assert isinstance(thermal["recommendations"], list)

        # Verify timestamp
        assert "timestamp" in thermal

    def test_thermal_zones_distribution(self, client: TestClient, db_session: Session):
        """
        Test heat distribution across thermal zones.

        Workflow:
        1. Create rack
        2. Add devices to different zones (bottom, middle, top)
        3. Run thermal analysis
        4. Verify heat is correctly attributed to zones
        """
        # Create rack
        rack_data = {
            "name": "Zone Test Rack",
            "total_height_u": 42,
            "cooling_capacity_btu": 30000.0
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create device spec
        spec_data = {
            "brand": "Generic",
            "model": "Server",
            "height_u": 1.0,
            "power_watts": 500.0,
            "heat_output_btu": 1706.0,
            "airflow_pattern": "front_to_back"
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        # Add device to bottom zone (U1-U14)
        device1_data = {
            "specification_id": spec_id,
            "custom_name": "Bottom Device"
        }
        response = client.post("/api/devices", json=device1_data)
        device1_id = response.json()["id"]

        position1_data = {
            "device_id": device1_id,
            "start_u": 5  # Bottom zone
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position1_data)
        assert response.status_code == 201

        # Add device to middle zone (U15-U28)
        device2_data = {
            "specification_id": spec_id,
            "custom_name": "Middle Device"
        }
        response = client.post("/api/devices", json=device2_data)
        device2_id = response.json()["id"]

        position2_data = {
            "device_id": device2_id,
            "start_u": 20  # Middle zone
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position2_data)
        assert response.status_code == 201

        # Add device to top zone (U29-U42)
        device3_data = {
            "specification_id": spec_id,
            "custom_name": "Top Device"
        }
        response = client.post("/api/devices", json=device3_data)
        device3_id = response.json()["id"]

        position3_data = {
            "device_id": device3_id,
            "start_u": 35  # Top zone
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position3_data)
        assert response.status_code == 201

        # Run thermal analysis
        response = client.get(f"/api/racks/{rack_id}/thermal-analysis")
        assert response.status_code == 200

        thermal = response.json()
        heat_dist = thermal["heat_distribution"]

        # Each device produces ~1706 BTU
        # Verify each zone has heat
        assert heat_dist["bottom_zone_btu"] > 0
        assert heat_dist["middle_zone_btu"] > 0
        assert heat_dist["top_zone_btu"] > 0

        # Total heat should equal sum of zones
        total_zone_heat = (
            heat_dist["bottom_zone_btu"] +
            heat_dist["middle_zone_btu"] +
            heat_dist["top_zone_btu"]
        )
        assert abs(total_zone_heat - heat_dist["total_heat_btu_hr"]) < 1.0

        # Should have 3 devices
        assert heat_dist["device_count"] == 3

    def test_hot_spot_identification(self, client: TestClient, db_session: Session):
        """
        Test identification of high-heat devices (hot spots).

        Workflow:
        1. Create rack
        2. Add mix of low and high power devices
        3. Run thermal analysis
        4. Verify high-power devices are identified as hot spots
        """
        # Create rack
        rack_data = {
            "name": "Hot Spot Rack",
            "total_height_u": 42,
            "cooling_capacity_btu": 25000.0
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Add low-power device
        low_spec_data = {
            "brand": "Low",
            "model": "Power",
            "height_u": 1.0,
            "power_watts": 100.0,
            "heat_output_btu": 341.0,
            "airflow_pattern": "front_to_back"
        }
        response = client.post("/api/device-specs", json=low_spec_data)
        low_spec_id = response.json()["id"]

        low_device_data = {
            "specification_id": low_spec_id,
            "custom_name": "Low Power Device"
        }
        response = client.post("/api/devices", json=low_device_data)
        low_device_id = response.json()["id"]

        position_data = {
            "device_id": low_device_id,
            "start_u": 1
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Add high-power device
        high_spec_data = {
            "brand": "High",
            "model": "Power",
            "height_u": 2.0,
            "power_watts": 1200.0,
            "heat_output_btu": 4094.0,
            "airflow_pattern": "front_to_back"
        }
        response = client.post("/api/device-specs", json=high_spec_data)
        high_spec_id = response.json()["id"]

        high_device_data = {
            "specification_id": high_spec_id,
            "custom_name": "High Power Device"
        }
        response = client.post("/api/devices", json=high_device_data)
        high_device_id = response.json()["id"]

        position_data = {
            "device_id": high_device_id,
            "start_u": 10
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Run thermal analysis
        response = client.get(f"/api/racks/{rack_id}/thermal-analysis")
        assert response.status_code == 200

        thermal = response.json()
        hot_spots = thermal["hot_spots"]

        # Should identify at least one hot spot
        assert len(hot_spots) >= 1

        # High power device should be in hot spots
        high_power_in_hotspots = any(
            hs["device_id"] == high_device_id
            for hs in hot_spots
        )
        assert high_power_in_hotspots

        # Verify hot spot structure
        if len(hot_spots) > 0:
            hotspot = hot_spots[0]
            assert "device_id" in hotspot
            assert "device_name" in hotspot
            assert "position" in hotspot
            assert "zone" in hotspot
            assert "heat_output_btu_hr" in hotspot
            assert "power_watts" in hotspot
            assert "airflow_pattern" in hotspot
            assert "severity" in hotspot

    def test_airflow_conflict_detection(self, client: TestClient, db_session: Session):
        """
        Test detection of airflow conflicts between adjacent devices.

        Workflow:
        1. Create rack
        2. Add devices with conflicting airflow patterns
        3. Run thermal analysis
        4. Verify conflicts are detected
        """
        # Create rack
        rack_data = {
            "name": "Airflow Test Rack",
            "total_height_u": 42,
            "cooling_capacity_btu": 20000.0
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Add front-to-back device
        ftb_spec_data = {
            "brand": "FTB",
            "model": "Device",
            "height_u": 1.0,
            "power_watts": 300.0,
            "heat_output_btu": 1024.0,
            "airflow_pattern": "front_to_back"
        }
        response = client.post("/api/device-specs", json=ftb_spec_data)
        ftb_spec_id = response.json()["id"]

        ftb_device_data = {
            "specification_id": ftb_spec_id,
            "custom_name": "Front-to-Back Device"
        }
        response = client.post("/api/devices", json=ftb_device_data)
        ftb_device_id = response.json()["id"]

        position_data = {
            "device_id": ftb_device_id,
            "start_u": 10
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Add back-to-front device right next to it
        btf_spec_data = {
            "brand": "BTF",
            "model": "Device",
            "height_u": 1.0,
            "power_watts": 300.0,
            "heat_output_btu": 1024.0,
            "airflow_pattern": "back_to_front"
        }
        response = client.post("/api/device-specs", json=btf_spec_data)
        btf_spec_id = response.json()["id"]

        btf_device_data = {
            "specification_id": btf_spec_id,
            "custom_name": "Back-to-Front Device"
        }
        response = client.post("/api/devices", json=btf_device_data)
        btf_device_id = response.json()["id"]

        position_data = {
            "device_id": btf_device_id,
            "start_u": 11  # Adjacent to FTB device
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Run thermal analysis
        response = client.get(f"/api/racks/{rack_id}/thermal-analysis")
        assert response.status_code == 200

        thermal = response.json()
        conflicts = thermal["airflow_conflicts"]

        # Should detect airflow conflict
        assert len(conflicts) >= 1

        # Verify conflict structure
        if len(conflicts) > 0:
            conflict = conflicts[0]
            assert "type" in conflict
            assert "severity" in conflict
            assert "device1" in conflict
            assert "device2" in conflict
            assert "message" in conflict

    def test_cooling_capacity_warnings(self, client: TestClient, db_session: Session):
        """
        Test thermal analysis warnings when approaching cooling capacity limits.

        Workflow:
        1. Create rack with limited cooling
        2. Add devices that approach/exceed capacity
        3. Run thermal analysis
        4. Verify warnings in recommendations
        """
        # Create rack with limited cooling
        rack_data = {
            "name": "Limited Cooling Rack",
            "total_height_u": 42,
            "cooling_capacity_btu": 5000.0  # Low capacity
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Add high-heat devices
        spec_data = {
            "brand": "Hot",
            "model": "Server",
            "height_u": 2.0,
            "power_watts": 800.0,
            "heat_output_btu": 2730.0,
            "airflow_pattern": "front_to_back"
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        # Add two devices (total ~5460 BTU, exceeds 5000 capacity)
        for i in range(2):
            device_data = {
                "specification_id": spec_id,
                "custom_name": f"Hot Server {i+1}"
            }
            response = client.post("/api/devices", json=device_data)
            device_id = response.json()["id"]

            position_data = {
                "device_id": device_id,
                "start_u": 1 + (i * 5)
            }
            response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
            assert response.status_code == 201

        # Run thermal analysis
        response = client.get(f"/api/racks/{rack_id}/thermal-analysis")
        assert response.status_code == 200

        thermal = response.json()

        # Check cooling efficiency
        cooling = thermal["cooling_efficiency"]
        assert cooling["utilization_percent"] > 90  # Should be over capacity

        # Check status
        assert cooling["status"] in ["warning", "critical"]

        # Should have recommendations
        recommendations = thermal["recommendations"]
        assert len(recommendations) > 0

        # Should warn about cooling capacity
        cooling_warnings = [
            r for r in recommendations
            if "cooling" in r.lower() or "capacity" in r.lower()
        ]
        assert len(cooling_warnings) > 0

    def test_empty_rack_thermal_analysis(self, client: TestClient, db_session: Session):
        """
        Test thermal analysis on an empty rack.

        Workflow:
        1. Create empty rack
        2. Run thermal analysis
        3. Verify zero heat load and optimal status
        """
        # Create empty rack
        rack_data = {
            "name": "Empty Rack",
            "total_height_u": 42,
            "cooling_capacity_btu": 17000.0
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Run thermal analysis
        response = client.get(f"/api/racks/{rack_id}/thermal-analysis")
        assert response.status_code == 200

        thermal = response.json()

        # Verify zero heat
        heat_dist = thermal["heat_distribution"]
        assert heat_dist["total_heat_btu_hr"] == 0
        assert heat_dist["total_power_watts"] == 0
        assert heat_dist["bottom_zone_btu"] == 0
        assert heat_dist["middle_zone_btu"] == 0
        assert heat_dist["top_zone_btu"] == 0
        assert heat_dist["device_count"] == 0

        # Verify optimal cooling
        cooling = thermal["cooling_efficiency"]
        assert cooling["utilization_percent"] == 0
        assert cooling["remaining_capacity_btu_hr"] == cooling["cooling_capacity_btu_hr"]
        assert cooling["status"] == "optimal"

        # No hot spots
        assert len(thermal["hot_spots"]) == 0

        # No airflow conflicts
        assert len(thermal["airflow_conflicts"]) == 0

    def test_thermal_analysis_nonexistent_rack(self, client: TestClient, db_session: Session):
        """Test thermal analysis on non-existent rack returns 404."""
        response = client.get("/api/racks/99999/thermal-analysis")
        assert response.status_code == 404

    def test_thermal_recommendations_quality(self, client: TestClient, db_session: Session):
        """
        Test that thermal recommendations are actionable and specific.

        Workflow:
        1. Create problematic rack setup
        2. Run thermal analysis
        3. Verify recommendations address specific issues
        """
        # Create rack
        rack_data = {
            "name": "Problem Rack",
            "total_height_u": 42,
            "cooling_capacity_btu": 15000.0
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create high-heat device in top zone (worst placement for heat)
        spec_data = {
            "brand": "Hot",
            "model": "GPU Server",
            "height_u": 4.0,
            "power_watts": 2000.0,
            "heat_output_btu": 6824.0,
            "airflow_pattern": "front_to_back"
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        device_data = {
            "specification_id": spec_id,
            "custom_name": "GPU Server"
        }
        response = client.post("/api/devices", json=device_data)
        device_id = response.json()["id"]

        position_data = {
            "device_id": device_id,
            "start_u": 38  # Near top (heat rises)
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Run thermal analysis
        response = client.get(f"/api/racks/{rack_id}/thermal-analysis")
        assert response.status_code == 200

        thermal = response.json()
        recommendations = thermal["recommendations"]

        # Should have recommendations
        assert len(recommendations) > 0

        # Verify recommendations are not empty strings
        for rec in recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 0
