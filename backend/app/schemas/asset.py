"""
Asset Schemas - Pydantic models for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class AssetType(str, Enum):
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


class AssetStatus(str, Enum):
    """Current status of an asset."""
    ACTIVE = "active"
    UNDER_MAINTENANCE = "under_maintenance"
    DECOMMISSIONED = "decommissioned"
    PLANNED = "planned"


class AssetBase(BaseModel):
    """Base schema for asset data."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: AssetType = AssetType.OTHER
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = None
    ward_id: Optional[int] = None
    zone: Optional[str] = None
    base_repair_cost: float = Field(default=10000.0, gt=0)
    sla_days: int = Field(default=7, gt=0, le=365)


class AssetCreate(AssetBase):
    """Schema for creating a new asset."""
    asset_code: Optional[str] = Field(None, max_length=50)
    
    @field_validator('asset_code', mode='before')
    @classmethod
    def generate_asset_code(cls, v, info):
        """Generate asset code if not provided."""
        if v is None:
            import uuid
            return f"AST-{uuid.uuid4().hex[:8].upper()}"
        return v


class AssetUpdate(BaseModel):
    """Schema for updating an existing asset."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: Optional[AssetType] = None
    status: Optional[AssetStatus] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = None
    ward_id: Optional[int] = None
    zone: Optional[str] = None
    base_repair_cost: Optional[float] = Field(None, gt=0)
    sla_days: Optional[int] = Field(None, gt=0, le=365)
    condition_score: Optional[float] = Field(None, ge=0, le=100)


class AssetResponse(BaseModel):
    """Schema for asset response."""
    id: int
    asset_code: str
    name: str
    description: Optional[str] = None
    asset_type: str
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    ward_id: Optional[int] = None
    zone: Optional[str] = None
    base_repair_cost: float
    sla_days: int
    condition_score: Optional[float] = None
    last_maintenance_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Computed fields from relationships
    open_issue_count: Optional[int] = 0
    current_debt: Optional[float] = 0.0
    mdi_score: Optional[float] = 100.0
    
    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    """Schema for paginated asset list response."""
    items: List[AssetResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        from_attributes = True


class AssetWithDebt(BaseModel):
    """Asset with current debt information for map display."""
    id: int
    asset_code: str
    name: str
    asset_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    base_repair_cost: float
    current_debt: float = 0.0
    debt_multiplier: float = 1.0
    mdi_score: float = 100.0
    open_issues: int = 0
    overdue_issues: int = 0
    max_delay_days: int = 0
    
    class Config:
        from_attributes = True
