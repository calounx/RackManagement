"""
Device Types API endpoints.
Handles CRUD operations for device type categories.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import DeviceType, Model
from ..schemas import (
    DeviceTypeCreate,
    DeviceTypeUpdate,
    DeviceTypeResponse
)
from .dependencies import get_db, pagination_params

router = APIRouter()


@router.get("/", response_model=List[DeviceTypeResponse])
async def list_device_types(
    pagination: dict = Depends(pagination_params),
    db: Session = Depends(get_db)
):
    """
    List all device types with model counts and pagination.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 1000)

    Returns device types with the count of models for each type.
    """
    query = db.query(
        DeviceType,
        func.count(Model.id).label('model_count')
    ).outerjoin(Model).group_by(DeviceType.id)

    device_types_with_counts = query.offset(pagination["skip"]).limit(pagination["limit"]).all()

    # Convert to response format with model_count
    result = []
    for device_type, model_count in device_types_with_counts:
        device_type_dict = {
            "id": device_type.id,
            "name": device_type.name,
            "slug": device_type.slug,
            "icon": device_type.icon,
            "description": device_type.description,
            "color": device_type.color,
            "created_at": device_type.created_at,
            "updated_at": device_type.updated_at,
            "model_count": model_count
        }
        result.append(device_type_dict)

    return result


@router.get("/{type_id}", response_model=DeviceTypeResponse)
async def get_device_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single device type by ID with details.

    - **type_id**: Device type ID

    Returns device type information including model count.
    """
    device_type = db.query(DeviceType).filter(DeviceType.id == type_id).first()

    if not device_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device type with ID {type_id} not found"
        )

    # Get model count
    model_count = db.query(func.count(Model.id)).filter(Model.device_type_id == type_id).scalar()

    # Build response with model_count
    response = {
        "id": device_type.id,
        "name": device_type.name,
        "slug": device_type.slug,
        "icon": device_type.icon,
        "description": device_type.description,
        "color": device_type.color,
        "created_at": device_type.created_at,
        "updated_at": device_type.updated_at,
        "model_count": model_count
    }

    return response


@router.post("/", response_model=DeviceTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_device_type(
    device_type: DeviceTypeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new device type.

    TODO: Add admin-only authentication when auth system is implemented.

    - **name**: Device type name (required, e.g., "Switch", "Server")
    - **slug**: URL-friendly identifier (required, unique)
    - **icon**: Optional emoji or unicode character for UI
    - **description**: Optional description of the device type
    - **color**: Optional UI color code (e.g., "#FF5733")
    """
    # Check for duplicate name
    existing_name = db.query(DeviceType).filter(DeviceType.name == device_type.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device type with name '{device_type.name}' already exists"
        )

    # Check for duplicate slug
    existing_slug = db.query(DeviceType).filter(DeviceType.slug == device_type.slug).first()
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device type with slug '{device_type.slug}' already exists"
        )

    try:
        db_device_type = DeviceType(**device_type.model_dump())
        db.add(db_device_type)
        db.commit()
        db.refresh(db_device_type)

        # Return with model_count = 0 for new type
        response = {
            "id": db_device_type.id,
            "name": db_device_type.name,
            "slug": db_device_type.slug,
            "icon": db_device_type.icon,
            "description": db_device_type.description,
            "color": db_device_type.color,
            "created_at": db_device_type.created_at,
            "updated_at": db_device_type.updated_at,
            "model_count": 0
        }

        return response

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create device type: {str(e)}"
        )


@router.put("/{type_id}", response_model=DeviceTypeResponse)
async def update_device_type(
    type_id: int,
    device_type_update: DeviceTypeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing device type.

    TODO: Add admin-only authentication when auth system is implemented.

    - **type_id**: Device type ID to update
    - All fields are optional; only provided fields will be updated
    """
    db_device_type = db.query(DeviceType).filter(DeviceType.id == type_id).first()

    if not db_device_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device type with ID {type_id} not found"
        )

    # Check for name conflict if name is being updated
    update_data = device_type_update.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != db_device_type.name:
        existing = db.query(DeviceType).filter(DeviceType.name == update_data["name"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Device type with name '{update_data['name']}' already exists"
            )

    # Check for slug conflict if slug is being updated
    if "slug" in update_data and update_data["slug"] != db_device_type.slug:
        existing = db.query(DeviceType).filter(DeviceType.slug == update_data["slug"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Device type with slug '{update_data['slug']}' already exists"
            )

    try:
        # Update only provided fields
        for field, value in update_data.items():
            setattr(db_device_type, field, value)

        db.commit()
        db.refresh(db_device_type)

        # Get model count
        model_count = db.query(func.count(Model.id)).filter(Model.device_type_id == type_id).scalar()

        response = {
            "id": db_device_type.id,
            "name": db_device_type.name,
            "slug": db_device_type.slug,
            "icon": db_device_type.icon,
            "description": db_device_type.description,
            "color": db_device_type.color,
            "created_at": db_device_type.created_at,
            "updated_at": db_device_type.updated_at,
            "model_count": model_count
        }

        return response

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update device type: {str(e)}"
        )


@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a device type if no models exist.

    - **type_id**: Device type ID to delete

    Note: This will fail if any models are currently using this device type.
    """
    db_device_type = db.query(DeviceType).filter(DeviceType.id == type_id).first()

    if not db_device_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device type with ID {type_id} not found"
        )

    # Check if any models are using this device type
    model_count = db.query(func.count(Model.id)).filter(Model.device_type_id == type_id).scalar()
    if model_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete device type: {model_count} model(s) are using it"
        )

    try:
        db.delete(db_device_type)
        db.commit()
        return None

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete device type: {str(e)}"
        )
