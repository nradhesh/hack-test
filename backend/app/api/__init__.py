# API routes package initialization
from fastapi import APIRouter

from app.api.routes import assets, issues, debt, scores, explanations, wards

api_router = APIRouter()

# Include all route modules
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(issues.router, prefix="/issues", tags=["Issues"])
api_router.include_router(debt.router, prefix="/debt", tags=["Debt"])
api_router.include_router(scores.router, prefix="/scores", tags=["Scores"])
api_router.include_router(explanations.router, prefix="/explain", tags=["Explanations"])
api_router.include_router(wards.router, prefix="/wards", tags=["Wards"])
