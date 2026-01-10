"""
Device Specifications API endpoints.
Handles CRUD operations for device specifications.
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..models import DeviceSpecification, SourceType as ModelSourceType
from ..schemas import (
    DeviceSpecificationCreate,
    DeviceSpecificationUpdate,
    DeviceSpecificationResponse,
    DeviceSpecificationFetch,
    WidthType,
    SourceType
)
from .dependencies import get_db, pagination_params
from ..fetchers.factory import SpecFetcherFactory
from ..exceptions import ResourceNotFoundError, ExternalServiceError
from ..utils.retry import retry_on_db_error
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize fetcher factory
fetcher_factory = SpecFetcherFactory()


@router.get("/", response_model=List[DeviceSpecificationResponse])
async def list_device_specs(
    brand: Optional[str] = Query(None, description="Filter by brand (case-insensitive partial match)"),
    model: Optional[str] = Query(None, description="Filter by model (case-insensitive partial match)"),
    width_type: Optional[WidthType] = Query(None, description="Filter by width type"),
    source: Optional[SourceType] = Query(None, description="Filter by source type"),
    pagination: dict = Depends(pagination_params),
    db: Session = Depends(get_db)
):
    """
    List all device specifications with optional filtering and pagination.

    - **brand**: Filter by brand name (partial match, case-insensitive)
    - **model**: Filter by model name (partial match, case-insensitive)
    - **width_type**: Filter by rack width type (11", 18", 19", 23")
    - **source**: Filter by data source (manufacturer, user, web)
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 1000)
    """
    query = db.query(DeviceSpecification)

    if brand:
        query = query.filter(DeviceSpecification.brand.ilike(f"%{brand}%"))
    if model:
        query = query.filter(DeviceSpecification.model.ilike(f"%{model}%"))
    if width_type:
        query = query.filter(DeviceSpecification.width_type == width_type)
    if source:
        query = query.filter(DeviceSpecification.source == source)

    specs = query.offset(pagination["skip"]).limit(pagination["limit"]).all()
    return specs


@router.get("/search", response_model=List[DeviceSpecificationResponse])
async def search_device_specs(
    q: str = Query(..., min_length=1, description="Search query for brand or model"),
    db: Session = Depends(get_db)
):
    """
    Search device specifications by brand or model name.

    - **q**: Search query (searches both brand and model fields)

    Returns specifications where brand OR model contains the search term (case-insensitive).
    """
    search_term = f"%{q}%"
    specs = db.query(DeviceSpecification).filter(
        or_(
            DeviceSpecification.brand.ilike(search_term),
            DeviceSpecification.model.ilike(search_term)
        )
    ).limit(50).all()

    if not specs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No device specifications found matching '{q}'"
        )

    return specs


@router.get("/{spec_id}", response_model=DeviceSpecificationResponse)
async def get_device_spec(
    spec_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single device specification by ID.

    - **spec_id**: Device specification ID
    """
    spec = db.query(DeviceSpecification).filter(DeviceSpecification.id == spec_id).first()

    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device specification with ID {spec_id} not found"
        )

    return spec


@router.post("/", response_model=DeviceSpecificationResponse, status_code=status.HTTP_201_CREATED)
async def create_device_spec(
    spec: DeviceSpecificationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new device specification.

    - **brand**: Device brand/manufacturer (required)
    - **model**: Device model number (required)
    - **height_u**: Height in rack units (required)
    - **width_type**: Rack width compatibility (11", 18", 19", 23")
    - **depth_mm**: Depth in millimeters
    - **weight_kg**: Weight in kilograms
    - **power_watts**: Power consumption in watts
    - **heat_output_btu**: Heat output in BTU (auto-calculated from watts if not provided)
    """
    # Check for duplicate brand/model combination
    existing = db.query(DeviceSpecification).filter(
        DeviceSpecification.brand == spec.brand,
        DeviceSpecification.model == spec.model,
        DeviceSpecification.variant == spec.variant
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device specification for {spec.brand} {spec.model}" +
                   (f" ({spec.variant})" if spec.variant else "") +
                   " already exists"
        )

    db_spec = DeviceSpecification(**spec.model_dump())
    db.add(db_spec)
    db.commit()
    db.refresh(db_spec)

    return db_spec


@router.put("/{spec_id}", response_model=DeviceSpecificationResponse)
async def update_device_spec(
    spec_id: int,
    spec_update: DeviceSpecificationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing device specification.

    - **spec_id**: Device specification ID to update
    - All fields are optional; only provided fields will be updated
    """
    db_spec = db.query(DeviceSpecification).filter(DeviceSpecification.id == spec_id).first()

    if not db_spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device specification with ID {spec_id} not found"
        )

    # Update only provided fields
    update_data = spec_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_spec, field, value)

    db.commit()
    db.refresh(db_spec)

    return db_spec


@router.delete("/{spec_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_spec(
    spec_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a device specification.

    - **spec_id**: Device specification ID to delete

    Note: This will fail if any devices are currently using this specification.
    """
    db_spec = db.query(DeviceSpecification).filter(DeviceSpecification.id == spec_id).first()

    if not db_spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device specification with ID {spec_id} not found"
        )

    # Check if any devices are using this specification
    if db_spec.devices:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete specification: {len(db_spec.devices)} device(s) are using it"
        )

    db.delete(db_spec)
    db.commit()

    return None


@router.post("/fetch", response_model=DeviceSpecificationResponse, status_code=status.HTTP_201_CREATED)
async def fetch_device_spec(
    spec_request: DeviceSpecificationFetch,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Automatically fetch device specification from manufacturer websites.

    This endpoint:
    1. Checks if specification already exists in database
    2. Attempts to fetch from manufacturer website if not found
    3. Saves fetched specification to database
    4. Returns the specification with confidence level

    - **brand**: Device brand/manufacturer (e.g., "Cisco", "Ubiquiti")
    - **model**: Device model number (e.g., "Catalyst 2960-48TT-L")

    The fetcher will:
    - Use manufacturer-specific strategies for high-quality data
    - Parse PDF datasheets and HTML specification pages
    - Validate extracted data
    - Assign confidence levels (HIGH, MEDIUM, LOW)
    - Cache results to avoid repeated fetches
    """
    if not settings.SPEC_FETCH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Automatic spec fetching is currently disabled"
        )

    # Check if spec already exists
    existing = db.query(DeviceSpecification).filter(
        DeviceSpecification.brand.ilike(spec_request.brand),
        DeviceSpecification.model.ilike(spec_request.model)
    ).first()

    if existing:
        logger.info(f"Spec already exists for {spec_request.brand} {spec_request.model}")
        return existing

    # Get appropriate fetcher for this manufacturer
    fetcher = fetcher_factory.get_fetcher(spec_request.brand)

    try:
        # Fetch specification
        logger.info(f"Fetching spec for {spec_request.brand} {spec_request.model}")
        device_spec = await fetcher.fetch_with_cache(spec_request.brand, spec_request.model)

        if not device_spec:
            raise ResourceNotFoundError(
                resource="Device specification",
                identifier=f"{spec_request.brand} {spec_request.model}"
            )

        # Create database entry
        spec_data = device_spec.to_dict()
        spec_data.update({
            "source": ModelSourceType.WEB_FETCHED,
            "fetched_at": datetime.utcnow()
        })

        db_spec = DeviceSpecification(**spec_data)
        db.add(db_spec)
        db.commit()
        db.refresh(db_spec)

        logger.info(
            f"Successfully fetched and saved spec for {spec_request.brand} {spec_request.model} "
            f"with confidence {device_spec.confidence}"
        )

        return db_spec

    except ExternalServiceError as e:
        logger.error(f"External service error fetching spec: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch specification from manufacturer: {e.message}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching spec: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch specification: {str(e)}"
        )


@router.get("/fetch/supported-manufacturers")
async def get_supported_manufacturers():
    """
    Get list of manufacturers with dedicated spec fetchers.

    Returns manufacturers that have specific fetching implementations
    with higher-quality data extraction. Other manufacturers will use
    generic fetching strategies.
    """
    return {
        "supported_manufacturers": fetcher_factory.get_supported_manufacturers(),
        "total_count": len(fetcher_factory.get_supported_manufacturers()),
        "generic_fallback_available": True
    }
