"""
Issue Schemas - Pydantic models for issue API validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class IssueSeverity(str, Enum):
    """Severity levels for maintenance issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueCategory(str, Enum):
    """Categories of maintenance issues."""
    POTHOLE = "pothole"
    CRACK = "crack"
    FLOODING = "flooding"
    BLOCKAGE = "blockage"
    OUTAGE = "outage"
    DAMAGE = "damage"
    WEAR = "wear"
    LEAK = "leak"
    VANDALISM = "vandalism"
    OTHER = "other"


class IssueBase(BaseModel):
    """Base schema for issue data."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    asset_id: int = Field(..., gt=0)
    category: IssueCategory = IssueCategory.OTHER
    severity: IssueSeverity = IssueSeverity.MEDIUM
    estimated_repair_cost: Optional[float] = Field(None, ge=0)
    reported_by: Optional[str] = None
    reporter_contact: Optional[str] = None


class IssueCreate(IssueBase):
    """Schema for creating a new issue."""
    issue_code: Optional[str] = Field(None, max_length=50)
    report_date: Optional[datetime] = None
    
    @field_validator('issue_code', mode='before')
    @classmethod
    def generate_issue_code(cls, v):
        """Generate issue code if not provided."""
        if v is None:
            import uuid
            return f"ISS-{uuid.uuid4().hex[:8].upper()}"
        return v
    
    @field_validator('report_date', mode='before')
    @classmethod
    def set_report_date(cls, v):
        """Set report date to now if not provided."""
        if v is None:
            return datetime.utcnow()
        return v


class IssueUpdate(BaseModel):
    """Schema for updating an existing issue."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[IssueCategory] = None
    severity: Optional[IssueSeverity] = None
    estimated_repair_cost: Optional[float] = Field(None, ge=0)


class IssueResolve(BaseModel):
    """Schema for resolving an issue."""
    resolution_notes: Optional[str] = None
    actual_repair_cost: Optional[float] = Field(None, ge=0)


class IssueResponse(BaseModel):
    """Schema for issue response."""
    id: int
    issue_code: str
    title: str
    description: Optional[str] = None
    asset_id: int
    category: str
    severity: str
    estimated_repair_cost: Optional[float] = None
    actual_repair_cost: Optional[float] = None
    report_date: datetime
    expected_fix_date: Optional[datetime] = None
    resolution_date: Optional[datetime] = None
    is_resolved: bool
    is_overdue: bool = False
    days_open: int = 0
    current_delay_days: int = 0
    current_debt_amount: float = 0.0
    current_debt_multiplier: float = 1.0
    reported_by: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class IssueListResponse(BaseModel):
    """Schema for paginated issue list response."""
    items: List[IssueResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        from_attributes = True


class IssueSummary(BaseModel):
    """Summary of issues for dashboard display."""
    total_issues: int = 0
    open_issues: int = 0
    resolved_issues: int = 0
    overdue_issues: int = 0
    critical_issues: int = 0
    total_debt: float = 0.0
    avg_delay_days: float = 0.0
