"""
Main FastAPI Application Entry Point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import get_settings
from app.core.database import init_db, SessionLocal
from app.api import api_router

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def seed_initial_data():
    """Seed database with initial data if empty."""
    from app.models.ward import Ward
    from app.models.asset import Asset, AssetType, AssetStatus
    from app.models.issue import Issue, IssueSeverity, IssueCategory
    from app.services.debt_service import DebtService
    from app.core.config import get_sla_days
    from datetime import datetime, timedelta
    import random
    
    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Ward).first()
        if existing:
            logger.info("Database already has data, skipping seed")
            return
        
        logger.info("Seeding database with initial data...")
        
        # Create wards
        wards_data = [
            {"ward_code": "W001", "name": "Downtown Central", "zone": "Central", "center_latitude": 12.9716, "center_longitude": 77.5946},
            {"ward_code": "W002", "name": "Riverside East", "zone": "East", "center_latitude": 12.9816, "center_longitude": 77.6046},
            {"ward_code": "W003", "name": "Industrial North", "zone": "North", "center_latitude": 12.9916, "center_longitude": 77.5846},
            {"ward_code": "W004", "name": "Residential South", "zone": "South", "center_latitude": 12.9616, "center_longitude": 77.5746},
            {"ward_code": "W005", "name": "Commercial West", "zone": "West", "center_latitude": 12.9716, "center_longitude": 77.5646},
        ]
        
        wards = []
        for data in wards_data:
            ward = Ward(**data)
            db.add(ward)
            wards.append(ward)
        db.commit()
        for w in wards:
            db.refresh(w)
        logger.info(f"Created {len(wards)} wards")
        
        # Create assets
        asset_configs = [
            (AssetType.ROAD, 50000, 14, "Main Road", "MR"),
            (AssetType.DRAIN, 15000, 7, "Storm Drain", "SD"),
            (AssetType.STREETLIGHT, 5000, 3, "Street Light", "SL"),
            (AssetType.BRIDGE, 200000, 21, "Flyover Bridge", "FB"),
            (AssetType.SIDEWALK, 20000, 10, "Pedestrian Walk", "PW"),
        ]
        
        assets = []
        asset_counter = 1
        
        for ward in wards:
            for asset_type, base_cost, sla, name_prefix, code_prefix in asset_configs:
                for i in range(random.randint(2, 4)):
                    lat_offset = random.uniform(-0.01, 0.01)
                    lng_offset = random.uniform(-0.01, 0.01)
                    
                    asset = Asset(
                        asset_code=f"{code_prefix}-{asset_counter:04d}",
                        name=f"{name_prefix} {ward.name} #{i+1}",
                        asset_type=asset_type,
                        status=AssetStatus.ACTIVE,
                        ward_id=ward.id,
                        zone=ward.zone,
                        latitude=ward.center_latitude + lat_offset,
                        longitude=ward.center_longitude + lng_offset,
                        base_repair_cost=base_cost * random.uniform(0.8, 1.2),
                        sla_days=sla,
                        condition_score=random.uniform(60, 100),
                    )
                    db.add(asset)
                    assets.append(asset)
                    asset_counter += 1
        
        db.commit()
        for a in assets:
            db.refresh(a)
        logger.info(f"Created {len(assets)} assets")
        
        # Create issues
        categories_by_type = {
            AssetType.ROAD: [IssueCategory.POTHOLE, IssueCategory.CRACK, IssueCategory.WEAR],
            AssetType.DRAIN: [IssueCategory.BLOCKAGE, IssueCategory.FLOODING],
            AssetType.STREETLIGHT: [IssueCategory.OUTAGE, IssueCategory.DAMAGE],
            AssetType.BRIDGE: [IssueCategory.CRACK, IssueCategory.DAMAGE],
            AssetType.SIDEWALK: [IssueCategory.CRACK, IssueCategory.DAMAGE, IssueCategory.WEAR],
        }
        
        issues = []
        issue_counter = 1
        
        for asset in assets:
            if random.random() > 0.5:
                continue
            
            num_issues = random.randint(1, 3)
            categories = categories_by_type.get(asset.asset_type, [IssueCategory.OTHER])
            
            for _ in range(num_issues):
                days_ago = random.randint(1, 60)
                report_date = datetime.utcnow() - timedelta(days=days_ago)
                
                severity = random.choice(list(IssueSeverity))
                category = random.choice(categories)
                
                sla_days = get_sla_days(asset.asset_type.value)
                expected_fix = report_date + timedelta(days=sla_days)
                
                is_resolved = random.random() < 0.3
                resolution_date = None
                if is_resolved:
                    resolution_date = report_date + timedelta(days=random.randint(1, sla_days + 10))
                
                issue = Issue(
                    issue_code=f"ISS-{issue_counter:06d}",
                    title=f"{category.value.title()} issue at {asset.name}",
                    description=f"Reported {category.value} requiring maintenance attention.",
                    asset_id=asset.id,
                    category=category,
                    severity=severity,
                    estimated_repair_cost=asset.base_repair_cost * random.uniform(0.5, 1.5),
                    report_date=report_date,
                    expected_fix_date=expected_fix,
                    is_resolved=is_resolved,
                    resolution_date=resolution_date,
                    reported_by="System",
                )
                db.add(issue)
                issues.append(issue)
                issue_counter += 1
        
        db.commit()
        for i in issues:
            db.refresh(i)
        logger.info(f"Created {len(issues)} issues")
        
        # Update debt tracking
        debt_service = DebtService(db)
        for issue in issues:
            if not issue.is_resolved:
                result = debt_service.calculate_issue_debt(issue)
                debt_service.update_issue_debt_tracking(issue, result)
        db.commit()
        
        logger.info("Database seeded successfully!")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting MDI application...")
    init_db()
    logger.info("Database initialized")
    seed_initial_data()
    yield
    logger.info("Shutting down MDI application...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Urban Infrastructure Credit Score System - Quantifies maintenance debt",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    from app.core.database import check_db_connection
    db_healthy = check_db_connection()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
    }
