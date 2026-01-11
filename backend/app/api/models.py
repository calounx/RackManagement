"""
Models API endpoints.
Handles CRUD operations for device model specifications from catalog.
"""

from typing import List, Optional
from datetime import datetime
import re
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from ..models import Model, Brand, DeviceType, Device
from ..schemas import (
    ModelCreate,
    ModelUpdate,
    ModelResponse,
    ModelFetchRequest,
    BrandSummary,
    DeviceTypeSummary
)
from .dependencies import get_db, pagination_params

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[ModelResponse])
async def list_models(
    brand_id: Optional[int] = Query(None, description="Filter by brand ID"),
    device_type_id: Optional[int] = Query(None, description="Filter by device type ID"),
    search: Optional[str] = Query(None, description="Search models by name (case-insensitive partial match)"),
    pagination: dict = Depends(pagination_params),
    db: Session = Depends(get_db)
):
    """
    List all models with filters and pagination.

    - **brand_id**: Filter by brand ID
    - **device_type_id**: Filter by device type ID
    - **search**: Search models by name (partial match, case-insensitive)
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 1000)

    Returns models with brand and device type information, plus device count.
    """
    query = db.query(Model).options(
        joinedload(Model.brand),
        joinedload(Model.device_type)
    )

    # Apply filters
    if brand_id:
        query = query.filter(Model.brand_id == brand_id)
    if device_type_id:
        query = query.filter(Model.device_type_id == device_type_id)
    if search:
        query = query.filter(Model.name.ilike(f"%{search}%"))

    models = query.offset(pagination["skip"]).limit(pagination["limit"]).all()

    # Build response with nested objects and device_count
    result = []
    for model in models:
        device_count = len(model.devices) if model.devices else 0

        model_dict = {
            "id": model.id,
            "brand_id": model.brand_id,
            "device_type_id": model.device_type_id,
            "name": model.name,
            "variant": model.variant,
            "description": model.description,
            "release_date": model.release_date,
            "end_of_life": model.end_of_life,
            "height_u": model.height_u,
            "width_type": model.width_type,
            "depth_mm": model.depth_mm,
            "weight_kg": model.weight_kg,
            "power_watts": model.power_watts,
            "heat_output_btu": model.heat_output_btu,
            "airflow_pattern": model.airflow_pattern,
            "max_operating_temp_c": model.max_operating_temp_c,
            "typical_ports": model.typical_ports,
            "mounting_type": model.mounting_type,
            "datasheet_url": model.datasheet_url,
            "image_url": model.image_url,
            "source": model.source,
            "confidence": model.confidence,
            "fetched_at": model.fetched_at,
            "last_updated": model.last_updated,
            "device_count": device_count,
            "brand": {
                "id": model.brand.id,
                "name": model.brand.name,
                "slug": model.brand.slug,
                "logo_url": model.brand.logo_url
            },
            "device_type": {
                "id": model.device_type.id,
                "name": model.device_type.name,
                "slug": model.device_type.slug,
                "icon": model.device_type.icon,
                "color": model.device_type.color
            }
        }
        result.append(model_dict)

    return result


@router.get("/search", response_model=List[ModelResponse])
async def search_models(
    q: str = Query(..., min_length=1, description="Search query for model name"),
    db: Session = Depends(get_db)
):
    """
    Search models by name.

    - **q**: Search query (searches model name field)

    Returns models where name contains the search term (case-insensitive).
    Limited to 50 results.
    """
    search_term = f"%{q}%"
    models = db.query(Model).options(
        joinedload(Model.brand),
        joinedload(Model.device_type)
    ).filter(Model.name.ilike(search_term)).limit(50).all()

    if not models:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No models found matching '{q}'"
        )

    # Build response with nested objects and device_count
    result = []
    for model in models:
        device_count = len(model.devices) if model.devices else 0

        model_dict = {
            "id": model.id,
            "brand_id": model.brand_id,
            "device_type_id": model.device_type_id,
            "name": model.name,
            "variant": model.variant,
            "description": model.description,
            "release_date": model.release_date,
            "end_of_life": model.end_of_life,
            "height_u": model.height_u,
            "width_type": model.width_type,
            "depth_mm": model.depth_mm,
            "weight_kg": model.weight_kg,
            "power_watts": model.power_watts,
            "heat_output_btu": model.heat_output_btu,
            "airflow_pattern": model.airflow_pattern,
            "max_operating_temp_c": model.max_operating_temp_c,
            "typical_ports": model.typical_ports,
            "mounting_type": model.mounting_type,
            "datasheet_url": model.datasheet_url,
            "image_url": model.image_url,
            "source": model.source,
            "confidence": model.confidence,
            "fetched_at": model.fetched_at,
            "last_updated": model.last_updated,
            "device_count": device_count,
            "brand": {
                "id": model.brand.id,
                "name": model.brand.name,
                "slug": model.brand.slug,
                "logo_url": model.brand.logo_url
            },
            "device_type": {
                "id": model.device_type.id,
                "name": model.device_type.name,
                "slug": model.device_type.slug,
                "icon": model.device_type.icon,
                "color": model.device_type.color
            }
        }
        result.append(model_dict)

    return result


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single model by ID with details.

    - **model_id**: Model ID

    Returns model information including brand, device type, and device count.
    """
    model = db.query(Model).options(
        joinedload(Model.brand),
        joinedload(Model.device_type)
    ).filter(Model.id == model_id).first()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID {model_id} not found"
        )

    # Get device count
    device_count = len(model.devices) if model.devices else 0

    # Build response with nested objects
    response = {
        "id": model.id,
        "brand_id": model.brand_id,
        "device_type_id": model.device_type_id,
        "name": model.name,
        "variant": model.variant,
        "description": model.description,
        "release_date": model.release_date,
        "end_of_life": model.end_of_life,
        "height_u": model.height_u,
        "width_type": model.width_type,
        "depth_mm": model.depth_mm,
        "weight_kg": model.weight_kg,
        "power_watts": model.power_watts,
        "heat_output_btu": model.heat_output_btu,
        "airflow_pattern": model.airflow_pattern,
        "max_operating_temp_c": model.max_operating_temp_c,
        "typical_ports": model.typical_ports,
        "mounting_type": model.mounting_type,
        "datasheet_url": model.datasheet_url,
        "image_url": model.image_url,
        "source": model.source,
        "confidence": model.confidence,
        "fetched_at": model.fetched_at,
        "last_updated": model.last_updated,
        "device_count": device_count,
        "brand": {
            "id": model.brand.id,
            "name": model.brand.name,
            "slug": model.brand.slug,
            "logo_url": model.brand.logo_url
        },
        "device_type": {
            "id": model.device_type.id,
            "name": model.device_type.name,
            "slug": model.device_type.slug,
            "icon": model.device_type.icon,
            "color": model.device_type.color
        }
    }

    return response


@router.post("/", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model: ModelCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new model manually.

    - **brand_id**: Brand ID (required)
    - **device_type_id**: Device type ID (required)
    - **name**: Model name (required)
    - **variant**: Optional model variant (e.g., "AC", "DC", "PoE+")
    - **height_u**: Height in rack units (required)
    - **description**: Optional model description
    - All other physical, power, and connectivity fields are optional
    """
    # Validate that brand exists
    brand = db.query(Brand).filter(Brand.id == model.brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {model.brand_id} not found"
        )

    # Validate that device type exists
    device_type = db.query(DeviceType).filter(DeviceType.id == model.device_type_id).first()
    if not device_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device type with ID {model.device_type_id} not found"
        )

    # Check for duplicate brand/name/variant combination
    existing = db.query(Model).filter(
        Model.brand_id == model.brand_id,
        Model.name == model.name,
        Model.variant == model.variant
    ).first()

    if existing:
        variant_text = f" ({model.variant})" if model.variant else ""
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Model '{model.name}'{variant_text} for brand '{brand.name}' already exists"
        )

    try:
        db_model = Model(**model.model_dump())
        db.add(db_model)
        db.commit()
        db.refresh(db_model)

        # Load relationships
        db.refresh(db_model, ["brand", "device_type"])

        # Build response
        response = {
            "id": db_model.id,
            "brand_id": db_model.brand_id,
            "device_type_id": db_model.device_type_id,
            "name": db_model.name,
            "variant": db_model.variant,
            "description": db_model.description,
            "release_date": db_model.release_date,
            "end_of_life": db_model.end_of_life,
            "height_u": db_model.height_u,
            "width_type": db_model.width_type,
            "depth_mm": db_model.depth_mm,
            "weight_kg": db_model.weight_kg,
            "power_watts": db_model.power_watts,
            "heat_output_btu": db_model.heat_output_btu,
            "airflow_pattern": db_model.airflow_pattern,
            "max_operating_temp_c": db_model.max_operating_temp_c,
            "typical_ports": db_model.typical_ports,
            "mounting_type": db_model.mounting_type,
            "datasheet_url": db_model.datasheet_url,
            "image_url": db_model.image_url,
            "source": db_model.source,
            "confidence": db_model.confidence,
            "fetched_at": db_model.fetched_at,
            "last_updated": db_model.last_updated,
            "device_count": 0,
            "brand": {
                "id": db_model.brand.id,
                "name": db_model.brand.name,
                "slug": db_model.brand.slug,
                "logo_url": db_model.brand.logo_url
            },
            "device_type": {
                "id": db_model.device_type.id,
                "name": db_model.device_type.name,
                "slug": db_model.device_type.slug,
                "icon": db_model.device_type.icon,
                "color": db_model.device_type.color
            }
        }

        return response

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create model: {str(e)}"
        )


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    model_update: ModelUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing model.

    - **model_id**: Model ID to update
    - All fields are optional; only provided fields will be updated
    """
    db_model = db.query(Model).filter(Model.id == model_id).first()

    if not db_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID {model_id} not found"
        )

    update_data = model_update.model_dump(exclude_unset=True)

    # Validate brand_id if being updated
    if "brand_id" in update_data:
        brand = db.query(Brand).filter(Brand.id == update_data["brand_id"]).first()
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand with ID {update_data['brand_id']} not found"
            )

    # Validate device_type_id if being updated
    if "device_type_id" in update_data:
        device_type = db.query(DeviceType).filter(DeviceType.id == update_data["device_type_id"]).first()
        if not device_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device type with ID {update_data['device_type_id']} not found"
            )

    # Check for duplicate if name, brand_id, or variant is being updated
    if any(key in update_data for key in ["brand_id", "name", "variant"]):
        new_brand_id = update_data.get("brand_id", db_model.brand_id)
        new_name = update_data.get("name", db_model.name)
        new_variant = update_data.get("variant", db_model.variant)

        existing = db.query(Model).filter(
            Model.id != model_id,
            Model.brand_id == new_brand_id,
            Model.name == new_name,
            Model.variant == new_variant
        ).first()

        if existing:
            brand = db.query(Brand).filter(Brand.id == new_brand_id).first()
            variant_text = f" ({new_variant})" if new_variant else ""
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Model '{new_name}'{variant_text} for brand '{brand.name}' already exists"
            )

    try:
        # Update only provided fields
        for field, value in update_data.items():
            setattr(db_model, field, value)

        db.commit()
        db.refresh(db_model)
        db.refresh(db_model, ["brand", "device_type"])

        # Get device count
        device_count = len(db_model.devices) if db_model.devices else 0

        response = {
            "id": db_model.id,
            "brand_id": db_model.brand_id,
            "device_type_id": db_model.device_type_id,
            "name": db_model.name,
            "variant": db_model.variant,
            "description": db_model.description,
            "release_date": db_model.release_date,
            "end_of_life": db_model.end_of_life,
            "height_u": db_model.height_u,
            "width_type": db_model.width_type,
            "depth_mm": db_model.depth_mm,
            "weight_kg": db_model.weight_kg,
            "power_watts": db_model.power_watts,
            "heat_output_btu": db_model.heat_output_btu,
            "airflow_pattern": db_model.airflow_pattern,
            "max_operating_temp_c": db_model.max_operating_temp_c,
            "typical_ports": db_model.typical_ports,
            "mounting_type": db_model.mounting_type,
            "datasheet_url": db_model.datasheet_url,
            "image_url": db_model.image_url,
            "source": db_model.source,
            "confidence": db_model.confidence,
            "fetched_at": db_model.fetched_at,
            "last_updated": db_model.last_updated,
            "device_count": device_count,
            "brand": {
                "id": db_model.brand.id,
                "name": db_model.brand.name,
                "slug": db_model.brand.slug,
                "logo_url": db_model.brand.logo_url
            },
            "device_type": {
                "id": db_model.device_type.id,
                "name": db_model.device_type.name,
                "slug": db_model.device_type.slug,
                "icon": db_model.device_type.icon,
                "color": db_model.device_type.color
            }
        }

        return response

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update model: {str(e)}"
        )


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a model if no devices exist.

    - **model_id**: Model ID to delete

    Note: This will fail if any devices are currently using this model.
    """
    db_model = db.query(Model).filter(Model.id == model_id).first()

    if not db_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID {model_id} not found"
        )

    # Check if any devices are using this model
    device_count = db.query(func.count(Device.id)).filter(Device.model_id == model_id).scalar()
    if device_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete model: {device_count} device(s) are using it"
        )

    try:
        db.delete(db_model)
        db.commit()
        return None

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete model: {str(e)}"
        )


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug format.

    Args:
        text: Input text to slugify

    Returns:
        Slugified text (lowercase, alphanumeric + hyphens)
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)

    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r'[^a-z0-9-]', '', text)

    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)

    # Strip hyphens from start and end
    text = text.strip('-')

    return text


def infer_device_type(brand: str, model: str, db: Session) -> int:
    """
    Infer device type ID from brand and model name.

    Args:
        brand: Device brand name
        model: Device model name
        db: Database session

    Returns:
        Device type ID
    """
    # Cache device types to avoid repeated queries
    if not hasattr(infer_device_type, '_cache'):
        infer_device_type._cache = {}
        for dt in db.query(DeviceType).all():
            infer_device_type._cache[dt.slug] = dt.id

    cache = infer_device_type._cache
    combined = f"{brand} {model}".lower()

    # Check for keywords and product lines in order of specificity
    # Format: (keyword/pattern, device_type_slug)
    patterns = [
        # Switches - specific product lines first
        ('catalyst', 'switch'),      # Cisco Catalyst
        ('nexus', 'switch'),         # Cisco Nexus
        ('powerconnect', 'switch'),  # Dell PowerConnect
        ('aruba', 'switch'),         # HPE Aruba
        ('procurve', 'switch'),      # HP ProCurve
        ('switch', 'switch'),        # Generic

        # Routers
        ('asr', 'router'),           # Cisco ASR
        ('isr', 'router'),           # Cisco ISR
        ('router', 'router'),        # Generic

        # Firewalls
        ('fortigate', 'firewall'),   # Fortinet FortiGate
        ('palo alto', 'firewall'),   # Palo Alto
        ('asa', 'firewall'),         # Cisco ASA
        ('firewall', 'firewall'),    # Generic
        ('firepower', 'firewall'),   # Cisco Firepower

        # Servers
        ('poweredge', 'server'),     # Dell PowerEdge
        ('proliant', 'server'),      # HPE ProLiant
        ('primergy', 'server'),      # Fujitsu Primergy
        ('thinkserver', 'server'),   # Lenovo ThinkServer
        ('server', 'server'),        # Generic

        # Storage
        ('powerstore', 'storage'),   # Dell PowerStore
        ('powervault', 'storage'),   # Dell PowerVault
        ('nimble', 'storage'),       # HPE Nimble
        ('compellent', 'storage'),   # Dell Compellent
        ('storage', 'storage'),      # Generic
        ('san', 'storage'),          # Storage Area Network
        ('nas', 'storage'),          # Network Attached Storage

        # PDUs
        ('pdu', 'pdu'),
        ('power distribution', 'pdu'),
        ('rack pdu', 'pdu'),

        # UPS
        ('ups', 'ups'),
        ('uninterruptible', 'ups'),
        ('smart-ups', 'ups'),        # APC Smart-UPS

        # Patch Panels
        ('patch panel', 'patch_panel'),
        ('patch', 'patch_panel'),
    ]

    for pattern, slug in patterns:
        if pattern in combined:
            return cache.get(slug, cache['other'])

    # Default to 'other'
    return cache['other']


@router.post("/fetch", response_model=ModelResponse)
async def fetch_model_specs(
    request: ModelFetchRequest,
    db: Session = Depends(get_db)
):
    """
    Fetch model specifications from manufacturer websites or datasheets.

    This endpoint:
    - Gets or creates the brand if it doesn't exist
    - Checks if the model already exists and returns it if found
    - Uses the SpecFetcherFactory to get the appropriate manufacturer fetcher
    - Fetches specifications using existing fetcher infrastructure
    - Infers device type if not provided
    - Creates a Model record with all fetched specifications
    - Returns ModelResponse with full relationships

    **Request Body:**
    - brand: Brand name (e.g., "Cisco", "Dell")
    - model: Model name (e.g., "Catalyst 9300", "PowerEdge R740")
    - device_type_id: Optional device type ID (will be inferred if not provided)

    **Returns:**
    - Full model information with brand and device type details

    **Errors:**
    - 404: Model specifications not found
    - 400: Invalid request or validation error
    - 500: Internal server error
    """
    try:
        # 1. Get or create brand
        brand = db.query(Brand).filter(
            func.lower(Brand.name) == request.brand.lower()
        ).first()

        if not brand:
            logger.info(f"Brand '{request.brand}' not found, creating new brand")
            brand = Brand(
                name=request.brand.strip(),
                slug=slugify(request.brand),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(brand)
            db.flush()  # Get the ID without committing

        # 2. Check if model already exists
        existing = db.query(Model).filter(
            Model.brand_id == brand.id,
            func.lower(Model.name) == request.model.lower()
        ).first()

        if existing:
            logger.info(f"Model '{request.model}' from '{request.brand}' already exists, returning existing")
            # Load relationships
            db.refresh(existing, ["brand", "device_type"])

            # Get device count
            device_count = len(existing.devices) if existing.devices else 0

            # Build response
            response = {
                "id": existing.id,
                "brand_id": existing.brand_id,
                "device_type_id": existing.device_type_id,
                "name": existing.name,
                "variant": existing.variant,
                "description": existing.description,
                "release_date": existing.release_date,
                "end_of_life": existing.end_of_life,
                "height_u": existing.height_u,
                "width_type": existing.width_type,
                "depth_mm": existing.depth_mm,
                "weight_kg": existing.weight_kg,
                "power_watts": existing.power_watts,
                "heat_output_btu": existing.heat_output_btu,
                "airflow_pattern": existing.airflow_pattern,
                "max_operating_temp_c": existing.max_operating_temp_c,
                "typical_ports": existing.typical_ports,
                "mounting_type": existing.mounting_type,
                "datasheet_url": existing.datasheet_url,
                "image_url": existing.image_url,
                "source": existing.source,
                "confidence": existing.confidence,
                "fetched_at": existing.fetched_at,
                "last_updated": existing.last_updated,
                "device_count": device_count,
                "brand": {
                    "id": existing.brand.id,
                    "name": existing.brand.name,
                    "slug": existing.brand.slug,
                    "logo_url": existing.brand.logo_url
                },
                "device_type": {
                    "id": existing.device_type.id,
                    "name": existing.device_type.name,
                    "slug": existing.device_type.slug,
                    "icon": existing.device_type.icon,
                    "color": existing.device_type.color
                }
            }
            return response

        # 3. Fetch specs using existing fetcher infrastructure
        logger.info(f"Fetching specs for '{request.brand} {request.model}' from manufacturer")

        from ..fetchers.factory import get_default_factory

        factory = get_default_factory()
        fetcher = factory.get_fetcher(request.brand)

        # Fetch with cache to avoid repeated requests
        device_spec = await fetcher.fetch_with_cache(request.brand, request.model)

        if not device_spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model specifications not found for '{request.brand} {request.model}'. "
                       f"The manufacturer website may not have this model or it may not be supported yet."
            )

        # 4. Infer device type if not provided
        device_type_id = request.device_type_id
        if not device_type_id:
            device_type_id = infer_device_type(request.brand, request.model, db)
            logger.info(f"Inferred device type ID: {device_type_id}")

        # Validate device type exists
        device_type = db.query(DeviceType).filter(DeviceType.id == device_type_id).first()
        if not device_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device type with ID {device_type_id} not found"
            )

        # 5. Create model with fetched specifications
        logger.info(f"Creating model '{device_spec.model}' from fetched specs")

        # Convert enum values to strings
        width_type_str = device_spec.width_type.value if device_spec.width_type else None
        airflow_str = device_spec.airflow_pattern.value if device_spec.airflow_pattern else None
        confidence_str = device_spec.confidence.value if hasattr(device_spec.confidence, 'value') else str(device_spec.confidence)

        model = Model(
            brand_id=brand.id,
            device_type_id=device_type_id,
            name=device_spec.model,
            variant=device_spec.variant,
            height_u=device_spec.height_u,
            width_type=width_type_str,
            depth_mm=device_spec.depth_mm,
            weight_kg=device_spec.weight_kg,
            power_watts=device_spec.power_watts,
            heat_output_btu=device_spec.heat_output_btu,
            airflow_pattern=airflow_str,
            max_operating_temp_c=device_spec.max_operating_temp_c,
            typical_ports=device_spec.typical_ports,
            mounting_type=device_spec.mounting_type,
            datasheet_url=device_spec.source_url,
            source="web_fetched",
            confidence=confidence_str,
            fetched_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        # Load relationships
        db.refresh(model, ["brand", "device_type"])

        logger.info(f"Successfully created model ID {model.id}")

        # 6. Build response with full relationships
        response = {
            "id": model.id,
            "brand_id": model.brand_id,
            "device_type_id": model.device_type_id,
            "name": model.name,
            "variant": model.variant,
            "description": model.description,
            "release_date": model.release_date,
            "end_of_life": model.end_of_life,
            "height_u": model.height_u,
            "width_type": model.width_type,
            "depth_mm": model.depth_mm,
            "weight_kg": model.weight_kg,
            "power_watts": model.power_watts,
            "heat_output_btu": model.heat_output_btu,
            "airflow_pattern": model.airflow_pattern,
            "max_operating_temp_c": model.max_operating_temp_c,
            "typical_ports": model.typical_ports,
            "mounting_type": model.mounting_type,
            "datasheet_url": model.datasheet_url,
            "image_url": model.image_url,
            "source": model.source,
            "confidence": model.confidence,
            "fetched_at": model.fetched_at,
            "last_updated": model.last_updated,
            "device_count": 0,
            "brand": {
                "id": model.brand.id,
                "name": model.brand.name,
                "slug": model.brand.slug,
                "logo_url": model.brand.logo_url
            },
            "device_type": {
                "id": model.device_type.id,
                "name": model.device_type.name,
                "slug": model.device_type.slug,
                "icon": model.device_type.icon,
                "color": model.device_type.color
            }
        }

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching model specs: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch model specifications: {str(e)}"
        )


@router.post("/import", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def bulk_import_from_dcim(
    dcim_connection_id: int = Query(..., description="DCIM connection ID to import from"),
    device_type_filter: Optional[str] = Query(None, description="Filter by device type (optional)"),
    brand_filter: Optional[str] = Query(None, description="Filter by brand (optional)")
):
    """
    Bulk import models from external DCIM system.

    TODO: Implement in Phase 7 - DCIM integration for bulk model import.

    This endpoint will:
    - Connect to specified DCIM system (NetBox, RackTables, etc.)
    - Fetch device type catalog from DCIM
    - Map DCIM manufacturers to brands (create if needed)
    - Map DCIM device types to our device types
    - Import model specifications with all available fields
    - Handle conflicts and duplicates intelligently
    - Return import summary with success/failure counts

    Currently returns 501 Not Implemented.
    """
    return {
        "message": "Bulk model import from DCIM not yet implemented. Coming in Phase 7.",
        "dcim_connection_id": dcim_connection_id,
        "device_type_filter": device_type_filter,
        "brand_filter": brand_filter,
        "status": "not_implemented"
    }
