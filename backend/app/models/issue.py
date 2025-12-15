"""
Issue Model - Represents maintenance issues reported for assets.

Issues track reported problems, their severity, and resolution status.
Each issue contributes to the maintenance debt when unresolved past SLA.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class IssueSeverity(str, enum.Enum):
    """Severity levels for maintenance issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueCategory(str, enum.Enum):
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


class Issue(Base):
    """
    Maintenance issue model.
    
    Represents a reported problem with an urban asset
    that requires maintenance attention.
    """
    __tablename__ = "issues"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Issue identification
    issue_code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Link to asset
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    
    # Issue classification
    category = Column(
        SQLEnum(IssueCategory),
        nullable=False,
        default=IssueCategory.OTHER
    )
    severity = Column(
        SQLEnum(IssueSeverity),
        nullable=False,
        default=IssueSeverity.MEDIUM,
        index=True
    )
    
    # Cost estimation
    estimated_repair_cost = Column(Float, nullable=True)
    actual_repair_cost = Column(Float, nullable=True)
    
    # Timeline tracking
    report_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    expected_fix_date = Column(DateTime, nullable=True)
    resolution_date = Column(DateTime, nullable=True)
    
    # Status
    is_resolved = Column(Boolean, default=False, index=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Reporter information
    reported_by = Column(String(255), nullable=True)
    reporter_contact = Column(String(255), nullable=True)
    
    # Current debt tracking (updated by debt engine)
    current_delay_days = Column(Integer, default=0)
    current_debt_amount = Column(Float, default=0.0)
    current_debt_multiplier = Column(Float, default=1.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = relationship("Asset", back_populates="issues")
    
    def __repr__(self):
        return f"<Issue(id={self.id}, code='{self.issue_code}', resolved={self.is_resolved})>"
    
    @property
    def is_overdue(self) -> bool:
        """Check if issue is past its expected fix date."""
        if self.is_resolved:
            return False
        if self.expected_fix_date is None:
            return False
        return datetime.utcnow() > self.expected_fix_date
    
    @property
    def days_open(self) -> int:
        """Number of days since issue was reported."""
        end_date = self.resolution_date if self.is_resolved else datetime.utcnow()
        return (end_date - self.report_date).days
    
    def resolve(self, notes: str = None, actual_cost: float = None):
        """Mark the issue as resolved."""
        self.is_resolved = True
        self.resolution_date = datetime.utcnow()
        if notes:
            self.resolution_notes = notes
        if actual_cost is not None:
            self.actual_repair_cost = actual_cost
    
    def to_dict(self) -> dict:
        """Convert issue to dictionary representation."""
        return {
            "id": self.id,
            "issue_code": self.issue_code,
            "title": self.title,
            "description": self.description,
            "asset_id": self.asset_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "estimated_repair_cost": self.estimated_repair_cost,
            "actual_repair_cost": self.actual_repair_cost,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "expected_fix_date": self.expected_fix_date.isoformat() if self.expected_fix_date else None,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None,
            "is_resolved": self.is_resolved,
            "is_overdue": self.is_overdue,
            "days_open": self.days_open,
            "current_delay_days": self.current_delay_days,
            "current_debt_amount": self.current_debt_amount,
            "current_debt_multiplier": self.current_debt_multiplier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
