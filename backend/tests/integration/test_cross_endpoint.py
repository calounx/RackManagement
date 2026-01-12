"""
Integration Tests for Cross-Endpoint Operations

Tests operations that span multiple endpoints and verify data consistency:
- Device movement between racks
- Bulk operations
- Data consistency (update spec reflects in device, etc.)
- Complex multi-step operations
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestDeviceMovement:
    """Test device movement and positioning across racks."""

    def test_move_device_between_racks(self, client: TestClient, db_session: Session):
        """
        Test moving a device from one rack to another.

        Workflow:
        1. Create two racks
        2. Create device and add to rack1
        3. Remove from rack1
        4. Add to rack2
        5. Verify device is only in rack2
        """
        # Create two racks
        rack1_data = {"name": "Source Rack", "total_height_u": 42}
        response = client.post("/api/racks", json=rack1_data)
        rack1_id = response.json()["id"]

        rack2_data = {"name": "Target Rack", "total_height_u": 42}
        response = client.post("/api/racks", json=rack2_data)
        rack2_id = response.json()["id"]

        # Create device
        spec_data = {
            "brand": "Cisco",
            "model": "Catalyst 9200",
            "height_u": 1.0,
            "power_watts": 180.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        device_data = {
            "specification_id": spec_id,
            "custom_name": "Mobile Switch"
        }
        response = client.post("/api/devices", json=device_data)
        device_id = response.json()["id"]

        # Add to rack1
        position_data = {
            "device_id": device_id,
            "start_u": 10
        }
        response = client.post(f"/api/racks/{rack1_id}/positions", json=position_data)
        assert response.status_code == 201
        position1_id = response.json()["id"]

        # Verify in rack1
        response = client.get(f"/api/racks/{rack1_id}/layout")
        assert len(response.json()["positions"]) == 1

        # Remove from rack1
        response = client.delete(f"/api/racks/{rack1_id}/positions/{position1_id}")
        assert response.status_code == 204

        # Verify not in rack1
        response = client.get(f"/api/racks/{rack1_id}/layout")
        assert len(response.json()["positions"]) == 0

        # Add to rack2
        position_data = {
            "device_id": device_id,
            "start_u": 5
        }
        response = client.post(f"/api/racks/{rack2_id}/positions", json=position_data)
        assert response.status_code == 201

        # Verify in rack2
        response = client.get(f"/api/racks/{rack2_id}/layout")
        assert len(response.json()["positions"]) == 1
        assert response.json()["positions"][0]["device_id"] == device_id

        # Verify device still intact
        response = client.get(f"/api/devices/{device_id}")
        assert response.status_code == 200
        assert response.json()["custom_name"] == "Mobile Switch"

    def test_reposition_device_in_same_rack(self, client: TestClient, db_session: Session):
        """
        Test moving a device to a different position in the same rack.

        Workflow:
        1. Create rack with device at U10
        2. Move device to U20
        3. Verify new position and old position is freed
        """
        # Create rack
        rack_data = {"name": "Test Rack", "total_height_u": 42}
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create device
        spec_data = {
            "brand": "Dell",
            "model": "PowerEdge R750",
            "height_u": 2.0,
            "power_watts": 800.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        device_data = {
            "specification_id": spec_id,
            "custom_name": "Database Server"
        }
        response = client.post("/api/devices", json=device_data)
        device_id = response.json()["id"]

        # Add at U10
        position_data = {
            "device_id": device_id,
            "start_u": 10
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201
        position_id = response.json()["id"]

        # Delete old position
        response = client.delete(f"/api/racks/{rack_id}/positions/{position_id}")
        assert response.status_code == 204

        # Add at U20
        position_data = {
            "device_id": device_id,
            "start_u": 20
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201
        new_position = response.json()

        # Verify new position
        assert new_position["start_u"] == 20
        assert new_position["device_id"] == device_id

        # Verify only one position in rack
        response = client.get(f"/api/racks/{rack_id}/layout")
        positions = response.json()["positions"]
        assert len(positions) == 1
        assert positions[0]["start_u"] == 20

    def test_device_with_connections_can_move_racks(self, client: TestClient, db_session: Session):
        """
        Test that device with connections can be moved between racks.
        Connections should remain intact.

        Workflow:
        1. Create two racks
        2. Create two devices, both in rack1
        3. Create connection between them
        4. Move one device to rack2
        5. Verify connection still exists
        """
        # Create racks
        rack1_data = {"name": "Rack 1", "total_height_u": 42}
        response = client.post("/api/racks", json=rack1_data)
        rack1_id = response.json()["id"]

        rack2_data = {"name": "Rack 2", "total_height_u": 42}
        response = client.post("/api/racks", json=rack2_data)
        rack2_id = response.json()["id"]

        # Create two devices
        spec_data = {
            "brand": "Test",
            "model": "Device",
            "height_u": 1.0,
            "power_watts": 100.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        device1_data = {
            "specification_id": spec_id,
            "custom_name": "Device 1"
        }
        response = client.post("/api/devices", json=device1_data)
        device1_id = response.json()["id"]

        device2_data = {
            "specification_id": spec_id,
            "custom_name": "Device 2"
        }
        response = client.post("/api/devices", json=device2_data)
        device2_id = response.json()["id"]

        # Add both to rack1
        for device_id, start_u in [(device1_id, 1), (device2_id, 5)]:
            position_data = {
                "device_id": device_id,
                "start_u": start_u
            }
            response = client.post(f"/api/racks/{rack1_id}/positions", json=position_data)
            assert response.status_code == 201

        # Create connection
        connection_data = {
            "from_device_id": device1_id,
            "to_device_id": device2_id,
            "cable_type": "Cat6"
        }
        response = client.post("/api/connections", json=connection_data)
        assert response.status_code == 201
        connection_id = response.json()["id"]

        # Move device1 to rack2
        # First, get position ID
        response = client.get(f"/api/racks/{rack1_id}/layout")
        positions = response.json()["positions"]
        device1_position_id = next(p["id"] for p in positions if p["device_id"] == device1_id)

        # Remove from rack1
        response = client.delete(f"/api/racks/{rack1_id}/positions/{device1_position_id}")
        assert response.status_code == 204

        # Add to rack2
        position_data = {
            "device_id": device1_id,
            "start_u": 10
        }
        response = client.post(f"/api/racks/{rack2_id}/positions", json=position_data)
        assert response.status_code == 201

        # Verify connection still exists
        response = client.get(f"/api/connections/{connection_id}")
        assert response.status_code == 200
        connection = response.json()
        assert connection["from_device_id"] == device1_id
        assert connection["to_device_id"] == device2_id


class TestBulkOperations:
    """Test bulk operations across endpoints."""

    def test_bulk_device_creation_and_placement(self, client: TestClient, db_session: Session):
        """
        Test creating multiple devices and placing them in a rack.

        Workflow:
        1. Create specification
        2. Create multiple devices from same spec
        3. Create rack
        4. Add all devices to rack
        5. Verify rack layout
        """
        # Create specification
        spec_data = {
            "brand": "HPE",
            "model": "ProLiant DL360",
            "height_u": 1.0,
            "power_watts": 500.0,
            "heat_output_btu": 1706.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        # Create rack
        rack_data = {"name": "Compute Rack", "total_height_u": 42}
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create 10 devices
        device_ids = []
        for i in range(10):
            device_data = {
                "specification_id": spec_id,
                "custom_name": f"Compute-{i+1:02d}",
                "access_frequency": "low"
            }
            response = client.post("/api/devices", json=device_data)
            assert response.status_code == 201
            device_ids.append(response.json()["id"])

        # Add all devices to rack
        current_u = 1
        for device_id in device_ids:
            position_data = {
                "device_id": device_id,
                "start_u": current_u
            }
            response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
            assert response.status_code == 201
            current_u += 2  # Leave 1U spacing

        # Verify rack layout
        response = client.get(f"/api/racks/{rack_id}/layout")
        layout = response.json()
        assert len(layout["positions"]) == 10
        assert layout["total_power_watts"] == 5000.0  # 10 * 500W

    def test_bulk_connection_creation(self, client: TestClient, db_session: Session):
        """
        Test creating multiple connections in a star topology.

        Workflow:
        1. Create switch and multiple servers
        2. Connect all servers to switch
        3. Verify all connections
        """
        # Create switch spec
        switch_spec_data = {
            "brand": "Cisco",
            "model": "Nexus 9300",
            "height_u": 1.0,
            "power_watts": 300.0
        }
        response = client.post("/api/device-specs", json=switch_spec_data)
        switch_spec_id = response.json()["id"]

        # Create server spec
        server_spec_data = {
            "brand": "Dell",
            "model": "PowerEdge R650",
            "height_u": 1.0,
            "power_watts": 600.0
        }
        response = client.post("/api/device-specs", json=server_spec_data)
        server_spec_id = response.json()["id"]

        # Create switch
        switch_data = {
            "specification_id": switch_spec_id,
            "custom_name": "Core Switch"
        }
        response = client.post("/api/devices", json=switch_data)
        switch_id = response.json()["id"]

        # Create 5 servers
        server_ids = []
        for i in range(5):
            server_data = {
                "specification_id": server_spec_id,
                "custom_name": f"Server-{i+1}"
            }
            response = client.post("/api/devices", json=server_data)
            server_ids.append(response.json()["id"])

        # Connect all servers to switch
        connection_ids = []
        for i, server_id in enumerate(server_ids):
            connection_data = {
                "from_device_id": switch_id,
                "to_device_id": server_id,
                "from_port": f"Gi1/0/{i+1}",
                "to_port": "eth0",
                "cable_type": "Cat6"
            }
            response = client.post("/api/connections", json=connection_data)
            assert response.status_code == 201
            connection_ids.append(response.json()["id"])

        # Verify all connections exist
        assert len(connection_ids) == 5
        for connection_id in connection_ids:
            response = client.get(f"/api/connections/{connection_id}")
            assert response.status_code == 200


class TestDataConsistencyAcrossEndpoints:
    """Test data consistency when updates propagate across endpoints."""

    def test_specification_update_reflects_in_devices(self, client: TestClient, db_session: Session):
        """
        Test that updating a specification reflects in all devices using it.

        Workflow:
        1. Create specification
        2. Create multiple devices from spec
        3. Update specification power consumption
        4. Verify devices show updated power
        """
        # Create specification
        spec_data = {
            "brand": "APC",
            "model": "Smart-UPS 3000",
            "height_u": 2.0,
            "power_watts": 100.0,
            "heat_output_btu": 341.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        # Create devices
        device_ids = []
        for i in range(3):
            device_data = {
                "specification_id": spec_id,
                "custom_name": f"UPS-{i+1}"
            }
            response = client.post("/api/devices", json=device_data)
            device_ids.append(response.json()["id"])

        # Update specification
        update_data = {
            "power_watts": 150.0,
            "heat_output_btu": 512.0
        }
        response = client.patch(f"/api/device-specs/{spec_id}", json=update_data)
        assert response.status_code == 200

        # Verify all devices reflect update
        for device_id in device_ids:
            response = client.get(f"/api/devices/{device_id}")
            device = response.json()
            assert device["specification"]["power_watts"] == 150.0
            assert device["specification"]["heat_output_btu"] == 512.0

    def test_rack_updates_affect_thermal_analysis(self, client: TestClient, db_session: Session):
        """
        Test that rack cooling capacity updates affect thermal analysis.

        Workflow:
        1. Create rack with devices
        2. Run thermal analysis
        3. Update rack cooling capacity
        4. Run thermal analysis again
        5. Verify analysis reflects new capacity
        """
        # Create rack
        rack_data = {
            "name": "Test Rack",
            "total_height_u": 42,
            "cooling_capacity_btu": 10000.0
        }
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create high-heat device
        spec_data = {
            "brand": "Test",
            "model": "Hot Server",
            "height_u": 2.0,
            "power_watts": 1000.0,
            "heat_output_btu": 3412.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        device_data = {
            "specification_id": spec_id,
            "custom_name": "Hot Device"
        }
        response = client.post("/api/devices", json=device_data)
        device_id = response.json()["id"]

        # Add to rack
        position_data = {
            "device_id": device_id,
            "start_u": 20
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Run thermal analysis
        response = client.get(f"/api/racks/{rack_id}/thermal-analysis")
        assert response.status_code == 200
        thermal1 = response.json()
        original_capacity = thermal1["cooling_efficiency"]["cooling_capacity_btu_hr"]
        assert original_capacity == 10000.0

        # Update rack cooling capacity
        update_data = {
            "cooling_capacity_btu": 20000.0
        }
        response = client.patch(f"/api/racks/{rack_id}", json=update_data)
        assert response.status_code == 200

        # Run thermal analysis again
        response = client.get(f"/api/racks/{rack_id}/thermal-analysis")
        assert response.status_code == 200
        thermal2 = response.json()
        new_capacity = thermal2["cooling_efficiency"]["cooling_capacity_btu_hr"]
        assert new_capacity == 20000.0
        assert new_capacity > original_capacity

    def test_device_position_affects_rack_metrics(self, client: TestClient, db_session: Session):
        """
        Test that device positioning affects rack utilization and power metrics.

        Workflow:
        1. Create empty rack, check metrics
        2. Add device, verify metrics update
        3. Add another device, verify cumulative metrics
        4. Remove device, verify metrics decrease
        """
        # Create rack
        rack_data = {"name": "Metrics Rack", "total_height_u": 42}
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Check initial metrics
        response = client.get(f"/api/racks/{rack_id}/layout")
        layout = response.json()
        assert layout["utilization_percent"] == 0
        assert layout["total_power_watts"] == 0

        # Create and add first device (2U, 500W)
        spec1_data = {
            "brand": "Device1",
            "model": "Model1",
            "height_u": 2.0,
            "power_watts": 500.0,
            "weight_kg": 10.0
        }
        response = client.post("/api/device-specs", json=spec1_data)
        spec1_id = response.json()["id"]

        device1_data = {
            "specification_id": spec1_id,
            "custom_name": "Device 1"
        }
        response = client.post("/api/devices", json=device1_data)
        device1_id = response.json()["id"]

        position1_data = {
            "device_id": device1_id,
            "start_u": 1
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position1_data)
        position1_id = response.json()["id"]

        # Check metrics after first device
        response = client.get(f"/api/racks/{rack_id}/layout")
        layout = response.json()
        assert layout["utilization_percent"] == pytest.approx(4.76, abs=0.1)  # 2U / 42U * 100
        assert layout["total_power_watts"] == 500.0
        assert layout["total_weight_kg"] == 10.0

        # Create and add second device (1U, 300W)
        spec2_data = {
            "brand": "Device2",
            "model": "Model2",
            "height_u": 1.0,
            "power_watts": 300.0,
            "weight_kg": 5.0
        }
        response = client.post("/api/device-specs", json=spec2_data)
        spec2_id = response.json()["id"]

        device2_data = {
            "specification_id": spec2_id,
            "custom_name": "Device 2"
        }
        response = client.post("/api/devices", json=device2_data)
        device2_id = response.json()["id"]

        position2_data = {
            "device_id": device2_id,
            "start_u": 5
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position2_data)
        position2_id = response.json()["id"]

        # Check cumulative metrics
        response = client.get(f"/api/racks/{rack_id}/layout")
        layout = response.json()
        assert layout["utilization_percent"] == pytest.approx(7.14, abs=0.1)  # 3U / 42U * 100
        assert layout["total_power_watts"] == 800.0  # 500 + 300
        assert layout["total_weight_kg"] == 15.0  # 10 + 5

        # Remove first device
        response = client.delete(f"/api/racks/{rack_id}/positions/{position1_id}")
        assert response.status_code == 204

        # Check metrics after removal
        response = client.get(f"/api/racks/{rack_id}/layout")
        layout = response.json()
        assert layout["utilization_percent"] == pytest.approx(2.38, abs=0.1)  # 1U / 42U * 100
        assert layout["total_power_watts"] == 300.0
        assert layout["total_weight_kg"] == 5.0
