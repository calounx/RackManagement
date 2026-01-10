"""
SQLAlchemy database models
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey, Enum, DateTime
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


class RoutingPath(str, enum.Enum):
    """Cable routing method"""
    DIRECT = "direct"
    CABLE_TRAY = "cable_tray"
    CONDUIT = "conduit"


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

    # Relationships
    devices = relationship("Device", back_populates="specification")


class Device(Base):
    """User's actual device instances"""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    custom_name = Column(String, nullable=False)

    # Link to specification
    specification_id = Column(Integer, ForeignKey("device_specifications.id"), nullable=False)

    # Quick reference (denormalized for performance)
    brand = Column(String, index=True)
    model = Column(String, index=True)

    # User-defined properties
    access_frequency = Column(Enum(AccessFrequency), default=AccessFrequency.MEDIUM)
    notes = Column(String, nullable=True)

    # Relationships
    specification = relationship("DeviceSpecification", back_populates="devices")
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

    # Cooling
    cooling_type = Column(String, default="front-to-back")  # "front-to-back", "bottom-to-top"

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
