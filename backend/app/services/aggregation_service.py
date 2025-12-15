"""
Aggregation Service - Business logic for aggregating scores at ward and city levels.

This service aggregates asset-level debt and scores up to ward
and city-wide metrics.
"""

from datetime import date, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.core.debt_engine import MDIScoreCalculator
from app.core.config import get_settings
from app.models.asset import Asset
from app.models.issue import Issue
from app.models.debt import DebtSnapshot
from app.models.ward import Ward, WardScore, CityScore
from app.schemas.score import (
    MDIScoreResponse,
    WardScoreResponse,
    CityScoreResponse,
    WardRanking,
    MDIScoreHistoryPoint,
)
from app.services.debt_service import DebtService

logger = logging.getLogger(__name__)
settings = get_settings()


class AggregationService:
    """
    Service for aggregating MDI scores across organizational levels.
    
    Provides methods for:
    - Calculating ward-level aggregated scores
    - Calculating city-wide scores
    - Ranking wards and assets
    - Historical score tracking
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.mdi_calculator = MDIScoreCalculator()
        self.debt_service = DebtService(db)
    
    def get_asset_mdi_score(self, asset_id: int) -> Optional[MDIScoreResponse]:
        """
        Get MDI score for a single asset.
        
        Args:
            asset_id: ID of the asset
            
        Returns:
            MDIScoreResponse with score details
        """
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return None
        
        # Calculate current debt
        issue_debts, total_debt, total_base_cost = self.debt_service.calculate_asset_debt(asset)
        
        # Calculate MDI score
        mdi_result = self.mdi_calculator.calculate_score(total_debt, total_base_cost)
        
        # Get metrics
        overdue_count = sum(1 for d in issue_debts if d.is_overdue)
        max_delay = max((d.delay_days for d in issue_debts if d.is_overdue), default=0)
        
        # Get historical trend
        score_change_7d = None
        score_change_30d = None
        score_trend = "stable"
        
        week_ago = date.today() - timedelta(days=7)
        month_ago = date.today() - timedelta(days=30)
        
        snapshot_7d = self.db.query(DebtSnapshot).filter(
            DebtSnapshot.asset_id == asset_id,
            DebtSnapshot.snapshot_date == week_ago
        ).first()
        
        snapshot_30d = self.db.query(DebtSnapshot).filter(
            DebtSnapshot.asset_id == asset_id,
            DebtSnapshot.snapshot_date == month_ago
        ).first()
        
        if snapshot_7d:
            score_change_7d = mdi_result.score - snapshot_7d.mdi_score
        if snapshot_30d:
            score_change_30d = mdi_result.score - snapshot_30d.mdi_score
        
        if score_change_7d is not None:
            if score_change_7d > 5:
                score_trend = "improving"
            elif score_change_7d < -5:
                score_trend = "declining"
        
        return MDIScoreResponse(
            asset_id=asset.id,
            asset_code=asset.asset_code,
            asset_name=asset.name,
            asset_type=asset.asset_type.value,
            mdi_score=mdi_result.score,
            score_category=mdi_result.category,
            description=mdi_result.description,
            total_debt=total_debt,
            total_base_cost=total_base_cost,
            open_issues=len(issue_debts),
            overdue_issues=overdue_count,
            max_delay_days=max_delay,
            score_change_7d=score_change_7d,
            score_change_30d=score_change_30d,
            score_trend=score_trend,
        )
    
    def calculate_ward_score(
        self,
        ward_id: int,
        score_date: Optional[date] = None
    ) -> Optional[WardScoreResponse]:
        """
        Calculate aggregated MDI score for a ward.
        
        Args:
            ward_id: ID of the ward
            score_date: Date to calculate for (defaults to today)
            
        Returns:
            WardScoreResponse with aggregated metrics
        """
        if score_date is None:
            score_date = date.today()
        
        # Get ward
        ward = self.db.query(Ward).filter(Ward.id == ward_id).first()
        if not ward:
            return None
        
        # Get all assets in ward
        from app.models.asset import AssetStatus
        assets = self.db.query(Asset).filter(
            Asset.ward_id == ward_id,
            Asset.status == AssetStatus.ACTIVE
        ).all()
        
        if not assets:
            # Empty ward, perfect score
            return WardScoreResponse(
                ward_id=ward.id,
                ward_code=ward.ward_code,
                ward_name=ward.name,
                zone=ward.zone,
                mdi_score=100.0,
                score_category="Excellent",
                score_description="No assets or all assets well-maintained",
                total_debt=0.0,
                total_base_cost=0.0,
                total_assets=0,
                assets_with_issues=0,
                assets_overdue=0,
                open_issues=0,
                overdue_issues=0,
                critical_issues=0,
                avg_delay_days=0.0,
                max_delay_days=0,
            )
        
        # Aggregate metrics
        total_debt = 0.0
        total_base_cost = 0.0
        assets_with_issues = 0
        assets_overdue = 0
        total_open_issues = 0
        total_overdue_issues = 0
        critical_issues = 0
        all_delays = []
        max_delay = 0
        
        for asset in assets:
            issue_debts, debt, base_cost = self.debt_service.calculate_asset_debt(
                asset, score_date
            )
            total_debt += debt
            total_base_cost += base_cost
            
            if issue_debts:
                assets_with_issues += 1
                total_open_issues += len(issue_debts)
                
                overdue = [d for d in issue_debts if d.is_overdue]
                if overdue:
                    assets_overdue += 1
                    total_overdue_issues += len(overdue)
                    delays = [d.delay_days for d in overdue]
                    all_delays.extend(delays)
                    max_delay = max(max_delay, max(delays))
            
            # Count critical issues
            for issue in asset.issues:
                if not issue.is_resolved and issue.severity.value == "critical":
                    critical_issues += 1
        
        # Calculate MDI score
        mdi_result = self.mdi_calculator.calculate_score(total_debt, total_base_cost)
        
        # Calculate average delay
        avg_delay = sum(all_delays) / len(all_delays) if all_delays else 0.0
        
        # Get trend
        week_ago = score_date - timedelta(days=7)
        prev_score = self.db.query(WardScore).filter(
            WardScore.ward_id == ward_id,
            WardScore.score_date == week_ago
        ).first()
        
        score_change_7d = None
        score_trend = "stable"
        if prev_score:
            score_change_7d = mdi_result.score - prev_score.mdi_score
            if score_change_7d > 5:
                score_trend = "improving"
            elif score_change_7d < -5:
                score_trend = "declining"
        
        return WardScoreResponse(
            ward_id=ward.id,
            ward_code=ward.ward_code,
            ward_name=ward.name,
            zone=ward.zone,
            mdi_score=mdi_result.score,
            score_category=mdi_result.category,
            score_description=mdi_result.description,
            total_debt=total_debt,
            total_base_cost=total_base_cost,
            total_assets=len(assets),
            assets_with_issues=assets_with_issues,
            assets_overdue=assets_overdue,
            open_issues=total_open_issues,
            overdue_issues=total_overdue_issues,
            critical_issues=critical_issues,
            avg_delay_days=avg_delay,
            max_delay_days=max_delay,
            score_change_7d=score_change_7d,
            score_trend=score_trend,
        )
    
    def save_ward_score(self, ward_id: int, score_date: Optional[date] = None) -> Optional[WardScore]:
        """
        Calculate and save ward score to database.
        
        Args:
            ward_id: ID of the ward
            score_date: Date for the score
            
        Returns:
            Created or updated WardScore
        """
        if score_date is None:
            score_date = date.today()
        
        # Calculate score
        ward_score_response = self.calculate_ward_score(ward_id, score_date)
        if not ward_score_response:
            return None
        
        # Check for existing
        existing = self.db.query(WardScore).filter(
            WardScore.ward_id == ward_id,
            WardScore.score_date == score_date
        ).first()
        
        if existing:
            score_record = existing
        else:
            score_record = WardScore(ward_id=ward_id, score_date=score_date)
        
        # Update fields
        score_record.mdi_score = ward_score_response.mdi_score
        score_record.score_category = ward_score_response.score_category
        score_record.total_debt = ward_score_response.total_debt
        score_record.total_base_cost = ward_score_response.total_base_cost
        score_record.total_assets = ward_score_response.total_assets
        score_record.assets_with_issues = ward_score_response.assets_with_issues
        score_record.assets_overdue = ward_score_response.assets_overdue
        score_record.total_open_issues = ward_score_response.open_issues
        score_record.total_overdue_issues = ward_score_response.overdue_issues
        score_record.avg_delay_days = ward_score_response.avg_delay_days
        score_record.max_delay_days = ward_score_response.max_delay_days
        
        self.db.add(score_record)
        self.db.commit()
        self.db.refresh(score_record)
        
        return score_record
    
    def calculate_city_score(
        self,
        city_code: str = "default",
        score_date: Optional[date] = None
    ) -> CityScoreResponse:
        """
        Calculate city-wide aggregated MDI score.
        
        Args:
            city_code: City identifier
            score_date: Date to calculate for
            
        Returns:
            CityScoreResponse with city-wide metrics
        """
        if score_date is None:
            score_date = date.today()
        
        # Get all wards
        wards = self.db.query(Ward).all()
        
        # Calculate scores for all wards
        ward_scores = []
        total_debt = 0.0
        total_base_cost = 0.0
        total_assets = 0
        total_open_issues = 0
        
        category_counts = {
            "excellent": 0,
            "good": 0,
            "fair": 0,
            "poor": 0,
            "critical": 0,
        }
        
        for ward in wards:
            score = self.calculate_ward_score(ward.id, score_date)
            if score:
                ward_scores.append(score)
                total_debt += score.total_debt
                total_base_cost += score.total_base_cost
                total_assets += score.total_assets
                total_open_issues += score.open_issues
                
                # Count by category
                cat_lower = score.score_category.lower()
                if cat_lower in category_counts:
                    category_counts[cat_lower] += 1
        
        # Calculate city MDI score
        mdi_result = self.mdi_calculator.calculate_score(total_debt, total_base_cost)
        
        # Sort wards for rankings
        sorted_wards = sorted(ward_scores, key=lambda w: w.mdi_score, reverse=True)
        
        top_wards = [
            WardRanking(
                rank=i + 1,
                ward_id=w.ward_id,
                ward_name=w.ward_name,
                mdi_score=w.mdi_score,
                score_category=w.score_category,
                total_debt=w.total_debt,
                score_change=w.score_change_7d,
            )
            for i, w in enumerate(sorted_wards[:5])
        ]
        
        bottom_wards = [
            WardRanking(
                rank=len(sorted_wards) - i,
                ward_id=w.ward_id,
                ward_name=w.ward_name,
                mdi_score=w.mdi_score,
                score_category=w.score_category,
                total_debt=w.total_debt,
                score_change=w.score_change_7d,
            )
            for i, w in enumerate(reversed(sorted_wards[-5:]))
        ]
        
        # Get trend
        week_ago = score_date - timedelta(days=7)
        month_ago = score_date - timedelta(days=30)
        
        prev_score_7d = self.db.query(CityScore).filter(
            CityScore.city_code == city_code,
            CityScore.score_date == week_ago
        ).first()
        
        prev_score_30d = self.db.query(CityScore).filter(
            CityScore.city_code == city_code,
            CityScore.score_date == month_ago
        ).first()
        
        score_change_7d = None
        score_change_30d = None
        score_trend = "stable"
        
        if prev_score_7d:
            score_change_7d = mdi_result.score - prev_score_7d.mdi_score
            if score_change_7d > 5:
                score_trend = "improving"
            elif score_change_7d < -5:
                score_trend = "declining"
        
        if prev_score_30d:
            score_change_30d = mdi_result.score - prev_score_30d.mdi_score
        
        return CityScoreResponse(
            city_code=city_code,
            city_name="City",  # Could be configurable
            mdi_score=mdi_result.score,
            score_category=mdi_result.category,
            score_description=mdi_result.description,
            total_debt=total_debt,
            total_base_cost=total_base_cost,
            total_wards=len(wards),
            total_assets=total_assets,
            total_open_issues=total_open_issues,
            wards_excellent=category_counts["excellent"],
            wards_good=category_counts["good"],
            wards_fair=category_counts["fair"],
            wards_poor=category_counts["poor"],
            wards_critical=category_counts["critical"],
            top_wards=top_wards,
            bottom_wards=bottom_wards,
            score_change_7d=score_change_7d,
            score_change_30d=score_change_30d,
            score_trend=score_trend,
        )
    
    def save_city_score(
        self,
        city_code: str = "default",
        score_date: Optional[date] = None
    ) -> CityScore:
        """
        Calculate and save city score to database.
        """
        if score_date is None:
            score_date = date.today()
        
        city_score_response = self.calculate_city_score(city_code, score_date)
        
        # Check for existing
        existing = self.db.query(CityScore).filter(
            CityScore.city_code == city_code,
            CityScore.score_date == score_date
        ).first()
        
        if existing:
            score_record = existing
        else:
            score_record = CityScore(city_code=city_code, score_date=score_date)
        
        # Update fields
        score_record.mdi_score = city_score_response.mdi_score
        score_record.score_category = city_score_response.score_category
        score_record.total_debt = city_score_response.total_debt
        score_record.total_base_cost = city_score_response.total_base_cost
        score_record.total_wards = city_score_response.total_wards
        score_record.total_assets = city_score_response.total_assets
        score_record.total_open_issues = city_score_response.total_open_issues
        score_record.wards_excellent = city_score_response.wards_excellent
        score_record.wards_good = city_score_response.wards_good
        score_record.wards_fair = city_score_response.wards_fair
        score_record.wards_poor = city_score_response.wards_poor
        score_record.wards_critical = city_score_response.wards_critical
        
        self.db.add(score_record)
        self.db.commit()
        self.db.refresh(score_record)
        
        return score_record
    
    def calculate_all_scores(self) -> None:
        """
        Calculate and save scores for all wards and city.
        
        Called by background worker for daily score updates.
        """
        today = date.today()
        
        # Update all ward scores
        wards = self.db.query(Ward).all()
        logger.info(f"Calculating scores for {len(wards)} wards")
        
        for ward in wards:
            try:
                self.save_ward_score(ward.id, today)
            except Exception as e:
                logger.error(f"Error calculating ward {ward.id} score: {e}")
        
        # Update city score
        try:
            self.save_city_score("default", today)
            logger.info("City score updated successfully")
        except Exception as e:
            logger.error(f"Error calculating city score: {e}")
        
        self.db.commit()
