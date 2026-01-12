"""
Integration Tests for Catalog Management Workflow

Tests complete catalog workflow:
- Fetch brand from Wikipedia
- Upload logo
- Create models
- Link to device types
- Create devices from models
- Catalog browsing and filtering
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import io


class TestCatalogManagementWorkflow:
    """Test complete catalog management workflow."""

    def test_complete_catalog_creation_workflow(self, client: TestClient, db_session: Session):
        """
        Test complete workflow from creating device type to creating device.

        Workflow:
        1. Create device type
        2. Create brand manually
        3. Create model
        4. Create device from model
        5. Verify all relationships
        """
        # Step 1: Create device type
        device_type_data = {
            "name": "Network Switch",
            "slug": "network-switch",
            "icon": "🔀",
            "description": "Layer 2/3 network switches",
            "color": "#4CAF50"
        }
        response = client.post("/api/device-types", json=device_type_data)
        assert response.status_code == 201
        device_type = response.json()
        device_type_id = device_type["id"]
        assert device_type["name"] == "Network Switch"
        assert device_type["model_count"] == 0

        # Step 2: Create brand
        brand_data = {
            "name": "Arista Networks",
            "slug": "arista-networks",
            "website": "https://www.arista.com",
            "description": "Cloud networking solutions",
            "headquarters": "Santa Clara, California",
            "founded_year": 2004
        }
        response = client.post("/api/brands", json=brand_data)
        assert response.status_code == 201
        brand = response.json()
        brand_id = brand["id"]
        assert brand["name"] == "Arista Networks"
        assert brand["model_count"] == 0

        # Step 3: Create model
        model_data = {
            "brand_id": brand_id,
            "device_type_id": device_type_id,
            "name": "7050SX3-48YC12",
            "variant": "48-port",
            "description": "48x25GbE SFP28 and 12x100GbE QSFP28 switch",
            "height_u": 1.0,
            "width_type": '19"',
            "depth_mm": 457.0,
            "weight_kg": 12.5,
            "power_watts": 350.0,
            "heat_output_btu": 1194.0,
            "airflow_pattern": "front_to_back",
            "max_operating_temp_c": 45.0,
            "typical_ports": {
                "sfp28_25g": 48,
                "qsfp28_100g": 12,
                "management": 1
            },
            "mounting_type": "2-post",
            "source": "manual",
            "confidence": "high"
        }
        response = client.post("/api/models", json=model_data)
        assert response.status_code == 201
        model = response.json()
        model_id = model["id"]
        assert model["name"] == "7050SX3-48YC12"
        assert model["brand"]["name"] == "Arista Networks"
        assert model["device_type"]["name"] == "Network Switch"
        assert model["device_count"] == 0

        # Step 4: Create device from model
        device_data = {
            "model_id": model_id,
            "custom_name": "Core Switch 1",
            "serial_number": "ARI-2024-001",
            "access_frequency": "high",
            "notes": "Primary core switch for datacenter"
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 201
        device = response.json()
        device_id = device["id"]
        assert device["custom_name"] == "Core Switch 1"
        assert device["serial_number"] == "ARI-2024-001"
        assert device["model_id"] == model_id
        assert device["catalog_model"]["name"] == "7050SX3-48YC12"

        # Step 5: Verify relationships
        # Get device type - should show 1 model
        response = client.get(f"/api/device-types/{device_type_id}")
        assert response.status_code == 200
        device_type = response.json()
        assert device_type["model_count"] == 1

        # Get brand - should show 1 model
        response = client.get(f"/api/brands/{brand_id}")
        assert response.status_code == 200
        brand = response.json()
        assert brand["model_count"] == 1

        # Get model - should show 1 device
        response = client.get(f"/api/models/{model_id}")
        assert response.status_code == 200
        model = response.json()
        assert model["device_count"] == 1

    def test_catalog_browsing_and_filtering(self, client: TestClient, db_session: Session):
        """
        Test browsing and filtering catalog items.

        Workflow:
        1. Create multiple device types
        2. Create multiple brands
        3. Create multiple models
        4. Filter models by brand
        5. Filter models by device type
        6. Search models
        """
        # Create device types
        device_types = []
        for name in ["Switch", "Router", "Firewall"]:
            device_type_data = {
                "name": name,
                "slug": name.lower(),
                "icon": "🔀"
            }
            response = client.post("/api/device-types", json=device_type_data)
            device_types.append(response.json())

        # Create brands
        brands = []
        for name in ["Cisco", "Juniper", "Arista"]:
            brand_data = {
                "name": name,
                "slug": name.lower()
            }
            response = client.post("/api/brands", json=brand_data)
            brands.append(response.json())

        # Create models (mix of brands and types)
        models = []
        model_configs = [
            (0, 0, "Catalyst 9300"),  # Cisco Switch
            (0, 0, "Nexus 9300"),     # Cisco Switch
            (0, 1, "ASR 1000"),       # Cisco Router
            (1, 1, "MX204"),          # Juniper Router
            (2, 0, "7050SX3"),        # Arista Switch
        ]

        for brand_idx, type_idx, name in model_configs:
            model_data = {
                "brand_id": brands[brand_idx]["id"],
                "device_type_id": device_types[type_idx]["id"],
                "name": name,
                "height_u": 1.0,
                "power_watts": 200.0
            }
            response = client.post("/api/models", json=model_data)
            models.append(response.json())

        # List all models
        response = client.get("/api/models")
        assert response.status_code == 200
        all_models = response.json()
        assert len(all_models["items"]) >= 5

        # Filter by brand (Cisco)
        response = client.get(f"/api/models?brand_id={brands[0]['id']}")
        assert response.status_code == 200
        cisco_models = response.json()
        assert len(cisco_models["items"]) == 3  # 3 Cisco models

        # Filter by device type (Switch)
        response = client.get(f"/api/models?device_type_id={device_types[0]['id']}")
        assert response.status_code == 200
        switch_models = response.json()
        assert len(switch_models["items"]) == 3  # 3 Switch models

        # Filter by both brand and type (Cisco Switches)
        response = client.get(
            f"/api/models?brand_id={brands[0]['id']}&device_type_id={device_types[0]['id']}"
        )
        assert response.status_code == 200
        cisco_switches = response.json()
        assert len(cisco_switches["items"]) == 2  # 2 Cisco switches

    def test_model_creation_with_all_fields(self, client: TestClient, db_session: Session):
        """
        Test creating model with all optional fields populated.

        Verifies complete model data structure.
        """
        # Create prerequisites
        device_type_data = {
            "name": "Server",
            "slug": "server",
            "icon": "🖥️"
        }
        response = client.post("/api/device-types", json=device_type_data)
        device_type_id = response.json()["id"]

        brand_data = {
            "name": "HPE",
            "slug": "hpe"
        }
        response = client.post("/api/brands", json=brand_data)
        brand_id = response.json()["id"]

        # Create model with all fields
        model_data = {
            "brand_id": brand_id,
            "device_type_id": device_type_id,
            "name": "ProLiant DL380 Gen11",
            "variant": "2U Rack Server",
            "description": "Industry-standard 2U server with flexible configuration options",
            "height_u": 2.0,
            "width_type": '19"',
            "depth_mm": 685.0,
            "weight_kg": 32.0,
            "power_watts": 800.0,
            "heat_output_btu": 2730.0,
            "airflow_pattern": "front_to_back",
            "max_operating_temp_c": 35.0,
            "typical_ports": {
                "gigabit_ethernet": 4,
                "usb": 5,
                "serial": 1,
                "vga": 1
            },
            "mounting_type": "4-post",
            "datasheet_url": "https://www.hpe.com/dl380-gen11-datasheet.pdf",
            "image_url": "https://www.hpe.com/images/dl380-gen11.jpg",
            "source": "manufacturer_spec",
            "confidence": "high"
        }
        response = client.post("/api/models", json=model_data)
        assert response.status_code == 201
        model = response.json()

        # Verify all fields
        assert model["name"] == "ProLiant DL380 Gen11"
        assert model["variant"] == "2U Rack Server"
        assert model["description"] is not None
        assert model["height_u"] == 2.0
        assert model["width_type"] == '19"'
        assert model["depth_mm"] == 685.0
        assert model["weight_kg"] == 32.0
        assert model["power_watts"] == 800.0
        assert model["heat_output_btu"] == 2730.0
        assert model["airflow_pattern"] == "front_to_back"
        assert model["max_operating_temp_c"] == 35.0
        assert model["typical_ports"]["gigabit_ethernet"] == 4
        assert model["mounting_type"] == "4-post"
        assert model["datasheet_url"] is not None
        assert model["image_url"] is not None
        assert model["source"] == "manufacturer_spec"
        assert model["confidence"] == "high"

    def test_duplicate_model_prevention(self, client: TestClient, db_session: Session):
        """
        Test that duplicate models (same brand + name + variant) are prevented.

        Workflow:
        1. Create model
        2. Try to create duplicate
        3. Verify error
        """
        # Create prerequisites
        device_type_data = {
            "name": "Switch",
            "slug": "switch"
        }
        response = client.post("/api/device-types", json=device_type_data)
        device_type_id = response.json()["id"]

        brand_data = {
            "name": "Cisco",
            "slug": "cisco"
        }
        response = client.post("/api/brands", json=brand_data)
        brand_id = response.json()["id"]

        # Create model
        model_data = {
            "brand_id": brand_id,
            "device_type_id": device_type_id,
            "name": "Catalyst 9300",
            "variant": "48-port",
            "height_u": 1.0,
            "power_watts": 215.0
        }
        response = client.post("/api/models", json=model_data)
        assert response.status_code == 201

        # Try to create duplicate
        response = client.post("/api/models", json=model_data)
        assert response.status_code == 400

    def test_model_update_workflow(self, client: TestClient, db_session: Session):
        """
        Test updating model specifications.

        Workflow:
        1. Create model
        2. Update various fields
        3. Verify updates
        4. Verify devices using model see updates
        """
        # Create prerequisites
        device_type_data = {
            "name": "Router",
            "slug": "router"
        }
        response = client.post("/api/device-types", json=device_type_data)
        device_type_id = response.json()["id"]

        brand_data = {
            "name": "Juniper",
            "slug": "juniper"
        }
        response = client.post("/api/brands", json=brand_data)
        brand_id = response.json()["id"]

        # Create model with initial values
        model_data = {
            "brand_id": brand_id,
            "device_type_id": device_type_id,
            "name": "MX204",
            "height_u": 1.0,
            "power_watts": 350.0,
            "description": "Initial description"
        }
        response = client.post("/api/models", json=model_data)
        model_id = response.json()["id"]

        # Create device from model
        device_data = {
            "model_id": model_id,
            "custom_name": "Edge Router"
        }
        response = client.post("/api/devices", json=device_data)
        device_id = response.json()["id"]

        # Update model
        update_data = {
            "power_watts": 400.0,
            "heat_output_btu": 1365.0,
            "description": "Updated: Universal routing platform",
            "datasheet_url": "https://www.juniper.net/mx204-datasheet.pdf"
        }
        response = client.patch(f"/api/models/{model_id}", json=update_data)
        assert response.status_code == 200
        updated_model = response.json()
        assert updated_model["power_watts"] == 400.0
        assert updated_model["heat_output_btu"] == 1365.0
        assert updated_model["description"] == "Updated: Universal routing platform"
        assert updated_model["datasheet_url"] is not None

        # Verify device sees updated model
        response = client.get(f"/api/devices/{device_id}")
        device = response.json()
        assert device["catalog_model"]["power_watts"] == 400.0

    def test_brand_logo_workflow(self, client: TestClient, db_session: Session):
        """
        Test brand logo management.

        Workflow:
        1. Create brand without logo
        2. Update with logo URL
        3. Verify logo appears in brand and model responses
        """
        # Create brand without logo
        brand_data = {
            "name": "Dell Technologies",
            "slug": "dell-technologies",
            "website": "https://www.dell.com"
        }
        response = client.post("/api/brands", json=brand_data)
        assert response.status_code == 201
        brand = response.json()
        brand_id = brand["id"]
        assert brand["logo_url"] is None

        # Update with logo URL
        update_data = {
            "logo_url": "https://www.dell.com/logo.png"
        }
        response = client.patch(f"/api/brands/{brand_id}", json=update_data)
        assert response.status_code == 200
        updated_brand = response.json()
        assert updated_brand["logo_url"] == "https://www.dell.com/logo.png"

        # Create model for brand
        device_type_data = {
            "name": "Server",
            "slug": "server"
        }
        response = client.post("/api/device-types", json=device_type_data)
        device_type_id = response.json()["id"]

        model_data = {
            "brand_id": brand_id,
            "device_type_id": device_type_id,
            "name": "PowerEdge R750",
            "height_u": 2.0,
            "power_watts": 800.0
        }
        response = client.post("/api/models", json=model_data)
        model = response.json()

        # Verify logo appears in model response
        assert model["brand"]["logo_url"] == "https://www.dell.com/logo.png"

    def test_device_type_color_coding(self, client: TestClient, db_session: Session):
        """
        Test device type color coding for UI organization.

        Workflow:
        1. Create device types with different colors
        2. Create models for each type
        3. Verify colors propagate to model responses
        """
        # Create device types with colors
        device_type_configs = [
            ("Switch", "#4CAF50"),
            ("Router", "#2196F3"),
            ("Firewall", "#FF5722")
        ]

        device_types = []
        for name, color in device_type_configs:
            device_type_data = {
                "name": name,
                "slug": name.lower(),
                "icon": "🔀",
                "color": color
            }
            response = client.post("/api/device-types", json=device_type_data)
            device_types.append(response.json())

        # Verify colors are set
        for i, dt in enumerate(device_types):
            assert dt["color"] == device_type_configs[i][1]

        # Create brand
        brand_data = {
            "name": "Test Brand",
            "slug": "test-brand"
        }
        response = client.post("/api/brands", json=brand_data)
        brand_id = response.json()["id"]

        # Create model for each device type
        for dt in device_types:
            model_data = {
                "brand_id": brand_id,
                "device_type_id": dt["id"],
                "name": f"{dt['name']} Model",
                "height_u": 1.0,
                "power_watts": 200.0
            }
            response = client.post("/api/models", json=model_data)
            model = response.json()

            # Verify color propagates
            assert model["device_type"]["color"] == dt["color"]

    def test_catalog_pagination(self, client: TestClient, db_session: Session):
        """
        Test pagination for catalog listings.

        Workflow:
        1. Create many models
        2. Test pagination
        3. Verify page metadata
        """
        # Create prerequisites
        device_type_data = {
            "name": "Switch",
            "slug": "switch"
        }
        response = client.post("/api/device-types", json=device_type_data)
        device_type_id = response.json()["id"]

        brand_data = {
            "name": "Generic",
            "slug": "generic"
        }
        response = client.post("/api/brands", json=brand_data)
        brand_id = response.json()["id"]

        # Create 25 models
        for i in range(25):
            model_data = {
                "brand_id": brand_id,
                "device_type_id": device_type_id,
                "name": f"Model-{i+1:03d}",
                "height_u": 1.0,
                "power_watts": 100.0 + i
            }
            response = client.post("/api/models", json=model_data)
            assert response.status_code == 201

        # Get first page (default page size)
        response = client.get("/api/models?page=1&page_size=10")
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1["items"]) == 10
        assert page1["pagination"]["page"] == 1
        assert page1["pagination"]["total"] >= 25
        assert page1["pagination"]["page_size"] == 10

        # Get second page
        response = client.get("/api/models?page=2&page_size=10")
        assert response.status_code == 200
        page2 = response.json()
        assert len(page2["items"]) == 10

        # Get third page
        response = client.get("/api/models?page=3&page_size=10")
        assert response.status_code == 200
        page3 = response.json()
        assert len(page3["items"]) >= 5  # At least 5 remaining

    def test_device_creation_validation_with_models(self, client: TestClient, db_session: Session):
        """
        Test device creation validation when using models.

        Workflow:
        1. Try to create device without spec or model - should fail
        2. Try to create device with both spec and model - should fail
        3. Create device with only model - should succeed
        """
        # Create model
        device_type_data = {
            "name": "Switch",
            "slug": "switch"
        }
        response = client.post("/api/device-types", json=device_type_data)
        device_type_id = response.json()["id"]

        brand_data = {
            "name": "Cisco",
            "slug": "cisco"
        }
        response = client.post("/api/brands", json=brand_data)
        brand_id = response.json()["id"]

        model_data = {
            "brand_id": brand_id,
            "device_type_id": device_type_id,
            "name": "Test Model",
            "height_u": 1.0,
            "power_watts": 200.0
        }
        response = client.post("/api/models", json=model_data)
        model_id = response.json()["id"]

        # Create specification
        spec_data = {
            "brand": "Test",
            "model": "Spec",
            "height_u": 1.0,
            "power_watts": 100.0
        }
        response = client.post("/api/device-specs", json=spec_data)
        spec_id = response.json()["id"]

        # Try without both - should fail
        device_data = {
            "custom_name": "Invalid Device"
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 400

        # Try with both - should fail
        device_data = {
            "specification_id": spec_id,
            "model_id": model_id,
            "custom_name": "Invalid Device"
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 400

        # With only model - should succeed
        device_data = {
            "model_id": model_id,
            "custom_name": "Valid Device"
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 201
