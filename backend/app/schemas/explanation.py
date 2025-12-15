"""
Explanation Schemas - Pydantic models for AI-powered explanations.
"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ExplanationType(str, Enum):
    """Types of explanations available."""
    ASSET_DEBT = "asset_debt"
    ASSET_SCORE = "asset_score"
    WARD_SCORE = "ward_score"
    CITY_SCORE = "city_score"
    COST_INCREASE = "cost_increase"
    PRIORITY_RANKING = "priority_ranking"
    DELAY_IMPACT = "delay_impact"


class ExplanationRequest(BaseModel):
    """Request for generating an explanation."""
    explanation_type: ExplanationType
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None  # asset, ward, city
    include_recommendations: bool = True
    include_comparison: bool = False
    language: str = "en"


class CostBreakdown(BaseModel):
    """Breakdown of cost increase factors."""
    original_cost: float
    current_cost: float
    increase_amount: float
    increase_percentage: float
    delay_contribution: float
    severity_contribution: float


class DelayImpact(BaseModel):
    """Impact analysis of maintenance delay."""
    delay_days: int
    extra_cost_incurred: float
    multiplier_applied: float
    potential_future_cost: float
    recommended_action: str


class ExplanationResponse(BaseModel):
    """Response containing human-readable explanation."""
    explanation_type: str
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None
    
    # Main explanation text
    summary: str
    detailed_explanation: str
    
    # Key metrics highlighted
    key_facts: List[str] = []
    
    # Cost analysis (if applicable)
    cost_breakdown: Optional[CostBreakdown] = None
    
    # Delay analysis (if applicable)
    delay_impact: Optional[DelayImpact] = None
    
    # Recommendations
    recommendations: List[str] = []
    
    # Priority level
    urgency: str = "normal"  # low, normal, high, critical
    
    # Comparison (if requested)
    comparison_text: Optional[str] = None
    
    class Config:
        from_attributes = True


class AssetExplanation(BaseModel):
    """Detailed explanation for an asset's debt status."""
    asset_id: int
    asset_code: str
    asset_name: str
    asset_type: str
    
    # Summary
    headline: str
    summary: str
    
    # Debt explanation
    debt_explanation: str
    cost_increase_reason: str
    
    # Timeline
    sla_status: str
    days_overdue: int
    expected_fix_date: Optional[date] = None
    
    # Financial impact
    original_cost: float
    current_cost: float
    additional_cost: float
    cost_multiplier: float
    
    # Future projection
    cost_if_delayed_7d: float
    cost_if_delayed_30d: float
    
    # Recommendation
    recommended_action: str
    urgency_level: str


class WardExplanation(BaseModel):
    """Detailed explanation for a ward's score."""
    ward_id: int
    ward_name: str
    
    # Summary
    headline: str
    summary: str
    
    # Score explanation
    score_explanation: str
    main_contributing_factors: List[str] = []
    
    # Asset breakdown
    total_assets: int
    problem_assets: int
    critical_assets: int
    
    # Financial summary
    total_debt: float
    debt_trend: str
    
    # Comparison
    city_average_score: Optional[float] = None
    rank_in_city: Optional[int] = None
    
    # Recommendations
    top_priorities: List[str] = []
    estimated_cost_to_improve: float


class PriorityExplanation(BaseModel):
    """Explanation of maintenance prioritization."""
    entity_type: str
    priorities: List[dict] = []
    
    methodology_explanation: str
    ranking_factors: List[str] = []
    
    top_recommendation: str
    estimated_savings_if_acted: float
