"""
Brands API endpoints.
Handles CRUD operations for device manufacturers and brands.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from ..models import Brand, Model, DeviceType
from ..schemas import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    ModelResponse,
    BrandSummary,
    DeviceTypeSummary
)
from .dependencies import get_db, pagination_params

router = APIRouter()


@router.get("/", response_model=List[BrandResponse])
async def list_brands(
    search: Optional[str] = Query(None, description="Search brands by name (case-insensitive partial match)"),
    device_type: Optional[int] = Query(None, description="Filter by device type ID"),
    pagination: dict = Depends(pagination_params),
    db: Session = Depends(get_db)
):
    """
    List all brands with filters and pagination.

    - **search**: Search brands by name (partial match, case-insensitive)
    - **device_type**: Filter by device type ID (shows brands that have models of this type)
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 1000)

    Returns brands with the count of models for each brand.
    """
    query = db.query(
        Brand,
        func.count(Model.id).label('model_count')
    ).outerjoin(Model).group_by(Brand.id)

    # Apply search filter
    if search:
        query = query.filter(Brand.name.ilike(f"%{search}%"))

    # Apply device_type filter
    if device_type:
        # Filter brands that have at least one model of this device type
        query = query.having(
            func.count(func.nullif(Model.device_type_id != device_type, True)) > 0
        )

    brands_with_counts = query.offset(pagination["skip"]).limit(pagination["limit"]).all()

    # Convert to response format with model_count
    result = []
    for brand, model_count in brands_with_counts:
        brand_dict = {
            "id": brand.id,
            "name": brand.name,
            "slug": brand.slug,
            "website": brand.website,
            "support_url": brand.support_url,
            "logo_url": brand.logo_url,
            "description": brand.description,
            "founded_year": brand.founded_year,
            "headquarters": brand.headquarters,
            "last_fetched_at": brand.last_fetched_at,
            "fetch_confidence": brand.fetch_confidence,
            "fetch_source": brand.fetch_source,
            "created_at": brand.created_at,
            "updated_at": brand.updated_at,
            "model_count": model_count
        }
        result.append(brand_dict)

    return result


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single brand by ID with details.

    - **brand_id**: Brand ID

    Returns brand information including model count.
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Get model count
    model_count = db.query(func.count(Model.id)).filter(Model.brand_id == brand_id).scalar()

    # Build response with model_count
    response = {
        "id": brand.id,
        "name": brand.name,
        "slug": brand.slug,
        "website": brand.website,
        "support_url": brand.support_url,
        "logo_url": brand.logo_url,
        "description": brand.description,
        "founded_year": brand.founded_year,
        "headquarters": brand.headquarters,
        "last_fetched_at": brand.last_fetched_at,
        "fetch_confidence": brand.fetch_confidence,
        "fetch_source": brand.fetch_source,
        "created_at": brand.created_at,
        "updated_at": brand.updated_at,
        "model_count": model_count
    }

    return response


@router.get("/{brand_id}/models", response_model=List[ModelResponse])
async def list_brand_models(
    brand_id: int,
    pagination: dict = Depends(pagination_params),
    db: Session = Depends(get_db)
):
    """
    List all models for a specific brand.

    - **brand_id**: Brand ID
    - **skip**: Number of records to skip
    - **limit**: Maximum records to return

    Returns all models associated with this brand, including brand and device type details.
    """
    # Check if brand exists
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Query models with relationships
    models = db.query(Model).options(
        joinedload(Model.brand),
        joinedload(Model.device_type)
    ).filter(Model.brand_id == brand_id).offset(pagination["skip"]).limit(pagination["limit"]).all()

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


@router.post("/", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand: BrandCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new brand manually.

    - **name**: Brand name (required, unique)
    - **slug**: URL-friendly identifier (required, unique)
    - **website**: Optional official website URL
    - **support_url**: Optional support/documentation URL
    - **logo_url**: Optional brand logo image URL
    - **description**: Optional brand description
    - **founded_year**: Optional year the company was founded
    - **headquarters**: Optional headquarters location
    """
    # Check for duplicate name
    existing_name = db.query(Brand).filter(Brand.name == brand.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Brand with name '{brand.name}' already exists"
        )

    # Check for duplicate slug
    existing_slug = db.query(Brand).filter(Brand.slug == brand.slug).first()
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Brand with slug '{brand.slug}' already exists"
        )

    try:
        db_brand = Brand(**brand.model_dump())
        db.add(db_brand)
        db.commit()
        db.refresh(db_brand)

        # Return with model_count = 0 for new brand
        response = {
            "id": db_brand.id,
            "name": db_brand.name,
            "slug": db_brand.slug,
            "website": db_brand.website,
            "support_url": db_brand.support_url,
            "logo_url": db_brand.logo_url,
            "description": db_brand.description,
            "founded_year": db_brand.founded_year,
            "headquarters": db_brand.headquarters,
            "last_fetched_at": db_brand.last_fetched_at,
            "fetch_confidence": db_brand.fetch_confidence,
            "fetch_source": db_brand.fetch_source,
            "created_at": db_brand.created_at,
            "updated_at": db_brand.updated_at,
            "model_count": 0
        }

        return response

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create brand: {str(e)}"
        )


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: int,
    brand_update: BrandUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing brand.

    - **brand_id**: Brand ID to update
    - All fields are optional; only provided fields will be updated
    """
    db_brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not db_brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Check for name conflict if name is being updated
    update_data = brand_update.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != db_brand.name:
        existing = db.query(Brand).filter(Brand.name == update_data["name"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Brand with name '{update_data['name']}' already exists"
            )

    # Check for slug conflict if slug is being updated
    if "slug" in update_data and update_data["slug"] != db_brand.slug:
        existing = db.query(Brand).filter(Brand.slug == update_data["slug"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Brand with slug '{update_data['slug']}' already exists"
            )

    try:
        # Update only provided fields
        for field, value in update_data.items():
            setattr(db_brand, field, value)

        db.commit()
        db.refresh(db_brand)

        # Get model count
        model_count = db.query(func.count(Model.id)).filter(Model.brand_id == brand_id).scalar()

        response = {
            "id": db_brand.id,
            "name": db_brand.name,
            "slug": db_brand.slug,
            "website": db_brand.website,
            "support_url": db_brand.support_url,
            "logo_url": db_brand.logo_url,
            "description": db_brand.description,
            "founded_year": db_brand.founded_year,
            "headquarters": db_brand.headquarters,
            "last_fetched_at": db_brand.last_fetched_at,
            "fetch_confidence": db_brand.fetch_confidence,
            "fetch_source": db_brand.fetch_source,
            "created_at": db_brand.created_at,
            "updated_at": db_brand.updated_at,
            "model_count": model_count
        }

        return response

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update brand: {str(e)}"
        )


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a brand if no models exist.

    - **brand_id**: Brand ID to delete

    Note: This will fail if any models are currently using this brand.
    """
    db_brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not db_brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Check if any models are using this brand
    model_count = db.query(func.count(Model.id)).filter(Model.brand_id == brand_id).scalar()
    if model_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete brand: {model_count} model(s) are using it"
        )

    try:
        db.delete(db_brand)
        db.commit()
        return None

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete brand: {str(e)}"
        )


@router.post("/fetch", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def fetch_brand_from_web(
    brand_name: str = Query(..., description="Brand name to fetch information for")
):
    """
    Fetch brand information from web sources (Wikipedia, official website, etc.).

    TODO: Implement in Phase 3 - Web fetching for brand information.

    This endpoint will:
    - Search for brand information on Wikipedia and other sources
    - Extract company details (founded year, headquarters, website, etc.)
    - Create or update brand entry with fetched data
    - Return confidence level for the fetched information

    Currently returns 501 Not Implemented.
    """
    return {
        "message": "Brand web fetching not yet implemented. Coming in Phase 3.",
        "requested_brand": brand_name,
        "status": "not_implemented"
    }


@router.post("/validate", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def validate_brand_against_dcim(
    brand_id: int = Query(..., description="Brand ID to validate"),
    dcim_connection_id: int = Query(..., description="DCIM connection ID to validate against")
):
    """
    Validate brand against external DCIM system.

    TODO: Implement in Phase 7 - DCIM integration for brand validation.

    This endpoint will:
    - Connect to specified DCIM system (NetBox, RackTables, etc.)
    - Check if brand exists in DCIM
    - Compare brand information between systems
    - Suggest updates or corrections
    - Return validation results and recommendations

    Currently returns 501 Not Implemented.
    """
    return {
        "message": "Brand DCIM validation not yet implemented. Coming in Phase 7.",
        "brand_id": brand_id,
        "dcim_connection_id": dcim_connection_id,
        "status": "not_implemented"
    }
