"""
Ward API Routes - CRUD operations for wards.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db
from app.models.ward import Ward

router = APIRouter()


class WardCreate(BaseModel):
    """Schema for creating a ward."""
    ward_code: str
    name: str
    description: Optional[str] = None
    zone: Optional[str] = None
    center_latitude: Optional[float] = None
    center_longitude: Optional[float] = None
    population: Optional[int] = None
    area_sq_km: Optional[float] = None
    ward_officer: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class WardResponse(BaseModel):
    """Schema for ward responses."""
    id: int
    ward_code: str
    name: str
    description: Optional[str] = None
    zone: Optional[str] = None
    center_latitude: Optional[float] = None
    center_longitude: Optional[float] = None
    population: Optional[int] = None
    area_sq_km: Optional[float] = None
    ward_officer: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[WardResponse])
def list_wards(
    db: Session = Depends(get_db),
):
    """List all wards."""
    wards = db.query(Ward).all()
    return wards


@router.get("/{ward_id}", response_model=WardResponse)
def get_ward(
    ward_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific ward."""
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    return ward


@router.post("", response_model=WardResponse, status_code=201)
def create_ward(
    ward_in: WardCreate,
    db: Session = Depends(get_db),
):
    """Create a new ward."""
    # Check for duplicate code
    existing = db.query(Ward).filter(Ward.ward_code == ward_in.ward_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ward code already exists")
    
    ward = Ward(**ward_in.model_dump())
    db.add(ward)
    db.commit()
    db.refresh(ward)
    return ward


@router.put("/{ward_id}", response_model=WardResponse)
def update_ward(
    ward_id: int,
    ward_in: WardCreate,
    db: Session = Depends(get_db),
):
    """Update a ward."""
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    for field, value in ward_in.model_dump(exclude_unset=True).items():
        setattr(ward, field, value)
    
    db.commit()
    db.refresh(ward)
    return ward


@router.delete("/{ward_id}", status_code=204)
def delete_ward(
    ward_id: int,
    db: Session = Depends(get_db),
):
    """Delete a ward."""
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    db.delete(ward)
    db.commit()
    return None
