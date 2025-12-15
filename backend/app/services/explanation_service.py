"""
Explanation Service - AI-powered human-readable explanations.

This service generates natural language explanations for debt
calculations, score changes, and maintenance priorities.
"""

from datetime import date, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
import logging
from app.core.config import get_settings
from app.models.asset import Asset
from app.models.issue import Issue
from app.models.ward import Ward
from app.services.debt_service import DebtService
from app.services.aggregation_service import AggregationService
from app.schemas.explanation import (
    ExplanationType,
    ExplanationResponse,
    AssetExplanation,
    WardExplanation,
    CostBreakdown,
    DelayImpact,
)

logger = logging.getLogger(__name__)
settings = get_settings()

class ExplanationService:
    """
    Service for generating human-readable explanations.
    Converts debt calculations and scores into natural
    language that non-technical users can understand.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.debt_service = DebtService(db)
        self.aggregation_service = AggregationService(db)
    
    def explain_asset_debt(self, asset_id: int) -> Optional[AssetExplanation]:
        """
        Generate explanation for an asset's debt status.
        
        Args:
            asset_id: ID of the asset
            
        Returns:
            AssetExplanation with human-readable text
        """
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return None
        
        # Get debt calculation
        debt_response = self.debt_service.get_asset_debt(asset_id)
        if not debt_response:
            return None
        
        # Generate headline
        if debt_response.total_debt <= 0:
            headline = f"✅ {asset.name} is well-maintained with no debt"
        elif debt_response.avg_debt_multiplier < 1.5:
            headline = f"⚠️ {asset.name} has minor maintenance delays"
        elif debt_response.avg_debt_multiplier < 2.0:
            headline = f"🔶 {asset.name} requires attention - costs increasing"
        else:
            headline = f"🔴 {asset.name} is accumulating significant debt"
        
        # Generate summary
        if debt_response.open_issues == 0:
            summary = f"This {asset.asset_type.value} currently has no open maintenance issues."
        else:
            summary = (
                f"This {asset.asset_type.value} has {debt_response.open_issues} open "
                f"maintenance issue{'s' if debt_response.open_issues > 1 else ''}, "
                f"of which {debt_response.overdue_issues} "
                f"{'are' if debt_response.overdue_issues > 1 else 'is'} overdue."
            )
        
        # Debt explanation
        if debt_response.total_debt > 0:
            debt_explanation = (
                f"Due to maintenance delays, the total repair cost has increased from "
                f"₹{debt_response.total_base_cost:,.0f} to ₹{debt_response.total_current_cost:,.0f}, "
                f"an increase of ₹{debt_response.total_debt:,.0f} "
                f"({debt_response.avg_debt_multiplier:.1f}× the original cost)."
            )
        else:
            debt_explanation = "No additional costs have accumulated from delays."
        
        # Cost increase reason
        if debt_response.max_delay_days > 0:
            cost_reason = (
                f"The cost has increased because maintenance has been delayed by up to "
                f"{debt_response.max_delay_days} days past the SLA deadline. Each day of delay "
                f"compounds the damage and increases repair complexity."
            )
        else:
            cost_reason = "All issues are within their SLA window - no cost increase yet."
        
        # SLA status
        if debt_response.overdue_issues > 0:
            sla_status = f"⚠️ SLA BREACHED for {debt_response.overdue_issues} issue(s)"
        elif debt_response.open_issues > 0:
            sla_status = "✅ Within SLA timeline"
        else:
            sla_status = "No active issues"
        
        # Future projections
        simulation = self.debt_service.simulate_future_debt(
            asset_id=asset_id,
            future_days=30
        )
        
        cost_in_7d = simulation.simulation_points[7].current_cost if len(simulation.simulation_points) > 7 else debt_response.total_current_cost
        cost_in_30d = simulation.simulation_points[-1].current_cost if simulation.simulation_points else debt_response.total_current_cost
        
        # Recommendation
        if debt_response.total_debt <= 0:
            recommendation = "Continue regular maintenance schedule."
            urgency = "low"
        elif debt_response.avg_debt_multiplier < 1.5:
            recommendation = "Schedule maintenance within the next week to prevent cost escalation."
            urgency = "normal"
        elif debt_response.avg_debt_multiplier < 2.0:
            recommendation = "Prioritize maintenance immediately - costs are rising rapidly."
            urgency = "high"
        else:
            recommendation = "URGENT: Immediate maintenance required to prevent further cost explosion."
            urgency = "critical"
        
        return AssetExplanation(
            asset_id=asset.id,
            asset_code=asset.asset_code,
            asset_name=asset.name,
            asset_type=asset.asset_type.value,
            headline=headline,
            summary=summary,
            debt_explanation=debt_explanation,
            cost_increase_reason=cost_reason,
            sla_status=sla_status,
            days_overdue=debt_response.max_delay_days,
            expected_fix_date=None,  # TODO: Get from latest issue
            original_cost=debt_response.total_base_cost,
            current_cost=debt_response.total_current_cost,
            additional_cost=debt_response.total_debt,
            cost_multiplier=debt_response.avg_debt_multiplier,
            cost_if_delayed_7d=cost_in_7d,
            cost_if_delayed_30d=cost_in_30d,
            recommended_action=recommendation,
            urgency_level=urgency,
        )
    
    def explain_ward_score(self, ward_id: int) -> Optional[WardExplanation]:
        """
        Generate explanation for a ward's MDI score.
        
        Args:
            ward_id: ID of the ward
            
        Returns:
            WardExplanation with human-readable text
        """
        ward = self.db.query(Ward).filter(Ward.id == ward_id).first()
        if not ward:
            return None
        
        # Get ward score
        score = self.aggregation_service.calculate_ward_score(ward_id)
        if not score:
            return None
        
        # Generate headline
        if score.mdi_score >= 90:
            headline = f"🌟 {ward.name} is in excellent condition"
        elif score.mdi_score >= 70:
            headline = f"✅ {ward.name} is well-maintained"
        elif score.mdi_score >= 50:
            headline = f"⚠️ {ward.name} needs attention"
        elif score.mdi_score >= 30:
            headline = f"🔶 {ward.name} has significant maintenance backlog"
        else:
            headline = f"🔴 {ward.name} requires urgent intervention"
        
        # Generate summary
        summary = (
            f"{ward.name} has an MDI score of {score.mdi_score:.1f}/100, "
            f"categorized as '{score.score_category}'. "
            f"It contains {score.total_assets} infrastructure assets, "
            f"of which {score.assets_with_issues} have open maintenance issues."
        )
        
        # Score explanation
        if score.total_debt <= 0:
            score_explanation = (
                "This ward has no accumulated maintenance debt, indicating all issues "
                "are being addressed within SLA timelines."
            )
        else:
            score_explanation = (
                f"This ward has accumulated ₹{score.total_debt:,.0f} in maintenance debt "
                f"across its assets. The debt represents additional costs incurred due to "
                f"delayed repairs, where neglect has allowed issues to worsen."
            )
        
        # Contributing factors
        factors = []
        if score.overdue_issues > 0:
            factors.append(f"{score.overdue_issues} overdue maintenance issues")
        if score.avg_delay_days > 0:
            factors.append(f"Average delay of {score.avg_delay_days:.0f} days past SLA")
        if score.critical_issues > 0:
            factors.append(f"{score.critical_issues} critical severity issues pending")
        if score.total_debt > score.total_base_cost * 0.5:
            factors.append("Accumulated debt exceeds 50% of base maintenance costs")
        
        if not factors:
            factors.append("Infrastructure is well-maintained")
        
        # Top priorities
        priorities = []
        if score.critical_issues > 0:
            priorities.append(f"Immediately address {score.critical_issues} critical issues")
        if score.overdue_issues > 0:
            priorities.append(f"Resolve {score.overdue_issues} overdue issues to stop debt growth")
        if score.assets_overdue > 0:
            priorities.append(f"Audit {score.assets_overdue} assets with overdue maintenance")
        
        if not priorities:
            priorities.append("Continue current maintenance schedule")
        
        # Estimated cost to improve
        # Rough estimate: fixing debt + 20% overhead
        cost_to_improve = score.total_debt * 1.2 if score.total_debt > 0 else 0
        
        return WardExplanation(
            ward_id=ward.id,
            ward_name=ward.name,
            headline=headline,
            summary=summary,
            score_explanation=score_explanation,
            main_contributing_factors=factors,
            total_assets=score.total_assets,
            problem_assets=score.assets_with_issues,
            critical_assets=score.assets_overdue,
            total_debt=score.total_debt,
            debt_trend=score.score_trend or "stable",
            city_average_score=None,  # TODO: Calculate
            rank_in_city=None,  # TODO: Calculate
            top_priorities=priorities,
            estimated_cost_to_improve=cost_to_improve,
        )
    
    def generate_explanation(
        self,
        explanation_type: ExplanationType,
        entity_id: Optional[int] = None,
        include_recommendations: bool = True
    ) -> ExplanationResponse:
        """
        Generate a generic explanation based on type.
        
        Args:
            explanation_type: Type of explanation to generate
            entity_id: ID of the entity (asset, ward, etc.)
            include_recommendations: Whether to include action items
            
        Returns:
            ExplanationResponse with explanation text
        """
        if explanation_type == ExplanationType.ASSET_DEBT and entity_id:
            asset_exp = self.explain_asset_debt(entity_id)
            if asset_exp:
                return ExplanationResponse(
                    explanation_type=explanation_type.value,
                    entity_id=entity_id,
                    entity_type="asset",
                    summary=asset_exp.headline,
                    detailed_explanation=f"{asset_exp.summary}\n\n{asset_exp.debt_explanation}",
                    key_facts=[
                        f"Original cost: ₹{asset_exp.original_cost:,.0f}",
                        f"Current cost: ₹{asset_exp.current_cost:,.0f}",
                        f"Cost multiplier: {asset_exp.cost_multiplier:.1f}×",
                        f"Days overdue: {asset_exp.days_overdue}",
                    ],
                    cost_breakdown=CostBreakdown(
                        original_cost=asset_exp.original_cost,
                        current_cost=asset_exp.current_cost,
                        increase_amount=asset_exp.additional_cost,
                        increase_percentage=((asset_exp.cost_multiplier - 1) * 100),
                        delay_contribution=asset_exp.additional_cost * 0.8,  # Estimate
                        severity_contribution=asset_exp.additional_cost * 0.2,
                    ),
                    delay_impact=DelayImpact(
                        delay_days=asset_exp.days_overdue,
                        extra_cost_incurred=asset_exp.additional_cost,
                        multiplier_applied=asset_exp.cost_multiplier,
                        potential_future_cost=asset_exp.cost_if_delayed_30d,
                        recommended_action=asset_exp.recommended_action,
                    ),
                    recommendations=[asset_exp.recommended_action] if include_recommendations else [],
                    urgency=asset_exp.urgency_level,
                )
        
        elif explanation_type == ExplanationType.WARD_SCORE and entity_id:
            ward_exp = self.explain_ward_score(entity_id)
            if ward_exp:
                return ExplanationResponse(
                    explanation_type=explanation_type.value,
                    entity_id=entity_id,
                    entity_type="ward",
                    summary=ward_exp.headline,
                    detailed_explanation=f"{ward_exp.summary}\n\n{ward_exp.score_explanation}",
                    key_facts=[
                        f"Total assets: {ward_exp.total_assets}",
                        f"Problem assets: {ward_exp.problem_assets}",
                        f"Total debt: ₹{ward_exp.total_debt:,.0f}",
                        f"Debt trend: {ward_exp.debt_trend}",
                    ],
                    recommendations=ward_exp.top_priorities if include_recommendations else [],
                    urgency="high" if ward_exp.critical_assets > 0 else "normal",
                )
        
        # Default response
        return ExplanationResponse(
            explanation_type=explanation_type.value,
            summary="Unable to generate explanation",
            detailed_explanation="The requested entity was not found or data is unavailable.",
            key_facts=[],
            recommendations=[],
            urgency="normal",
        )
    
    def generate_cost_comparison(
        self,
        asset_id: int,
        days_to_compare: List[int] = [0, 7, 14, 30, 60]
    ) -> str:
        """
        Generate a cost comparison showing the impact of waiting.
        
        Returns text explaining how costs increase over different timeframes.
        """
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return "Asset not found"
        
        debt_response = self.debt_service.get_asset_debt(asset_id)
        if not debt_response:
            return "Unable to calculate debt"
        
        simulation = self.debt_service.simulate_future_debt(
            asset_id=asset_id,
            future_days=max(days_to_compare)
        )
        
        lines = [
            f"## Cost of Waiting: {asset.name}",
            "",
            "| Wait Period | Repair Cost | Extra Cost | Multiplier |",
            "|-------------|-------------|------------|------------|",
        ]
        
        for day in days_to_compare:
            if day < len(simulation.simulation_points):
                point = simulation.simulation_points[day]
                extra = point.current_cost - point.base_cost
                lines.append(
                    f"| {day} days | ₹{point.current_cost:,.0f} | "
                    f"+₹{extra:,.0f} | {point.multiplier:.2f}× |"
                )
        
        lines.append("")
        lines.append(
            f"**Conclusion**: Delaying maintenance by {days_to_compare[-1]} days would cost "
            f"an additional ₹{simulation.total_debt_accumulated:,.0f}. "
            f"Acting now saves money."
        )
        
        return "\n".join(lines)
