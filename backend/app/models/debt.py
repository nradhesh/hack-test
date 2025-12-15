"""
Debt Snapshot Model - Stores daily debt calculations for assets.

Debt snapshots capture the maintenance debt state at a point in time,
enabling historical tracking and trend analysis.
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, Float, DateTime, Date, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class DebtSnapshot(Base):
    """
    Daily debt snapshot for an asset.
    
    Captures the calculated debt state for trending
    and historical analysis.
    """
    __tablename__ = "debt_snapshots"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to asset
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    
    # Snapshot date
    snapshot_date = Column(Date, nullable=False, index=True)
    
    # Debt calculation results
    total_base_cost = Column(Float, nullable=False, default=0.0)
    total_current_cost = Column(Float, nullable=False, default=0.0)
    total_debt = Column(Float, nullable=False, default=0.0)
    
    # Issue counts
    open_issue_count = Column(Integer, default=0)
    overdue_issue_count = Column(Integer, default=0)
    
    # Aggregated metrics
    avg_delay_days = Column(Float, default=0.0)
    max_delay_days = Column(Integer, default=0)
    avg_debt_multiplier = Column(Float, default=1.0)
    max_debt_multiplier = Column(Float, default=1.0)
    
    # MDI Score for the asset at this point
    mdi_score = Column(Float, default=100.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    asset = relationship("Asset", back_populates="debt_snapshots")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_debt_snapshots_asset_date', 'asset_id', 'snapshot_date'),
    )
    
    def __repr__(self):
        return f"<DebtSnapshot(asset_id={self.asset_id}, date={self.snapshot_date}, debt=${self.total_debt:.2f})>"
    
    @property
    def debt_ratio(self) -> float:
        """Ratio of debt to base cost."""
        if self.total_base_cost <= 0:
            return 0.0
        return self.total_debt / self.total_base_cost
    
    def to_dict(self) -> dict:
        """Convert snapshot to dictionary representation."""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "snapshot_date": self.snapshot_date.isoformat() if self.snapshot_date else None,
            "total_base_cost": self.total_base_cost,
            "total_current_cost": self.total_current_cost,
            "total_debt": self.total_debt,
            "open_issue_count": self.open_issue_count,
            "overdue_issue_count": self.overdue_issue_count,
            "avg_delay_days": self.avg_delay_days,
            "max_delay_days": self.max_delay_days,
            "avg_debt_multiplier": self.avg_debt_multiplier,
            "max_debt_multiplier": self.max_debt_multiplier,
            "mdi_score": self.mdi_score,
            "debt_ratio": self.debt_ratio,
        }


class MaintenanceEvent(Base):
    """
    Record of maintenance activities performed on assets.
    
    Tracks actual maintenance work that resolves issues
    and resets debt accumulation.
    """
    __tablename__ = "maintenance_events"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to asset
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    
    # Event details
    event_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_type = Column(String(50), nullable=False, default="repair")
    description = Column(String(500), nullable=True)
    
    # Cost tracking
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    
    # Debt at time of maintenance
    debt_at_maintenance = Column(Float, default=0.0)
    cost_saved_vs_delay = Column(Float, default=0.0)
    
    # Issues resolved by this maintenance
    issues_resolved_count = Column(Integer, default=0)
    
    # Work details
    performed_by = Column(String(255), nullable=True)
    contractor = Column(String(255), nullable=True)
    work_order_id = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MaintenanceEvent(id={self.id}, asset_id={self.asset_id}, date={self.event_date})>"
    
    def to_dict(self) -> dict:
        """Convert event to dictionary representation."""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "event_type": self.event_type,
            "description": self.description,
            "estimated_cost": self.estimated_cost,
            "actual_cost": self.actual_cost,
            "debt_at_maintenance": self.debt_at_maintenance,
            "cost_saved_vs_delay": self.cost_saved_vs_delay,
            "issues_resolved_count": self.issues_resolved_count,
            "performed_by": self.performed_by,
            "contractor": self.contractor,
        }

