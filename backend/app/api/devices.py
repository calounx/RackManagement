"""
Devices API endpoints.
Handles CRUD operations for user devices and quick-add functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from ..models import Device, DeviceSpecification, RackPosition, Connection, Model
from ..schemas import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceQuickAdd,
    DeviceFromModel,
    AccessFrequency
)
from .dependencies import get_db, pagination_params

router = APIRouter()


@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    specification_id: Optional[int] = Query(None, description="Filter by specification ID"),
    access_frequency: Optional[AccessFrequency] = Query(None, description="Filter by access frequency"),
    pagination: dict = Depends(pagination_params),
    db: Session = Depends(get_db)
):
    """
    List all user devices with optional filtering and pagination.

    - **specification_id**: Filter devices by their specification
    - **access_frequency**: Filter by how often the device is accessed
    - **skip**: Number of records to skip
    - **limit**: Maximum records to return

    Includes device specification details in the response.
    """
    query = db.query(Device).options(joinedload(Device.specification))

    if specification_id:
        query = query.filter(Device.specification_id == specification_id)
    if access_frequency:
        query = query.filter(Device.access_frequency == access_frequency)

    devices = query.offset(pagination["skip"]).limit(pagination["limit"]).all()
    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single device by ID with specification details.

    - **device_id**: Device ID
    """
    device = db.query(Device).options(
        joinedload(Device.specification)
    ).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    return device


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new device from an existing device specification or catalog model.

    - **specification_id**: ID of the device specification to use (legacy, optional)
    - **model_id**: ID of the catalog model to use (new, optional)
    - **custom_name**: Optional custom name for this device instance
    - **serial_number**: Optional serial number
    - **access_frequency**: How often the device is accessed (default: MEDIUM)
    - **notes**: Optional notes about the device

    Note: Either specification_id OR model_id must be provided.
    """
    # Validate that either specification_id or model_id is provided
    if not device.specification_id and not device.model_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either specification_id or model_id must be provided"
        )

    if device.specification_id and device.model_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one of specification_id or model_id should be provided, not both"
        )

    # Validate specification if provided
    if device.specification_id:
        spec = db.query(DeviceSpecification).filter(
            DeviceSpecification.id == device.specification_id
        ).first()
        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device specification with ID {device.specification_id} not found"
            )

    # Validate model if provided
    if device.model_id:
        model = db.query(Model).filter(Model.id == device.model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catalog model with ID {device.model_id} not found"
            )

    db_device = Device(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)

    # Load relationships
    if device.specification_id:
        db.refresh(db_device, ["specification"])
    if device.model_id:
        db.refresh(db_device, ["catalog_model"])

    return db_device


@router.post("/quick-add", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def quick_add_device(
    quick_add: DeviceQuickAdd,
    db: Session = Depends(get_db)
):
    """
    Quick-add a device by searching for its specification by brand and model.

    - **brand**: Device brand name (case-insensitive partial match)
    - **model**: Device model name (case-insensitive partial match)
    - **custom_name**: Optional custom name for this device instance
    - **serial_number**: Optional serial number
    - **access_frequency**: How often the device is accessed (default: MEDIUM)
    - **notes**: Optional notes

    This endpoint searches for a matching device specification and creates
    a device instance from it. If multiple specifications match, it returns
    the first one. If none match, it suggests similar specifications.
    """
    # Search for matching specification
    search_brand = f"%{quick_add.brand}%"
    search_model = f"%{quick_add.model}%"

    spec = db.query(DeviceSpecification).filter(
        DeviceSpecification.brand.ilike(search_brand),
        DeviceSpecification.model.ilike(search_model)
    ).first()

    if not spec:
        # Try to find suggestions
        suggestions = db.query(DeviceSpecification).filter(
            or_(
                DeviceSpecification.brand.ilike(search_brand),
                DeviceSpecification.model.ilike(search_model)
            )
        ).limit(5).all()

        suggestion_text = ""
        if suggestions:
            suggestion_text = " Did you mean one of these? " + ", ".join(
                [f"{s.brand} {s.model}" for s in suggestions]
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No device specification found for brand '{quick_add.brand}' " +
                   f"and model '{quick_add.model}'.{suggestion_text}"
        )

    # Create device from specification
    device_data = quick_add.model_dump(exclude={"brand", "model"})
    device_data["specification_id"] = spec.id

    db_device = Device(**device_data)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    db.refresh(db_device, ["specification"])

    return db_device


@router.post("/bulk", response_model=List[DeviceResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_devices(
    specification_id: int = Query(..., description="Specification ID to use for all devices"),
    quantity: int = Query(..., ge=1, le=100, description="Number of devices to create"),
    name_prefix: Optional[str] = Query(None, description="Optional prefix for device names"),
    db: Session = Depends(get_db)
):
    """
    Create multiple devices from the same specification.

    - **specification_id**: Device specification to use
    - **quantity**: Number of devices to create (1-100)
    - **name_prefix**: Optional prefix for device names (will append number)

    Creates multiple device instances with auto-generated names if prefix is provided.
    """
    # Validate specification exists
    spec = db.query(DeviceSpecification).filter(
        DeviceSpecification.id == specification_id
    ).first()

    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device specification with ID {specification_id} not found"
        )

    devices = []
    for i in range(1, quantity + 1):
        custom_name = f"{name_prefix} {i}" if name_prefix else None

        db_device = Device(
            specification_id=specification_id,
            custom_name=custom_name
        )
        db.add(db_device)
        devices.append(db_device)

    db.commit()

    # Refresh all devices to load relationships
    for device in devices:
        db.refresh(device)
        db.refresh(device, ["specification"])

    return devices


@router.post("/from-model", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device_from_model(
    device_data: DeviceFromModel,
    db: Session = Depends(get_db)
):
    """
    Create a new device from a catalog model with auto-populated specifications.

    - **model_id**: ID of the catalog model to use (required)
    - **custom_name**: Optional custom name for this device instance
    - **serial_number**: Optional serial number
    - **access_frequency**: How often the device is accessed (default: MEDIUM)
    - **notes**: Optional notes about the device

    This endpoint automatically populates device specifications from the catalog model,
    providing a streamlined workflow for creating devices.
    """
    # Validate that model exists
    model = db.query(Model).options(
        joinedload(Model.brand),
        joinedload(Model.device_type)
    ).filter(Model.id == device_data.model_id).first()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog model with ID {device_data.model_id} not found"
        )

    # Create device with model_id
    db_device = Device(
        model_id=device_data.model_id,
        custom_name=device_data.custom_name,
        serial_number=device_data.serial_number,
        access_frequency=device_data.access_frequency,
        notes=device_data.notes,
        # Populate denormalized fields from model for quick reference
        brand=model.brand.name if model.brand else None,
        model=model.name
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)

    # Load catalog_model relationship
    db.refresh(db_device, ["catalog_model"])

    return db_device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing device.

    - **device_id**: Device ID to update
    - All fields are optional; only provided fields will be updated

    Note: You cannot change the specification_id after creation.
    """
    db_device = db.query(Device).filter(Device.id == device_id).first()

    if not db_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Update only provided fields
    update_data = device_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_device, field, value)

    db.commit()
    db.refresh(db_device)
    db.refresh(db_device, ["specification"])

    return db_device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a device.

    - **device_id**: Device ID to delete

    This will cascade delete:
    - All rack positions for this device
    - All connections involving this device
    """
    db_device = db.query(Device).filter(Device.id == device_id).first()

    if not db_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Cascade delete positions and connections (handled by database relationships)
    db.delete(db_device)
    db.commit()

    return None
