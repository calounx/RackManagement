"""
SQLAlchemy database models
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey, Enum, DateTime, Text, Date, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class WidthType(str, enum.Enum):
    """Rack width types"""
    ELEVEN_INCH = "11\""
    EIGHTEEN_INCH = "18\""
    NINETEEN_INCH = "19\""
    TWENTY_THREE_INCH = "23\""


class SourceType(str, enum.Enum):
    """Device specification source"""
    WEB_FETCHED = "web_fetched"
    MANUFACTURER_SPEC = "manufacturer_spec"
    COMMUNITY = "community"
    USER_CUSTOM = "user_custom"


class ConfidenceLevel(str, enum.Enum):
    """Confidence in specification accuracy"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AccessFrequency(str, enum.Enum):
    """How often device needs to be accessed"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CableType(str, enum.Enum):
    """Cable types"""
    CAT5E = "Cat5e"
    CAT6 = "Cat6"
    CAT6A = "Cat6a"
    CAT7 = "Cat7"
    FIBER_SM = "Fiber-SM"
    FIBER_MM = "Fiber-MM"
    POWER = "Power"
    CONSOLE = "Console"


class AirflowPattern(str, enum.Enum):
    """Device airflow patterns"""
    FRONT_TO_BACK = "front_to_back"
    BACK_TO_FRONT = "back_to_front"
    SIDE_TO_SIDE = "side_to_side"
    PASSIVE = "passive"  # No active cooling


class ThermalZone(str, enum.Enum):
    """Thermal zones within a rack"""
    BOTTOM = "bottom"  # U1-U14 (coolest - intake air)
    MIDDLE = "middle"  # U15-U28 (moderate)
    TOP = "top"  # U29-U42 (warmest - heat rises)


class RoutingPath(str, enum.Enum):
    """Cable routing method"""
    DIRECT = "direct"
    CABLE_TRAY = "cable_tray"
    CONDUIT = "conduit"


class FetchConfidence(str, enum.Enum):
    """Confidence level for fetched data"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DCIMType(str, enum.Enum):
    """DCIM system types"""
    NETBOX = "netbox"
    RACKTABLES = "racktables"
    RALPH = "ralph"


class MigrationStatus(str, enum.Enum):
    """Status of migration from DeviceSpecification to Model"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DeviceSpecification(Base):
    """Device specification lookup database"""
    __tablename__ = "device_specifications"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, index=True, nullable=False)
    model = Column(String, index=True, nullable=False)
    variant = Column(String, nullable=True)

    # Physical dimensions
    height_u = Column(Float, nullable=False)  # Rack units
    width_type = Column(Enum(WidthType), nullable=True)
    depth_mm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)

    # Power and thermal
    power_watts = Column(Float, nullable=True)
    heat_output_btu = Column(Float, nullable=True)
    airflow_pattern = Column(Enum(AirflowPattern), default=AirflowPattern.FRONT_TO_BACK)
    max_operating_temp_c = Column(Float, nullable=True)  # Maximum operating temperature

    # Ports (JSON field)
    typical_ports = Column(JSON, nullable=True)  # {"gigabit_ethernet": 48, "sfp": 2, ...}

    # Mounting
    mounting_type = Column(String, nullable=True)  # "2-post", "4-post", "wall-mount"

    # Source metadata
    source = Column(Enum(SourceType), default=SourceType.USER_CUSTOM)
    source_url = Column(String, nullable=True)
    confidence = Column(Enum(ConfidenceLevel), default=ConfidenceLevel.MEDIUM)
    fetched_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Migration fields (transition to new Model system)
    migrated_to_model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    migration_status = Column(Enum(MigrationStatus), nullable=True)
    deprecated = Column(Boolean, default=False)

    # Relationships
    devices = relationship("Device", back_populates="specification")
    migrated_to_model = relationship("Model", foreign_keys=[migrated_to_model_id])


class Device(Base):
    """User's actual device instances"""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    custom_name = Column(String, nullable=False)

    # Link to specification (legacy)
    specification_id = Column(Integer, ForeignKey("device_specifications.id"), nullable=False)

    # Link to new catalog model (optional during transition)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)

    # Quick reference (denormalized for performance)
    brand = Column(String, index=True)
    model = Column(String, index=True)

    # User-defined properties
    access_frequency = Column(Enum(AccessFrequency), default=AccessFrequency.MEDIUM)
    notes = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)

    # Relationships
    specification = relationship("DeviceSpecification", back_populates="devices")
    catalog_model = relationship("Model", back_populates="devices")
    rack_positions = relationship("RackPosition", back_populates="device", cascade="all, delete-orphan")
    connections_from = relationship("Connection", foreign_keys="[Connection.from_device_id]", back_populates="from_device")
    connections_to = relationship("Connection", foreign_keys="[Connection.to_device_id]", back_populates="to_device")


class Rack(Base):
    """Network rack"""
    __tablename__ = "racks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)

    # Physical properties
    total_height_u = Column(Integer, default=42)  # Standard 42U
    width_inches = Column(Enum(WidthType), default=WidthType.NINETEEN_INCH)
    depth_mm = Column(Float, default=700.0)
    max_weight_kg = Column(Float, default=500.0)
    max_power_watts = Column(Float, default=5000.0)

    # Thermal and cooling
    cooling_type = Column(String, default="front-to-back")  # "front-to-back", "bottom-to-top"
    cooling_capacity_btu = Column(Float, default=17000.0)  # ~5 tons = 17,000 BTU/hr
    ambient_temp_c = Column(Float, default=22.0)  # Data center ambient temperature
    max_inlet_temp_c = Column(Float, default=27.0)  # ASHRAE recommended max inlet temp
    airflow_cfm = Column(Float, nullable=True)  # Cubic feet per minute airflow

    # Relationships
    positions = relationship("RackPosition", back_populates="rack", cascade="all, delete-orphan")


class RackPosition(Base):
    """Device position in rack"""
    __tablename__ = "rack_positions"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    rack_id = Column(Integer, ForeignKey("racks.id"), nullable=False)

    # Position
    start_u = Column(Integer, nullable=False)  # 1-42 (bottom to top)
    locked = Column(Boolean, default=False)  # Prevent optimization from moving

    # Relationships
    device = relationship("Device", back_populates="rack_positions")
    rack = relationship("Rack", back_populates="positions")


class Connection(Base):
    """Connection between devices"""
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)

    # Devices
    from_device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    to_device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)

    # Ports
    from_port = Column(String, nullable=True)  # e.g., "Gi0/1"
    to_port = Column(String, nullable=True)

    # Cable properties
    cable_type = Column(Enum(CableType), default=CableType.CAT6)
    cable_category_required = Column(String, nullable=True)  # Auto-determined
    calculated_length_m = Column(Float, nullable=True)  # Calculated based on positions
    routing_path = Column(Enum(RoutingPath), default=RoutingPath.DIRECT)

    # Relationships
    from_device = relationship("Device", foreign_keys=[from_device_id], back_populates="connections_from")
    to_device = relationship("Device", foreign_keys=[to_device_id], back_populates="connections_to")


# ============================================================================
# Catalog Models - New device catalog system
# ============================================================================


class DeviceType(Base):
    """Device type categories (e.g., Switch, Server, Firewall)"""
    __tablename__ = "device_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    icon = Column(String(50), nullable=True)  # emoji/unicode character
    description = Column(Text, nullable=True)
    color = Column(String(50), nullable=True)  # UI color coding (e.g., "#FF5733")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    models = relationship("Model", back_populates="device_type")


class Brand(Base):
    """Hardware manufacturer/brand information"""
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    website = Column(String(500), nullable=True)
    support_url = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    founded_year = Column(Integer, nullable=True)
    headquarters = Column(String(200), nullable=True)

    # Metadata for web-fetched information
    last_fetched_at = Column(DateTime, nullable=True)
    fetch_confidence = Column(Enum(FetchConfidence), nullable=True)
    fetch_source = Column(String(100), nullable=True)  # e.g., "wikipedia", "official_website"

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    models = relationship("Model", back_populates="brand")


class Model(Base):
    """Device model specifications from catalog"""
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False, index=True)
    device_type_id = Column(Integer, ForeignKey("device_types.id"), nullable=False, index=True)

    # Model identification
    name = Column(String(200), nullable=False, index=True)
    variant = Column(String(100), nullable=True)  # e.g., "AC", "DC", "PoE+"
    description = Column(Text, nullable=True)

    # Lifecycle
    release_date = Column(Date, nullable=True)
    end_of_life = Column(Date, nullable=True)

    # Physical dimensions
    height_u = Column(Float, nullable=False)
    width_type = Column(String(10), nullable=True)  # "19\"", "23\"", etc.
    depth_mm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)

    # Power and thermal
    power_watts = Column(Float, nullable=True)
    heat_output_btu = Column(Float, nullable=True)
    airflow_pattern = Column(String(50), nullable=True)  # "front_to_back", "side_to_side", etc.
    max_operating_temp_c = Column(Float, nullable=True)

    # Connectivity
    typical_ports = Column(JSON, nullable=True)  # {"gigabit_ethernet": 48, "sfp": 2, ...}

    # Mounting
    mounting_type = Column(String(100), nullable=True)  # "2-post", "4-post", "wall-mount"

    # Documentation
    datasheet_url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)

    # Source metadata
    source = Column(String(50), nullable=True)  # "netbox", "deviceatlas", "manual"
    confidence = Column(String(20), nullable=True)  # "high", "medium", "low"
    fetched_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    brand = relationship("Brand", back_populates="models")
    device_type = relationship("DeviceType", back_populates="models")
    devices = relationship("Device", back_populates="catalog_model")

    # Indexes and constraints
    __table_args__ = (
        Index("ix_models_brand_name_variant", "brand_id", "name", "variant", unique=True),
    )


class DCIMConnection(Base):
    """External DCIM system connections for importing device catalogs"""
    __tablename__ = "dcim_connections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(Enum(DCIMType), nullable=False)  # netbox, racktables, ralph
    base_url = Column(String(500), nullable=False)
    api_token = Column(String(500), nullable=True)  # Will be encrypted in production
    is_public = Column(Boolean, default=False)  # Public instances don't need auth

    # Sync metadata
    last_sync = Column(DateTime, nullable=True)
    sync_status = Column(String(50), nullable=True)  # "success", "failed", "in_progress"

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================================================
# Authentication Models - JWT-based authentication system
# ============================================================================


class UserRole(str, enum.Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
    )


class TokenBlacklist(Base):
    """Token blacklist for logout functionality"""
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    token_jti = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User")

    # Index for cleanup queries
    __table_args__ = (
        Index("ix_token_blacklist_expires", "expires_at"),
    )
