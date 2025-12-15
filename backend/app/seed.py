"""
Database Seed Script - Populates sample data for demonstration.
"""

from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, init_db
from app.models.asset import Asset, AssetType, AssetStatus
from app.models.issue import Issue, IssueSeverity, IssueCategory
from app.models.ward import Ward
from app.services.debt_service import DebtService
from app.core.config import get_sla_days


def create_wards(db: Session) -> list[Ward]:
    """Create sample wards."""
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
    
    print(f"Created {len(wards)} wards")
    return wards


def create_assets(db: Session, wards: list[Ward]) -> list[Asset]:
    """Create sample assets."""
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
    
    print(f"Created {len(assets)} assets")
    return assets


def create_issues(db: Session, assets: list[Asset]) -> list[Issue]:
    """Create sample issues with varying delays."""
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
        if random.random() > 0.6:
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
                reported_by="System Seed",
            )
            db.add(issue)
            issues.append(issue)
            issue_counter += 1
    
    db.commit()
    for i in issues:
        db.refresh(i)
    
    print(f"Created {len(issues)} issues")
    return issues


def update_debt_tracking(db: Session, issues: list[Issue]):
    """Calculate and update debt for all issues."""
    debt_service = DebtService(db)
    
    for issue in issues:
        if not issue.is_resolved:
            result = debt_service.calculate_issue_debt(issue)
            debt_service.update_issue_debt_tracking(issue, result)
    
    db.commit()
    print("Updated debt tracking for all issues")


def seed_database():
    """Main seed function."""
    print("Initializing database...")
    init_db()
    
    db = SessionLocal()
    try:
        existing = db.query(Ward).first()
        if existing:
            print("Database already seeded. Skipping.")
            return
        
        print("Seeding database with sample data...")
        wards = create_wards(db)
        assets = create_assets(db, wards)
        issues = create_issues(db, assets)
        update_debt_tracking(db, issues)
        
        print("Database seeded successfully!")
        
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
