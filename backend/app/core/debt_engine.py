"""
Core Debt Computation Engine.

This module implements the deterministic debt calculation logic
that computes maintenance debt based on compound growth formulas.

The debt represents the additional cost incurred due to delayed
maintenance beyond the expected repair timeline (SLA).
"""

from datetime import datetime, date
from typing import Optional, Tuple
from dataclasses import dataclass
import math
import logging

from app.core.config import get_settings, get_sla_days, SEVERITY_MULTIPLIERS

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class DebtCalculationResult:
    """Result of a debt calculation."""
    base_cost: float
    current_cost: float
    maintenance_debt: float
    debt_multiplier: float
    delay_days: int
    expected_fix_date: date
    is_overdue: bool
    decay_rate_used: float
    

@dataclass
class MDIScoreResult:
    """Result of MDI score calculation."""
    score: float
    category: str
    description: str
    total_debt: float
    total_base_cost: float


class DebtEngine:
    """
    The core engine for calculating maintenance debt.
    
    Implements compound growth formula:
    decay_cost = base_cost × (1 + decay_rate) ^ delay_days
    maintenance_debt = decay_cost - base_cost
    """
    
    def __init__(
        self,
        decay_rate: Optional[float] = None,
        max_multiplier: Optional[float] = None
    ):
        """
        Initialize the debt engine.
        
        Args:
            decay_rate: Daily compound rate (default from settings)
            max_multiplier: Maximum debt multiplier cap (default from settings)
        """
        self.decay_rate = decay_rate or settings.DEFAULT_DECAY_RATE
        self.max_multiplier = max_multiplier or settings.MAX_DEBT_MULTIPLIER
        
    def calculate_expected_fix_date(
        self,
        report_date: date,
        asset_type: str
    ) -> date:
        """
        Calculate the expected fix date based on SLA.
        
        Args:
            report_date: Date when issue was reported
            asset_type: Type of asset (road, drain, streetlight, etc.)
            
        Returns:
            Expected fix date (report_date + SLA_days)
        """
        from datetime import timedelta
        sla_days = get_sla_days(asset_type)
        return report_date + timedelta(days=sla_days)
    
    def calculate_delay_days(
        self,
        current_date: date,
        expected_fix_date: date
    ) -> int:
        """
        Calculate the number of days past the expected fix date.
        
        Args:
            current_date: Current date
            expected_fix_date: Expected fix date from SLA
            
        Returns:
            Number of delay days (0 if not overdue)
        """
        if current_date <= expected_fix_date:
            return 0
        return (current_date - expected_fix_date).days
    
    def calculate_decay_cost(
        self,
        base_cost: float,
        delay_days: int,
        severity: str = "medium"
    ) -> Tuple[float, float]:
        """
        Calculate the decayed (increased) cost due to delay.
        
        Uses compound growth formula:
        decay_cost = base_cost × (1 + decay_rate) ^ delay_days
        
        Args:
            base_cost: Original repair cost
            delay_days: Days past expected fix date
            severity: Issue severity level
            
        Returns:
            Tuple of (decay_cost, debt_multiplier)
        """
        if delay_days <= 0:
            return base_cost, 1.0
        
        # Get severity multiplier
        severity_mult = SEVERITY_MULTIPLIERS.get(severity.lower(), 1.0)
        
        # Calculate compound growth
        # Formula: decay_cost = base_cost × (1 + decay_rate) ^ delay_days
        raw_multiplier = math.pow(1 + self.decay_rate, delay_days)
        
        # Apply severity multiplier to the growth portion
        growth_portion = raw_multiplier - 1
        adjusted_growth = growth_portion * severity_mult
        effective_multiplier = 1 + adjusted_growth
        
        # Cap the multiplier to prevent runaway costs
        capped_multiplier = min(effective_multiplier, self.max_multiplier)
        
        decay_cost = base_cost * capped_multiplier
        
        return decay_cost, capped_multiplier
    
    def calculate_debt(
        self,
        base_cost: float,
        report_date: date,
        asset_type: str,
        current_date: Optional[date] = None,
        severity: str = "medium"
    ) -> DebtCalculationResult:
        """
        Calculate complete maintenance debt for an issue.
        
        This is the main calculation method that combines all
        debt calculation logic.
        
        Args:
            base_cost: Original repair cost
            report_date: Date when issue was reported
            asset_type: Type of asset
            current_date: Current date (defaults to today)
            severity: Issue severity level
            
        Returns:
            DebtCalculationResult with all debt details
        """
        if current_date is None:
            current_date = date.today()
            
        # Convert datetime to date if needed
        if isinstance(report_date, datetime):
            report_date = report_date.date()
        if isinstance(current_date, datetime):
            current_date = current_date.date()
            
        # Calculate expected fix date
        expected_fix_date = self.calculate_expected_fix_date(
            report_date, asset_type
        )
        
        # Calculate delay
        delay_days = self.calculate_delay_days(current_date, expected_fix_date)
        
        # Calculate decayed cost
        current_cost, multiplier = self.calculate_decay_cost(
            base_cost, delay_days, severity
        )
        
        # Calculate debt (additional cost beyond base)
        maintenance_debt = current_cost - base_cost
        
        logger.debug(
            f"Debt calculation: base=${base_cost:.2f}, "
            f"delay={delay_days}d, multiplier={multiplier:.2f}x, "
            f"debt=${maintenance_debt:.2f}"
        )
        
        return DebtCalculationResult(
            base_cost=base_cost,
            current_cost=current_cost,
            maintenance_debt=maintenance_debt,
            debt_multiplier=multiplier,
            delay_days=delay_days,
            expected_fix_date=expected_fix_date,
            is_overdue=delay_days > 0,
            decay_rate_used=self.decay_rate,
        )
    
    def simulate_future_debt(
        self,
        base_cost: float,
        report_date: date,
        asset_type: str,
        future_days: int,
        severity: str = "medium"
    ) -> list[DebtCalculationResult]:
        """
        Simulate debt accumulation over future days.
        
        Useful for visualizing how costs increase with delay.
        
        Args:
            base_cost: Original repair cost
            report_date: Date when issue was reported
            asset_type: Type of asset
            future_days: Number of days to simulate
            severity: Issue severity level
            
        Returns:
            List of DebtCalculationResult for each future day
        """
        from datetime import timedelta
        
        results = []
        start_date = date.today()
        
        for day_offset in range(future_days + 1):
            sim_date = start_date + timedelta(days=day_offset)
            result = self.calculate_debt(
                base_cost=base_cost,
                report_date=report_date,
                asset_type=asset_type,
                current_date=sim_date,
                severity=severity
            )
            results.append(result)
            
        return results


class MDIScoreCalculator:
    """
    Calculator for Maintenance Debt Index scores.
    
    MDI is a normalized score from 0-100 where:
    - Higher score = healthier infrastructure
    - Lower score = accumulated neglect
    """
    
    # MDI score thresholds and categories
    CATEGORIES = [
        (90, "Excellent", "Infrastructure is well-maintained with minimal debt"),
        (70, "Good", "Minor maintenance delays, debt is manageable"),
        (50, "Fair", "Significant delays accumulating, attention needed"),
        (30, "Poor", "Critical maintenance backlog, urgent action required"),
        (0, "Critical", "Severe neglect, emergency intervention needed"),
    ]
    
    def __init__(self, reference_debt: float = 100000.0):
        """
        Initialize the MDI score calculator.
        
        Args:
            reference_debt: Reference debt level for normalization
                           (debt at which score drops significantly)
        """
        self.reference_debt = reference_debt
        
    def calculate_score(
        self,
        total_debt: float,
        total_base_cost: float
    ) -> MDIScoreResult:
        """
        Calculate MDI score from total debt and base cost.
        
        Uses logarithmic normalization:
        score = 100 × (1 - log(1 + debt/ref) / log(1 + max_mult))
        
        Args:
            total_debt: Total accumulated maintenance debt
            total_base_cost: Total base repair costs
            
        Returns:
            MDIScoreResult with score and category
        """
        if total_base_cost <= 0:
            # No assets or costs, perfect score
            return MDIScoreResult(
                score=100.0,
                category="Excellent",
                description="No maintenance debt - infrastructure is pristine",
                total_debt=0.0,
                total_base_cost=0.0,
            )
        
        # Calculate debt ratio
        debt_ratio = total_debt / total_base_cost if total_base_cost > 0 else 0
        
        # Logarithmic normalization
        # This ensures score decreases smoothly as debt increases
        max_multiplier = settings.MAX_DEBT_MULTIPLIER
        
        if debt_ratio <= 0:
            score = 100.0
        else:
            # Normalize using log scale
            log_debt = math.log(1 + debt_ratio)
            log_max = math.log(max_multiplier)
            normalized = log_debt / log_max
            score = max(0, 100 * (1 - normalized))
        
        # Round to 1 decimal place
        score = round(score, 1)
        
        # Determine category
        category, description = self._get_category(score)
        
        return MDIScoreResult(
            score=score,
            category=category,
            description=description,
            total_debt=total_debt,
            total_base_cost=total_base_cost,
        )
    
    def _get_category(self, score: float) -> Tuple[str, str]:
        """Get category name and description for a score."""
        for threshold, category, description in self.CATEGORIES:
            if score >= threshold:
                return category, description
        return "Critical", "Severe neglect, emergency intervention needed"
    
    def calculate_from_debts(
        self,
        debt_results: list[DebtCalculationResult]
    ) -> MDIScoreResult:
        """
        Calculate MDI score from a list of debt results.
        
        Args:
            debt_results: List of DebtCalculationResult objects
            
        Returns:
            MDIScoreResult for the aggregate
        """
        if not debt_results:
            return self.calculate_score(0, 0)
            
        total_debt = sum(r.maintenance_debt for r in debt_results)
        total_base = sum(r.base_cost for r in debt_results)
        
        return self.calculate_score(total_debt, total_base)


# Singleton instances for common use
debt_engine = DebtEngine()
mdi_calculator = MDIScoreCalculator()
