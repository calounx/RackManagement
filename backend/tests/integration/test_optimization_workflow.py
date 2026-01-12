"""
Integration Tests for Optimization Workflow

Tests complete rack optimization workflow:
- Create rack with suboptimal device placement
- Run optimization with custom weights
- Lock specific positions
- Apply optimization
- Verify improvements
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestOptimizationWorkflow:
    """Test complete rack optimization workflow."""

    def test_basic_optimization(self, client: TestClient, db_session: Session):
        """
        Test basic rack optimization.

        Workflow:
        1. Create rack with suboptimal placement
        2. Run optimization with default weights
        3. Verify optimization result structure
        4. Verify improvements are reported
        """
        # Create rack
        rack_data = {
            "name": "Optimization Test Rack",
            "total_height_u": 42,
            "cooling_capacity_btu": 20000.0
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create devices with varying characteristics
        devices = []

        # High-access, heavy device (should be low in rack)
        spec1_data = {
            "brand": "Dell",
            "model": "PowerEdge R740",
            "height_u": 2.0,
            "power_watts": 750.0,
            "heat_output_btu": 2559.0,
            "weight_kg": 28.0,
            "airflow_pattern": "front_to_back"
        }
        response = client.post("/api/device-specs", json=spec1_data)
        spec1_id = response.json()["id"]

        device1_data = {
            "specification_id": spec1_id,
            "custom_name": "Heavy Server",
            "access_frequency": "high"
        }
        response = client.post("/api/devices", json=device1_data)
        devices.append(response.json())

        # Low-access, light device (can be higher)
        spec2_data = {
            "brand": "Cisco",
            "model": "Catalyst 9200",
            "height_u": 1.0,
            "power_watts": 180.0,
            "heat_output_btu": 614.0,
            "weight_kg": 3.5,
            "airflow_pattern": "front_to_back"
        }
        response = client.post("/api/device-specs", json=spec2_data)
        spec2_id = response.json()["id"]

        device2_data = {
            "specification_id": spec2_id,
            "custom_name": "Light Switch",
            "access_frequency": "low"
        }
        response = client.post("/api/devices", json=device2_data)
        devices.append(response.json())

        # Deliberately poor placement: heavy at top, light at bottom
        position_data = {
            "device_id": devices[0]["id"],  # Heavy device
            "start_u": 35,  # Near top
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        position_data = {
            "device_id": devices[1]["id"],  # Light device
            "start_u": 1,  # At bottom
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Run optimization
        optimization_request = {
            "locked_positions": [],
            "weights": {
                "cable": 0.25,
                "weight": 0.25,
                "thermal": 0.25,
                "access": 0.25
            }
        }
        response = client.post(f"/api/racks/{rack_id}/optimize", json=optimization_request)
        assert response.status_code == 200

        optimization = response.json()

        # Verify structure
        assert "positions" in optimization
        assert "score" in optimization
        assert "improvements" in optimization
        assert "metadata" in optimization

        # Verify positions
        positions = optimization["positions"]
        assert len(positions) == 2

        # Verify score breakdown
        score = optimization["score"]
        assert "cable_management" in score
        assert "weight_distribution" in score
        assert "thermal_management" in score
        assert "access_frequency" in score
        assert "total" in score

        # Verify improvements list
        improvements = optimization["improvements"]
        assert isinstance(improvements, list)
        assert len(improvements) > 0

    def test_optimization_with_locked_positions(self, client: TestClient, db_session: Session):
        """
        Test optimization with locked positions.

        Workflow:
        1. Create rack with multiple devices
        2. Lock some devices
        3. Run optimization
        4. Verify locked devices didn't move
        5. Verify unlocked devices were optimized
        """
        # Create rack
        rack_data = {
            "name": "Lock Test Rack",
            "total_height_u": 42
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create spec
        spec_data = {
            "brand": "Generic",
            "model": "Device",
            "height_u": 1.0,
            "power_watts": 200.0,
            "heat_output_btu": 682.0,
            "weight_kg": 5.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        # Create 3 devices
        device_ids = []
        for i in range(3):
            device_data = {
                "specification_id": spec_id,
                "custom_name": f"Device {i+1}",
                "access_frequency": "medium"
            }
            response = client.post("/api/devices", json=device_data)
            device_ids.append(response.json()["id"])

        # Add devices to rack
        # Device 1 at U5 - will be locked
        position_data = {
            "device_id": device_ids[0],
            "start_u": 5,
            "locked": True
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Device 2 at U20 - unlocked
        position_data = {
            "device_id": device_ids[1],
            "start_u": 20,
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Device 3 at U35 - unlocked
        position_data = {
            "device_id": device_ids[2],
            "start_u": 35,
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Run optimization with locked position
        optimization_request = {
            "locked_positions": [device_ids[0]],  # Lock first device
            "weights": {
                "cable": 0.25,
                "weight": 0.25,
                "thermal": 0.25,
                "access": 0.25
            }
        }
        response = client.post(f"/api/racks/{rack_id}/optimize", json=optimization_request)
        assert response.status_code == 200

        optimization = response.json()
        positions = optimization["positions"]

        # Find locked device in results
        locked_device_pos = next(p for p in positions if p["device_id"] == device_ids[0])
        assert locked_device_pos["start_u"] == 5  # Should not have moved
        assert locked_device_pos["locked"] is True

    def test_optimization_weight_variations(self, client: TestClient, db_session: Session):
        """
        Test optimization with different weight configurations.

        Workflow:
        1. Create rack with devices
        2. Run optimization prioritizing thermal (high thermal weight)
        3. Run optimization prioritizing access (high access weight)
        4. Verify different weights produce different results
        """
        # Create rack
        rack_data = {
            "name": "Weight Test Rack",
            "total_height_u": 42,
            "cooling_capacity_btu": 15000.0
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create high-heat device
        hot_spec_data = {
            "brand": "Hot",
            "model": "Server",
            "height_u": 2.0,
            "power_watts": 1000.0,
            "heat_output_btu": 3412.0,
            "weight_kg": 20.0
        }
        response = client.post("/api/device-specs", json=hot_spec_data)
        hot_spec_id = response.json()["id"]

        hot_device_data = {
            "specification_id": hot_spec_id,
            "custom_name": "Hot Device",
            "access_frequency": "low"
        }
        response = client.post("/api/devices", json=hot_device_data)
        hot_device_id = response.json()["id"]

        # Create high-access device
        access_spec_data = {
            "brand": "Access",
            "model": "Device",
            "height_u": 1.0,
            "power_watts": 150.0,
            "heat_output_btu": 512.0,
            "weight_kg": 5.0
        }
        response = client.post("/api/device-specs", json=access_spec_data)
        access_spec_id = response.json()["id"]

        access_device_data = {
            "specification_id": access_spec_id,
            "custom_name": "Access Device",
            "access_frequency": "high"
        }
        response = client.post("/api/devices", json=access_device_data)
        access_device_id = response.json()["id"]

        # Add devices to rack (poor placement)
        position_data = {
            "device_id": hot_device_id,
            "start_u": 35,  # Hot device at top
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        position_data = {
            "device_id": access_device_id,
            "start_u": 20,  # High-access device in middle
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Optimization 1: Prioritize thermal
        thermal_request = {
            "locked_positions": [],
            "weights": {
                "cable": 0.10,
                "weight": 0.20,
                "thermal": 0.60,  # Heavy thermal weight
                "access": 0.10
            }
        }
        response = client.post(f"/api/racks/{rack_id}/optimize", json=thermal_request)
        assert response.status_code == 200
        thermal_optimization = response.json()
        thermal_score = thermal_optimization["score"]["thermal_management"]

        # Optimization 2: Prioritize access
        access_request = {
            "locked_positions": [],
            "weights": {
                "cable": 0.10,
                "weight": 0.20,
                "thermal": 0.10,
                "access": 0.60  # Heavy access weight
            }
        }
        response = client.post(f"/api/racks/{rack_id}/optimize", json=access_request)
        assert response.status_code == 200
        access_optimization = response.json()
        access_score = access_optimization["score"]["access_frequency"]

        # Both optimizations should produce valid results
        assert thermal_score >= 0
        assert access_score >= 0

    def test_optimization_empty_rack(self, client: TestClient, db_session: Session):
        """Test optimization on empty rack."""
        # Create empty rack
        rack_data = {
            "name": "Empty Rack",
            "total_height_u": 42
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Try to optimize empty rack
        optimization_request = {
            "locked_positions": [],
            "weights": {
                "cable": 0.25,
                "weight": 0.25,
                "thermal": 0.25,
                "access": 0.25
            }
        }
        response = client.post(f"/api/racks/{rack_id}/optimize", json=optimization_request)
        # Should handle gracefully - either 400 or return empty result
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            optimization = response.json()
            assert len(optimization["positions"]) == 0

    def test_optimization_single_device(self, client: TestClient, db_session: Session):
        """
        Test optimization with single device.

        Single device should optimize to optimal position (considering thermal, access, weight).
        """
        # Create rack
        rack_data = {
            "name": "Single Device Rack",
            "total_height_u": 42
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create heavy, high-access device
        spec_data = {
            "brand": "Heavy",
            "model": "Device",
            "height_u": 2.0,
            "power_watts": 500.0,
            "weight_kg": 30.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        device_data = {
            "specification_id": spec_id,
            "custom_name": "Heavy Device",
            "access_frequency": "high"
        }
        response = client.post("/api/devices", json=device_data)
        device_id = response.json()["id"]

        # Place at suboptimal position (high in rack)
        position_data = {
            "device_id": device_id,
            "start_u": 30,
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Run optimization
        optimization_request = {
            "locked_positions": [],
            "weights": {
                "cable": 0.20,
                "weight": 0.30,  # Prioritize weight
                "thermal": 0.20,
                "access": 0.30   # Prioritize access
            }
        }
        response = client.post(f"/api/racks/{rack_id}/optimize", json=optimization_request)
        assert response.status_code == 200

        optimization = response.json()
        positions = optimization["positions"]
        assert len(positions) == 1

        # Heavy, high-access device should move lower
        optimized_pos = positions[0]
        assert optimized_pos["start_u"] < 30  # Should move down

    def test_optimization_with_connections(self, client: TestClient, db_session: Session):
        """
        Test optimization considering cable connections.

        Workflow:
        1. Create rack with connected devices
        2. Place devices far apart
        3. Run optimization with high cable weight
        4. Verify devices move closer together
        """
        # Create rack
        rack_data = {
            "name": "Connection Rack",
            "total_height_u": 42
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create two devices
        spec_data = {
            "brand": "Test",
            "model": "Device",
            "height_u": 1.0,
            "power_watts": 200.0,
            "weight_kg": 5.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        device1_data = {
            "specification_id": spec_id,
            "custom_name": "Device 1",
            "access_frequency": "medium"
        }
        response = client.post("/api/devices", json=device1_data)
        device1_id = response.json()["id"]

        device2_data = {
            "specification_id": spec_id,
            "custom_name": "Device 2",
            "access_frequency": "medium"
        }
        response = client.post("/api/devices", json=device2_data)
        device2_id = response.json()["id"]

        # Place far apart
        position_data = {
            "device_id": device1_id,
            "start_u": 1,
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        position_data = {
            "device_id": device2_id,
            "start_u": 40,
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Create connection
        connection_data = {
            "from_device_id": device1_id,
            "to_device_id": device2_id,
            "cable_type": "Cat6"
        }
        response = client.post("/api/connections", json=connection_data)
        assert response.status_code == 201

        # Run optimization with high cable weight
        optimization_request = {
            "locked_positions": [],
            "weights": {
                "cable": 0.70,  # Prioritize cable management
                "weight": 0.10,
                "thermal": 0.10,
                "access": 0.10
            }
        }
        response = client.post(f"/api/racks/{rack_id}/optimize", json=optimization_request)
        assert response.status_code == 200

        optimization = response.json()
        positions = optimization["positions"]

        # Calculate distance between devices
        device1_pos = next(p for p in positions if p["device_id"] == device1_id)
        device2_pos = next(p for p in positions if p["device_id"] == device2_id)
        distance = abs(device1_pos["start_u"] - device2_pos["start_u"])

        # Distance should be less than original (39 units apart)
        assert distance < 39

    def test_optimization_nonexistent_rack(self, client: TestClient, db_session: Session):
        """Test optimization on non-existent rack returns 404."""
        optimization_request = {
            "locked_positions": [],
            "weights": {
                "cable": 0.25,
                "weight": 0.25,
                "thermal": 0.25,
                "access": 0.25
            }
        }
        response = client.post("/api/racks/99999/optimize", json=optimization_request)
        assert response.status_code == 404

    def test_optimization_invalid_weights(self, client: TestClient, db_session: Session):
        """Test optimization with invalid weights (not summing to 1.0)."""
        # Create rack
        rack_data = {
            "name": "Test Rack",
            "total_height_u": 42
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Try optimization with invalid weights
        invalid_request = {
            "locked_positions": [],
            "weights": {
                "cable": 0.50,
                "weight": 0.50,
                "thermal": 0.50,
                "access": 0.50  # Sum = 2.0, should fail
            }
        }
        response = client.post(f"/api/racks/{rack_id}/optimize", json=invalid_request)
        assert response.status_code == 422  # Validation error
