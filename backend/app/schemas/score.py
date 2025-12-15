"""
Score Schemas - Pydantic models for MDI score responses.
"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class MDIScoreBase(BaseModel):
    """Base MDI score fields."""
    mdi_score: float = Field(..., ge=0, le=100)
    score_category: str
    description: str
    total_debt: float
    total_base_cost: float


class MDIScoreResponse(MDIScoreBase):
    """Schema for asset MDI score response."""
    asset_id: int
    asset_code: str
    asset_name: str
    asset_type: str
    
    # Current state
    open_issues: int
    overdue_issues: int
    max_delay_days: int
    
    # Trend (if historical data available)
    score_change_7d: Optional[float] = None
    score_change_30d: Optional[float] = None
    score_trend: Optional[str] = None  # improving, declining, stable
    
    class Config:
        from_attributes = True


class MDIScoreHistoryPoint(BaseModel):
    """Single point in score history."""
    date: date
    mdi_score: float
    total_debt: float
    open_issues: int


class MDIScoreHistory(BaseModel):
    """Score history for trending."""
    entity_id: int
    entity_type: str  # asset, ward, city
    entity_name: str
    history: List[MDIScoreHistoryPoint] = []
    current_score: float
    score_change: float
    trend: str


class WardScoreResponse(BaseModel):
    """Schema for ward MDI score response."""
    ward_id: int
    ward_code: str
    ward_name: str
    zone: Optional[str] = None
    
    # Score
    mdi_score: float
    score_category: str
    score_description: str
    
    # Aggregated metrics
    total_debt: float
    total_base_cost: float
    total_assets: int
    assets_with_issues: int
    assets_overdue: int
    
    # Issue counts
    open_issues: int
    overdue_issues: int
    critical_issues: int
    
    # Performance
    avg_delay_days: float
    max_delay_days: int
    
    # Ranking (if provided)
    city_rank: Optional[int] = None
    total_wards: Optional[int] = None
    
    # Trend
    score_change_7d: Optional[float] = None
    score_trend: Optional[str] = None
    
    class Config:
        from_attributes = True


class WardRanking(BaseModel):
    """Ward ranking entry."""
    rank: int
    ward_id: int
    ward_name: str
    mdi_score: float
    score_category: str
    total_debt: float
    score_change: Optional[float] = None


class CityScoreResponse(BaseModel):
    """Schema for city-wide MDI score response."""
    city_code: str
    city_name: str
    
    # Overall score
    mdi_score: float
    score_category: str
    score_description: str
    
    # Aggregated metrics
    total_debt: float
    total_base_cost: float
    total_wards: int
    total_assets: int
    total_open_issues: int
    
    # Ward breakdown
    wards_excellent: int
    wards_good: int
    wards_fair: int
    wards_poor: int
    wards_critical: int
    
    # Rankings
    top_wards: List[WardRanking] = []
    bottom_wards: List[WardRanking] = []
    
    # Trend
    score_change_7d: Optional[float] = None
    score_change_30d: Optional[float] = None
    score_trend: Optional[str] = None
    
    class Config:
        from_attributes = True


class ScoreDashboard(BaseModel):
    """Dashboard summary for quick overview."""
    city_score: float
    city_category: str
    
    # Counts
    total_assets: int
    total_issues: int
    overdue_issues: int
    
    # Debt
    total_city_debt: float
    debt_change_24h: float
    debt_change_7d: float
    
    # Top concerns
    critical_assets: int
    wards_needing_attention: int
    
    # Recent activity
    issues_reported_today: int
    issues_resolved_today: int
