"""
Asset API Routes - CRUD operations for infrastructure assets.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from app.api.deps import get_db
from app.models.asset import Asset, AssetType, AssetStatus
from app.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetListResponse,
    AssetWithDebt,
)
from app.services.debt_service import DebtService

router = APIRouter()


@router.get("", response_model=AssetListResponse)
def list_assets(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    asset_type: Optional[str] = None,
    ward_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    List all assets with pagination and filtering.
    """
    query = db.query(Asset)
    
    # Apply filters
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    if ward_id:
        query = query.filter(Asset.ward_id == ward_id)
    if status:
        query = query.filter(Asset.status == status)
    if search:
        query = query.filter(
            Asset.name.ilike(f"%{search}%") | 
            Asset.asset_code.ilike(f"%{search}%")
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    assets = query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    # Convert to response
    items = []
    debt_service = DebtService(db)
    
    from app.services.aggregation_service import AggregationService
    agg_service = AggregationService(db)
    
    for asset in assets:
        debt_response = debt_service.get_asset_debt(asset.id)
        score_response = agg_service.get_asset_mdi_score(asset.id)
        
        items.append(AssetResponse(
            id=asset.id,
            asset_code=asset.asset_code,
            name=asset.name,
            description=asset.description,
            asset_type=asset.asset_type.value,
            status=asset.status.value,
            latitude=asset.latitude,
            longitude=asset.longitude,
            address=asset.address,
            ward_id=asset.ward_id,
            zone=asset.zone,
            base_repair_cost=asset.base_repair_cost,
            sla_days=asset.sla_days,
            condition_score=asset.condition_score,
            last_maintenance_date=asset.last_maintenance_date,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
            open_issue_count=debt_response.open_issues if debt_response else 0,
            current_debt=debt_response.total_debt if debt_response else 0.0,
            mdi_score=score_response.mdi_score if score_response else 100.0,
        ))
    
    return AssetListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/map", response_model=List[AssetWithDebt])
def get_assets_for_map(
    db: Session = Depends(get_db),
    ward_id: Optional[int] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lng: Optional[float] = None,
    max_lng: Optional[float] = None,
):
    """
    Get assets optimized for map display with debt information.
    """
    query = db.query(Asset).filter(
        Asset.status == AssetStatus.ACTIVE,
        Asset.latitude.isnot(None),
        Asset.longitude.isnot(None),
    )
    
    # Apply geographic bounds
    if min_lat is not None:
        query = query.filter(Asset.latitude >= min_lat)
    if max_lat is not None:
        query = query.filter(Asset.latitude <= max_lat)
    if min_lng is not None:
        query = query.filter(Asset.longitude >= min_lng)
    if max_lng is not None:
        query = query.filter(Asset.longitude <= max_lng)
    
    if ward_id:
        query = query.filter(Asset.ward_id == ward_id)
    
    assets = query.limit(500).all()  # Limit for performance
    
    debt_service = DebtService(db)
    result = []
    
    for asset in assets:
        debt_response = debt_service.get_asset_debt(asset.id)
        
        # Calculate MDI score
        from app.services.aggregation_service import AggregationService
        agg_service = AggregationService(db)
        score = agg_service.get_asset_mdi_score(asset.id)
        
        result.append(AssetWithDebt(
            id=asset.id,
            asset_code=asset.asset_code,
            name=asset.name,
            asset_type=asset.asset_type.value,
            latitude=asset.latitude,
            longitude=asset.longitude,
            base_repair_cost=asset.base_repair_cost,
            current_debt=debt_response.total_debt if debt_response else 0.0,
            debt_multiplier=debt_response.avg_debt_multiplier if debt_response else 1.0,
            mdi_score=score.mdi_score if score else 100.0,
            open_issues=debt_response.open_issues if debt_response else 0,
            overdue_issues=debt_response.overdue_issues if debt_response else 0,
            max_delay_days=debt_response.max_delay_days if debt_response else 0,
        ))
    
    return result


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a single asset by ID.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    debt_service = DebtService(db)
    debt_response = debt_service.get_asset_debt(asset.id)
    
    from app.services.aggregation_service import AggregationService
    agg_service = AggregationService(db)
    score = agg_service.get_asset_mdi_score(asset.id)
    
    return AssetResponse(
        id=asset.id,
        asset_code=asset.asset_code,
        name=asset.name,
        description=asset.description,
        asset_type=asset.asset_type.value,
        status=asset.status.value,
        latitude=asset.latitude,
        longitude=asset.longitude,
        address=asset.address,
        ward_id=asset.ward_id,
        zone=asset.zone,
        base_repair_cost=asset.base_repair_cost,
        sla_days=asset.sla_days,
        condition_score=asset.condition_score,
        last_maintenance_date=asset.last_maintenance_date,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        open_issue_count=debt_response.open_issues if debt_response else 0,
        current_debt=debt_response.total_debt if debt_response else 0.0,
        mdi_score=score.mdi_score if score else 100.0,
    )


@router.post("", response_model=AssetResponse, status_code=201)
def create_asset(
    asset_in: AssetCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new asset.
    """
    # Generate asset code if not provided
    asset_code = asset_in.asset_code or f"AST-{uuid.uuid4().hex[:8].upper()}"
    
    # Check for duplicate code
    existing = db.query(Asset).filter(Asset.asset_code == asset_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Asset code already exists")
    
    # Map string to enum
    try:
        asset_type_enum = AssetType(asset_in.asset_type.value)
    except ValueError:
        asset_type_enum = AssetType.OTHER
    
    asset = Asset(
        asset_code=asset_code,
        name=asset_in.name,
        description=asset_in.description,
        asset_type=asset_type_enum,
        status=AssetStatus.ACTIVE,
        latitude=asset_in.latitude,
        longitude=asset_in.longitude,
        address=asset_in.address,
        ward_id=asset_in.ward_id,
        zone=asset_in.zone,
        base_repair_cost=asset_in.base_repair_cost,
        sla_days=asset_in.sla_days,
    )
    
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    return AssetResponse(
        id=asset.id,
        asset_code=asset.asset_code,
        name=asset.name,
        description=asset.description,
        asset_type=asset.asset_type.value,
        status=asset.status.value,
        latitude=asset.latitude,
        longitude=asset.longitude,
        address=asset.address,
        ward_id=asset.ward_id,
        zone=asset.zone,
        base_repair_cost=asset.base_repair_cost,
        sla_days=asset.sla_days,
        condition_score=asset.condition_score,
        last_maintenance_date=asset.last_maintenance_date,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        open_issue_count=0,
        current_debt=0.0,
        mdi_score=100.0,
    )


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: int,
    asset_in: AssetUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing asset.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Update fields
    update_data = asset_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "asset_type" and value:
            value = AssetType(value.value)
        elif field == "status" and value:
            value = AssetStatus(value.value)
        setattr(asset, field, value)
    
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    debt_service = DebtService(db)
    debt_response = debt_service.get_asset_debt(asset.id)
    
    return AssetResponse(
        id=asset.id,
        asset_code=asset.asset_code,
        name=asset.name,
        description=asset.description,
        asset_type=asset.asset_type.value,
        status=asset.status.value,
        latitude=asset.latitude,
        longitude=asset.longitude,
        address=asset.address,
        ward_id=asset.ward_id,
        zone=asset.zone,
        base_repair_cost=asset.base_repair_cost,
        sla_days=asset.sla_days,
        condition_score=asset.condition_score,
        last_maintenance_date=asset.last_maintenance_date,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        open_issue_count=debt_response.open_issues if debt_response else 0,
        current_debt=debt_response.total_debt if debt_response else 0.0,
    )


@router.delete("/{asset_id}", status_code=204)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete an asset and all related data.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    db.delete(asset)
    db.commit()
    return None
