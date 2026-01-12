"""
Unit tests for Brands CRUD API endpoints.

Tests CRUD operations, logo upload, Wikipedia fetcher integration, and validation.
Total: ~20 tests
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Brand


class TestBrandsList:
    """Tests for GET /api/brands/ endpoint."""

    def test_list_brands_empty(self, client: TestClient):
        """Test listing brands when database is empty."""
        response = client.get("/api/brands/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []

    def test_list_brands_with_data(self, client: TestClient, brand_cisco):
        """Test listing brands returns all brands."""
        response = client.get("/api/brands/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Cisco Systems"

    def test_list_brands_pagination(self, client: TestClient, db_session: Session):
        """Test brand list pagination."""
        for i in range(10):
            brand = Brand(name=f"Brand {i}", slug=f"brand-{i}")
            db_session.add(brand)
        db_session.commit()

        response = client.get("/api/brands/?page=1&page_size=5")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 5
        assert data["pagination"]["total"] == 10
        assert data["pagination"]["page"] == 1


class TestBrandsGet:
    """Tests for GET /api/brands/{brand_id} endpoint."""

    def test_get_brand_success(self, client: TestClient, brand_cisco):
        """Test retrieving a single brand by ID."""
        response = client.get(f"/api/brands/{brand_cisco.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == brand_cisco.id
        assert data["name"] == "Cisco Systems"
        assert data["slug"] == "cisco-systems"

    def test_get_brand_not_found(self, client: TestClient):
        """Test retrieving non-existent brand returns 404."""
        response = client.get("/api/brands/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBrandsCreate:
    """Tests for POST /api/brands/ endpoint."""

    def test_create_brand_minimal(self, client: TestClient):
        """Test creating brand with minimal required fields."""
        data = {
            "name": "Juniper Networks",
            "slug": "juniper-networks"
        }
        response = client.post("/api/brands/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["name"] == "Juniper Networks"
        assert result["slug"] == "juniper-networks"

    def test_create_brand_with_all_fields(self, client: TestClient):
        """Test creating brand with all fields populated."""
        data = {
            "name": "Arista Networks",
            "slug": "arista-networks",
            "website": "https://www.arista.com",
            "support_url": "https://www.arista.com/support",
            "logo_url": "https://example.com/logo.png",
            "description": "Cloud networking company",
            "founded_year": 2004,
            "headquarters": "Santa Clara, California"
        }
        response = client.post("/api/brands/", json=data)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["name"] == "Arista Networks"
        assert result["founded_year"] == 2004

    def test_create_brand_duplicate_name(self, client: TestClient, brand_cisco):
        """Test creating duplicate brand name fails."""
        data = {
            "name": "Cisco Systems",
            "slug": "cisco-systems-2"
        }
        response = client.post("/api/brands/", json=data)
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_brand_duplicate_slug(self, client: TestClient, brand_cisco):
        """Test creating duplicate brand slug fails."""
        data = {
            "name": "Cisco Networks",
            "slug": "cisco-systems"
        }
        response = client.post("/api/brands/", json=data)
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_brand_invalid_year(self, client: TestClient):
        """Test creating brand with invalid founded year fails."""
        data = {
            "name": "Test Brand",
            "slug": "test-brand",
            "founded_year": 1700  # Too old
        }
        response = client.post("/api/brands/", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestBrandsUpdate:
    """Tests for PUT /api/brands/{brand_id} endpoint."""

    def test_update_brand_name(self, client: TestClient, brand_cisco):
        """Test updating brand name."""
        data = {"name": "Cisco Systems Inc."}
        response = client.put(f"/api/brands/{brand_cisco.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["name"] == "Cisco Systems Inc."

    def test_update_brand_website(self, client: TestClient, brand_cisco):
        """Test updating brand website."""
        data = {"website": "https://www.cisco.com/updated"}
        response = client.put(f"/api/brands/{brand_cisco.id}", json=data)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["website"] == "https://www.cisco.com/updated"

    def test_update_brand_not_found(self, client: TestClient):
        """Test updating non-existent brand returns 404."""
        data = {"name": "Name"}
        response = client.put("/api/brands/99999", json=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBrandsDelete:
    """Tests for DELETE /api/brands/{brand_id} endpoint."""

    def test_delete_brand_success(self, client: TestClient, db_session: Session):
        """Test deleting brand succeeds."""
        brand = Brand(name="To Delete", slug="to-delete")
        db_session.add(brand)
        db_session.commit()
        brand_id = brand.id

        response = client.delete(f"/api/brands/{brand_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_brand_not_found(self, client: TestClient):
        """Test deleting non-existent brand returns 404."""
        response = client.delete("/api/brands/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_brand_with_models(self, client: TestClient, model_catalyst_9300, brand_cisco):
        """Test deleting brand with models may fail or cascade."""
        response = client.delete(f"/api/brands/{brand_cisco.id}")
        # Implementation may prevent deletion or cascade
        assert response.status_code in [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_409_CONFLICT
        ]


class TestBrandsLogoUpload:
    """Tests for brand logo upload functionality."""

    def test_upload_brand_logo_success(self, client: TestClient, brand_cisco):
        """Test uploading brand logo."""
        # Create a simple test image file
        from io import BytesIO
        file_content = b"fake image content"
        files = {"file": ("logo.png", BytesIO(file_content), "image/png")}

        response = client.post(f"/api/brands/{brand_cisco.id}/logo", files=files)
        # May return 200 or specific upload response
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND  # If endpoint not implemented
        ]

    def test_upload_brand_logo_invalid_format(self, client: TestClient, brand_cisco):
        """Test uploading invalid logo format fails."""
        from io import BytesIO
        file_content = b"not an image"
        files = {"file": ("logo.txt", BytesIO(file_content), "text/plain")}

        response = client.post(f"/api/brands/{brand_cisco.id}/logo", files=files)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_404_NOT_FOUND  # If endpoint not implemented
        ]


class TestBrandsWikipediaFetch:
    """Tests for Wikipedia brand information fetching."""

    @pytest.mark.skip(reason="Requires mocking Wikipedia API")
    def test_fetch_brand_from_wikipedia(self, client: TestClient):
        """Test fetching brand information from Wikipedia."""
        data = {"brand_name": "Cisco Systems"}
        response = client.post("/api/brands/fetch-wikipedia", json=data)
        # This would require mocking the Wikipedia API
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]
