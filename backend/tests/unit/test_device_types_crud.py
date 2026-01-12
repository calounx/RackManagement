"""
Unit tests for Device Types CRUD API endpoints.

Tests CRUD operations and validation.
Total: ~12 tests
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import DeviceType


class TestDeviceTypesList:
    """Tests for GET /api/device-types/ endpoint."""

    def test_list_device_types_empty(self, client: TestClient):
        """Test listing device types when database is empty."""
        response = client.get("/api/device-types/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []

    def test_list_device_types_with_data(
        self, client: TestClient, device_type_switch
    ):
        """Test listing device types returns all types."""
        response = client.get("/api/device-types/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Switch"


class TestDeviceTypesGet:
    """Tests for GET /api/device-types/{type_id} endpoint."""

    def test_get_device_type_success(
        self, client: TestClient, device_type_switch
    ):
        """Test retrieving a single device type by ID."""
        response = client.get(f"/api/device-types/{device_type_switch.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == device_type_switch.id
        assert data["name"] == "Switch"
        assert data["slug"] == "switch"

    def test_get_device_type_not_found(self, client: TestClient):
        """Test retrieving non-existent device type returns 404."""
        response = client.get("/api/device-types/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeviceTypesCreate:
    """Tests for POST /api/device-types/ endpoint."""

    def test_create_device_type_minimal(self, client: TestClient):
        """Test creating device type with minimal required fields."""
        data = {
            "name": "Router",
            "slug": "router"
        }
        response = client.post("/api/device-types/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["name"] == "Router"
        assert result["slug"] == "router"

    def test_create_device_type_with_all_fields(self, client: TestClient):
        """Test creating device type with all fields populated."""
        data = {
            "name": "Load Balancer",
            "slug": "load-balancer",
            "icon": "⚖️",
            "description": "Application load balancer",
            "color": "#9C27B0"
        }
        response = client.post("/api/device-types/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["name"] == "Load Balancer"
        assert result["icon"] == "⚖️"
        assert result["color"] == "#9C27B0"

    def test_create_device_type_duplicate_name(
        self, client: TestClient, device_type_switch
    ):
        """Test creating duplicate device type name fails."""
        data = {
            "name": "Switch",
            "slug": "switch-2"
        }
        response = client.post("/api/device-types/", json=data)
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_device_type_duplicate_slug(
        self, client: TestClient, device_type_switch
    ):
        """Test creating duplicate device type slug fails."""
        data = {
            "name": "Network Switch",
            "slug": "switch"
        }
        response = client.post("/api/device-types/", json=data)
        assert response.status_code == status.HTTP_409_CONFLICT


class TestDeviceTypesUpdate:
    """Tests for PUT /api/device-types/{type_id} endpoint."""

    def test_update_device_type_name(
        self, client: TestClient, device_type_switch
    ):
        """Test updating device type name."""
        data = {"name": "Network Switch"}
        response = client.put(f"/api/device-types/{device_type_switch.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["name"] == "Network Switch"

    def test_update_device_type_color(
        self, client: TestClient, device_type_switch
    ):
        """Test updating device type color."""
        data = {"color": "#FF5722"}
        response = client.put(f"/api/device-types/{device_type_switch.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["color"] == "#FF5722"


class TestDeviceTypesDelete:
    """Tests for DELETE /api/device-types/{type_id} endpoint."""

    def test_delete_device_type_success(
        self, client: TestClient, db_session: Session
    ):
        """Test deleting device type succeeds."""
        device_type = DeviceType(
            name="To Delete",
            slug="to-delete"
        )
        db_session.add(device_type)
        db_session.commit()
        type_id = device_type.id

        response = client.delete(f"/api/device-types/{type_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_device_type_not_found(self, client: TestClient):
        """Test deleting non-existent device type returns 404."""
        response = client.delete("/api/device-types/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_device_type_with_models(
        self, client: TestClient, model_catalyst_9300, device_type_switch
    ):
        """Test deleting device type with models may fail."""
        response = client.delete(f"/api/device-types/{device_type_switch.id}")
        # Implementation may prevent deletion or cascade
        assert response.status_code in [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_409_CONFLICT
        ]
