"""
DCIM Integration API endpoints.
Handles NetBox integration for device specification and rack layout synchronization.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from ..integrations.netbox import NetBoxClient
from ..schemas import (
    NetBoxImportRequest,
    NetBoxImportResult,
    NetBoxHealthResponse
)
from .dependencies import get_db
from ..models import Rack, Device, DeviceSpecification, RackPosition
from ..exceptions import DCIMConnectionError, DCIMAuthenticationError, DCIMNotFoundError
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dcim", tags=["DCIM Integration"])


@router.get("/health", response_model=NetBoxHealthResponse)
async def check_netbox_health():
    """
    Check NetBox connection status.

    Returns connectivity and authentication status.
    Tests the connection to NetBox DCIM system.

    Returns:
        NetBoxHealthResponse with connection status and URL
    """
    if not settings.NETBOX_ENABLED:
        return NetBoxHealthResponse(
            connected=False,
            url=None,
            message="NetBox integration is disabled. Enable with NETBOX_ENABLED=true"
        )

    try:
        client = NetBoxClient()
        is_healthy = await client.health_check()

        return NetBoxHealthResponse(
            connected=is_healthy,
            url=client.base_url,
            message="NetBox connection successful" if is_healthy else "Connection failed - check credentials"
        )

    except ValueError as e:
        # Configuration error
        logger.error(f"NetBox configuration error: {e}")
        return NetBoxHealthResponse(
            connected=False,
            url=None,
            message=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"NetBox health check failed: {e}")
        return NetBoxHealthResponse(
            connected=False,
            url=settings.NETBOX_URL if settings.NETBOX_URL else None,
            message=f"NetBox error: {str(e)}"
        )


@router.post("/import-rack", response_model=NetBoxImportResult, status_code=status.HTTP_201_CREATED)
async def import_rack_from_netbox(
    request: NetBoxImportRequest,
    db: Session = Depends(get_db)
):
    """
    Import a rack and its devices from NetBox.

    This endpoint fetches a rack from NetBox by name and creates it in HomeRack
    with all associated devices and their specifications.

    Args:
        request: NetBoxImportRequest with rack name and import options

    Request Body:
        - **rack_name**: NetBox rack name to import (required)
        - **import_devices**: Whether to import devices (default: true)
        - **overwrite_existing**: Overwrite if rack exists (default: false)

    Creates:
        - Rack with specifications from NetBox
        - Device specifications (if not already exist)
        - Devices positioned in rack

    Returns:
        NetBoxImportResult with success status and details

    Raises:
        HTTPException 404: If rack not found in NetBox
        HTTPException 409: If rack exists and overwrite_existing is false
        HTTPException 401: If NetBox authentication fails
        HTTPException 503: If NetBox connection fails
    """
    if not settings.NETBOX_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NetBox integration is disabled. Enable with NETBOX_ENABLED=true"
        )

    try:
        client = NetBoxClient()

        # 1. Fetch rack from NetBox
        logger.info(f"Fetching rack '{request.rack_name}' from NetBox")
        netbox_rack = await client.get_rack(request.rack_name)

        if not netbox_rack:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rack '{request.rack_name}' not found in NetBox"
            )

        # 2. Check if rack exists locally
        existing_rack = db.query(Rack).filter(Rack.name == netbox_rack["name"]).first()

        if existing_rack and not request.overwrite_existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Rack '{request.rack_name}' already exists in HomeRack. Use overwrite_existing=true to replace."
            )

        # 3. Create or update rack
        if existing_rack:
            # Update existing rack
            logger.info(f"Updating existing rack: {existing_rack.id}")
            for field, value in netbox_rack.items():
                if field != "id" and hasattr(existing_rack, field):
                    setattr(existing_rack, field, value)
            rack = existing_rack
        else:
            # Create new rack
            logger.info(f"Creating new rack: {netbox_rack['name']}")
            rack_data = {k: v for k, v in netbox_rack.items() if k != "id"}
            rack = Rack(**rack_data)
            db.add(rack)

        db.commit()
        db.refresh(rack)
        logger.info(f"Rack saved with ID: {rack.id}")

        devices_imported = 0

        # 4. Import devices if requested
        if request.import_devices:
            logger.info(f"Importing devices from NetBox rack ID: {netbox_rack['id']}")
            netbox_devices = await client.list_devices_in_rack(str(netbox_rack["id"]))

            for netbox_device in netbox_devices:
                try:
                    brand = netbox_device.get("brand", "Unknown")
                    model = netbox_device.get("model", "Unknown")

                    # Get or create device specification
                    spec = db.query(DeviceSpecification).filter(
                        DeviceSpecification.brand == brand,
                        DeviceSpecification.model == model
                    ).first()

                    if not spec:
                        # Fetch full specs from NetBox
                        logger.info(f"Fetching device type from NetBox: {brand} {model}")
                        device_type = await client.get_device_type(brand, model)

                        if device_type:
                            # Create device specification
                            spec_data = {k: v for k, v in device_type.items() if k != "id" and hasattr(DeviceSpecification, k)}
                            spec = DeviceSpecification(**spec_data)
                            db.add(spec)
                            db.flush()
                            logger.info(f"Created device specification: {spec.id}")

                    # Create device
                    device = Device(
                        specification_id=spec.id if spec else None,
                        custom_name=netbox_device.get("name"),
                        serial_number=netbox_device.get("serial"),
                        notes=f"Imported from NetBox: {client.base_url}/dcim/devices/{netbox_device.get('id')}/"
                    )
                    db.add(device)
                    db.flush()
                    logger.info(f"Created device: {device.id}")

                    # Create rack position if device has a position
                    position = netbox_device.get("position")
                    if position is not None:
                        rack_position = RackPosition(
                            rack_id=rack.id,
                            device_id=device.id,
                            start_u=position
                        )
                        db.add(rack_position)
                        logger.info(f"Created rack position at U{position}")

                    devices_imported += 1

                except Exception as e:
                    logger.error(f"Failed to import device {netbox_device.get('name')}: {e}")
                    # Continue with other devices

            db.commit()
            logger.info(f"Successfully imported {devices_imported} devices")

        return NetBoxImportResult(
            success=True,
            rack_id=rack.id,
            rack_name=rack.name,
            devices_imported=devices_imported,
            message=f"Successfully imported rack '{rack.name}' with {devices_imported} devices from NetBox"
        )

    except DCIMAuthenticationError as e:
        logger.error(f"NetBox authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NetBox authentication failed. Check NETBOX_TOKEN environment variable."
        )

    except DCIMConnectionError as e:
        logger.error(f"NetBox connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"NetBox connection error: {str(e)}"
        )

    except DCIMNotFoundError as e:
        logger.error(f"NetBox resource not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error during NetBox import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )
