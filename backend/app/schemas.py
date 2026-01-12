"""
Pydantic schemas for API request/response validation
"""
from __future__ import annotations
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class WidthType(str, Enum):
    ELEVEN_INCH = "11\""
    EIGHTEEN_INCH = "18\""
    NINETEEN_INCH = "19\""
    TWENTY_THREE_INCH = "23\""


class SourceType(str, Enum):
    WEB_FETCHED = "web_fetched"
    MANUFACTURER_SPEC = "manufacturer_spec"
    COMMUNITY = "community"
    USER_CUSTOM = "user_custom"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AccessFrequency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CableType(str, Enum):
    CAT5E = "Cat5e"
    CAT6 = "Cat6"
    CAT6A = "Cat6a"
    CAT7 = "Cat7"
    FIBER_SM = "Fiber-SM"
    FIBER_MM = "Fiber-MM"
    POWER = "Power"
    CONSOLE = "Console"


class RoutingPath(str, Enum):
    DIRECT = "direct"
    CABLE_TRAY = "cable_tray"
    CONDUIT = "conduit"


class AirflowPattern(str, Enum):
    """Device airflow patterns"""
    FRONT_TO_BACK = "front_to_back"
    BACK_TO_FRONT = "back_to_front"
    SIDE_TO_SIDE = "side_to_side"
    PASSIVE = "passive"


class ThermalZone(str, Enum):
    """Thermal zones within a rack"""
    BOTTOM = "bottom"
    MIDDLE = "middle"
    TOP = "top"


# Device Specification Schemas
class DeviceSpecificationBase(BaseModel):
    """Base device specification schema"""
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    variant: Optional[str] = None
    height_u: float = Field(..., ge=0, le=50)
    width_type: Optional[WidthType] = None
    depth_mm: Optional[float] = Field(None, ge=0, le=1500)
    weight_kg: Optional[float] = Field(None, ge=0, le=500)
    power_watts: Optional[float] = Field(None, ge=0, le=10000)
    heat_output_btu: Optional[float] = Field(None, ge=0)
    airflow_pattern: Optional[AirflowPattern] = AirflowPattern.FRONT_TO_BACK
    max_operating_temp_c: Optional[float] = Field(None, ge=-20, le=100)
    typical_ports: Optional[Dict[str, int]] = None
    mounting_type: Optional[str] = None

    @validator('heat_output_btu', always=True)
    def calculate_btu_from_watts(cls, v, values):
        """Auto-calculate BTU if missing but watts available"""
        if v is None and 'power_watts' in values and values['power_watts']:
            # 1 Watt ≈ 3.412 BTU/hr
            return values['power_watts'] * 3.412
        return v


class DeviceSpecificationCreate(DeviceSpecificationBase):
    """Schema for creating device specification"""
    source: SourceType = SourceType.USER_CUSTOM
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class DeviceSpecificationUpdate(BaseModel):
    """Schema for updating device specification"""
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    variant: Optional[str] = None
    height_u: Optional[float] = Field(None, ge=0, le=50)
    width_type: Optional[WidthType] = None
    depth_mm: Optional[float] = Field(None, ge=0, le=1500)
    weight_kg: Optional[float] = Field(None, ge=0, le=500)
    power_watts: Optional[float] = Field(None, ge=0, le=10000)
    heat_output_btu: Optional[float] = Field(None, ge=0)
    airflow_pattern: Optional[AirflowPattern] = None
    max_operating_temp_c: Optional[float] = Field(None, ge=-20, le=100)
    typical_ports: Optional[Dict[str, int]] = None
    mounting_type: Optional[str] = None
    source: Optional[SourceType] = None
    confidence: Optional[ConfidenceLevel] = None


class DeviceSpecificationResponse(DeviceSpecificationBase):
    """Schema for device specification response"""
    id: int
    source: SourceType
    source_url: Optional[str]
    confidence: ConfidenceLevel
    fetched_at: Optional[datetime]
    last_updated: datetime

    class Config:
        from_attributes = True


class DeviceSpecificationFetch(BaseModel):
    """Schema for fetching device specs from web"""
    brand: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)


# Device Schemas
class DeviceBase(BaseModel):
    """Base device schema"""
    custom_name: Optional[str] = Field(None, min_length=1, max_length=200)
    access_frequency: AccessFrequency = AccessFrequency.MEDIUM
    notes: Optional[str] = None


class DeviceCreate(DeviceBase):
    """Schema for creating device"""
    specification_id: Optional[int] = Field(None, gt=0)
    model_id: Optional[int] = Field(None, gt=0, description="ID of catalog model (alternative to specification_id)")
    serial_number: Optional[str] = Field(None, max_length=200, description="Device serial number")


class DeviceUpdate(BaseModel):
    """Schema for updating device"""
    custom_name: Optional[str] = Field(None, min_length=1, max_length=200)
    access_frequency: Optional[AccessFrequency] = None
    notes: Optional[str] = None


class DeviceQuickAdd(BaseModel):
    """Schema for quick adding devices by brand/model"""
    brand: str
    model: str
    custom_name: Optional[str] = None
    access_frequency: AccessFrequency = AccessFrequency.MEDIUM
    notes: Optional[str] = None


class DeviceResponse(DeviceBase):
    """Schema for device response"""
    id: int
    specification_id: Optional[int]
    model_id: Optional[int]
    specification: Optional[DeviceSpecificationResponse]
    catalog_model: Optional[ModelResponse] = Field(None, description="Catalog model details if model_id is set")
    serial_number: Optional[str]

    class Config:
        from_attributes = True


class DeviceFromModel(BaseModel):
    """Schema for creating device from catalog model"""
    model_id: int = Field(..., gt=0, description="Catalog model ID")
    custom_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Custom device name")
    serial_number: Optional[str] = Field(None, max_length=200, description="Device serial number")
    access_frequency: AccessFrequency = AccessFrequency.MEDIUM
    notes: Optional[str] = None


# Rack Schemas
class RackBase(BaseModel):
    """Base rack schema"""
    name: str = Field(..., min_length=1, max_length=200)
    location: Optional[str] = None
    total_height_u: int = Field(42, ge=1, le=100)
    width_inches: WidthType = WidthType.NINETEEN_INCH
    depth_mm: float = Field(700.0, ge=200, le=1500)
    max_weight_kg: float = Field(500.0, ge=0, le=2000)
    max_power_watts: float = Field(5000.0, ge=0, le=50000)
    cooling_type: str = "front-to-back"
    cooling_capacity_btu: float = Field(17000.0, ge=0, le=100000)
    ambient_temp_c: float = Field(22.0, ge=10, le=35)
    max_inlet_temp_c: float = Field(27.0, ge=15, le=40)
    airflow_cfm: Optional[float] = Field(None, ge=0)


class RackCreate(RackBase):
    """Schema for creating rack"""
    pass


class RackUpdate(BaseModel):
    """Schema for updating rack"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = None
    total_height_u: Optional[int] = Field(None, ge=1, le=100)
    width_inches: Optional[WidthType] = None
    depth_mm: Optional[float] = Field(None, ge=200, le=1500)
    max_weight_kg: Optional[float] = Field(None, ge=0, le=2000)
    max_power_watts: Optional[float] = Field(None, ge=0, le=50000)
    cooling_type: Optional[str] = None
    cooling_capacity_btu: Optional[float] = Field(None, ge=0, le=100000)
    ambient_temp_c: Optional[float] = Field(None, ge=10, le=35)
    max_inlet_temp_c: Optional[float] = Field(None, ge=15, le=40)
    airflow_cfm: Optional[float] = Field(None, ge=0)


class RackResponse(RackBase):
    """Schema for rack response"""
    id: int

    class Config:
        from_attributes = True


# Rack Position Schemas
class RackPositionBase(BaseModel):
    """Base rack position schema"""
    device_id: int
    start_u: int = Field(..., ge=1, le=100)
    locked: bool = False


class RackPositionCreate(RackPositionBase):
    """Schema for creating rack position"""
    pass


class RackPositionResponse(BaseModel):
    """Schema for rack position response"""
    id: int
    device_id: int
    rack_id: int
    start_u: int
    locked: bool
    device: DeviceResponse

    class Config:
        from_attributes = True
class RackLayoutResponse(BaseModel):
    """Schema for rack layout with positioned devices"""
    rack: RackResponse
    positions: List[RackPositionResponse]
    utilization_percent: float
    total_weight_kg: float
    total_power_watts: float

    class Config:
        from_attributes = True


# Thermal Analysis Schemas
class ThermalHeatDistribution(BaseModel):
    """Heat distribution across thermal zones"""
    total_heat_btu_hr: float
    total_power_watts: float
    bottom_zone_btu: float
    middle_zone_btu: float
    top_zone_btu: float
    device_count: int


class ThermalCoolingEfficiency(BaseModel):
    """Cooling system efficiency metrics"""
    cooling_capacity_btu_hr: float
    cooling_capacity_tons: float
    heat_load_btu_hr: float
    utilization_percent: float
    remaining_capacity_btu_hr: float
    remaining_capacity_tons: float
    status: str  # "optimal", "acceptable", "warning", "critical"


class ThermalHotSpot(BaseModel):
    """High-heat device identification"""
    device_id: int
    device_name: str
    position: str
    zone: str
    heat_output_btu_hr: float
    power_watts: float
    airflow_pattern: str
    severity: str  # "high", "medium", "low"


class ThermalAirflowConflict(BaseModel):
    """Airflow pattern conflict between devices"""
    type: str
    severity: str
    device1: Dict[str, Any]
    device2: Dict[str, Any]
    message: str


class ThermalAnalysisResponse(BaseModel):
    """Complete thermal analysis for a rack"""
    rack_id: int
    rack_name: str
    heat_distribution: ThermalHeatDistribution
    cooling_efficiency: ThermalCoolingEfficiency
    hot_spots: List[ThermalHotSpot]
    airflow_conflicts: List[ThermalAirflowConflict]
    recommendations: List[str]
    timestamp: datetime




# Connection Schemas
class ConnectionBase(BaseModel):
    """Base connection schema"""
    from_device_id: int
    to_device_id: int
    from_port: Optional[str] = None
    to_port: Optional[str] = None
    cable_type: CableType = CableType.CAT6
    cable_length_m: Optional[float] = Field(None, ge=0)
    routing_path: Optional[RoutingPath] = RoutingPath.DIRECT
    notes: Optional[str] = None


class ConnectionCreate(ConnectionBase):
    """Schema for creating connection"""
    pass


class ConnectionUpdate(BaseModel):
    """Schema for updating connection"""
    from_port: Optional[str] = None
    to_port: Optional[str] = None
    cable_type: Optional[CableType] = None
    cable_length_m: Optional[float] = Field(None, ge=0)
    routing_path: Optional[RoutingPath] = None
    notes: Optional[str] = None


class ConnectionResponse(BaseModel):
    """Schema for connection response"""
    id: int
    from_device_id: int
    to_device_id: int
    from_port: Optional[str]
    to_port: Optional[str]
    cable_type: CableType
    cable_length_m: Optional[float]
    routing_path: Optional[RoutingPath]
    notes: Optional[str]
    from_device: DeviceResponse
    to_device: DeviceResponse

    class Config:
        from_attributes = True


# Optimization Schemas
class OptimizationWeights(BaseModel):
    """Optimization factor weights"""
    cable: float = Field(0.30, ge=0, le=1)
    weight: float = Field(0.25, ge=0, le=1)
    thermal: float = Field(0.25, ge=0, le=1)
    access: float = Field(0.20, ge=0, le=1)

    @validator('*')
    def check_sum(cls, v, values):
        """Ensure weights sum to ~1.0"""
        total = sum(values.values()) + v
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class OptimizationRequest(BaseModel):
    """Request for rack optimization"""
    locked_positions: List[int] = []  # Device IDs to keep locked
    weights: OptimizationWeights = OptimizationWeights()


class ScoreBreakdown(BaseModel):
    """Score breakdown by factor"""
    cable_management: float
    weight_distribution: float
    thermal_management: float
    access_frequency: float
    total: float


class OptimizationResult(BaseModel):
    """Optimization result"""
    positions: List[RackPositionResponse]
    score: ScoreBreakdown
    improvements: List[str]
    metadata: Dict[str, Any]


# BOM Schemas
class CableItem(BaseModel):
    """Cable item in BOM"""
    from_device: str
    to_device: str
    cable_type: CableType
    length_m: float
    quantity: int = 1


class BOMResponse(BaseModel):
    """Bill of Materials response"""
    cables: List[CableItem]
    cable_summary: Dict[str, int]  # e.g., {"Cat6 2m": 10}
    total_cables: int
    total_cost: Optional[float] = None


# ============================================================================
# Catalog Schemas - New device catalog system
# ============================================================================

class DCIMType(str, Enum):
    """DCIM system types"""
    NETBOX = "netbox"
    RACKTABLES = "racktables"
    RALPH = "ralph"


class FetchConfidence(str, Enum):
    """Confidence level for fetched data"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Pagination helper
class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses"""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


# DeviceType Schemas
class DeviceTypeBase(BaseModel):
    """Base device type schema with shared fields"""
    name: str = Field(..., min_length=1, max_length=100, description="Device type name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly identifier")
    icon: Optional[str] = Field(None, max_length=50, description="Emoji or unicode character")
    description: Optional[str] = Field(None, description="Device type description")
    color: Optional[str] = Field(None, max_length=50, description="UI color code (e.g., #FF5733)")


class DeviceTypeCreate(DeviceTypeBase):
    """Schema for creating device type"""
    pass


class DeviceTypeUpdate(BaseModel):
    """Schema for updating device type"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Device type name")
    slug: Optional[str] = Field(None, min_length=1, max_length=100, description="URL-friendly identifier")
    icon: Optional[str] = Field(None, max_length=50, description="Emoji or unicode character")
    description: Optional[str] = Field(None, description="Device type description")
    color: Optional[str] = Field(None, max_length=50, description="UI color code")


class DeviceTypeSummary(BaseModel):
    """Minimal device type info for nested responses"""
    id: int
    name: str
    slug: str
    icon: Optional[str]
    color: Optional[str]

    class Config:
        from_attributes = True


class DeviceTypeResponse(DeviceTypeBase):
    """Schema for device type response with full details"""
    id: int
    created_at: datetime
    updated_at: datetime
    model_count: int = Field(0, description="Number of models using this type")

    class Config:
        from_attributes = True


class DeviceTypeListResponse(BaseModel):
    """Paginated list of device types"""
    items: List[DeviceTypeResponse]
    pagination: PaginationMetadata


# Brand Schemas
class BrandBase(BaseModel):
    """Base brand schema with shared fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Brand name")
    slug: str = Field(..., min_length=1, max_length=200, description="URL-friendly identifier")
    website: Optional[str] = Field(None, max_length=500, description="Official website URL")
    support_url: Optional[str] = Field(None, max_length=500, description="Support/documentation URL")
    logo_url: Optional[str] = Field(None, max_length=500, description="Brand logo image URL")
    description: Optional[str] = Field(None, description="Brand description")
    founded_year: Optional[int] = Field(None, ge=1800, le=2100, description="Year founded")
    headquarters: Optional[str] = Field(None, max_length=200, description="Headquarters location")


class BrandCreate(BrandBase):
    """Schema for creating brand"""
    pass


class BrandUpdate(BaseModel):
    """Schema for updating brand"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Brand name")
    slug: Optional[str] = Field(None, min_length=1, max_length=200, description="URL-friendly identifier")
    website: Optional[str] = Field(None, max_length=500, description="Official website URL")
    support_url: Optional[str] = Field(None, max_length=500, description="Support/documentation URL")
    logo_url: Optional[str] = Field(None, max_length=500, description="Brand logo image URL")
    description: Optional[str] = Field(None, description="Brand description")
    founded_year: Optional[int] = Field(None, ge=1800, le=2100, description="Year founded")
    headquarters: Optional[str] = Field(None, max_length=200, description="Headquarters location")


class BrandSummary(BaseModel):
    """Minimal brand info for nested responses"""
    id: int
    name: str
    slug: str
    logo_url: Optional[str]

    class Config:
        from_attributes = True


class BrandResponse(BrandBase):
    """Schema for brand response with full details"""
    id: int
    last_fetched_at: Optional[datetime] = Field(None, description="When brand info was last fetched")
    fetch_confidence: Optional[FetchConfidence] = Field(None, description="Confidence in fetched data")
    fetch_source: Optional[str] = Field(None, max_length=100, description="Source of fetched data")
    created_at: datetime
    updated_at: datetime
    model_count: int = Field(0, description="Number of models from this brand")

    class Config:
        from_attributes = True


class BrandListResponse(BaseModel):
    """Paginated list of brands"""
    items: List[BrandResponse]
    pagination: PaginationMetadata


# Model Schemas
class ModelBase(BaseModel):
    """Base model schema with shared physical/technical fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Model name")
    variant: Optional[str] = Field(None, max_length=100, description="Model variant (e.g., AC, DC, PoE+)")
    description: Optional[str] = Field(None, description="Model description")

    # Lifecycle
    release_date: Optional[datetime] = Field(None, description="Product release date")
    end_of_life: Optional[datetime] = Field(None, description="End of life date")

    # Physical dimensions
    height_u: float = Field(..., ge=0, le=50, description="Height in rack units")
    width_type: Optional[str] = Field(None, max_length=10, description="Width type (e.g., 19\", 23\")")
    depth_mm: Optional[float] = Field(None, ge=0, le=1500, description="Depth in millimeters")
    weight_kg: Optional[float] = Field(None, ge=0, le=500, description="Weight in kilograms")

    # Power and thermal
    power_watts: Optional[float] = Field(None, ge=0, le=10000, description="Power consumption in watts")
    heat_output_btu: Optional[float] = Field(None, ge=0, description="Heat output in BTU/hr")
    airflow_pattern: Optional[str] = Field(None, max_length=50, description="Airflow pattern")
    max_operating_temp_c: Optional[float] = Field(None, ge=-20, le=100, description="Max operating temperature")

    # Connectivity
    typical_ports: Optional[Dict[str, int]] = Field(None, description="Typical port configuration")

    # Mounting
    mounting_type: Optional[str] = Field(None, max_length=100, description="Mounting type")

    # Documentation
    datasheet_url: Optional[str] = Field(None, max_length=500, description="Datasheet URL")
    image_url: Optional[str] = Field(None, max_length=500, description="Product image URL")


class ModelCreate(ModelBase):
    """Schema for creating model"""
    brand_id: int = Field(..., gt=0, description="Brand ID")
    device_type_id: int = Field(..., gt=0, description="Device type ID")
    source: Optional[str] = Field(None, max_length=50, description="Data source")
    confidence: Optional[str] = Field(None, max_length=20, description="Data confidence level")


class ModelUpdate(BaseModel):
    """Schema for updating model - all fields optional"""
    brand_id: Optional[int] = Field(None, gt=0, description="Brand ID")
    device_type_id: Optional[int] = Field(None, gt=0, description="Device type ID")
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Model name")
    variant: Optional[str] = Field(None, max_length=100, description="Model variant")
    description: Optional[str] = Field(None, description="Model description")
    release_date: Optional[datetime] = Field(None, description="Product release date")
    end_of_life: Optional[datetime] = Field(None, description="End of life date")
    height_u: Optional[float] = Field(None, ge=0, le=50, description="Height in rack units")
    width_type: Optional[str] = Field(None, max_length=10, description="Width type")
    depth_mm: Optional[float] = Field(None, ge=0, le=1500, description="Depth in millimeters")
    weight_kg: Optional[float] = Field(None, ge=0, le=500, description="Weight in kilograms")
    power_watts: Optional[float] = Field(None, ge=0, le=10000, description="Power consumption in watts")
    heat_output_btu: Optional[float] = Field(None, ge=0, description="Heat output in BTU/hr")
    airflow_pattern: Optional[str] = Field(None, max_length=50, description="Airflow pattern")
    max_operating_temp_c: Optional[float] = Field(None, ge=-20, le=100, description="Max operating temperature")
    typical_ports: Optional[Dict[str, int]] = Field(None, description="Typical port configuration")
    mounting_type: Optional[str] = Field(None, max_length=100, description="Mounting type")
    datasheet_url: Optional[str] = Field(None, max_length=500, description="Datasheet URL")
    image_url: Optional[str] = Field(None, max_length=500, description="Product image URL")
    source: Optional[str] = Field(None, max_length=50, description="Data source")
    confidence: Optional[str] = Field(None, max_length=20, description="Data confidence level")


class ModelResponse(ModelBase):
    """Schema for model response with full details and relationships"""
    id: int
    brand_id: int
    device_type_id: int
    brand: BrandSummary = Field(..., description="Brand information")
    device_type: DeviceTypeSummary = Field(..., description="Device type information")
    source: Optional[str] = Field(None, description="Data source")
    confidence: Optional[str] = Field(None, description="Data confidence level")
    fetched_at: Optional[datetime] = Field(None, description="When data was fetched")
    last_updated: datetime
    device_count: int = Field(0, description="Number of devices using this model")

    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    """Paginated list of models"""
    items: List[ModelResponse]
    pagination: PaginationMetadata


# DCIMConnection Schemas
class DCIMConnectionBase(BaseModel):
    """Base DCIM connection schema with shared fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Connection name")
    type: DCIMType = Field(..., description="DCIM system type")
    base_url: str = Field(..., min_length=1, max_length=500, description="Base URL of DCIM system")
    api_token: Optional[str] = Field(None, max_length=500, description="API authentication token")
    is_public: bool = Field(False, description="Whether this is a public instance")


class DCIMConnectionCreate(DCIMConnectionBase):
    """Schema for creating DCIM connection"""
    pass


class DCIMConnectionUpdate(BaseModel):
    """Schema for updating DCIM connection"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Connection name")
    type: Optional[DCIMType] = Field(None, description="DCIM system type")
    base_url: Optional[str] = Field(None, min_length=1, max_length=500, description="Base URL")
    api_token: Optional[str] = Field(None, max_length=500, description="API authentication token")
    is_public: Optional[bool] = Field(None, description="Whether this is a public instance")


class DCIMConnectionResponse(DCIMConnectionBase):
    """Schema for DCIM connection response with sync status"""
    id: int
    last_sync: Optional[datetime] = Field(None, description="Last successful sync timestamp")
    sync_status: Optional[str] = Field(None, max_length=50, description="Current sync status")
    created_at: datetime
    updated_at: datetime

    # Mask API token in responses
    api_token: Optional[str] = Field(None, description="API token (masked)")

    @validator('api_token', always=True)
    def mask_api_token(cls, v):
        """Mask API token for security"""
        if v and len(v) > 8:
            return f"{v[:4]}{'*' * (len(v) - 8)}{v[-4:]}"
        return "****" if v else None

    class Config:
        from_attributes = True


class DCIMConnectionListResponse(BaseModel):
    """Paginated list of DCIM connections"""
    items: List[DCIMConnectionResponse]
    pagination: PaginationMetadata


class DCIMConnectionTestResult(BaseModel):
    """Result of testing a DCIM connection"""
    success: bool = Field(..., description="Whether connection test succeeded")
    message: str = Field(..., description="Test result message")
    response_time_ms: Optional[float] = Field(None, description="API response time in milliseconds")
    system_info: Optional[Dict[str, Any]] = Field(None, description="System information from DCIM")


# ============================================================================
# Web Fetch Schemas - Phase 3
# ============================================================================

class BrandFetchRequest(BaseModel):
    """Request to fetch brand information from web sources"""
    brand_name: str = Field(..., min_length=1, max_length=200, description="Brand name to fetch")

    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "Cisco Systems"
            }
        }


class BrandInfoResponse(BaseModel):
    """Brand information fetched from web sources (before saving to database)"""
    name: str = Field(..., description="Brand name")
    slug: str = Field(..., description="URL-friendly identifier")
    website: Optional[str] = Field(None, description="Official website URL")
    description: Optional[str] = Field(None, description="Brand description")
    founded_year: Optional[int] = Field(None, description="Year founded")
    headquarters: Optional[str] = Field(None, description="Headquarters location")
    logo_url: Optional[str] = Field(None, description="Logo image URL")
    fetch_confidence: FetchConfidence = Field(..., description="Confidence in fetched data")
    fetch_source: str = Field(..., description="Source of fetched data")

    class Config:
        from_attributes = True


class ModelFetchRequest(BaseModel):
    """Request to fetch model specifications from manufacturer websites"""
    brand: str = Field(..., min_length=1, max_length=200, description="Brand name")
    model: str = Field(..., min_length=1, max_length=200, description="Model name")
    device_type_id: Optional[int] = Field(None, gt=0, description="Device type ID (optional - will be inferred if not provided)")

    class Config:
        json_schema_extra = {
            "example": {
                "brand": "Cisco",
                "model": "Catalyst 9300",
                "device_type_id": 2
            }
        }


# ============================================================================
# NetBox DCIM Integration Schemas - Phase 4
# ============================================================================

class NetBoxHealthResponse(BaseModel):
    """NetBox connection health check response"""
    connected: bool = Field(..., description="Whether NetBox connection is healthy")
    url: Optional[str] = Field(None, description="NetBox instance URL")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "connected": True,
                "url": "https://netbox.example.com",
                "message": "NetBox connection successful"
            }
        }


class NetBoxImportRequest(BaseModel):
    """Request to import rack from NetBox"""
    rack_name: str = Field(..., min_length=1, max_length=200, description="NetBox rack name to import")
    import_devices: bool = Field(default=True, description="Import devices in rack")
    overwrite_existing: bool = Field(default=False, description="Overwrite existing rack if found")

    class Config:
        json_schema_extra = {
            "example": {
                "rack_name": "DC1-R01",
                "import_devices": True,
                "overwrite_existing": False
            }
        }


class NetBoxImportResult(BaseModel):
    """Result of NetBox rack import operation"""
    success: bool = Field(..., description="Whether import succeeded")
    rack_id: int = Field(..., description="ID of imported/updated rack")
    rack_name: str = Field(..., description="Name of imported rack")
    devices_imported: int = Field(..., ge=0, description="Number of devices imported")
    message: str = Field(..., description="Import result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "rack_id": 1,
                "rack_name": "DC1-R01",
                "devices_imported": 15,
                "message": "Successfully imported rack 'DC1-R01' with 15 devices from NetBox"
            }
        }


# Rebuild models to resolve forward references
# These calls are needed because some models have forward references to classes defined later
DeviceResponse.model_rebuild()  # Has forward reference to ModelResponse
RackResponse.model_rebuild()    # Has forward reference to RackPositionResponse


# ============================================================================
# Authentication Schemas - JWT-based auth system
# ============================================================================

class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class UserBase(BaseModel):
    """Base user schema"""
    email: str = Field(..., min_length=3, max_length=255, description="User email address")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    role: UserRole = Field(default=UserRole.USER, description="User role")


class UserUpdate(BaseModel):
    """Schema for updating user"""
    email: Optional[str] = Field(None, min_length=3, max_length=255, description="User email address")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="New password")
    role: Optional[UserRole] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="User active status")


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., min_length=3, description="Email address (username)")
    password: str = Field(..., min_length=1, description="Password")


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class TokenRefresh(BaseModel):
    """Schema for refreshing access token"""
    refresh_token: str = Field(..., description="JWT refresh token")


class TokenPayload(BaseModel):
    """Schema for JWT token payload"""
    sub: int = Field(..., description="User ID (subject)")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    type: str = Field(..., description="Token type (access or refresh)")


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
