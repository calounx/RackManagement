"""
Brands API endpoints.
Handles CRUD operations for device manufacturers and brands.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from pathlib import Path
from uuid import uuid4
import os

from ..models import Brand, Model, DeviceType
from ..schemas import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    ModelResponse,
    BrandSummary,
    DeviceTypeSummary,
    BrandFetchRequest,
    BrandInfoResponse
)
from .dependencies import get_db, pagination_params
from ..config import settings
from ..fetchers.wikipedia import WikipediaFetcher
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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


@router.post("/{brand_id}/logo", response_model=BrandResponse)
async def upload_brand_logo(
    brand_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a brand logo image.

    - **brand_id**: Brand ID to upload logo for
    - **file**: Image file to upload (.png, .jpg, .jpeg, .svg, .webp)

    File size limit: 5MB
    Returns updated brand with new logo_url.
    """
    # Check if brand exists
    db_brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not db_brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_LOGO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed formats: {', '.join(settings.ALLOWED_LOGO_FORMATS)}"
        )

    # Read file content and validate size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > settings.MAX_LOGO_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_LOGO_SIZE_MB}MB"
        )

    try:
        # Ensure upload directory exists
        upload_dir = Path(settings.BRAND_LOGOS_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Delete old logo file if exists
        if db_brand.logo_url and db_brand.logo_url.startswith("/uploads/brand_logos/"):
            old_filename = db_brand.logo_url.split("/")[-1]
            old_file_path = upload_dir / old_filename
            if old_file_path.exists():
                old_file_path.unlink()

        # Generate unique filename: slug_uuid.ext
        unique_filename = f"{db_brand.slug}_{uuid4().hex[:8]}{file_ext}"
        file_path = upload_dir / unique_filename

        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Update brand logo_url
        db_brand.logo_url = f"/uploads/brand_logos/{unique_filename}"
        db.commit()
        db.refresh(db_brand)

        # Get model count
        model_count = db.query(func.count(Model.id)).filter(Model.brand_id == brand_id).scalar()

        # Build response
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
        # Clean up file if it was created
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload logo: {str(e)}"
        )


@router.delete("/{brand_id}/logo", response_model=BrandResponse)
async def delete_brand_logo(
    brand_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove a brand's logo.

    - **brand_id**: Brand ID to remove logo from

    Deletes the logo file and clears the logo_url field.
    """
    db_brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not db_brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    try:
        # Delete logo file if exists
        if db_brand.logo_url and db_brand.logo_url.startswith("/uploads/brand_logos/"):
            filename = db_brand.logo_url.split("/")[-1]
            file_path = Path(settings.BRAND_LOGOS_DIR) / filename
            if file_path.exists():
                file_path.unlink()

        # Clear logo_url
        db_brand.logo_url = None
        db.commit()
        db.refresh(db_brand)

        # Get model count
        model_count = db.query(func.count(Model.id)).filter(Model.brand_id == brand_id).scalar()

        # Build response
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
            detail=f"Failed to delete logo: {str(e)}"
        )


@router.post("/fetch", response_model=BrandInfoResponse, status_code=status.HTTP_200_OK)
async def fetch_brand_from_web(
    request: BrandFetchRequest,
    db: Session = Depends(get_db)
):
    """
    Fetch brand information from Wikipedia and other web sources.

    This endpoint:
    - Searches for brand information on Wikipedia
    - Extracts company details (founded year, headquarters, website, etc.)
    - Checks if brand already exists in database
    - Returns fetched information for preview (does NOT create the brand)
    - User can edit and confirm before saving via regular create endpoint

    **Phase 3 Implementation - Web Fetching**
    """
    brand_name = request.brand_name.strip()

    # Step 1: Check if brand already exists
    existing_brand = db.query(Brand).filter(
        func.lower(Brand.name) == brand_name.lower()
    ).first()

    if existing_brand:
        logger.info(f"Brand '{brand_name}' already exists in database")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Brand '{existing_brand.name}' already exists in the database"
        )

    # Step 2: Fetch from Wikipedia
    logger.info(f"Fetching brand information for '{brand_name}' from Wikipedia")
    fetcher = WikipediaFetcher()

    try:
        brand_info = await fetcher.fetch_brand_info(brand_name)

        if not brand_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand '{brand_name}' not found on Wikipedia. Please add the brand manually or try a different name."
            )

        # Return fetched info for preview (not saved to database yet)
        brand_data = brand_info.to_dict()
        logger.info(f"Successfully fetched Wikipedia data for: {brand_name}")

        return BrandInfoResponse(
            name=brand_data["name"],
            slug=brand_data["slug"],
            website=brand_data.get("website"),
            description=brand_data.get("description"),
            founded_year=brand_data.get("founded_year"),
            headquarters=brand_data.get("headquarters"),
            logo_url=brand_data.get("logo_url"),
            fetch_confidence=brand_data.get("fetch_confidence"),
            fetch_source=brand_data.get("fetch_source", "wikipedia")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching brand from Wikipedia: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch brand information: {str(e)}"
        )
    finally:
        await fetcher.close()


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
