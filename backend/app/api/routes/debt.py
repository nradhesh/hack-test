"""
Debt API Routes - Debt calculation and simulation endpoints.
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.debt import (
    DebtResponse,
    DebtHistoryResponse,
    DebtSimulationRequest,
    DebtSimulationResponse,
    WardDebtSummary,
    CityDebtSummary,
)
from app.services.debt_service import DebtService
from app.models.asset import Asset
from app.models.ward import Ward

router = APIRouter()


@router.get("/asset/{asset_id}", response_model=DebtResponse)
def get_asset_debt(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """
    Get current debt calculation for an asset.
    
    Returns detailed breakdown of debt per issue and
    aggregated totals.
    """
    debt_service = DebtService(db)
    debt_response = debt_service.get_asset_debt(asset_id)
    
    if not debt_response:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return debt_response


@router.get("/asset/{asset_id}/history", response_model=DebtHistoryResponse)
def get_asset_debt_history(
    asset_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get historical debt snapshots for an asset.
    
    Returns daily snapshots for trending and analysis.
    """
    debt_service = DebtService(db)
    history = debt_service.get_debt_history(asset_id, days)
    
    if not history:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return history


@router.post("/simulate", response_model=DebtSimulationResponse)
def simulate_debt(
    simulation_request: DebtSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Simulate future debt accumulation.
    
    Shows how costs will increase over time if
    maintenance is delayed.
    """
    debt_service = DebtService(db)
    
    simulation = debt_service.simulate_future_debt(
        asset_id=simulation_request.asset_id,
        issue_id=simulation_request.issue_id,
        base_cost=simulation_request.base_cost,
        report_date=simulation_request.report_date,
        asset_type=simulation_request.asset_type,
        severity=simulation_request.severity,
        future_days=simulation_request.future_days,
    )
    
    return simulation


@router.get("/ward/{ward_id}", response_model=WardDebtSummary)
def get_ward_debt(
    ward_id: int,
    db: Session = Depends(get_db),
):
    """
    Get aggregated debt summary for a ward.
    """
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    # Get all assets in ward
    assets = db.query(Asset).filter(Asset.ward_id == ward_id).all()
    
    debt_service = DebtService(db)
    
    total_debt = 0.0
    total_base_cost = 0.0
    assets_with_debt = 0
    highest_debt = 0.0
    highest_debt_asset_id = None
    
    for asset in assets:
        debt_response = debt_service.get_asset_debt(asset.id)
        if debt_response:
            total_debt += debt_response.total_debt
            total_base_cost += debt_response.total_base_cost
            if debt_response.total_debt > 0:
                assets_with_debt += 1
            if debt_response.total_debt > highest_debt:
                highest_debt = debt_response.total_debt
                highest_debt_asset_id = asset.id
    
    return WardDebtSummary(
        ward_id=ward.id,
        ward_name=ward.name,
        total_assets=len(assets),
        total_debt=total_debt,
        total_base_cost=total_base_cost,
        assets_with_debt=assets_with_debt,
        avg_debt_per_asset=total_debt / len(assets) if assets else 0.0,
        highest_debt_asset_id=highest_debt_asset_id,
        highest_debt_amount=highest_debt,
    )


@router.get("/city", response_model=CityDebtSummary)
def get_city_debt(
    db: Session = Depends(get_db),
):
    """
    Get city-wide debt summary with ward breakdown.
    """
    wards = db.query(Ward).all()
    debt_service = DebtService(db)
    
    total_debt = 0.0
    total_base_cost = 0.0
    total_assets = 0
    ward_summaries = []
    
    for ward in wards:
        assets = db.query(Asset).filter(Asset.ward_id == ward.id).all()
        
        ward_debt = 0.0
        ward_base_cost = 0.0
        assets_with_debt = 0
        highest_debt = 0.0
        highest_debt_asset_id = None
        
        for asset in assets:
            debt_response = debt_service.get_asset_debt(asset.id)
            if debt_response:
                ward_debt += debt_response.total_debt
                ward_base_cost += debt_response.total_base_cost
                if debt_response.total_debt > 0:
                    assets_with_debt += 1
                if debt_response.total_debt > highest_debt:
                    highest_debt = debt_response.total_debt
                    highest_debt_asset_id = asset.id
        
        summary = WardDebtSummary(
            ward_id=ward.id,
            ward_name=ward.name,
            total_assets=len(assets),
            total_debt=ward_debt,
            total_base_cost=ward_base_cost,
            assets_with_debt=assets_with_debt,
            avg_debt_per_asset=ward_debt / len(assets) if assets else 0.0,
            highest_debt_asset_id=highest_debt_asset_id,
            highest_debt_amount=highest_debt,
        )
        ward_summaries.append(summary)
        
        total_debt += ward_debt
        total_base_cost += ward_base_cost
        total_assets += len(assets)
    
    # Sort for rankings
    sorted_by_debt = sorted(ward_summaries, key=lambda w: w.total_debt, reverse=True)
    
    return CityDebtSummary(
        total_wards=len(wards),
        total_assets=total_assets,
        total_debt=total_debt,
        total_base_cost=total_base_cost,
        ward_summaries=ward_summaries,
        worst_wards=sorted_by_debt[:5],
        best_wards=list(reversed(sorted_by_debt[-5:])),
    )


@router.post("/refresh/{asset_id}")
def refresh_asset_debt(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """
    Manually refresh debt calculation for an asset.
    
    Creates a new debt snapshot with current calculations.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    debt_service = DebtService(db)
    
    # Update all issue debt tracking
    for issue in asset.issues:
        if not issue.is_resolved:
            result = debt_service.calculate_issue_debt(issue)
            debt_service.update_issue_debt_tracking(issue, result)
    
    # Create snapshot
    snapshot = debt_service.create_debt_snapshot(asset_id)
    
    return {
        "message": "Debt refreshed successfully",
        "asset_id": asset_id,
        "snapshot_id": snapshot.id if snapshot else None,
        "total_debt": snapshot.total_debt if snapshot else 0.0,
        "mdi_score": snapshot.mdi_score if snapshot else 100.0,
    }


@router.post("/refresh-all")
def refresh_all_debts(
    db: Session = Depends(get_db),
):
    """
    Manually refresh debt calculations for all assets.
    
    This is typically done by the background worker.
    """
    debt_service = DebtService(db)
    debt_service.calculate_all_asset_debts()
    
    return {
        "message": "All debts refreshed successfully",
    }
