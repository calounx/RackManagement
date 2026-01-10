"""
Connections API endpoints.
Handles CRUD operations for cable connections between devices.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from ..models import Connection, Device, RackPosition, Rack, RoutingPath
from ..schemas import (
    ConnectionCreate,
    ConnectionUpdate,
    ConnectionResponse
)
from .dependencies import get_db, pagination_params

router = APIRouter()


def calculate_cable_length(
    from_position: RackPosition,
    to_position: RackPosition,
    routing_path: RoutingPath
) -> float:
    """
    Calculate cable length between two positioned devices.

    Args:
        from_position: Source device position
        to_position: Destination device position
        routing_path: Cable routing method (direct, cable_tray, conduit)

    Returns:
        Cable length in meters

    Formula:
    - Vertical distance: |from_U - to_U| * 0.04445m (1U = 44.45mm)
    - Horizontal distance: rack depth (converted to meters)
    - Base length: vertical + horizontal
    - Apply routing overhead: direct=1.2x, cable_tray=1.5x, conduit=1.8x
    """
    # Calculate vertical distance
    vertical_distance_u = abs(from_position.start_u - to_position.start_u)
    vertical_distance_m = vertical_distance_u * 0.04445  # 1U = 44.45mm

    # Get rack depth (assume both devices in same rack or similar depth)
    rack_depth_mm = from_position.rack.depth_mm or 600  # Default 600mm if not specified
    horizontal_distance_m = rack_depth_mm / 1000

    # Base cable length
    base_length = vertical_distance_m + horizontal_distance_m

    # Apply routing overhead multipliers
    overhead_multipliers = {
        RoutingPath.DIRECT: 1.2,
        RoutingPath.CABLE_TRAY: 1.5,
        RoutingPath.CONDUIT: 1.8
    }

    multiplier = overhead_multipliers.get(routing_path, 1.2)
    total_length = base_length * multiplier

    # Round to 2 decimal places
    return round(total_length, 2)


@router.get("/", response_model=List[ConnectionResponse])
async def list_connections(
    rack_id: Optional[int] = Query(None, description="Filter by rack ID"),
    from_device_id: Optional[int] = Query(None, description="Filter by source device ID"),
    to_device_id: Optional[int] = Query(None, description="Filter by destination device ID"),
    pagination: dict = Depends(pagination_params),
    db: Session = Depends(get_db)
):
    """
    List all cable connections with optional filtering.

    - **rack_id**: Show only connections within a specific rack
    - **from_device_id**: Show connections from a specific device
    - **to_device_id**: Show connections to a specific device
    - **skip**: Number of records to skip
    - **limit**: Maximum records to return

    Includes device details in the response.
    """
    query = db.query(Connection).options(
        joinedload(Connection.from_device).joinedload(Device.specification),
        joinedload(Connection.to_device).joinedload(Device.specification)
    )

    # Filter by rack: check if either device is in the specified rack
    if rack_id:
        from_positions = db.query(RackPosition.device_id).filter(
            RackPosition.rack_id == rack_id
        ).subquery()
        to_positions = db.query(RackPosition.device_id).filter(
            RackPosition.rack_id == rack_id
        ).subquery()

        query = query.filter(
            (Connection.from_device_id.in_(from_positions)) |
            (Connection.to_device_id.in_(to_positions))
        )

    if from_device_id:
        query = query.filter(Connection.from_device_id == from_device_id)

    if to_device_id:
        query = query.filter(Connection.to_device_id == to_device_id)

    connections = query.offset(pagination["skip"]).limit(pagination["limit"]).all()
    return connections


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single connection by ID.

    - **connection_id**: Connection ID
    """
    connection = db.query(Connection).options(
        joinedload(Connection.from_device).joinedload(Device.specification),
        joinedload(Connection.to_device).joinedload(Device.specification)
    ).filter(Connection.id == connection_id).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection with ID {connection_id} not found"
        )

    return connection


@router.post("/", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection: ConnectionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new cable connection between two devices.

    - **from_device_id**: Source device ID (required)
    - **to_device_id**: Destination device ID (required)
    - **from_port**: Source port identifier
    - **to_port**: Destination port identifier
    - **cable_type**: Type of cable (ethernet, fiber, power, etc.)
    - **cable_length_m**: Cable length in meters (auto-calculated if devices are positioned)
    - **routing_path**: How cable is routed (direct, cable_tray, conduit)
    - **notes**: Optional notes

    If both devices are positioned in racks and cable_length_m is not provided,
    it will be automatically calculated based on their positions.
    """
    # Validate both devices exist
    from_device = db.query(Device).filter(Device.id == connection.from_device_id).first()
    if not from_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source device with ID {connection.from_device_id} not found"
        )

    to_device = db.query(Device).filter(Device.id == connection.to_device_id).first()
    if not to_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination device with ID {connection.to_device_id} not found"
        )

    # Check if devices can connect to themselves
    if connection.from_device_id == connection.to_device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a connection from a device to itself"
        )

    # Auto-calculate cable length if not provided and both devices are positioned
    cable_length = connection.cable_length_m
    if cable_length is None:
        # Find positions for both devices
        from_position = db.query(RackPosition).options(
            joinedload(RackPosition.rack)
        ).filter(RackPosition.device_id == connection.from_device_id).first()

        to_position = db.query(RackPosition).options(
            joinedload(RackPosition.rack)
        ).filter(RackPosition.device_id == connection.to_device_id).first()

        # Only calculate if both devices are positioned in the same rack
        if from_position and to_position and from_position.rack_id == to_position.rack_id:
            cable_length = calculate_cable_length(
                from_position,
                to_position,
                connection.routing_path or RoutingPath.DIRECT
            )

    # Create connection
    db_connection = Connection(
        **connection.model_dump(exclude={"cable_length_m"}),
        cable_length_m=cable_length
    )

    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    db.refresh(db_connection, ["from_device", "to_device"])

    return db_connection


@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: int,
    connection_update: ConnectionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing connection.

    - **connection_id**: Connection ID to update
    - All fields are optional; only provided fields will be updated

    If routing_path is updated and cable_length_m is not provided,
    the cable length will be recalculated if both devices are positioned.
    """
    db_connection = db.query(Connection).filter(Connection.id == connection_id).first()

    if not db_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection with ID {connection_id} not found"
        )

    # Update only provided fields
    update_data = connection_update.model_dump(exclude_unset=True)

    # If routing_path changed but cable_length not provided, recalculate
    if "routing_path" in update_data and "cable_length_m" not in update_data:
        from_position = db.query(RackPosition).options(
            joinedload(RackPosition.rack)
        ).filter(RackPosition.device_id == db_connection.from_device_id).first()

        to_position = db.query(RackPosition).options(
            joinedload(RackPosition.rack)
        ).filter(RackPosition.device_id == db_connection.to_device_id).first()

        if from_position and to_position and from_position.rack_id == to_position.rack_id:
            new_routing = update_data["routing_path"]
            update_data["cable_length_m"] = calculate_cable_length(
                from_position,
                to_position,
                new_routing
            )

    for field, value in update_data.items():
        setattr(db_connection, field, value)

    db.commit()
    db.refresh(db_connection)
    db.refresh(db_connection, ["from_device", "to_device"])

    return db_connection


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a connection.

    - **connection_id**: Connection ID to delete
    """
    db_connection = db.query(Connection).filter(Connection.id == connection_id).first()

    if not db_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection with ID {connection_id} not found"
        )

    db.delete(db_connection)
    db.commit()

    return None
