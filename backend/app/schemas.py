"""
Pydantic schemas for API request/response validation
"""
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
    specification_id: int = Field(..., gt=0)


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
    specification_id: int
    specification: DeviceSpecificationResponse

    class Config:
        from_attributes = True


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


class RackLayoutResponse(BaseModel):
    """Schema for rack layout with positioned devices"""
    rack: RackResponse
    positions: List['RackPositionResponse']
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
