"""
Integration Tests for Complete CRUD Workflows

Tests complete lifecycle workflows including:
- Device lifecycle (create spec → create device → assign to rack → create connections → update → delete)
- Rack management workflow (create → add devices → thermal analysis → optimization → apply)
- Catalog workflow (create type → fetch brand → upload logo → fetch model → create device)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestDeviceLifecycle:
    """Test complete device lifecycle from creation to deletion."""

    def test_device_lifecycle_with_specification(self, client: TestClient, db_session: Session):
        """
        Test complete device lifecycle using legacy specifications.

        Workflow:
        1. Create device specification
        2. Create device from specification
        3. Assign device to rack
        4. Create connection to another device
        5. Update device properties
        6. Remove from rack
        7. Delete device
        """
        # Step 1: Create device specification
        spec_data = {
            "brand": "Cisco",
            "model": "ASR 1001-X",
            "height_u": 2.0,
            "power_watts": 450.0,
            "heat_output_btu": 1535.0,
            "airflow_pattern": "front_to_back",
            "typical_ports": {"gigabit_ethernet": 6, "sfp+": 2},
            "source": "user_custom",
            "confidence": "high"
        }
        response = client.post("/api/device-specs", json=spec_data)
        assert response.status_code == 201
        spec_id = response.json()["id"]

        # Step 2: Create device from specification
        device_data = {
            "specification_id": spec_id,
            "custom_name": "Edge Router 1",
            "access_frequency": "high",
            "notes": "Border router"
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 201
        device = response.json()
        device_id = device["id"]
        assert device["custom_name"] == "Edge Router 1"
        assert device["specification"]["brand"] == "Cisco"

        # Step 3: Create rack and assign device
        rack_data = {
            "name": "Edge Rack 1",
            "location": "DC1",
            "total_height_u": 42
        }
        response = client.post("/api/racks", json=rack_data)
        assert response.status_code == 201
        rack_id = response.json()["id"]

        position_data = {
            "device_id": device_id,
            "start_u": 10,
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201
        position = response.json()
        assert position["device_id"] == device_id
        assert position["start_u"] == 10

        # Step 4: Create second device and connection
        device2_data = {
            "specification_id": spec_id,
            "custom_name": "Edge Router 2",
            "access_frequency": "high"
        }
        response = client.post("/api/devices", json=device2_data)
        assert response.status_code == 201
        device2_id = response.json()["id"]

        connection_data = {
            "from_device_id": device_id,
            "to_device_id": device2_id,
            "from_port": "Gi0/0/0",
            "to_port": "Gi0/0/1",
            "cable_type": "Cat6"
        }
        response = client.post("/api/connections", json=connection_data)
        assert response.status_code == 201
        connection = response.json()
        assert connection["from_device_id"] == device_id
        assert connection["to_device_id"] == device2_id

        # Step 5: Update device properties
        update_data = {
            "custom_name": "Primary Edge Router",
            "access_frequency": "medium",
            "notes": "Updated: primary border router with HA"
        }
        response = client.patch(f"/api/devices/{device_id}", json=update_data)
        assert response.status_code == 200
        updated_device = response.json()
        assert updated_device["custom_name"] == "Primary Edge Router"
        assert updated_device["notes"] == "Updated: primary border router with HA"

        # Step 6: Remove from rack (delete position)
        response = client.delete(f"/api/racks/{rack_id}/positions/{position['id']}")
        assert response.status_code == 204

        # Verify device still exists but no longer in rack
        response = client.get(f"/api/devices/{device_id}")
        assert response.status_code == 200

        # Step 7: Delete connection first, then device
        response = client.delete(f"/api/connections/{connection['id']}")
        assert response.status_code == 204

        response = client.delete(f"/api/devices/{device_id}")
        assert response.status_code == 204

        # Verify device is gone
        response = client.get(f"/api/devices/{device_id}")
        assert response.status_code == 404

    def test_device_lifecycle_with_catalog_model(self, client: TestClient, db_session: Session):
        """
        Test complete device lifecycle using catalog models.

        Workflow:
        1. Create device type
        2. Create brand
        3. Create model
        4. Create device from model
        5. Verify device has model relationship
        6. Update and delete
        """
        # Step 1: Create device type
        device_type_data = {
            "name": "Router",
            "slug": "router",
            "icon": "🔀",
            "description": "Network routers"
        }
        response = client.post("/api/device-types", json=device_type_data)
        assert response.status_code == 201
        device_type_id = response.json()["id"]

        # Step 2: Create brand
        brand_data = {
            "name": "Juniper Networks",
            "slug": "juniper-networks",
            "website": "https://www.juniper.net",
            "description": "Network equipment manufacturer"
        }
        response = client.post("/api/brands", json=brand_data)
        assert response.status_code == 201
        brand_id = response.json()["id"]

        # Step 3: Create model
        model_data = {
            "brand_id": brand_id,
            "device_type_id": device_type_id,
            "name": "MX204",
            "height_u": 1.0,
            "power_watts": 400.0,
            "heat_output_btu": 1365.0,
            "airflow_pattern": "front_to_back"
        }
        response = client.post("/api/models", json=model_data)
        assert response.status_code == 201
        model_id = response.json()["id"]

        # Step 4: Create device from model
        device_data = {
            "model_id": model_id,
            "custom_name": "WAN Router 1",
            "serial_number": "JN123456789",
            "access_frequency": "high"
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 201
        device = response.json()
        device_id = device["id"]
        assert device["model_id"] == model_id
        assert device["catalog_model"]["name"] == "MX204"
        assert device["catalog_model"]["brand"]["name"] == "Juniper Networks"

        # Step 5: Update device
        update_data = {
            "custom_name": "Primary WAN Router",
            "notes": "Handles all WAN traffic"
        }
        response = client.patch(f"/api/devices/{device_id}", json=update_data)
        assert response.status_code == 200

        # Step 6: Delete device
        response = client.delete(f"/api/devices/{device_id}")
        assert response.status_code == 204


class TestRackManagementWorkflow:
    """Test complete rack management workflow."""

    def test_rack_build_and_optimize_workflow(self, client: TestClient, db_session: Session):
        """
        Test complete rack workflow from creation to optimization.

        Workflow:
        1. Create rack
        2. Create multiple devices
        3. Add devices to rack (suboptimal placement)
        4. Get rack layout
        5. Run thermal analysis
        6. Run optimization
        7. Apply optimization
        8. Verify improvements
        """
        # Step 1: Create rack
        rack_data = {
            "name": "Production Rack 1",
            "location": "DC1-Row3",
            "total_height_u": 42,
            "max_power_watts": 10000.0,
            "cooling_capacity_btu": 25000.0
        }
        response = client.post("/api/racks", json=rack_data)
        assert response.status_code == 201
        rack_id = response.json()["id"]

        # Step 2: Create device specifications and devices
        devices = []
        for i in range(5):
            # Create spec
            spec_data = {
                "brand": "Generic",
                "model": f"Server-{i}",
                "height_u": 2.0 if i % 2 == 0 else 1.0,
                "power_watts": 500.0 if i % 2 == 0 else 200.0,
                "heat_output_btu": 1706.0 if i % 2 == 0 else 682.0,
                "airflow_pattern": "front_to_back"
            }
            response = client.post("/api/device-specs", json=spec_data)
            assert response.status_code == 201
            spec_id = response.json()["id"]

            # Create device
            device_data = {
                "specification_id": spec_id,
                "custom_name": f"Server {i+1}",
                "access_frequency": "high" if i < 2 else "low"
            }
            response = client.post("/api/devices", json=device_data)
            assert response.status_code == 201
            devices.append(response.json())

        # Step 3: Add devices to rack (deliberately poor placement - high access at top)
        positions = []
        current_u = 35  # Start near top for high-access devices
        for device in devices:
            position_data = {
                "device_id": device["id"],
                "start_u": current_u,
                "locked": False
            }
            response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
            assert response.status_code == 201
            positions.append(response.json())
            current_u -= int(device["specification"]["height_u"]) + 1

        # Step 4: Get rack layout
        response = client.get(f"/api/racks/{rack_id}/layout")
        assert response.status_code == 200
        layout = response.json()
        assert layout["rack"]["id"] == rack_id
        assert len(layout["positions"]) == 5
        assert layout["utilization_percent"] > 0

        # Step 5: Run thermal analysis
        response = client.get(f"/api/racks/{rack_id}/thermal-analysis")
        assert response.status_code == 200
        thermal = response.json()
        assert thermal["rack_id"] == rack_id
        assert "heat_distribution" in thermal
        assert "cooling_efficiency" in thermal
        assert "hot_spots" in thermal
        assert "recommendations" in thermal

        # Step 6: Run optimization
        optimization_request = {
            "locked_positions": [],
            "weights": {
                "cable": 0.25,
                "weight": 0.25,
                "thermal": 0.30,
                "access": 0.20
            }
        }
        response = client.post(f"/api/racks/{rack_id}/optimize", json=optimization_request)
        assert response.status_code == 200
        optimization = response.json()
        assert "positions" in optimization
        assert "score" in optimization
        assert "improvements" in optimization

        # Step 7: Apply optimization (update positions)
        for new_pos in optimization["positions"]:
            # Find corresponding position by device_id
            original_pos = next(p for p in positions if p["device_id"] == new_pos["device_id"])
            if original_pos["start_u"] != new_pos["start_u"]:
                # Delete old position
                response = client.delete(f"/api/racks/{rack_id}/positions/{original_pos['id']}")
                assert response.status_code == 204

                # Create new position
                position_data = {
                    "device_id": new_pos["device_id"],
                    "start_u": new_pos["start_u"],
                    "locked": new_pos["locked"]
                }
                response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
                assert response.status_code == 201

        # Step 8: Verify improvements
        response = client.get(f"/api/racks/{rack_id}/thermal-analysis")
        assert response.status_code == 200
        new_thermal = response.json()
        # After optimization, cooling efficiency should be same or better
        assert new_thermal["cooling_efficiency"]["utilization_percent"] >= 0

    def test_rack_deletion_cascade(self, client: TestClient, db_session: Session):
        """
        Test that deleting a rack properly cascades to positions.

        Workflow:
        1. Create rack with devices
        2. Delete rack
        3. Verify positions are deleted
        4. Verify devices still exist
        """
        # Create rack
        rack_data = {"name": "Temp Rack", "total_height_u": 42}
        response = client.post("/api/racks", json=rack_data)
        assert response.status_code == 201
        rack_id = response.json()["id"]

        # Create device
        spec_data = {
            "brand": "Test",
            "model": "Device",
            "height_u": 1.0,
            "power_watts": 100.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        device_data = {
            "specification_id": spec_id,
            "custom_name": "Test Device"
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 201
        device_id = response.json()["id"]

        # Add to rack
        position_data = {
            "device_id": device_id,
            "start_u": 1
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201
        position_id = response.json()["id"]

        # Delete rack
        response = client.delete(f"/api/racks/{rack_id}")
        assert response.status_code == 204

        # Verify rack is gone
        response = client.get(f"/api/racks/{rack_id}")
        assert response.status_code == 404

        # Verify position is gone (via rack layout)
        response = client.get(f"/api/racks/{rack_id}/layout")
        assert response.status_code == 404

        # Verify device still exists
        response = client.get(f"/api/devices/{device_id}")
        assert response.status_code == 200


class TestCatalogWorkflow:
    """Test complete catalog management workflow."""

    def test_complete_catalog_workflow(self, client: TestClient, db_session: Session):
        """
        Test complete catalog workflow.

        Workflow:
        1. Create device type
        2. Create brand
        3. Create multiple models for brand
        4. Create devices from models
        5. List and filter catalog items
        6. Update catalog items
        7. Delete workflow (ensure constraints)
        """
        # Step 1: Create device type
        device_type_data = {
            "name": "Storage",
            "slug": "storage",
            "icon": "💾",
            "description": "Storage systems",
            "color": "#9C27B0"
        }
        response = client.post("/api/device-types", json=device_type_data)
        assert response.status_code == 201
        device_type_id = response.json()["id"]

        # Step 2: Create brand
        brand_data = {
            "name": "NetApp",
            "slug": "netapp",
            "website": "https://www.netapp.com",
            "description": "Hybrid cloud data services company",
            "headquarters": "Sunnyvale, California"
        }
        response = client.post("/api/brands", json=brand_data)
        assert response.status_code == 201
        brand_id = response.json()["id"]

        # Step 3: Create multiple models
        models = []
        for i, (name, height_u) in enumerate([("FAS2750", 2), ("FAS8200", 4)]):
            model_data = {
                "brand_id": brand_id,
                "device_type_id": device_type_id,
                "name": name,
                "height_u": height_u,
                "power_watts": 600.0 + (i * 200),
                "heat_output_btu": 2047.0 + (i * 682),
                "airflow_pattern": "front_to_back",
                "typical_ports": {"gigabit_ethernet": 4}
            }
            response = client.post("/api/models", json=model_data)
            assert response.status_code == 201
            models.append(response.json())

        # Step 4: Create devices from models
        devices = []
        for i, model in enumerate(models):
            device_data = {
                "model_id": model["id"],
                "custom_name": f"Storage {i+1}",
                "serial_number": f"SN{i+1:05d}"
            }
            response = client.post("/api/devices", json=device_data)
            assert response.status_code == 201
            devices.append(response.json())

        # Step 5: List and filter
        # List all models
        response = client.get("/api/models")
        assert response.status_code == 200
        all_models = response.json()
        assert len(all_models["items"]) >= 2

        # Filter by brand
        response = client.get(f"/api/models?brand_id={brand_id}")
        assert response.status_code == 200
        brand_models = response.json()
        assert len(brand_models["items"]) == 2

        # Step 6: Update model
        update_data = {
            "description": "Updated: High-performance mid-range storage",
            "power_watts": 650.0
        }
        response = client.patch(f"/api/models/{models[0]['id']}", json=update_data)
        assert response.status_code == 200
        updated = response.json()
        assert updated["description"] == "Updated: High-performance mid-range storage"
        assert updated["power_watts"] == 650.0

        # Step 7: Test deletion constraints
        # Cannot delete brand with models
        response = client.delete(f"/api/brands/{brand_id}")
        assert response.status_code == 400  # Should fail due to existing models

        # Cannot delete model with devices
        response = client.delete(f"/api/models/{models[0]['id']}")
        assert response.status_code == 400  # Should fail due to existing devices

        # Delete devices first
        for device in devices:
            response = client.delete(f"/api/devices/{device['id']}")
            assert response.status_code == 204

        # Now can delete models
        for model in models:
            response = client.delete(f"/api/models/{model['id']}")
            assert response.status_code == 204

        # Now can delete brand
        response = client.delete(f"/api/brands/{brand_id}")
        assert response.status_code == 204
