"""
Score API Routes - MDI score endpoints for assets, wards, and city.
"""

from typing import List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.score import (
    MDIScoreResponse,
    WardScoreResponse,
    CityScoreResponse,
    ScoreDashboard,
    MDIScoreHistory,
    MDIScoreHistoryPoint,
)
from app.services.aggregation_service import AggregationService
from app.models.asset import Asset
from app.models.ward import Ward, WardScore, CityScore
from app.models.debt import DebtSnapshot

router = APIRouter()


@router.get("/dashboard", response_model=ScoreDashboard)
def get_score_dashboard(
    db: Session = Depends(get_db),
):
    """
    Get quick dashboard summary of city scores.
    """
    agg_service = AggregationService(db)
    
    # Get city score
    city_score = agg_service.calculate_city_score()
    
    # Get recent activity
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    
    # Count issues
    from app.models.issue import Issue
    from datetime import datetime
    
    today_start = datetime.combine(today, datetime.min.time())
    
    issues_today = db.query(Issue).filter(
        Issue.report_date >= today_start
    ).count()
    
    resolved_today = db.query(Issue).filter(
        Issue.resolution_date >= today_start
    ).count()
    
    # Get debt changes
    yesterday_city_score = db.query(CityScore).filter(
        CityScore.city_code == "default",
        CityScore.score_date == yesterday
    ).first()
    
    week_city_score = db.query(CityScore).filter(
        CityScore.city_code == "default",
        CityScore.score_date == week_ago
    ).first()
    
    debt_change_24h = 0.0
    debt_change_7d = 0.0
    
    if yesterday_city_score:
        debt_change_24h = city_score.total_debt - yesterday_city_score.total_debt
    if week_city_score:
        debt_change_7d = city_score.total_debt - week_city_score.total_debt
    
    # Count critical assets and wards needing attention
    critical_count = db.query(Asset).join(Asset.issues).filter(
        Asset.status == "active",
    ).distinct().count()
    
    wards_needing_attention = city_score.wards_poor + city_score.wards_critical
    
    return ScoreDashboard(
        city_score=city_score.mdi_score,
        city_category=city_score.score_category,
        total_assets=city_score.total_assets,
        total_issues=city_score.total_open_issues,
        overdue_issues=0,  # Would need to calculate from issues
        total_city_debt=city_score.total_debt,
        debt_change_24h=debt_change_24h,
        debt_change_7d=debt_change_7d,
        critical_assets=critical_count,
        wards_needing_attention=wards_needing_attention,
        issues_reported_today=issues_today,
        issues_resolved_today=resolved_today,
    )


@router.get("/asset/{asset_id}", response_model=MDIScoreResponse)
def get_asset_score(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """
    Get MDI score for a specific asset.
    """
    agg_service = AggregationService(db)
    score = agg_service.get_asset_mdi_score(asset_id)
    
    if not score:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return score


@router.get("/asset/{asset_id}/history", response_model=MDIScoreHistory)
def get_asset_score_history(
    asset_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get score history for an asset.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    start_date = date.today() - timedelta(days=days)
    
    snapshots = db.query(DebtSnapshot).filter(
        DebtSnapshot.asset_id == asset_id,
        DebtSnapshot.snapshot_date >= start_date
    ).order_by(DebtSnapshot.snapshot_date).all()
    
    history = [
        MDIScoreHistoryPoint(
            date=s.snapshot_date,
            mdi_score=s.mdi_score,
            total_debt=s.total_debt,
            open_issues=s.open_issue_count,
        )
        for s in snapshots
    ]
    
    # Calculate trend
    current_score = history[-1].mdi_score if history else 100.0
    first_score = history[0].mdi_score if history else 100.0
    score_change = current_score - first_score
    
    if score_change > 5:
        trend = "improving"
    elif score_change < -5:
        trend = "declining"
    else:
        trend = "stable"
    
    return MDIScoreHistory(
        entity_id=asset.id,
        entity_type="asset",
        entity_name=asset.name,
        history=history,
        current_score=current_score,
        score_change=score_change,
        trend=trend,
    )


@router.get("/ward/{ward_id}", response_model=WardScoreResponse)
def get_ward_score(
    ward_id: int,
    db: Session = Depends(get_db),
):
    """
    Get MDI score for a specific ward.
    """
    agg_service = AggregationService(db)
    score = agg_service.calculate_ward_score(ward_id)
    
    if not score:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    # Calculate city rank
    all_wards = db.query(Ward).all()
    ward_scores = []
    for w in all_wards:
        ws = agg_service.calculate_ward_score(w.id)
        if ws:
            ward_scores.append((w.id, ws.mdi_score))
    
    # Sort by score descending
    ward_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Find rank
    rank = None
    for i, (wid, _) in enumerate(ward_scores):
        if wid == ward_id:
            rank = i + 1
            break
    
    score.city_rank = rank
    score.total_wards = len(ward_scores)
    
    return score


@router.get("/ward/{ward_id}/history", response_model=MDIScoreHistory)
def get_ward_score_history(
    ward_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get score history for a ward.
    """
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    start_date = date.today() - timedelta(days=days)
    
    scores = db.query(WardScore).filter(
        WardScore.ward_id == ward_id,
        WardScore.score_date >= start_date
    ).order_by(WardScore.score_date).all()
    
    history = [
        MDIScoreHistoryPoint(
            date=s.score_date,
            mdi_score=s.mdi_score,
            total_debt=s.total_debt,
            open_issues=s.total_open_issues,
        )
        for s in scores
    ]
    
    # Calculate trend
    current_score = history[-1].mdi_score if history else 100.0
    first_score = history[0].mdi_score if history else 100.0
    score_change = current_score - first_score
    
    if score_change > 5:
        trend = "improving"
    elif score_change < -5:
        trend = "declining"
    else:
        trend = "stable"
    
    return MDIScoreHistory(
        entity_id=ward.id,
        entity_type="ward",
        entity_name=ward.name,
        history=history,
        current_score=current_score,
        score_change=score_change,
        trend=trend,
    )


@router.get("/city", response_model=CityScoreResponse)
def get_city_score(
    city_code: str = "default",
    db: Session = Depends(get_db),
):
    """
    Get city-wide MDI score.
    """
    agg_service = AggregationService(db)
    score = agg_service.calculate_city_score(city_code)
    
    return score


@router.get("/wards", response_model=List[WardScoreResponse])
def get_all_ward_scores(
    sort_by: str = Query("score", enum=["score", "debt", "name"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    db: Session = Depends(get_db),
):
    """
    Get scores for all wards.
    """
    agg_service = AggregationService(db)
    wards = db.query(Ward).all()
    
    scores = []
    for ward in wards:
        score = agg_service.calculate_ward_score(ward.id)
        if score:
            scores.append(score)
    
    # Sort
    reverse = order == "desc"
    if sort_by == "score":
        scores.sort(key=lambda s: s.mdi_score, reverse=reverse)
    elif sort_by == "debt":
        scores.sort(key=lambda s: s.total_debt, reverse=reverse)
    elif sort_by == "name":
        scores.sort(key=lambda s: s.ward_name, reverse=reverse)
    
    # Add ranks
    for i, score in enumerate(scores):
        score.city_rank = i + 1 if not reverse else len(scores) - i
        score.total_wards = len(scores)
    
    return scores


@router.post("/refresh")
def refresh_all_scores(
    db: Session = Depends(get_db),
):
    """
    Manually refresh all scores.
    
    Creates new snapshots for all wards and city.
    """
    agg_service = AggregationService(db)
    agg_service.calculate_all_scores()
    
    return {
        "message": "All scores refreshed successfully",
    }
