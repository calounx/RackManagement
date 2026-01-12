"""
Unit tests for Models (Catalog) CRUD API endpoints.

Tests CRUD operations, model fetching, relationships with brands/device types.
Total: ~15 tests
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Model


class TestModelsList:
    """Tests for GET /api/models/ endpoint."""

    def test_list_models_empty(self, client: TestClient):
        """Test listing models when database is empty."""
        response = client.get("/api/models/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []

    def test_list_models_with_data(self, client: TestClient, model_catalyst_9300):
        """Test listing models returns all models."""
        response = client.get("/api/models/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Catalyst 9300"

    def test_list_models_includes_relationships(
        self, client: TestClient, model_catalyst_9300
    ):
        """Test model list includes brand and device_type details."""
        response = client.get("/api/models/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "brand" in data["items"][0]
        assert "device_type" in data["items"][0]

    def test_list_models_filter_by_brand(
        self, client: TestClient, model_catalyst_9300, model_poweredge_r740
    ):
        """Test filtering models by brand."""
        response = client.get(f"/api/models/?brand_id={model_catalyst_9300.brand_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["brand"]["name"] == "Cisco Systems"

    def test_list_models_filter_by_device_type(
        self, client: TestClient, model_catalyst_9300, model_poweredge_r740
    ):
        """Test filtering models by device type."""
        response = client.get(
            f"/api/models/?device_type_id={model_catalyst_9300.device_type_id}"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should only return switches
        assert all(item["device_type"]["slug"] == "switch" for item in data["items"])


class TestModelsGet:
    """Tests for GET /api/models/{model_id} endpoint."""

    def test_get_model_success(self, client: TestClient, model_catalyst_9300):
        """Test retrieving a single model by ID."""
        response = client.get(f"/api/models/{model_catalyst_9300.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == model_catalyst_9300.id
        assert data["name"] == "Catalyst 9300"

    def test_get_model_not_found(self, client: TestClient):
        """Test retrieving non-existent model returns 404."""
        response = client.get("/api/models/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestModelsCreate:
    """Tests for POST /api/models/ endpoint."""

    def test_create_model_minimal(
        self, client: TestClient, brand_cisco, device_type_switch
    ):
        """Test creating model with minimal required fields."""
        data = {
            "brand_id": brand_cisco.id,
            "device_type_id": device_type_switch.id,
            "name": "Catalyst 2960-X",
            "height_u": 1.0
        }
        response = client.post("/api/models/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["name"] == "Catalyst 2960-X"

    def test_create_model_with_all_fields(
        self, client: TestClient, brand_cisco, device_type_switch
    ):
        """Test creating model with all fields populated."""
        data = {
            "brand_id": brand_cisco.id,
            "device_type_id": device_type_switch.id,
            "name": "Nexus 9300",
            "variant": "ACI",
            "description": "Data center switch",
            "height_u": 1.0,
            "width_type": '19"',
            "depth_mm": 400.0,
            "weight_kg": 8.0,
            "power_watts": 250.0,
            "heat_output_btu": 853.0,
            "airflow_pattern": "front_to_back",
            "max_operating_temp_c": 45.0,
            "typical_ports": {"10gbe": 48, "40gbe": 6},
            "mounting_type": "4-post",
            "datasheet_url": "https://example.com/datasheet.pdf",
            "source": "manual",
            "confidence": "high"
        }
        response = client.post("/api/models/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["name"] == "Nexus 9300"
        assert result["variant"] == "ACI"

    def test_create_model_duplicate_brand_name_variant(
        self, client: TestClient, model_catalyst_9300
    ):
        """Test creating duplicate model fails."""
        data = {
            "brand_id": model_catalyst_9300.brand_id,
            "device_type_id": model_catalyst_9300.device_type_id,
            "name": "Catalyst 9300",
            "variant": "48-port",
            "height_u": 1.0
        }
        response = client.post("/api/models/", json=data)
        assert response.status_code == status.HTTP_409_CONFLICT


class TestModelsUpdate:
    """Tests for PUT /api/models/{model_id} endpoint."""

    def test_update_model_name(self, client: TestClient, model_catalyst_9300):
        """Test updating model name."""
        data = {"name": "Catalyst 9300-48P"}
        response = client.put(f"/api/models/{model_catalyst_9300.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["name"] == "Catalyst 9300-48P"

    def test_update_model_specs(self, client: TestClient, model_catalyst_9300):
        """Test updating model specifications."""
        data = {
            "power_watts": 230.0,
            "depth_mm": 450.0
        }
        response = client.put(f"/api/models/{model_catalyst_9300.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["power_watts"] == 230.0
        assert result["depth_mm"] == 450.0


class TestModelsDelete:
    """Tests for DELETE /api/models/{model_id} endpoint."""

    def test_delete_model_success(
        self, client: TestClient, db_session: Session, brand_cisco, device_type_switch
    ):
        """Test deleting model succeeds."""
        model = Model(
            brand_id=brand_cisco.id,
            device_type_id=device_type_switch.id,
            name="To Delete",
            height_u=1.0
        )
        db_session.add(model)
        db_session.commit()
        model_id = model.id

        response = client.delete(f"/api/models/{model_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_model_not_found(self, client: TestClient):
        """Test deleting non-existent model returns 404."""
        response = client.delete("/api/models/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
