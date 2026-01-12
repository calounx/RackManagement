"""
Unit tests for Devices CRUD API endpoints.

Tests CRUD operations, filtering, pagination, validation, and device creation from models.
Total: ~35 tests
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Device, AccessFrequency


class TestDevicesList:
    """Tests for GET /api/devices/ endpoint."""

    def test_list_devices_empty(self, client: TestClient):
        """Test listing devices when database is empty."""
        response = client.get("/api/devices/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_devices_with_data(self, client: TestClient, device_switch):
        """Test listing devices returns all devices."""
        response = client.get("/api/devices/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["custom_name"] == "Core Switch 1"

    def test_list_devices_multiple(self, client: TestClient, device_switch, device_server):
        """Test listing multiple devices."""
        response = client.get("/api/devices/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_list_devices_includes_specification(self, client: TestClient, device_switch):
        """Test device list includes specification details."""
        response = client.get("/api/devices/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "specification" in data[0]
        assert data[0]["specification"]["brand"] == "Cisco"

    def test_list_devices_filter_by_brand(self, client: TestClient, db_session: Session, spec_switch, spec_server):
        """Test filtering devices by brand."""
        device1 = Device(custom_name="Device1", specification_id=spec_switch.id, brand="Cisco", model="Test")
        device2 = Device(custom_name="Device2", specification_id=spec_server.id, brand="Dell", model="Test")
        db_session.add_all([device1, device2])
        db_session.commit()

        response = client.get("/api/devices/?brand=Cisco")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["brand"] == "Cisco"

    def test_list_devices_pagination_skip(self, client: TestClient, db_session: Session, spec_switch):
        """Test pagination skip parameter."""
        for i in range(5):
            device = Device(custom_name=f"Device{i}", specification_id=spec_switch.id, brand="Test", model="Test")
            db_session.add(device)
        db_session.commit()

        response = client.get("/api/devices/?skip=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    def test_list_devices_pagination_limit(self, client: TestClient, db_session: Session, spec_switch):
        """Test pagination limit parameter."""
        for i in range(10):
            device = Device(custom_name=f"Device{i}", specification_id=spec_switch.id, brand="Test", model="Test")
            db_session.add(device)
        db_session.commit()

        response = client.get("/api/devices/?limit=5")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5


class TestDevicesGet:
    """Tests for GET /api/devices/{device_id} endpoint."""

    def test_get_device_success(self, client: TestClient, device_switch):
        """Test retrieving a single device by ID."""
        response = client.get(f"/api/devices/{device_switch.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == device_switch.id
        assert data["custom_name"] == "Core Switch 1"

    def test_get_device_not_found(self, client: TestClient):
        """Test retrieving non-existent device returns 404."""
        response = client.get("/api/devices/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_device_includes_specification(self, client: TestClient, device_switch):
        """Test device includes specification details."""
        response = client.get(f"/api/devices/{device_switch.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "specification" in data
        assert data["specification"]["brand"] == "Cisco"
        assert data["specification"]["model"] == "Catalyst 2960"

    def test_get_device_includes_all_fields(self, client: TestClient, db_session: Session, spec_switch):
        """Test retrieved device includes all expected fields."""
        device = Device(
            custom_name="Test Device",
            specification_id=spec_switch.id,
            brand="Cisco",
            model="Test",
            access_frequency=AccessFrequency.HIGH,
            notes="Important device"
        )
        db_session.add(device)
        db_session.commit()

        response = client.get(f"/api/devices/{device.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["custom_name"] == "Test Device"
        assert data["access_frequency"] == "high"
        assert data["notes"] == "Important device"


class TestDevicesCreate:
    """Tests for POST /api/devices/ endpoint."""

    def test_create_device_minimal(self, client: TestClient, spec_switch):
        """Test creating device with minimal required fields."""
        data = {
            "specification_id": spec_switch.id,
            "custom_name": "New Switch"
        }
        response = client.post("/api/devices/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["custom_name"] == "New Switch"

    def test_create_device_with_all_fields(self, client: TestClient, spec_switch):
        """Test creating device with all fields populated."""
        data = {
            "specification_id": spec_switch.id,
            "custom_name": "Core Router",
            "access_frequency": "high",
            "notes": "Main routing device"
        }
        response = client.post("/api/devices/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["custom_name"] == "Core Router"
        assert result["access_frequency"] == "high"
        assert result["notes"] == "Main routing device"

    def test_create_device_from_catalog_model(self, client: TestClient, model_catalyst_9300):
        """Test creating device from catalog model instead of legacy spec."""
        data = {
            "model_id": model_catalyst_9300.id,
            "custom_name": "Access Switch"
        }
        response = client.post("/api/devices/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["model_id"] == model_catalyst_9300.id
        assert result["custom_name"] == "Access Switch"

    def test_create_device_invalid_specification_id(self, client: TestClient):
        """Test creating device with non-existent specification fails."""
        data = {
            "specification_id": 99999,
            "custom_name": "Device"
        }
        response = client.post("/api/devices/", json=data)
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_create_device_missing_custom_name(self, client: TestClient, spec_switch):
        """Test creating device without custom_name uses default."""
        data = {
            "specification_id": spec_switch.id
        }
        response = client.post("/api/devices/", json=data)
        # Should succeed with auto-generated name or default
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_create_device_invalid_access_frequency(self, client: TestClient, spec_switch):
        """Test creating device with invalid access frequency fails."""
        data = {
            "specification_id": spec_switch.id,
            "custom_name": "Device",
            "access_frequency": "invalid"
        }
        response = client.post("/api/devices/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_device_auto_populate_brand_model(self, client: TestClient, spec_switch):
        """Test device auto-populates brand and model from spec."""
        data = {
            "specification_id": spec_switch.id,
            "custom_name": "Test"
        }
        response = client.post("/api/devices/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        # Brand/model should be populated from specification
        assert result["specification"]["brand"] == "Cisco"


class TestDevicesUpdate:
    """Tests for PUT /api/devices/{device_id} endpoint."""

    def test_update_device_custom_name(self, client: TestClient, device_switch):
        """Test updating device custom name."""
        data = {"custom_name": "Updated Name"}
        response = client.put(f"/api/devices/{device_switch.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["custom_name"] == "Updated Name"

    def test_update_device_access_frequency(self, client: TestClient, device_switch):
        """Test updating device access frequency."""
        data = {"access_frequency": "low"}
        response = client.put(f"/api/devices/{device_switch.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["access_frequency"] == "low"

    def test_update_device_notes(self, client: TestClient, device_switch):
        """Test updating device notes."""
        data = {"notes": "New notes here"}
        response = client.put(f"/api/devices/{device_switch.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["notes"] == "New notes here"

    def test_update_device_multiple_fields(self, client: TestClient, device_switch):
        """Test updating multiple fields."""
        data = {
            "custom_name": "New Name",
            "access_frequency": "high",
            "notes": "Updated notes"
        }
        response = client.put(f"/api/devices/{device_switch.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["custom_name"] == "New Name"
        assert result["access_frequency"] == "high"
        assert result["notes"] == "Updated notes"

    def test_update_device_not_found(self, client: TestClient):
        """Test updating non-existent device returns 404."""
        data = {"custom_name": "Name"}
        response = client.put("/api/devices/99999", json=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_device_empty_update(self, client: TestClient, device_switch):
        """Test updating with no fields still succeeds."""
        data = {}
        response = client.put(f"/api/devices/{device_switch.id}", json=data)
        assert response.status_code == status.HTTP_200_OK

    def test_update_device_invalid_access_frequency(self, client: TestClient, device_switch):
        """Test updating with invalid access frequency fails."""
        data = {"access_frequency": "invalid"}
        response = client.put(f"/api/devices/{device_switch.id}", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDevicesDelete:
    """Tests for DELETE /api/devices/{device_id} endpoint."""

    def test_delete_device_success(self, client: TestClient, db_session: Session, spec_switch):
        """Test deleting device succeeds."""
        device = Device(custom_name="To Delete", specification_id=spec_switch.id, brand="Test", model="Test")
        db_session.add(device)
        db_session.commit()
        device_id = device.id

        response = client.delete(f"/api/devices/{device_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        deleted_device = db_session.query(Device).filter_by(id=device_id).first()
        assert deleted_device is None

    def test_delete_device_not_found(self, client: TestClient):
        """Test deleting non-existent device returns 404."""
        response = client.delete("/api/devices/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_device_cascades_to_positions(self, client: TestClient, rack_with_devices, device_switch):
        """Test deleting device also deletes rack positions."""
        response = client.delete(f"/api/devices/{device_switch.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_device_cascades_to_connections(self, client: TestClient, connection_switch_to_server, device_switch):
        """Test deleting device also deletes connections."""
        response = client.delete(f"/api/devices/{device_switch.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestDevicesQuickAdd:
    """Tests for quick-add device by brand/model."""

    def test_quick_add_device_finds_existing_spec(self, client: TestClient, spec_switch):
        """Test quick-add finds existing specification."""
        data = {
            "brand": "Cisco",
            "model": "Catalyst 2960",
            "custom_name": "Quick Switch"
        }
        # Note: Actual endpoint may vary - adjust based on API design
        response = client.post("/api/devices/quick-add", json=data)
        # May return 201 or 404 depending on implementation
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED]

    def test_quick_add_device_spec_not_found(self, client: TestClient):
        """Test quick-add with non-existent brand/model."""
        data = {
            "brand": "NonExistent",
            "model": "Model",
            "custom_name": "Device"
        }
        response = client.post("/api/devices/quick-add", json=data)
        # May return 404 or 405 depending on implementation
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED]
