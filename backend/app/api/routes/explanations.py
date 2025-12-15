"""
Explanation API Routes - AI-powered human-readable explanations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.explanation import ExplanationRequest, ExplanationResponse, AssetExplanation, WardExplanation
from app.services.explanation_service import ExplanationService

router = APIRouter()


@router.get("/asset/{asset_id}", response_model=AssetExplanation)
def explain_asset(asset_id: int, db: Session = Depends(get_db)):
    """Get human-readable explanation for an asset's debt status."""
    service = ExplanationService(db)
    explanation = service.explain_asset_debt(asset_id)
    if not explanation:
        raise HTTPException(status_code=404, detail="Asset not found")
    return explanation


@router.get("/ward/{ward_id}", response_model=WardExplanation)
def explain_ward(ward_id: int, db: Session = Depends(get_db)):
    """Get human-readable explanation for a ward's MDI score."""
    service = ExplanationService(db)
    explanation = service.explain_ward_score(ward_id)
    if not explanation:
        raise HTTPException(status_code=404, detail="Ward not found")
    return explanation


@router.post("/generate", response_model=ExplanationResponse)
def generate_explanation(request: ExplanationRequest, db: Session = Depends(get_db)):
    """Generate a custom explanation based on type."""
    service = ExplanationService(db)
    return service.generate_explanation(
        explanation_type=request.explanation_type,
        entity_id=request.entity_id,
        include_recommendations=request.include_recommendations,
    )


@router.get("/asset/{asset_id}/cost-comparison")
def get_cost_comparison(asset_id: int, db: Session = Depends(get_db)):
    """Get cost comparison showing impact of waiting."""
    service = ExplanationService(db)
    comparison = service.generate_cost_comparison(asset_id)
    return {"asset_id": asset_id, "comparison_markdown": comparison}
