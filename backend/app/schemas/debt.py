"""
Debt Schemas - Pydantic models for debt calculations and responses.
"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class DebtCalculation(BaseModel):
    """Individual debt calculation result."""
    issue_id: int
    base_cost: float
    current_cost: float
    maintenance_debt: float
    debt_multiplier: float
    delay_days: int
    expected_fix_date: date
    is_overdue: bool
    decay_rate_used: float


class DebtResponse(BaseModel):
    """Schema for asset debt response."""
    asset_id: int
    asset_code: str
    asset_name: str
    asset_type: str
    
    # Current debt status
    total_base_cost: float
    total_current_cost: float
    total_debt: float
    avg_debt_multiplier: float
    
    # Issue breakdown
    open_issues: int
    overdue_issues: int
    max_delay_days: int
    avg_delay_days: float
    
    # Individual issue debts
    issue_debts: List[DebtCalculation] = []
    
    class Config:
        from_attributes = True


class DebtSnapshotResponse(BaseModel):
    """Schema for debt snapshot history."""
    snapshot_date: date
    total_base_cost: float
    total_current_cost: float
    total_debt: float
    open_issue_count: int
    overdue_issue_count: int
    avg_delay_days: float
    max_delay_days: int
    mdi_score: float


class DebtHistoryResponse(BaseModel):
    """Schema for debt history over time."""
    asset_id: int
    asset_code: str
    asset_name: str
    snapshots: List[DebtSnapshotResponse] = []
    
    # Trend analysis
    debt_trend: str = "stable"  # increasing, decreasing, stable
    debt_change_percent: float = 0.0
    
    class Config:
        from_attributes = True


class DebtSimulationRequest(BaseModel):
    """Request for simulating future debt."""
    asset_id: Optional[int] = None
    issue_id: Optional[int] = None
    base_cost: Optional[float] = Field(None, gt=0)
    report_date: Optional[date] = None
    asset_type: Optional[str] = "road"
    severity: Optional[str] = "medium"
    future_days: int = Field(default=30, ge=1, le=365)


class DebtSimulationPoint(BaseModel):
    """Single point in debt simulation."""
    date: date
    day_offset: int
    base_cost: float
    current_cost: float
    debt: float
    multiplier: float
    delay_days: int
    is_overdue: bool


class DebtSimulationResponse(BaseModel):
    """Response for debt simulation."""
    simulation_points: List[DebtSimulationPoint]
    
    # Summary
    starting_cost: float
    ending_cost: float
    total_debt_accumulated: float
    max_multiplier: float
    
    # Key milestones
    sla_breach_date: Optional[date] = None
    double_cost_date: Optional[date] = None
    triple_cost_date: Optional[date] = None


class WardDebtSummary(BaseModel):
    """Debt summary for a ward."""
    ward_id: int
    ward_name: str
    total_assets: int
    total_debt: float
    total_base_cost: float
    assets_with_debt: int
    avg_debt_per_asset: float
    highest_debt_asset_id: Optional[int] = None
    highest_debt_amount: float = 0.0


class CityDebtSummary(BaseModel):
    """Debt summary for entire city."""
    total_wards: int
    total_assets: int
    total_debt: float
    total_base_cost: float
    ward_summaries: List[WardDebtSummary] = []
    
    # Rankings
    worst_wards: List[WardDebtSummary] = []
    best_wards: List[WardDebtSummary] = []
