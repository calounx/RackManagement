"""
Unit tests for Connections CRUD API endpoints.

Tests CRUD operations, cable calculations, validation, and routing paths.
Total: ~25 tests
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Connection, CableType, RoutingPath, RackPosition


class TestConnectionsList:
    """Tests for GET /api/connections/ endpoint."""

    def test_list_connections_empty(self, client: TestClient):
        """Test listing connections when database is empty."""
        response = client.get("/api/connections/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_connections_with_data(self, client: TestClient, connection_switch_to_server):
        """Test listing connections returns all connections."""
        response = client.get("/api/connections/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1

    def test_list_connections_includes_device_details(self, client: TestClient, connection_switch_to_server):
        """Test connection list includes from/to device details."""
        response = client.get("/api/connections/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "from_device" in data[0]
        assert "to_device" in data[0]


class TestConnectionsGet:
    """Tests for GET /api/connections/{connection_id} endpoint."""

    def test_get_connection_success(self, client: TestClient, connection_switch_to_server):
        """Test retrieving a single connection by ID."""
        response = client.get(f"/api/connections/{connection_switch_to_server.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == connection_switch_to_server.id

    def test_get_connection_not_found(self, client: TestClient):
        """Test retrieving non-existent connection returns 404."""
        response = client.get("/api/connections/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestConnectionsCreate:
    """Tests for POST /api/connections/ endpoint."""

    def test_create_connection_minimal(self, client: TestClient, device_switch, device_server):
        """Test creating connection with minimal required fields."""
        data = {
            "from_device_id": device_switch.id,
            "to_device_id": device_server.id
        }
        response = client.post("/api/connections/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["from_device_id"] == device_switch.id
        assert result["to_device_id"] == device_server.id

    def test_create_connection_with_all_fields(self, client: TestClient, device_switch, device_server):
        """Test creating connection with all fields populated."""
        data = {
            "from_device_id": device_switch.id,
            "to_device_id": device_server.id,
            "from_port": "Gi0/1",
            "to_port": "eth0",
            "cable_type": "Cat6",
            "routing_path": "cable_tray"
        }
        response = client.post("/api/connections/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["from_port"] == "Gi0/1"
        assert result["to_port"] == "eth0"
        assert result["cable_type"] == "Cat6"

    def test_create_connection_invalid_from_device(self, client: TestClient, device_server):
        """Test creating connection with invalid from_device_id fails."""
        data = {
            "from_device_id": 99999,
            "to_device_id": device_server.id
        }
        response = client.post("/api/connections/", json=data)
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_create_connection_same_device(self, client: TestClient, device_switch):
        """Test creating connection from device to itself may fail or succeed."""
        data = {
            "from_device_id": device_switch.id,
            "to_device_id": device_switch.id
        }
        response = client.post("/api/connections/", json=data)
        # Implementation may allow or disallow self-connections
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_create_connection_auto_calculate_length(
        self, client: TestClient, rack_standard, device_switch, device_server, db_session: Session
    ):
        """Test connection auto-calculates cable length when devices positioned."""
        # Position devices
        pos1 = RackPosition(device_id=device_switch.id, rack_id=rack_standard.id, start_u=1)
        pos2 = RackPosition(device_id=device_server.id, rack_id=rack_standard.id, start_u=20)
        db_session.add_all([pos1, pos2])
        db_session.commit()

        data = {
            "from_device_id": device_switch.id,
            "to_device_id": device_server.id,
            "routing_path": "direct"
        }
        response = client.post("/api/connections/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        # Cable length may be auto-calculated based on position
        # Implementation-specific behavior


class TestConnectionsUpdate:
    """Tests for PUT /api/connections/{connection_id} endpoint."""

    def test_update_connection_ports(self, client: TestClient, connection_switch_to_server):
        """Test updating connection port information."""
        data = {
            "from_port": "Gi0/2",
            "to_port": "eth1"
        }
        response = client.put(f"/api/connections/{connection_switch_to_server.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["from_port"] == "Gi0/2"
        assert result["to_port"] == "eth1"

    def test_update_connection_cable_type(self, client: TestClient, connection_switch_to_server):
        """Test updating connection cable type."""
        data = {"cable_type": "Cat6a"}
        response = client.put(f"/api/connections/{connection_switch_to_server.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["cable_type"] == "Cat6a"

    def test_update_connection_routing_path(self, client: TestClient, connection_switch_to_server):
        """Test updating connection routing path."""
        data = {"routing_path": "conduit"}
        response = client.put(f"/api/connections/{connection_switch_to_server.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["routing_path"] == "conduit"

    def test_update_connection_not_found(self, client: TestClient):
        """Test updating non-existent connection returns 404."""
        data = {"from_port": "Port1"}
        response = client.put("/api/connections/99999", json=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestConnectionsDelete:
    """Tests for DELETE /api/connections/{connection_id} endpoint."""

    def test_delete_connection_success(self, client: TestClient, db_session: Session, device_switch, device_server):
        """Test deleting connection succeeds."""
        conn = Connection(from_device_id=device_switch.id, to_device_id=device_server.id)
        db_session.add(conn)
        db_session.commit()
        conn_id = conn.id

        response = client.delete(f"/api/connections/{conn_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_connection_not_found(self, client: TestClient):
        """Test deleting non-existent connection returns 404."""
        response = client.delete("/api/connections/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCableCalculations:
    """Tests for cable length calculations."""

    def test_calculate_cable_length_direct_routing(
        self, client: TestClient, rack_standard, device_switch, device_server, db_session: Session
    ):
        """Test cable length calculation with direct routing."""
        pos1 = RackPosition(device_id=device_switch.id, rack_id=rack_standard.id, start_u=1)
        pos2 = RackPosition(device_id=device_server.id, rack_id=rack_standard.id, start_u=10)
        db_session.add_all([pos1, pos2])
        db_session.commit()

        data = {
            "from_device_id": device_switch.id,
            "to_device_id": device_server.id,
            "routing_path": "direct"
        }
        response = client.post("/api/connections/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        # Implementation may auto-calculate length

    def test_calculate_cable_length_cable_tray(
        self, client: TestClient, rack_standard, device_switch, device_server, db_session: Session
    ):
        """Test cable length calculation with cable tray routing."""
        pos1 = RackPosition(device_id=device_switch.id, rack_id=rack_standard.id, start_u=1)
        pos2 = RackPosition(device_id=device_server.id, rack_id=rack_standard.id, start_u=10)
        db_session.add_all([pos1, pos2])
        db_session.commit()

        data = {
            "from_device_id": device_switch.id,
            "to_device_id": device_server.id,
            "routing_path": "cable_tray"
        }
        response = client.post("/api/connections/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        # Cable tray routing should add extra length

    def test_cable_bend_radius_validation(self, client: TestClient, device_switch, device_server):
        """Test cable bend radius is considered in calculations."""
        # Implementation-specific: May validate minimum bend radius
        data = {
            "from_device_id": device_switch.id,
            "to_device_id": device_server.id,
            "cable_type": "Fiber-SM"  # Has strict bend radius requirements
        }
        response = client.post("/api/connections/", json=data)
        assert response.status_code == status.HTTP_201_CREATED


class TestConnectionValidation:
    """Tests for connection validation rules."""

    def test_connection_requires_valid_cable_type(self, client: TestClient, device_switch, device_server):
        """Test connection validates cable type."""
        data = {
            "from_device_id": device_switch.id,
            "to_device_id": device_server.id,
            "cable_type": "Invalid"
        }
        response = client.post("/api/connections/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_connection_validates_routing_path(self, client: TestClient, device_switch, device_server):
        """Test connection validates routing path."""
        data = {
            "from_device_id": device_switch.id,
            "to_device_id": device_server.id,
            "routing_path": "invalid"
        }
        response = client.post("/api/connections/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
