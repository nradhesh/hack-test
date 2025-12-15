"""
Asset Model - Represents urban infrastructure assets.

Each asset has geospatial location, maintenance parameters,
and links to issues and debt snapshots.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import enum

from app.core.database import Base


class AssetType(str, enum.Enum):
    """Types of urban infrastructure assets."""
    ROAD = "road"
    DRAIN = "drain"
    STREETLIGHT = "streetlight"
    BRIDGE = "bridge"
    SIDEWALK = "sidewalk"
    WATER_PIPE = "water_pipe"
    SEWER = "sewer"
    TRAFFIC_SIGNAL = "traffic_signal"
    PARK = "park"
    OTHER = "other"


class AssetStatus(str, enum.Enum):
    """Current status of an asset."""
    ACTIVE = "active"
    UNDER_MAINTENANCE = "under_maintenance"
    DECOMMISSIONED = "decommissioned"
    PLANNED = "planned"


class Asset(Base):
    """
    Urban infrastructure asset model.
    
    Stores information about roads, drains, streetlights,
    and other city infrastructure components.
    """
    __tablename__ = "assets"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Asset identification
    asset_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Asset classification
    asset_type = Column(
        SQLEnum(AssetType),
        nullable=False,
        default=AssetType.OTHER,
        index=True
    )
    status = Column(
        SQLEnum(AssetStatus),
        nullable=False,
        default=AssetStatus.ACTIVE
    )
    
    # Geospatial location (PostGIS point)
    location = Column(
        Geometry(geometry_type='POINT', srid=4326),
        nullable=True,
        index=True
    )
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Address information
    address = Column(String(500), nullable=True)
    ward_id = Column(Integer, nullable=True, index=True)
    zone = Column(String(100), nullable=True)
    
    # Maintenance parameters
    base_repair_cost = Column(Float, nullable=False, default=10000.0)
    expected_maintenance_interval_days = Column(Integer, nullable=False, default=365)
    sla_days = Column(Integer, nullable=False, default=7)
    
    # Condition tracking
    condition_score = Column(Float, nullable=True, default=100.0)
    last_maintenance_date = Column(DateTime, nullable=True)
    next_scheduled_maintenance = Column(DateTime, nullable=True)
    
    # Metadata
    installation_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    issues = relationship("Issue", back_populates="asset", cascade="all, delete-orphan")
    debt_snapshots = relationship("DebtSnapshot", back_populates="asset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Asset(id={self.id}, code='{self.asset_code}', type={self.asset_type.value})>"
    
    @property
    def has_open_issues(self) -> bool:
        """Check if asset has any unresolved issues."""
        return any(not issue.is_resolved for issue in self.issues)
    
    @property
    def open_issue_count(self) -> int:
        """Count of unresolved issues."""
        return sum(1 for issue in self.issues if not issue.is_resolved)
    
    def to_dict(self) -> dict:
        """Convert asset to dictionary representation."""
        return {
            "id": self.id,
            "asset_code": self.asset_code,
            "name": self.name,
            "description": self.description,
            "asset_type": self.asset_type.value,
            "status": self.status.value,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "ward_id": self.ward_id,
            "zone": self.zone,
            "base_repair_cost": self.base_repair_cost,
            "sla_days": self.sla_days,
            "condition_score": self.condition_score,
            "last_maintenance_date": self.last_maintenance_date.isoformat() if self.last_maintenance_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
