"""
Debt Service - Business logic for debt calculations and snapshots.

This service coordinates between the debt engine and the database,
managing debt calculations, snapshots, and issue debt tracking.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.core.debt_engine import DebtEngine, MDIScoreCalculator, DebtCalculationResult
from app.core.config import get_settings
from app.models.asset import Asset
from app.models.issue import Issue
from app.models.debt import DebtSnapshot
from app.schemas.debt import (
    DebtResponse,
    DebtCalculation,
    DebtHistoryResponse,
    DebtSnapshotResponse,
    DebtSimulationResponse,
    DebtSimulationPoint,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class DebtService:
    """
    Service for managing maintenance debt calculations.
    
    Provides methods for:
    - Calculating debt for individual issues
    - Calculating aggregate debt for assets
    - Creating and retrieving debt snapshots
    - Simulating future debt accumulation
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.debt_engine = DebtEngine()
        self.mdi_calculator = MDIScoreCalculator()
    
    def calculate_issue_debt(
        self,
        issue: Issue,
        current_date: Optional[date] = None
    ) -> DebtCalculationResult:
        """
        Calculate the current debt for a single issue.
        
        Args:
            issue: The issue to calculate debt for
            current_date: Date to calculate as of (defaults to today)
            
        Returns:
            DebtCalculationResult with full debt details
        """
        if current_date is None:
            current_date = date.today()
        
        # Use asset's base repair cost if issue doesn't have estimate
        base_cost = issue.estimated_repair_cost or issue.asset.base_repair_cost
        
        # Get asset type for SLA calculation
        asset_type = issue.asset.asset_type.value
        
        # Calculate debt
        result = self.debt_engine.calculate_debt(
            base_cost=base_cost,
            report_date=issue.report_date.date() if isinstance(issue.report_date, datetime) else issue.report_date,
            asset_type=asset_type,
            current_date=current_date,
            severity=issue.severity.value
        )
        
        return result
    
    def calculate_asset_debt(
        self,
        asset: Asset,
        current_date: Optional[date] = None
    ) -> Tuple[List[DebtCalculationResult], float, float]:
        """
        Calculate total debt for an asset (sum of all open issue debts).
        
        Args:
            asset: The asset to calculate debt for
            current_date: Date to calculate as of
            
        Returns:
            Tuple of (issue_debts, total_debt, total_base_cost)
        """
        if current_date is None:
            current_date = date.today()
        
        issue_debts = []
        total_debt = 0.0
        total_base_cost = 0.0
        
        # Get all open issues for this asset
        open_issues = [i for i in asset.issues if not i.is_resolved]
        
        for issue in open_issues:
            result = self.calculate_issue_debt(issue, current_date)
            issue_debts.append(result)
            total_debt += result.maintenance_debt
            total_base_cost += result.base_cost
        
        return issue_debts, total_debt, total_base_cost
    
    def update_issue_debt_tracking(
        self,
        issue: Issue,
        debt_result: DebtCalculationResult
    ) -> None:
        """
        Update the issue's cached debt tracking fields.
        
        Args:
            issue: The issue to update
            debt_result: The calculated debt result
        """
        issue.current_delay_days = debt_result.delay_days
        issue.current_debt_amount = debt_result.maintenance_debt
        issue.current_debt_multiplier = debt_result.debt_multiplier
        issue.expected_fix_date = datetime.combine(
            debt_result.expected_fix_date,
            datetime.min.time()
        )
        self.db.add(issue)
    
    def get_asset_debt(self, asset_id: int) -> Optional[DebtResponse]:
        """
        Get complete debt information for an asset.
        
        Args:
            asset_id: ID of the asset
            
        Returns:
            DebtResponse with all debt details
        """
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return None
        
        issue_debts, total_debt, total_base_cost = self.calculate_asset_debt(asset)
        
        # Build issue debt list
        issue_debt_list = []
        max_delay = 0
        total_delay = 0
        overdue_count = 0
        
        for i, issue in enumerate([iss for iss in asset.issues if not iss.is_resolved]):
            result = issue_debts[i] if i < len(issue_debts) else None
            if result:
                issue_debt_list.append(DebtCalculation(
                    issue_id=issue.id,
                    base_cost=result.base_cost,
                    current_cost=result.current_cost,
                    maintenance_debt=result.maintenance_debt,
                    debt_multiplier=result.debt_multiplier,
                    delay_days=result.delay_days,
                    expected_fix_date=result.expected_fix_date,
                    is_overdue=result.is_overdue,
                    decay_rate_used=result.decay_rate_used,
                ))
                
                if result.is_overdue:
                    overdue_count += 1
                    max_delay = max(max_delay, result.delay_days)
                    total_delay += result.delay_days
        
        open_issues = len(issue_debt_list)
        avg_delay = total_delay / overdue_count if overdue_count > 0 else 0
        avg_multiplier = sum(d.debt_multiplier for d in issue_debt_list) / open_issues if open_issues > 0 else 1.0
        
        return DebtResponse(
            asset_id=asset.id,
            asset_code=asset.asset_code,
            asset_name=asset.name,
            asset_type=asset.asset_type.value,
            total_base_cost=total_base_cost,
            total_current_cost=total_base_cost + total_debt,
            total_debt=total_debt,
            avg_debt_multiplier=avg_multiplier,
            open_issues=open_issues,
            overdue_issues=overdue_count,
            max_delay_days=max_delay,
            avg_delay_days=avg_delay,
            issue_debts=issue_debt_list,
        )
    
    def create_debt_snapshot(
        self,
        asset_id: int,
        snapshot_date: Optional[date] = None
    ) -> Optional[DebtSnapshot]:
        """
        Create a debt snapshot for an asset.
        
        Args:
            asset_id: ID of the asset
            snapshot_date: Date for the snapshot (defaults to today)
            
        Returns:
            Created DebtSnapshot or None if asset not found
        """
        if snapshot_date is None:
            snapshot_date = date.today()
        
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return None
        
        # Check if snapshot already exists for this date
        existing = self.db.query(DebtSnapshot).filter(
            DebtSnapshot.asset_id == asset_id,
            DebtSnapshot.snapshot_date == snapshot_date
        ).first()
        
        if existing:
            # Update existing snapshot
            snapshot = existing
        else:
            # Create new snapshot
            snapshot = DebtSnapshot(
                asset_id=asset_id,
                snapshot_date=snapshot_date
            )
        
        # Calculate current debt
        issue_debts, total_debt, total_base_cost = self.calculate_asset_debt(
            asset, snapshot_date
        )
        
        # Aggregate metrics
        open_issues = len(issue_debts)
        overdue_issues = sum(1 for d in issue_debts if d.is_overdue)
        delays = [d.delay_days for d in issue_debts if d.is_overdue]
        multipliers = [d.debt_multiplier for d in issue_debts]
        
        # Update snapshot
        snapshot.total_base_cost = total_base_cost
        snapshot.total_current_cost = total_base_cost + total_debt
        snapshot.total_debt = total_debt
        snapshot.open_issue_count = open_issues
        snapshot.overdue_issue_count = overdue_issues
        snapshot.avg_delay_days = sum(delays) / len(delays) if delays else 0
        snapshot.max_delay_days = max(delays) if delays else 0
        snapshot.avg_debt_multiplier = sum(multipliers) / len(multipliers) if multipliers else 1.0
        snapshot.max_debt_multiplier = max(multipliers) if multipliers else 1.0
        
        # Calculate MDI score
        mdi_result = self.mdi_calculator.calculate_score(total_debt, total_base_cost)
        snapshot.mdi_score = mdi_result.score
        
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        
        logger.info(f"Created debt snapshot for asset {asset_id}: debt=${total_debt:.2f}, MDI={mdi_result.score:.1f}")
        
        return snapshot
    
    def get_debt_history(
        self,
        asset_id: int,
        days: int = 30
    ) -> Optional[DebtHistoryResponse]:
        """
        Get debt history for an asset over time.
        
        Args:
            asset_id: ID of the asset
            days: Number of days of history to retrieve
            
        Returns:
            DebtHistoryResponse with historical snapshots
        """
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return None
        
        # Get snapshots
        start_date = date.today() - timedelta(days=days)
        snapshots = self.db.query(DebtSnapshot).filter(
            DebtSnapshot.asset_id == asset_id,
            DebtSnapshot.snapshot_date >= start_date
        ).order_by(DebtSnapshot.snapshot_date).all()
        
        # Convert to response
        snapshot_responses = [
            DebtSnapshotResponse(
                snapshot_date=s.snapshot_date,
                total_base_cost=s.total_base_cost,
                total_current_cost=s.total_current_cost,
                total_debt=s.total_debt,
                open_issue_count=s.open_issue_count,
                overdue_issue_count=s.overdue_issue_count,
                avg_delay_days=s.avg_delay_days,
                max_delay_days=s.max_delay_days,
                mdi_score=s.mdi_score,
            )
            for s in snapshots
        ]
        
        # Calculate trend
        debt_trend = "stable"
        debt_change = 0.0
        if len(snapshots) >= 2:
            first_debt = snapshots[0].total_debt
            last_debt = snapshots[-1].total_debt
            if first_debt > 0:
                debt_change = ((last_debt - first_debt) / first_debt) * 100
            if debt_change > 5:
                debt_trend = "increasing"
            elif debt_change < -5:
                debt_trend = "decreasing"
        
        return DebtHistoryResponse(
            asset_id=asset.id,
            asset_code=asset.asset_code,
            asset_name=asset.name,
            snapshots=snapshot_responses,
            debt_trend=debt_trend,
            debt_change_percent=debt_change,
        )
    
    def simulate_future_debt(
        self,
        asset_id: Optional[int] = None,
        issue_id: Optional[int] = None,
        base_cost: Optional[float] = None,
        report_date: Optional[date] = None,
        asset_type: str = "road",
        severity: str = "medium",
        future_days: int = 30
    ) -> DebtSimulationResponse:
        """
        Simulate future debt accumulation.
        
        Args:
            asset_id: Optional asset to simulate for
            issue_id: Optional specific issue to simulate
            base_cost: Base cost for simulation
            report_date: Report date for simulation
            asset_type: Type of asset
            severity: Issue severity
            future_days: Days to simulate ahead
            
        Returns:
            DebtSimulationResponse with simulation points
        """
        # Get parameters from existing entities if provided
        if issue_id:
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if issue:
                base_cost = base_cost or issue.estimated_repair_cost or issue.asset.base_repair_cost
                report_date = report_date or (
                    issue.report_date.date() if isinstance(issue.report_date, datetime) else issue.report_date
                )
                asset_type = issue.asset.asset_type.value
                severity = issue.severity.value
        elif asset_id:
            asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
            if asset:
                base_cost = base_cost or asset.base_repair_cost
                asset_type = asset.asset_type.value
        
        # Defaults
        base_cost = base_cost or 10000.0
        report_date = report_date or date.today()
        
        # Run simulation
        results = self.debt_engine.simulate_future_debt(
            base_cost=base_cost,
            report_date=report_date,
            asset_type=asset_type,
            future_days=future_days,
            severity=severity
        )
        
        # Convert to response
        points = []
        sla_breach_date = None
        double_cost_date = None
        triple_cost_date = None
        
        for i, result in enumerate(results):
            sim_date = date.today() + timedelta(days=i)
            points.append(DebtSimulationPoint(
                date=sim_date,
                day_offset=i,
                base_cost=result.base_cost,
                current_cost=result.current_cost,
                debt=result.maintenance_debt,
                multiplier=result.debt_multiplier,
                delay_days=result.delay_days,
                is_overdue=result.is_overdue,
            ))
            
            # Track milestones
            if result.is_overdue and sla_breach_date is None:
                sla_breach_date = sim_date
            if result.debt_multiplier >= 2.0 and double_cost_date is None:
                double_cost_date = sim_date
            if result.debt_multiplier >= 3.0 and triple_cost_date is None:
                triple_cost_date = sim_date
        
        return DebtSimulationResponse(
            simulation_points=points,
            starting_cost=base_cost,
            ending_cost=results[-1].current_cost if results else base_cost,
            total_debt_accumulated=results[-1].maintenance_debt if results else 0.0,
            max_multiplier=max(r.debt_multiplier for r in results) if results else 1.0,
            sla_breach_date=sla_breach_date,
            double_cost_date=double_cost_date,
            triple_cost_date=triple_cost_date,
        )
    
    def calculate_all_asset_debts(self) -> None:
        """
        Calculate and update debt for all assets.
        
        This is called by the background worker to update
        all debt snapshots daily.
        """
        assets = self.db.query(Asset).filter(Asset.status == "active").all()
        today = date.today()
        
        logger.info(f"Calculating debt for {len(assets)} assets")
        
        for asset in assets:
            try:
                # Update issue debt tracking
                for issue in asset.issues:
                    if not issue.is_resolved:
                        result = self.calculate_issue_debt(issue, today)
                        self.update_issue_debt_tracking(issue, result)
                
                # Create snapshot
                self.create_debt_snapshot(asset.id, today)
                
            except Exception as e:
                logger.error(f"Error calculating debt for asset {asset.id}: {e}")
                continue
        
        self.db.commit()
        logger.info("Completed debt calculation for all assets")
