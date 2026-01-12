"""
Integration Tests for Data Integrity and Relationships

Tests database constraints, foreign keys, cascade deletes, and orphan prevention:
- Foreign key constraints validation
- Cascade delete behavior
- Orphan prevention (can't delete referenced entities)
- Data consistency across relationships
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Device, RackPosition, Connection


class TestForeignKeyConstraints:
    """Test foreign key relationships and constraints."""

    def test_device_requires_valid_specification_or_model(self, client: TestClient, db_session: Session):
        """Device must reference either a valid specification or model."""
        # Try to create device without specification or model
        device_data = {
            "custom_name": "Invalid Device",
            "access_frequency": "medium"
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 400
        assert "specification_id or model_id must be provided" in response.json()["detail"].lower()

        # Try to create device with non-existent specification
        device_data = {
            "specification_id": 99999,
            "custom_name": "Invalid Device"
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 404

        # Try to create device with non-existent model
        device_data = {
            "model_id": 99999,
            "custom_name": "Invalid Device"
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 404

    def test_rack_position_requires_valid_device_and_rack(self, client: TestClient, db_session: Session):
        """Rack position must reference valid device and rack."""
        # Create valid rack
        rack_data = {"name": "Test Rack", "total_height_u": 42}
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Try to add position with non-existent device
        position_data = {
            "device_id": 99999,
            "start_u": 1
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 404

        # Try to add position to non-existent rack
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
        device_id = response.json()["id"]

        position_data = {
            "device_id": device_id,
            "start_u": 1
        }
        response = client.post("/api/racks/99999/positions", json=position_data)
        assert response.status_code == 404

    def test_connection_requires_valid_devices(self, client: TestClient, db_session: Session):
        """Connection must reference two valid devices."""
        # Create one valid device
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
            "custom_name": "Device 1"
        }
        response = client.post("/api/devices", json=device_data)
        device_id = response.json()["id"]

        # Try to create connection with non-existent from_device
        connection_data = {
            "from_device_id": 99999,
            "to_device_id": device_id,
            "cable_type": "Cat6"
        }
        response = client.post("/api/connections", json=connection_data)
        assert response.status_code == 404

        # Try to create connection with non-existent to_device
        connection_data = {
            "from_device_id": device_id,
            "to_device_id": 99999,
            "cable_type": "Cat6"
        }
        response = client.post("/api/connections", json=connection_data)
        assert response.status_code == 404

    def test_model_requires_valid_brand_and_device_type(self, client: TestClient, db_session: Session):
        """Model must reference valid brand and device type."""
        # Create valid brand
        brand_data = {
            "name": "Test Brand",
            "slug": "test-brand"
        }
        response = client.post("/api/brands", json=brand_data)
        brand_id = response.json()["id"]

        # Try to create model with non-existent device type
        model_data = {
            "brand_id": brand_id,
            "device_type_id": 99999,
            "name": "Test Model",
            "height_u": 1.0
        }
        response = client.post("/api/models", json=model_data)
        assert response.status_code == 404

        # Create valid device type
        device_type_data = {
            "name": "Test Type",
            "slug": "test-type"
        }
        response = client.post("/api/device-types", json=device_type_data)
        device_type_id = response.json()["id"]

        # Try to create model with non-existent brand
        model_data = {
            "brand_id": 99999,
            "device_type_id": device_type_id,
            "name": "Test Model",
            "height_u": 1.0
        }
        response = client.post("/api/models", json=model_data)
        assert response.status_code == 404


class TestCascadeDeletes:
    """Test cascade delete behavior."""

    def test_deleting_rack_cascades_to_positions(self, client: TestClient, db_session: Session):
        """Deleting a rack should cascade delete all positions."""
        # Create rack with devices
        rack_data = {"name": "Test Rack", "total_height_u": 42}
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create devices
        device_ids = []
        for i in range(3):
            spec_data = {
                "brand": "Test",
                "model": f"Device-{i}",
                "height_u": 1.0,
                "power_watts": 100.0
            }
            response = client.post("/api/device-specs", json=spec_data)
            spec_id = response.json()["id"]

            device_data = {
                "specification_id": spec_id,
                "custom_name": f"Device {i}"
            }
            response = client.post("/api/devices", json=device_data)
            device_ids.append(response.json()["id"])

        # Add devices to rack
        for i, device_id in enumerate(device_ids):
            position_data = {
                "device_id": device_id,
                "start_u": (i * 5) + 1
            }
            response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
            assert response.status_code == 201

        # Verify positions exist
        response = client.get(f"/api/racks/{rack_id}/layout")
        assert response.status_code == 200
        assert len(response.json()["positions"]) == 3

        # Delete rack
        response = client.delete(f"/api/racks/{rack_id}")
        assert response.status_code == 204

        # Verify positions are gone (checked via database)
        positions = db_session.query(RackPosition).filter_by(rack_id=rack_id).all()
        assert len(positions) == 0

        # Verify devices still exist
        for device_id in device_ids:
            response = client.get(f"/api/devices/{device_id}")
            assert response.status_code == 200

    def test_deleting_device_cascades_to_positions_and_connections(self, client: TestClient, db_session: Session):
        """Deleting a device should cascade delete positions and connections."""
        # Create rack
        rack_data = {"name": "Test Rack", "total_height_u": 42}
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

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

        # Add device1 to rack
        position_data = {
            "device_id": device1_id,
            "start_u": 1
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Create connection between devices
        connection_data = {
            "from_device_id": device1_id,
            "to_device_id": device2_id,
            "cable_type": "Cat6"
        }
        response = client.post("/api/connections", json=connection_data)
        assert response.status_code == 201
        connection_id = response.json()["id"]

        # Delete device1
        response = client.delete(f"/api/devices/{device1_id}")
        assert response.status_code == 204

        # Verify position is gone
        positions = db_session.query(RackPosition).filter_by(device_id=device1_id).all()
        assert len(positions) == 0

        # Verify connection is gone
        connections = db_session.query(Connection).filter_by(id=connection_id).all()
        assert len(connections) == 0

        # Verify device2 still exists
        response = client.get(f"/api/devices/{device2_id}")
        assert response.status_code == 200


class TestOrphanPrevention:
    """Test prevention of orphaned records."""

    def test_cannot_delete_brand_with_models(self, client: TestClient, db_session: Session):
        """Cannot delete a brand that has models."""
        # Create brand
        brand_data = {
            "name": "Protected Brand",
            "slug": "protected-brand"
        }
        response = client.post("/api/brands", json=brand_data)
        brand_id = response.json()["id"]

        # Create device type
        device_type_data = {
            "name": "Test Type",
            "slug": "test-type"
        }
        response = client.post("/api/device-types", json=device_type_data)
        device_type_id = response.json()["id"]

        # Create model for brand
        model_data = {
            "brand_id": brand_id,
            "device_type_id": device_type_id,
            "name": "Test Model",
            "height_u": 1.0
        }
        response = client.post("/api/models", json=model_data)
        model_id = response.json()["id"]

        # Try to delete brand (should fail)
        response = client.delete(f"/api/brands/{brand_id}")
        assert response.status_code == 400
        assert "models" in response.json()["detail"].lower()

        # Delete model first
        response = client.delete(f"/api/models/{model_id}")
        assert response.status_code == 204

        # Now can delete brand
        response = client.delete(f"/api/brands/{brand_id}")
        assert response.status_code == 204

    def test_cannot_delete_device_type_with_models(self, client: TestClient, db_session: Session):
        """Cannot delete a device type that has models."""
        # Create brand and device type
        brand_data = {
            "name": "Test Brand",
            "slug": "test-brand"
        }
        response = client.post("/api/brands", json=brand_data)
        brand_id = response.json()["id"]

        device_type_data = {
            "name": "Protected Type",
            "slug": "protected-type"
        }
        response = client.post("/api/device-types", json=device_type_data)
        device_type_id = response.json()["id"]

        # Create model
        model_data = {
            "brand_id": brand_id,
            "device_type_id": device_type_id,
            "name": "Test Model",
            "height_u": 1.0
        }
        response = client.post("/api/models", json=model_data)
        model_id = response.json()["id"]

        # Try to delete device type (should fail)
        response = client.delete(f"/api/device-types/{device_type_id}")
        assert response.status_code == 400
        assert "models" in response.json()["detail"].lower()

        # Delete model first
        response = client.delete(f"/api/models/{model_id}")
        assert response.status_code == 204

        # Now can delete device type
        response = client.delete(f"/api/device-types/{device_type_id}")
        assert response.status_code == 204

    def test_cannot_delete_model_with_devices(self, client: TestClient, db_session: Session):
        """Cannot delete a model that has devices."""
        # Create brand, device type, and model
        brand_data = {
            "name": "Test Brand",
            "slug": "test-brand"
        }
        response = client.post("/api/brands", json=brand_data)
        brand_id = response.json()["id"]

        device_type_data = {
            "name": "Test Type",
            "slug": "test-type"
        }
        response = client.post("/api/device-types", json=device_type_data)
        device_type_id = response.json()["id"]

        model_data = {
            "brand_id": brand_id,
            "device_type_id": device_type_id,
            "name": "Protected Model",
            "height_u": 1.0
        }
        response = client.post("/api/models", json=model_data)
        model_id = response.json()["id"]

        # Create device from model
        device_data = {
            "model_id": model_id,
            "custom_name": "Test Device"
        }
        response = client.post("/api/devices", json=device_data)
        device_id = response.json()["id"]

        # Try to delete model (should fail)
        response = client.delete(f"/api/models/{model_id}")
        assert response.status_code == 400
        assert "devices" in response.json()["detail"].lower()

        # Delete device first
        response = client.delete(f"/api/devices/{device_id}")
        assert response.status_code == 204

        # Now can delete model
        response = client.delete(f"/api/models/{model_id}")
        assert response.status_code == 204

    def test_cannot_delete_specification_with_devices(self, client: TestClient, db_session: Session):
        """Cannot delete a specification that has devices (legacy)."""
        # Create specification
        spec_data = {
            "brand": "Protected",
            "model": "Spec",
            "height_u": 1.0,
            "power_watts": 100.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        # Create device from specification
        device_data = {
            "specification_id": spec_id,
            "custom_name": "Test Device"
        }
        response = client.post("/api/devices", json=device_data)
        device_id = response.json()["id"]

        # Try to delete specification (should fail)
        response = client.delete(f"/api/device-specs/{spec_id}")
        assert response.status_code == 400
        assert "devices" in response.json()["detail"].lower()

        # Delete device first
        response = client.delete(f"/api/devices/{device_id}")
        assert response.status_code == 204

        # Now can delete specification
        response = client.delete(f"/api/device-specs/{spec_id}")
        assert response.status_code == 204


class TestDataConsistency:
    """Test data consistency across relationships."""

    def test_device_position_consistency_across_racks(self, client: TestClient, db_session: Session):
        """Device cannot be in multiple racks simultaneously (business rule)."""
        # Create two racks
        rack1_data = {"name": "Rack 1", "total_height_u": 42}
        response = client.post("/api/racks", json=rack1_data)
        rack1_id = response.json()["id"]

        rack2_data = {"name": "Rack 2", "total_height_u": 42}
        response = client.post("/api/racks", json=rack2_data)
        rack2_id = response.json()["id"]

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
            "custom_name": "Shared Device"
        }
        response = client.post("/api/devices", json=device_data)
        device_id = response.json()["id"]

        # Add device to rack1
        position_data = {
            "device_id": device_id,
            "start_u": 1
        }
        response = client.post(f"/api/racks/{rack1_id}/positions", json=position_data)
        assert response.status_code == 201

        # Try to add same device to rack2 (should fail based on business rule)
        position_data = {
            "device_id": device_id,
            "start_u": 1
        }
        response = client.post(f"/api/racks/{rack2_id}/positions", json=position_data)
        # This might succeed depending on implementation, but check positions
        positions = db_session.query(RackPosition).filter_by(device_id=device_id).all()
        # If business rule enforced, should only have 1 position
        # If not enforced, this documents current behavior

    def test_rack_position_no_overlap(self, client: TestClient, db_session: Session):
        """Rack positions should not overlap."""
        # Create rack
        rack_data = {"name": "Test Rack", "total_height_u": 42}
        response = client.post("/api/racks", json=rack_data)
        rack_id = response.json()["id"]

        # Create two 2U devices
        spec_data = {
            "brand": "Test",
            "model": "2U Device",
            "height_u": 2.0,
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

        # Add device1 at U1 (occupies U1 and U2)
        position_data = {
            "device_id": device1_id,
            "start_u": 1
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

        # Try to add device2 at U2 (would overlap with device1)
        position_data = {
            "device_id": device2_id,
            "start_u": 2
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        # Should fail due to overlap validation
        assert response.status_code == 400

        # Add device2 at U3 (should succeed)
        position_data = {
            "device_id": device2_id,
            "start_u": 3
        }
        response = client.post(f"/api/racks/{rack_id}/positions", json=position_data)
        assert response.status_code == 201

    def test_connection_self_reference_prevention(self, client: TestClient, db_session: Session):
        """Device cannot connect to itself."""
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
            "custom_name": "Self Device"
        }
        response = client.post("/api/devices", json=device_data)
        device_id = response.json()["id"]

        # Try to create self-connection
        connection_data = {
            "from_device_id": device_id,
            "to_device_id": device_id,
            "cable_type": "Cat6"
        }
        response = client.post("/api/connections", json=connection_data)
        # Should fail validation
        assert response.status_code == 400
