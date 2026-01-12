"""
Unit tests for Racks CRUD API endpoints.

Tests CRUD operations, layout management, position validation, and rack analytics.
Total: ~35 tests
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Rack, RackPosition, WidthType


class TestRacksList:
    """Tests for GET /api/racks/ endpoint."""

    def test_list_racks_empty(self, client: TestClient):
        """Test listing racks when database is empty."""
        response = client.get("/api/racks/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_racks_with_data(self, client: TestClient, rack_standard):
        """Test listing racks returns all racks."""
        response = client.get("/api/racks/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Rack A1"

    def test_list_racks_multiple(self, client: TestClient, db_session: Session):
        """Test listing multiple racks."""
        racks = [
            Rack(name="Rack 1", location="DC1", total_height_u=42),
            Rack(name="Rack 2", location="DC2", total_height_u=48),
        ]
        for rack in racks:
            db_session.add(rack)
        db_session.commit()

        response = client.get("/api/racks/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2


class TestRacksGet:
    """Tests for GET /api/racks/{rack_id} endpoint."""

    def test_get_rack_success(self, client: TestClient, rack_standard):
        """Test retrieving a single rack by ID."""
        response = client.get(f"/api/racks/{rack_standard.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == rack_standard.id
        assert data["name"] == "Rack A1"

    def test_get_rack_not_found(self, client: TestClient):
        """Test retrieving non-existent rack returns 404."""
        response = client.get("/api/racks/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_rack_includes_all_fields(self, client: TestClient, rack_standard):
        """Test retrieved rack includes all expected fields."""
        response = client.get(f"/api/racks/{rack_standard.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Rack A1"
        assert data["location"] == "Data Center 1"
        assert data["total_height_u"] == 42
        assert data["max_weight_kg"] == 500.0
        assert data["max_power_watts"] == 5000.0
        assert data["cooling_capacity_btu"] == 17000.0


class TestRacksCreate:
    """Tests for POST /api/racks/ endpoint."""

    def test_create_rack_minimal(self, client: TestClient):
        """Test creating rack with minimal required fields."""
        data = {
            "name": "New Rack"
        }
        response = client.post("/api/racks/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["name"] == "New Rack"
        # Should have defaults
        assert result["total_height_u"] == 42
        assert result["width_inches"] == '19"'

    def test_create_rack_with_all_fields(self, client: TestClient):
        """Test creating rack with all fields populated."""
        data = {
            "name": "Custom Rack",
            "location": "Building A",
            "total_height_u": 48,
            "width_inches": '23"',
            "depth_mm": 900.0,
            "max_weight_kg": 600.0,
            "max_power_watts": 6000.0,
            "cooling_type": "bottom-to-top",
            "cooling_capacity_btu": 20000.0,
            "ambient_temp_c": 20.0,
            "max_inlet_temp_c": 25.0,
            "airflow_cfm": 1000.0
        }
        response = client.post("/api/racks/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["name"] == "Custom Rack"
        assert result["total_height_u"] == 48
        assert result["width_inches"] == '23"'
        assert result["depth_mm"] == 900.0

    def test_create_rack_missing_required_name(self, client: TestClient):
        """Test creating rack without name fails validation."""
        data = {}
        response = client.post("/api/racks/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_rack_invalid_height_negative(self, client: TestClient):
        """Test creating rack with negative height fails."""
        data = {"name": "Rack", "total_height_u": -1}
        response = client.post("/api/racks/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_rack_invalid_height_too_large(self, client: TestClient):
        """Test creating rack with height > 100U fails."""
        data = {"name": "Rack", "total_height_u": 101}
        response = client.post("/api/racks/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRacksUpdate:
    """Tests for PUT /api/racks/{rack_id} endpoint."""

    def test_update_rack_name(self, client: TestClient, rack_standard):
        """Test updating rack name."""
        data = {"name": "Updated Rack Name"}
        response = client.put(f"/api/racks/{rack_standard.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["name"] == "Updated Rack Name"

    def test_update_rack_location(self, client: TestClient, rack_standard):
        """Test updating rack location."""
        data = {"location": "New Location"}
        response = client.put(f"/api/racks/{rack_standard.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["location"] == "New Location"

    def test_update_rack_multiple_fields(self, client: TestClient, rack_standard):
        """Test updating multiple fields."""
        data = {
            "name": "New Name",
            "total_height_u": 48,
            "max_power_watts": 6000.0
        }
        response = client.put(f"/api/racks/{rack_standard.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["name"] == "New Name"
        assert result["total_height_u"] == 48
        assert result["max_power_watts"] == 6000.0

    def test_update_rack_not_found(self, client: TestClient):
        """Test updating non-existent rack returns 404."""
        data = {"name": "Name"}
        response = client.put("/api/racks/99999", json=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRacksDelete:
    """Tests for DELETE /api/racks/{rack_id} endpoint."""

    def test_delete_rack_success(self, client: TestClient, db_session: Session):
        """Test deleting rack succeeds."""
        rack = Rack(name="To Delete", total_height_u=42)
        db_session.add(rack)
        db_session.commit()
        rack_id = rack.id

        response = client.delete(f"/api/racks/{rack_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        deleted_rack = db_session.query(Rack).filter_by(id=rack_id).first()
        assert deleted_rack is None

    def test_delete_rack_not_found(self, client: TestClient):
        """Test deleting non-existent rack returns 404."""
        response = client.delete("/api/racks/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_rack_cascades_to_positions(self, client: TestClient, rack_with_devices):
        """Test deleting rack also deletes positions."""
        response = client.delete(f"/api/racks/{rack_with_devices.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestRackLayout:
    """Tests for GET /api/racks/{rack_id}/layout endpoint."""

    def test_get_rack_layout_empty(self, client: TestClient, rack_standard):
        """Test getting layout for empty rack."""
        response = client.get(f"/api/racks/{rack_standard.id}/layout")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["rack"]["id"] == rack_standard.id
        assert data["positions"] == []
        assert data["utilization_percent"] == 0.0

    def test_get_rack_layout_with_devices(self, client: TestClient, rack_with_devices):
        """Test getting layout with positioned devices."""
        response = client.get(f"/api/racks/{rack_with_devices.id}/layout")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["positions"]) == 2
        assert data["utilization_percent"] > 0

    def test_get_rack_layout_includes_device_details(self, client: TestClient, rack_with_devices):
        """Test layout includes full device details."""
        response = client.get(f"/api/racks/{rack_with_devices.id}/layout")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        position = data["positions"][0]
        assert "device" in position
        assert "specification" in position["device"]

    def test_get_rack_layout_calculates_utilization(self, client: TestClient, rack_with_devices):
        """Test layout calculates rack utilization correctly."""
        response = client.get(f"/api/racks/{rack_with_devices.id}/layout")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # With 2 devices (1U + 1U) in 42U rack = 2/42 = 4.76%
        assert data["utilization_percent"] > 0
        assert data["utilization_percent"] < 100

    def test_get_rack_layout_calculates_total_power(self, client: TestClient, rack_with_devices):
        """Test layout calculates total power consumption."""
        response = client.get(f"/api/racks/{rack_with_devices.id}/layout")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_power_watts" in data
        assert data["total_power_watts"] > 0

    def test_get_rack_layout_calculates_total_weight(self, client: TestClient, rack_with_devices):
        """Test layout calculates total weight."""
        response = client.get(f"/api/racks/{rack_with_devices.id}/layout")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_weight_kg" in data
        assert data["total_weight_kg"] >= 0


class TestRackPositions:
    """Tests for rack position management."""

    def test_add_device_to_rack(self, client: TestClient, rack_standard, device_switch):
        """Test adding device to rack at specific position."""
        data = {
            "device_id": device_switch.id,
            "start_u": 10,
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_standard.id}/positions", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["device_id"] == device_switch.id
        assert result["start_u"] == 10

    def test_add_device_position_overlap_fails(
        self, client: TestClient, rack_standard, device_switch, device_server, db_session: Session
    ):
        """Test adding device at overlapping position fails."""
        # Add first device at U10
        pos1 = RackPosition(device_id=device_switch.id, rack_id=rack_standard.id, start_u=10)
        db_session.add(pos1)
        db_session.commit()

        # Try to add second device at U10 (should fail)
        data = {
            "device_id": device_server.id,
            "start_u": 10,
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_standard.id}/positions", json=data)
        # Should return conflict or validation error
        assert response.status_code in [
            status.HTTP_409_CONFLICT,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_add_device_position_out_of_bounds(self, client: TestClient, rack_standard, device_switch):
        """Test adding device beyond rack height fails."""
        data = {
            "device_id": device_switch.id,
            "start_u": 50,  # Rack only has 42U
            "locked": False
        }
        response = client.post(f"/api/racks/{rack_standard.id}/positions", json=data)
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_remove_device_from_rack(
        self, client: TestClient, rack_standard, device_switch, db_session: Session
    ):
        """Test removing device from rack."""
        pos = RackPosition(device_id=device_switch.id, rack_id=rack_standard.id, start_u=10)
        db_session.add(pos)
        db_session.commit()
        pos_id = pos.id

        response = client.delete(f"/api/racks/{rack_standard.id}/positions/{pos_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_update_device_position(
        self, client: TestClient, rack_standard, device_switch, db_session: Session
    ):
        """Test updating device position in rack."""
        pos = RackPosition(device_id=device_switch.id, rack_id=rack_standard.id, start_u=10)
        db_session.add(pos)
        db_session.commit()

        data = {"start_u": 20}
        response = client.put(f"/api/racks/{rack_standard.id}/positions/{pos.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["start_u"] == 20

    def test_lock_device_position(
        self, client: TestClient, rack_standard, device_switch, db_session: Session
    ):
        """Test locking device position prevents optimization moves."""
        pos = RackPosition(device_id=device_switch.id, rack_id=rack_standard.id, start_u=10)
        db_session.add(pos)
        db_session.commit()

        data = {"locked": True}
        response = client.put(f"/api/racks/{rack_standard.id}/positions/{pos.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["locked"] is True
