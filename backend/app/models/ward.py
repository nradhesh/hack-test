"""
Ward Model - Represents administrative divisions of the city.

Wards aggregate assets and provide geographic grouping
for MDI score calculations.
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Index

from app.core.database import Base


class Ward(Base):
    """
    Administrative ward/district model.
    
    Represents a geographic division of the city
    for aggregating infrastructure data.
    """
    __tablename__ = "wards"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Ward identification
    ward_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Center point for display (simple lat/lng)
    center_latitude = Column(Float, nullable=True)
    center_longitude = Column(Float, nullable=True)
    
    # Administrative info
    zone = Column(String(100), nullable=True)
    population = Column(Integer, nullable=True)
    area_sq_km = Column(Float, nullable=True)
    
    # Contact information
    ward_officer = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Ward(id={self.id}, code='{self.ward_code}', name='{self.name}')>"
    
    def to_dict(self) -> dict:
        """Convert ward to dictionary representation."""
        return {
            "id": self.id,
            "ward_code": self.ward_code,
            "name": self.name,
            "description": self.description,
            "center_latitude": self.center_latitude,
            "center_longitude": self.center_longitude,
            "zone": self.zone,
            "population": self.population,
            "area_sq_km": self.area_sq_km,
            "ward_officer": self.ward_officer,
        }


class WardScore(Base):
    """
    Daily MDI score snapshot for a ward.
    
    Aggregates all asset scores within the ward
    for historical tracking.
    """
    __tablename__ = "ward_scores"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to ward
    ward_id = Column(Integer, nullable=False, index=True)
    
    # Score date
    score_date = Column(Date, nullable=False, index=True)
    
    # MDI Score
    mdi_score = Column(Float, nullable=False, default=100.0)
    score_category = Column(String(50), default="Excellent")
    
    # Aggregated debt metrics
    total_debt = Column(Float, default=0.0)
    total_base_cost = Column(Float, default=0.0)
    
    # Asset counts
    total_assets = Column(Integer, default=0)
    assets_with_issues = Column(Integer, default=0)
    assets_overdue = Column(Integer, default=0)
    
    # Issue counts
    total_open_issues = Column(Integer, default=0)
    total_overdue_issues = Column(Integer, default=0)
    
    # Delay metrics
    avg_delay_days = Column(Float, default=0.0)
    max_delay_days = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_ward_scores_ward_date', 'ward_id', 'score_date'),
    )
    
    def __repr__(self):
        return f"<WardScore(ward_id={self.ward_id}, date={self.score_date}, score={self.mdi_score:.1f})>"
    
    def to_dict(self) -> dict:
        """Convert score to dictionary representation."""
        return {
            "id": self.id,
            "ward_id": self.ward_id,
            "score_date": self.score_date.isoformat() if self.score_date else None,
            "mdi_score": self.mdi_score,
            "score_category": self.score_category,
            "total_debt": self.total_debt,
            "total_base_cost": self.total_base_cost,
            "total_assets": self.total_assets,
            "assets_with_issues": self.assets_with_issues,
            "assets_overdue": self.assets_overdue,
            "total_open_issues": self.total_open_issues,
            "total_overdue_issues": self.total_overdue_issues,
            "avg_delay_days": self.avg_delay_days,
            "max_delay_days": self.max_delay_days,
        }


class CityScore(Base):
    """
    Daily MDI score for the entire city.
    
    Aggregates all ward scores for city-wide tracking.
    """
    __tablename__ = "city_scores"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # City identifier (for multi-city support)
    city_code = Column(String(50), nullable=False, default="default", index=True)
    
    # Score date
    score_date = Column(Date, nullable=False, index=True)
    
    # MDI Score
    mdi_score = Column(Float, nullable=False, default=100.0)
    score_category = Column(String(50), default="Excellent")
    
    # Aggregated metrics
    total_debt = Column(Float, default=0.0)
    total_base_cost = Column(Float, default=0.0)
    
    # Counts
    total_wards = Column(Integer, default=0)
    total_assets = Column(Integer, default=0)
    total_open_issues = Column(Integer, default=0)
    
    # Performance metrics
    wards_excellent = Column(Integer, default=0)
    wards_good = Column(Integer, default=0)
    wards_fair = Column(Integer, default=0)
    wards_poor = Column(Integer, default=0)
    wards_critical = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Composite index
    __table_args__ = (
        Index('ix_city_scores_city_date', 'city_code', 'score_date'),
    )
    
    def __repr__(self):
        return f"<CityScore(city='{self.city_code}', date={self.score_date}, score={self.mdi_score:.1f})>"
    
    def to_dict(self) -> dict:
        """Convert score to dictionary representation."""
        return {
            "id": self.id,
            "city_code": self.city_code,
            "score_date": self.score_date.isoformat() if self.score_date else None,
            "mdi_score": self.mdi_score,
            "score_category": self.score_category,
            "total_debt": self.total_debt,
            "total_base_cost": self.total_base_cost,
            "total_wards": self.total_wards,
            "total_assets": self.total_assets,
            "total_open_issues": self.total_open_issues,
            "ward_breakdown": {
                "excellent": self.wards_excellent,
                "good": self.wards_good,
                "fair": self.wards_fair,
                "poor": self.wards_poor,
                "critical": self.wards_critical,
            },
        }
