"""
Racks API endpoints.
Handles CRUD operations for racks and device positioning within racks.
"""

from typing import List, Optional, Set
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
import logging

from datetime import datetime
from ..models import Rack, RackPosition, Device, DeviceSpecification, WidthType
from ..schemas import (
    RackCreate,
    RackUpdate,
    RackResponse,
    RackPositionCreate,
    RackPositionResponse,
    RackLayoutResponse,
    ThermalAnalysisResponse,
    ThermalHeatDistribution,
    ThermalCoolingEfficiency,
    ThermalHotSpot,
    ThermalAirflowConflict,
    OptimizationRequest,
    OptimizationResult
)
from .dependencies import get_db, pagination_params
from ..thermal import (
    calculate_rack_heat_output,
    calculate_cooling_efficiency,
    check_airflow_conflicts,
    identify_hot_spots,
    get_thermal_recommendations
)
from ..cache import get_redis_cache
from ..cache.decorators import (
    invalidate_rack_thermal_cache,
    invalidate_rack_optimization_cache,
    generate_thermal_cache_key,
    generate_optimization_cache_key
)
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def width_type_to_inches(width_type: WidthType) -> float:
    """Convert WidthType enum to numeric inches."""
    mapping = {
        WidthType.ELEVEN_INCH: 11,
        WidthType.EIGHTEEN_INCH: 18,
        WidthType.NINETEEN_INCH: 19,
        WidthType.TWENTY_THREE_INCH: 23
    }
    return mapping.get(width_type, 19)  # Default to 19"


def is_width_compatible(rack_width_type: WidthType, device_width_type: Optional[WidthType]) -> bool:
    """
    Check if a device's width type is compatible with a rack's width.

    Args:
        rack_width_type: Rack width type enum
        device_width_type: Device width type enum

    Returns:
        True if compatible, False otherwise
    """
    if device_width_type is None:
        return True  # Unknown width assumed compatible

    rack_inches = width_type_to_inches(rack_width_type)

    compatibility_map = {
        WidthType.ELEVEN_INCH: [11, 18, 19, 23],
        WidthType.EIGHTEEN_INCH: [18, 19, 23],
        WidthType.NINETEEN_INCH: [19, 23],
        WidthType.TWENTY_THREE_INCH: [23]
    }

    compatible_widths = compatibility_map.get(device_width_type, [])
    return rack_inches in compatible_widths


def get_occupied_positions(rack_id: int, db: Session, exclude_position_id: Optional[int] = None) -> Set[int]:
    """
    Get all occupied U positions in a rack.

    Args:
        rack_id: Rack ID
        db: Database session
        exclude_position_id: Optional position ID to exclude (for updates)

    Returns:
        Set of occupied U positions
    """
    query = db.query(RackPosition).filter(RackPosition.rack_id == rack_id)

    if exclude_position_id:
        query = query.filter(RackPosition.id != exclude_position_id)

    positions = query.options(joinedload(RackPosition.device).joinedload(Device.specification)).all()

    occupied = set()
    for pos in positions:
        device_height = pos.device.specification.height_u
        for u in range(int(pos.start_u), int(pos.start_u + device_height)):
            occupied.add(u)

    return occupied


@router.get("/", response_model=List[RackResponse])
async def list_racks(
    pagination: dict = Depends(pagination_params),
    db: Session = Depends(get_db)
):
    """
    List all racks with pagination.

    - **skip**: Number of records to skip
    - **limit**: Maximum records to return
    """
    racks = db.query(Rack).offset(pagination["skip"]).limit(pagination["limit"]).all()
    return racks


@router.get("/{rack_id}", response_model=RackResponse)
async def get_rack(
    rack_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single rack by ID.

    - **rack_id**: Rack ID
    """
    rack = db.query(Rack).filter(Rack.id == rack_id).first()

    if not rack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rack with ID {rack_id} not found"
        )

    return rack


@router.get("/{rack_id}/layout", response_model=RackLayoutResponse)
async def get_rack_layout(
    rack_id: int,
    db: Session = Depends(get_db)
):
    """
    Get rack layout with all positioned devices and utilization metrics.

    - **rack_id**: Rack ID

    Returns rack details plus:
    - All positioned devices with their specifications
    - U utilization percentage
    - Total weight
    - Total power consumption
    """
    rack = db.query(Rack).filter(Rack.id == rack_id).first()

    if not rack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rack with ID {rack_id} not found"
        )

    # Get all positions with device and specification details
    positions = db.query(RackPosition).filter(
        RackPosition.rack_id == rack_id
    ).options(
        joinedload(RackPosition.device).joinedload(Device.specification)
    ).all()

    # Calculate metrics
    total_u_used = sum(pos.device.specification.height_u for pos in positions)
    utilization_percent = (total_u_used / rack.total_height_u) * 100 if rack.total_height_u > 0 else 0

    total_weight_kg = sum(
        pos.device.specification.weight_kg or 0 for pos in positions
    )

    total_power_watts = sum(
        pos.device.specification.power_watts or 0 for pos in positions
    )

    return {
        "rack": rack,
        "positions": positions,
        "utilization_percent": round(utilization_percent, 2),
        "total_weight_kg": round(total_weight_kg, 2),
        "total_power_watts": round(total_power_watts, 2)
    }


@router.get("/{rack_id}/thermal-analysis", response_model=ThermalAnalysisResponse)
async def get_thermal_analysis(
    rack_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive thermal analysis for a rack.

    - **rack_id**: Rack ID

    Returns:
    - Heat distribution by thermal zone (bottom/middle/top)
    - Cooling efficiency and capacity utilization
    - Hot spot identification (high-heat devices)
    - Airflow pattern conflicts
    - Thermal optimization recommendations

    **Best Practices**:
    - Keep cooling utilization between 70-85% for optimal efficiency
    - Place high-heat devices in bottom zone (coolest intake air)
    - Maintain consistent airflow direction (typically front-to-back)
    - Distribute heat evenly across zones to avoid hot spots
    - Ensure adequate spacing around devices >1500 BTU/hr

    **Caching**:
    - Results are cached for 5 minutes to improve performance
    - Cache is automatically invalidated when rack configuration changes
    """
    # Fetch rack
    rack = db.query(Rack).filter(Rack.id == rack_id).first()

    if not rack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rack with ID {rack_id} not found"
        )

    # Try to get from cache
    cache = get_redis_cache()
    cache_key = generate_thermal_cache_key(rack_id, rack.updated_at)
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        logger.info(f"Thermal analysis cache HIT for rack {rack_id}")
        # Return cached result with updated timestamp
        cached_result["timestamp"] = datetime.utcnow()
        cached_result["cached"] = True
        return cached_result

    logger.info(f"Thermal analysis cache MISS for rack {rack_id}")

    # Calculate heat distribution
    heat_dist = calculate_rack_heat_output(rack, db)

    # Calculate cooling efficiency
    cooling_eff = calculate_cooling_efficiency(rack, heat_dist["total_heat_btu_hr"])

    # Identify hot spots
    hot_spots = identify_hot_spots(rack, db, threshold_btu=1000.0)

    # Check airflow conflicts
    airflow_conflicts = check_airflow_conflicts(rack, db)

    # Get recommendations
    recommendations = get_thermal_recommendations(rack, db)

    result = {
        "rack_id": rack.id,
        "rack_name": rack.name,
        "heat_distribution": heat_dist,
        "cooling_efficiency": cooling_eff,
        "hot_spots": hot_spots,
        "airflow_conflicts": airflow_conflicts,
        "recommendations": recommendations,
        "timestamp": datetime.utcnow(),
        "cached": False
    }

    # Cache the result
    cache.set(cache_key, result, ttl=settings.CACHE_TTL_THERMAL)

    return result


@router.post("/", response_model=RackResponse, status_code=status.HTTP_201_CREATED)
async def create_rack(
    rack: RackCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new rack.

    - **name**: Rack name (required)
    - **location**: Physical location description
    - **total_height_u**: Total height in rack units (default: 42)
    - **width_inches**: Rack width type (11", 18", 19", or 23")
    - **depth_mm**: Rack depth in millimeters
    - **max_weight_kg**: Maximum weight capacity
    - **max_power_watts**: Maximum power capacity
    """
    db_rack = Rack(**rack.model_dump())
    db.add(db_rack)
    db.commit()
    db.refresh(db_rack)

    return db_rack


@router.post("/{rack_id}/positions", response_model=RackPositionResponse, status_code=status.HTTP_201_CREATED)
async def add_device_to_rack(
    rack_id: int,
    position: RackPositionCreate,
    db: Session = Depends(get_db)
):
    """
    Add a device to a rack at a specific position.

    - **rack_id**: Rack ID
    - **device_id**: Device ID to position
    - **start_u**: Starting U position (1-based, bottom of rack = 1)
    - **is_locked**: Whether position is locked (prevents optimization changes)

    Validates:
    - Rack and device exist
    - Device fits within rack height
    - Device width is compatible with rack width
    - Position doesn't overlap with existing devices
    """
    # Validate rack exists
    rack = db.query(Rack).filter(Rack.id == rack_id).first()
    if not rack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rack with ID {rack_id} not found"
        )

    # Validate device exists and load specification
    device = db.query(Device).options(
        joinedload(Device.specification)
    ).filter(Device.id == position.device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {position.device_id} not found"
        )

    # Validate device fits within rack height
    device_height = device.specification.height_u
    end_u = position.start_u + device_height

    if position.start_u < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start position must be at least 1"
        )

    if end_u > rack.total_height_u:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device doesn't fit: requires {device_height}U starting at U{position.start_u}, " +
                   f"but rack is only {rack.total_height_u}U tall"
        )

    # Validate width compatibility
    if not is_width_compatible(rack.width_inches, device.specification.width_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device width ({device.specification.width_type.value if device.specification.width_type else 'unknown'}) " +
                   f"is not compatible with rack width ({rack.width_inches}\")"
        )

    # Check for overlaps
    occupied = get_occupied_positions(rack_id, db)
    device_range = range(int(position.start_u), int(end_u))

    overlapping_positions = [u for u in device_range if u in occupied]
    if overlapping_positions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Position conflict: U positions {overlapping_positions} are already occupied"
        )

    # Create position
    db_position = RackPosition(
        rack_id=rack_id,
        **position.model_dump()
    )
    db.add(db_position)
    db.commit()
    db.refresh(db_position)
    db.refresh(db_position, ["device"])

    # Invalidate cache after adding device to rack
    invalidate_rack_thermal_cache(rack_id)
    invalidate_rack_optimization_cache(rack_id)
    logger.info(f"Invalidated cache for rack {rack_id} after adding device {position.device_id}")

    return db_position


@router.put("/{rack_id}", response_model=RackResponse)
async def update_rack(
    rack_id: int,
    rack_update: RackUpdate,
    db: Session = Depends(get_db)
):
    """
    Update rack properties.

    - **rack_id**: Rack ID to update
    - All fields are optional; only provided fields will be updated
    """
    db_rack = db.query(Rack).filter(Rack.id == rack_id).first()

    if not db_rack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rack with ID {rack_id} not found"
        )

    # Update only provided fields
    update_data = rack_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_rack, field, value)

    # Update timestamp
    db_rack.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_rack)

    # Invalidate cache after rack update
    invalidate_rack_thermal_cache(rack_id)
    invalidate_rack_optimization_cache(rack_id)
    logger.info(f"Invalidated cache for rack {rack_id} after update")

    return db_rack


@router.delete("/{rack_id}/positions/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_device_from_rack(
    rack_id: int,
    position_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove a device from a rack.

    - **rack_id**: Rack ID
    - **position_id**: Position ID to remove
    """
    position = db.query(RackPosition).filter(
        RackPosition.id == position_id,
        RackPosition.rack_id == rack_id
    ).first()

    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position {position_id} not found in rack {rack_id}"
        )

    db.delete(position)
    db.commit()

    # Invalidate cache after removing device from rack
    invalidate_rack_thermal_cache(rack_id)
    invalidate_rack_optimization_cache(rack_id)
    logger.info(f"Invalidated cache for rack {rack_id} after removing device position {position_id}")

    return None


@router.post("/{rack_id}/optimize", response_model=OptimizationResult)
async def optimize_rack_layout(
    rack_id: int,
    request: OptimizationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate optimized device placement for a rack.

    Uses multi-objective optimization algorithms to find the best device placement
    considering thermal management, power distribution, cable routing, and accessibility.

    - **rack_id**: Rack to optimize
    - **locked_positions**: Device IDs that cannot be moved (optional)
    - **weights**: Custom objective weights (optional)
        - cable: Cable management weight (default: 0.30)
        - weight: Weight distribution weight (default: 0.25)
        - thermal: Thermal management weight (default: 0.25)
        - access: Access frequency weight (default: 0.20)

    Returns optimized device positions with scores and improvement descriptions.
    Does NOT automatically apply changes - use as suggestions.

    **Caching**:
    - Results are cached for 10 minutes based on optimization configuration
    - Different weight configurations are cached separately
    """
    from ..optimization import OptimizationCoordinator

    # 1. Fetch rack
    rack = db.query(Rack).filter(Rack.id == rack_id).first()

    if not rack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rack with ID {rack_id} not found"
        )

    # 2. Try to get from cache
    cache = get_redis_cache()
    cache_key = generate_optimization_cache_key(
        rack_id,
        request.weights.model_dump() if request.weights else {},
        request.locked_positions
    )
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        logger.info(f"Optimization cache HIT for rack {rack_id}")
        return cached_result

    logger.info(f"Optimization cache MISS for rack {rack_id}")

    # 3. Fetch all devices (both in rack and available)
    devices = db.query(Device).options(
        joinedload(Device.specification)
    ).all()

    # Filter out devices without specifications
    devices_with_specs = [d for d in devices if d.specification is not None]

    if not devices_with_specs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No devices with specifications available for optimization"
        )

    # 4. Get current positions for comparison
    current_positions_query = db.query(RackPosition).filter(
        RackPosition.rack_id == rack_id
    ).all()
    current_positions = [(pos.device_id, pos.start_u) for pos in current_positions_query]

    # 5. Fetch connections for cable optimization
    from ..models import Connection
    connections = db.query(Connection).all()

    # 6. Use default weights if not provided
    weights = request.weights

    # 7. Run optimization
    try:
        coordinator = OptimizationCoordinator(
            rack=rack,
            devices=devices_with_specs,
            connections=connections,
            weights=weights,
            locked_device_ids=request.locked_positions or [],
            current_positions=current_positions if current_positions else None
        )

        best_solution, improvements, metadata = coordinator.optimize()

        # 8. Convert positions to API response format
        position_responses = []
        device_map = {d.id: d for d in devices_with_specs}

        for device_id, start_u in best_solution.positions:
            device = device_map[device_id]
            device_name = device.custom_name or f"{device.specification.brand} {device.specification.model}"

            position_responses.append(RackPositionResponse(
                id=None,  # New position (not saved yet)
                device_id=device_id,
                rack_id=rack.id,
                start_u=start_u,
                device_name=device_name
            ))

        result = OptimizationResult(
            positions=position_responses,
            score=best_solution.breakdown,
            improvements=improvements,
            metadata=metadata
        )

        # Cache the result
        cache.set(cache_key, result.model_dump(), ttl=settings.CACHE_TTL_OPTIMIZATION)

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
        )


@router.delete("/{rack_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rack(
    rack_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a rack.

    - **rack_id**: Rack ID to delete

    This will cascade delete all positions and connections in this rack.
    """
    db_rack = db.query(Rack).filter(Rack.id == rack_id).first()

    if not db_rack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rack with ID {rack_id} not found"
        )

    db.delete(db_rack)
    db.commit()

    # Invalidate cache after rack deletion
    invalidate_rack_thermal_cache(rack_id)
    invalidate_rack_optimization_cache(rack_id)
    logger.info(f"Invalidated cache for rack {rack_id} after deletion")

    return None
