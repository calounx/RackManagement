"""
Unit tests for Device Specifications CRUD API endpoints.

Tests all CRUD operations, validation, edge cases, filtering, and pagination.
Total: ~40 tests
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import DeviceSpecification, SourceType, ConfidenceLevel, WidthType, AirflowPattern


class TestDeviceSpecsList:
    """Tests for GET /api/device-specs/ endpoint."""

    def test_list_device_specs_empty(self, client: TestClient):
        """Test listing device specs when database is empty."""
        response = client.get("/api/device-specs/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_device_specs_with_data(self, client: TestClient, spec_switch):
        """Test listing device specs returns all specifications."""
        response = client.get("/api/device-specs/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["brand"] == "Cisco"
        assert data[0]["model"] == "Catalyst 2960"

    def test_list_device_specs_multiple(self, client: TestClient, db_session: Session):
        """Test listing multiple device specs."""
        specs_data = [
            {"brand": "Cisco", "model": "Catalyst 2960", "height_u": 1.0},
            {"brand": "Juniper", "model": "EX2300", "height_u": 1.0},
            {"brand": "HPE", "model": "Aruba 2930F", "height_u": 1.0},
        ]
        for spec_data in specs_data:
            spec = DeviceSpecification(**spec_data)
            db_session.add(spec)
        db_session.commit()

        response = client.get("/api/device-specs/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    def test_list_device_specs_filter_by_brand(self, client: TestClient, db_session: Session):
        """Test filtering device specs by brand name."""
        specs = [
            DeviceSpecification(brand="Cisco", model="Model1", height_u=1.0),
            DeviceSpecification(brand="Cisco", model="Model2", height_u=1.0),
            DeviceSpecification(brand="Juniper", model="Model3", height_u=1.0),
        ]
        for spec in specs:
            db_session.add(spec)
        db_session.commit()

        response = client.get("/api/device-specs/?brand=Cisco")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert all(item["brand"] == "Cisco" for item in data)

    def test_list_device_specs_filter_by_brand_case_insensitive(
        self, client: TestClient, db_session: Session
    ):
        """Test brand filter is case-insensitive."""
        spec = DeviceSpecification(brand="Cisco", model="Test", height_u=1.0)
        db_session.add(spec)
        db_session.commit()

        response = client.get("/api/device-specs/?brand=cisco")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1

    def test_list_device_specs_filter_by_brand_partial_match(
        self, client: TestClient, db_session: Session
    ):
        """Test brand filter supports partial matching."""
        spec = DeviceSpecification(brand="Cisco Systems", model="Test", height_u=1.0)
        db_session.add(spec)
        db_session.commit()

        response = client.get("/api/device-specs/?brand=Cis")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1

    def test_list_device_specs_filter_by_model(self, client: TestClient, db_session: Session):
        """Test filtering device specs by model name."""
        specs = [
            DeviceSpecification(brand="Cisco", model="Catalyst 2960", height_u=1.0),
            DeviceSpecification(brand="Cisco", model="Nexus 9300", height_u=1.0),
        ]
        for spec in specs:
            db_session.add(spec)
        db_session.commit()

        response = client.get("/api/device-specs/?model=Catalyst")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["model"] == "Catalyst 2960"

    def test_list_device_specs_filter_by_width_type(
        self, client: TestClient, db_session: Session
    ):
        """Test filtering device specs by width type."""
        specs = [
            DeviceSpecification(brand="A", model="M1", height_u=1.0, width_type=WidthType.NINETEEN_INCH),
            DeviceSpecification(brand="B", model="M2", height_u=1.0, width_type=WidthType.TWENTY_THREE_INCH),
        ]
        for spec in specs:
            db_session.add(spec)
        db_session.commit()

        response = client.get('/api/device-specs/?width_type=19"')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["width_type"] == '19"'

    def test_list_device_specs_filter_by_source(self, client: TestClient, db_session: Session):
        """Test filtering device specs by source type."""
        specs = [
            DeviceSpecification(
                brand="A", model="M1", height_u=1.0, source=SourceType.USER_CUSTOM
            ),
            DeviceSpecification(
                brand="B", model="M2", height_u=1.0, source=SourceType.WEB_FETCHED
            ),
        ]
        for spec in specs:
            db_session.add(spec)
        db_session.commit()

        response = client.get("/api/device-specs/?source=user_custom")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["source"] == "user_custom"

    def test_list_device_specs_multiple_filters(self, client: TestClient, db_session: Session):
        """Test combining multiple filters."""
        specs = [
            DeviceSpecification(brand="Cisco", model="Cat1", height_u=1.0),
            DeviceSpecification(brand="Cisco", model="Nexus", height_u=1.0),
            DeviceSpecification(brand="Juniper", model="Cat2", height_u=1.0),
        ]
        for spec in specs:
            db_session.add(spec)
        db_session.commit()

        response = client.get("/api/device-specs/?brand=Cisco&model=Cat")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["brand"] == "Cisco"
        assert "Cat" in data[0]["model"]

    def test_list_device_specs_pagination_skip(self, client: TestClient, db_session: Session):
        """Test pagination skip parameter."""
        for i in range(5):
            spec = DeviceSpecification(brand="Brand", model=f"Model{i}", height_u=1.0)
            db_session.add(spec)
        db_session.commit()

        response = client.get("/api/device-specs/?skip=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    def test_list_device_specs_pagination_limit(self, client: TestClient, db_session: Session):
        """Test pagination limit parameter."""
        for i in range(10):
            spec = DeviceSpecification(brand="Brand", model=f"Model{i}", height_u=1.0)
            db_session.add(spec)
        db_session.commit()

        response = client.get("/api/device-specs/?limit=5")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5

    def test_list_device_specs_pagination_skip_and_limit(
        self, client: TestClient, db_session: Session
    ):
        """Test pagination with both skip and limit."""
        for i in range(10):
            spec = DeviceSpecification(brand="Brand", model=f"Model{i}", height_u=1.0)
            db_session.add(spec)
        db_session.commit()

        response = client.get("/api/device-specs/?skip=3&limit=4")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 4


class TestDeviceSpecsSearch:
    """Tests for GET /api/device-specs/search endpoint."""

    def test_search_device_specs_by_brand(self, client: TestClient, spec_switch):
        """Test searching device specs by brand."""
        response = client.get("/api/device-specs/search?q=Cisco")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["brand"] == "Cisco"

    def test_search_device_specs_by_model(self, client: TestClient, spec_switch):
        """Test searching device specs by model."""
        response = client.get("/api/device-specs/search?q=Catalyst")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert "Catalyst" in data[0]["model"]

    def test_search_device_specs_case_insensitive(self, client: TestClient, spec_switch):
        """Test search is case-insensitive."""
        response = client.get("/api/device-specs/search?q=cisco")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1

    def test_search_device_specs_not_found(self, client: TestClient):
        """Test search returns 404 when no results found."""
        response = client.get("/api/device-specs/search?q=NonExistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_search_device_specs_missing_query(self, client: TestClient):
        """Test search requires query parameter."""
        response = client.get("/api/device-specs/search")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDeviceSpecsGet:
    """Tests for GET /api/device-specs/{spec_id} endpoint."""

    def test_get_device_spec_success(self, client: TestClient, spec_switch):
        """Test retrieving a single device spec by ID."""
        response = client.get(f"/api/device-specs/{spec_switch.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == spec_switch.id
        assert data["brand"] == "Cisco"
        assert data["model"] == "Catalyst 2960"

    def test_get_device_spec_not_found(self, client: TestClient):
        """Test retrieving non-existent device spec returns 404."""
        response = client.get("/api/device-specs/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_get_device_spec_invalid_id(self, client: TestClient):
        """Test retrieving device spec with invalid ID format."""
        response = client.get("/api/device-specs/invalid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_device_spec_includes_all_fields(self, client: TestClient, db_session: Session):
        """Test retrieved spec includes all expected fields."""
        spec = DeviceSpecification(
            brand="Cisco",
            model="Test Model",
            variant="AC",
            height_u=2.0,
            width_type=WidthType.NINETEEN_INCH,
            depth_mm=450.0,
            weight_kg=10.5,
            power_watts=200.0,
            heat_output_btu=682.4,
            airflow_pattern=AirflowPattern.FRONT_TO_BACK,
            max_operating_temp_c=45.0,
            typical_ports={"gigabit_ethernet": 48},
            mounting_type="4-post",
            source=SourceType.MANUFACTURER_SPEC,
            confidence=ConfidenceLevel.HIGH,
        )
        db_session.add(spec)
        db_session.commit()
        db_session.refresh(spec)

        response = client.get(f"/api/device-specs/{spec.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["brand"] == "Cisco"
        assert data["model"] == "Test Model"
        assert data["variant"] == "AC"
        assert data["height_u"] == 2.0
        assert data["width_type"] == '19"'
        assert data["depth_mm"] == 450.0
        assert data["weight_kg"] == 10.5
        assert data["power_watts"] == 200.0
        assert data["heat_output_btu"] == 682.4
        assert data["airflow_pattern"] == "front_to_back"
        assert data["max_operating_temp_c"] == 45.0
        assert data["typical_ports"] == {"gigabit_ethernet": 48}
        assert data["mounting_type"] == "4-post"
        assert data["source"] == "manufacturer_spec"
        assert data["confidence"] == "high"


class TestDeviceSpecsCreate:
    """Tests for POST /api/device-specs/ endpoint."""

    def test_create_device_spec_minimal(self, client: TestClient):
        """Test creating device spec with minimal required fields."""
        data = {
            "brand": "Test Brand",
            "model": "Test Model",
            "height_u": 1.0,
        }
        response = client.post("/api/device-specs/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["brand"] == "Test Brand"
        assert result["model"] == "Test Model"
        assert result["height_u"] == 1.0

    def test_create_device_spec_with_all_fields(self, client: TestClient):
        """Test creating device spec with all fields populated."""
        data = {
            "brand": "Cisco",
            "model": "Catalyst 9300",
            "variant": "48-port",
            "height_u": 1.0,
            "width_type": '19"',
            "depth_mm": 445.0,
            "weight_kg": 7.3,
            "power_watts": 215.0,
            "heat_output_btu": 733.0,
            "airflow_pattern": "front_to_back",
            "max_operating_temp_c": 45.0,
            "typical_ports": {"gigabit_ethernet": 48, "sfp+": 4},
            "mounting_type": "2-post",
            "source": "manufacturer_spec",
            "confidence": "high",
        }
        response = client.post("/api/device-specs/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["brand"] == "Cisco"
        assert result["variant"] == "48-port"
        assert result["typical_ports"] == {"gigabit_ethernet": 48, "sfp+": 4}

    def test_create_device_spec_duplicate_brand_model(
        self, client: TestClient, spec_switch
    ):
        """Test creating duplicate device spec returns 409 conflict."""
        data = {
            "brand": "Cisco",
            "model": "Catalyst 2960",
            "height_u": 1.0,
        }
        response = client.post("/api/device-specs/", json=data)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"].lower()

    def test_create_device_spec_auto_calculate_btu(self, client: TestClient):
        """Test BTU is auto-calculated from watts if not provided."""
        data = {
            "brand": "Test",
            "model": "Model",
            "height_u": 1.0,
            "power_watts": 100.0,
        }
        response = client.post("/api/device-specs/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        # 100W * 3.412 = 341.2 BTU
        assert result["heat_output_btu"] == pytest.approx(341.2, rel=0.01)

    def test_create_device_spec_missing_required_brand(self, client: TestClient):
        """Test creating spec without brand fails validation."""
        data = {"model": "Model", "height_u": 1.0}
        response = client.post("/api/device-specs/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_device_spec_missing_required_model(self, client: TestClient):
        """Test creating spec without model fails validation."""
        data = {"brand": "Brand", "height_u": 1.0}
        response = client.post("/api/device-specs/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_device_spec_missing_required_height(self, client: TestClient):
        """Test creating spec without height_u fails validation."""
        data = {"brand": "Brand", "model": "Model"}
        response = client.post("/api/device-specs/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_device_spec_invalid_height_negative(self, client: TestClient):
        """Test creating spec with negative height fails validation."""
        data = {"brand": "Brand", "model": "Model", "height_u": -1.0}
        response = client.post("/api/device-specs/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_device_spec_invalid_height_too_large(self, client: TestClient):
        """Test creating spec with height > 50U fails validation."""
        data = {"brand": "Brand", "model": "Model", "height_u": 51.0}
        response = client.post("/api/device-specs/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_device_spec_invalid_power_negative(self, client: TestClient):
        """Test creating spec with negative power fails validation."""
        data = {"brand": "Brand", "model": "Model", "height_u": 1.0, "power_watts": -10.0}
        response = client.post("/api/device-specs/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_device_spec_invalid_width_type(self, client: TestClient):
        """Test creating spec with invalid width type fails validation."""
        data = {
            "brand": "Brand",
            "model": "Model",
            "height_u": 1.0,
            "width_type": "invalid",
        }
        response = client.post("/api/device-specs/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDeviceSpecsUpdate:
    """Tests for PUT /api/device-specs/{spec_id} endpoint."""

    def test_update_device_spec_single_field(self, client: TestClient, spec_switch):
        """Test updating a single field."""
        data = {"power_watts": 150.0}
        response = client.put(f"/api/device-specs/{spec_switch.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["power_watts"] == 150.0
        # Other fields unchanged
        assert result["brand"] == "Cisco"
        assert result["model"] == "Catalyst 2960"

    def test_update_device_spec_multiple_fields(self, client: TestClient, spec_switch):
        """Test updating multiple fields."""
        data = {
            "power_watts": 200.0,
            "heat_output_btu": 682.4,
            "depth_mm": 400.0,
        }
        response = client.put(f"/api/device-specs/{spec_switch.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["power_watts"] == 200.0
        assert result["heat_output_btu"] == 682.4
        assert result["depth_mm"] == 400.0

    def test_update_device_spec_not_found(self, client: TestClient):
        """Test updating non-existent spec returns 404."""
        data = {"power_watts": 100.0}
        response = client.put("/api/device-specs/99999", json=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_device_spec_empty_update(self, client: TestClient, spec_switch):
        """Test updating with no fields still succeeds."""
        data = {}
        response = client.put(f"/api/device-specs/{spec_switch.id}", json=data)
        assert response.status_code == status.HTTP_200_OK

    def test_update_device_spec_change_brand_model(self, client: TestClient, spec_switch):
        """Test updating brand and model."""
        data = {"brand": "Juniper", "model": "EX2300"}
        response = client.put(f"/api/device-specs/{spec_switch.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["brand"] == "Juniper"
        assert result["model"] == "EX2300"

    def test_update_device_spec_invalid_height(self, client: TestClient, spec_switch):
        """Test updating with invalid height fails validation."""
        data = {"height_u": -1.0}
        response = client.put(f"/api/device-specs/{spec_switch.id}", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDeviceSpecsDelete:
    """Tests for DELETE /api/device-specs/{spec_id} endpoint."""

    def test_delete_device_spec_success(self, client: TestClient, db_session: Session):
        """Test deleting device spec succeeds."""
        spec = DeviceSpecification(brand="Test", model="Model", height_u=1.0)
        db_session.add(spec)
        db_session.commit()
        spec_id = spec.id

        response = client.delete(f"/api/device-specs/{spec_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        deleted_spec = db_session.query(DeviceSpecification).filter_by(id=spec_id).first()
        assert deleted_spec is None

    def test_delete_device_spec_not_found(self, client: TestClient):
        """Test deleting non-existent spec returns 404."""
        response = client.delete("/api/device-specs/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_device_spec_with_devices(self, client: TestClient, device_switch, spec_switch):
        """Test deleting spec in use by devices fails."""
        response = client.delete(f"/api/device-specs/{spec_switch.id}")
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "device(s) are using it" in response.json()["detail"].lower()
