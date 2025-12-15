"""
Issue API Routes - CRUD operations for maintenance issues.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from app.api.deps import get_db
from app.models.asset import Asset
from app.models.issue import Issue, IssueSeverity, IssueCategory
from app.schemas.issue import (
    IssueCreate,
    IssueUpdate,
    IssueResponse,
    IssueResolve,
    IssueListResponse,
    IssueSummary,
)
from app.services.debt_service import DebtService
from app.core.config import get_sla_days

router = APIRouter()


@router.get("", response_model=IssueListResponse)
def list_issues(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    asset_id: Optional[int] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    is_overdue: Optional[bool] = None,
):
    """
    List all issues with pagination and filtering.
    """
    query = db.query(Issue)
    
    # Apply filters
    if asset_id:
        query = query.filter(Issue.asset_id == asset_id)
    if severity:
        query = query.filter(Issue.severity == severity)
    if category:
        query = query.filter(Issue.category == category)
    if is_resolved is not None:
        query = query.filter(Issue.is_resolved == is_resolved)
    if is_overdue:
        now = datetime.utcnow()
        query = query.filter(
            Issue.is_resolved == False,
            Issue.expected_fix_date < now
        )
    
    # Order by report date descending
    query = query.order_by(Issue.report_date.desc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    issues = query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    # Convert to response
    items = []
    for issue in issues:
        items.append(IssueResponse(
            id=issue.id,
            issue_code=issue.issue_code,
            title=issue.title,
            description=issue.description,
            asset_id=issue.asset_id,
            category=issue.category.value,
            severity=issue.severity.value,
            estimated_repair_cost=issue.estimated_repair_cost,
            actual_repair_cost=issue.actual_repair_cost,
            report_date=issue.report_date,
            expected_fix_date=issue.expected_fix_date,
            resolution_date=issue.resolution_date,
            is_resolved=issue.is_resolved,
            is_overdue=issue.is_overdue,
            days_open=issue.days_open,
            current_delay_days=issue.current_delay_days,
            current_debt_amount=issue.current_debt_amount,
            current_debt_multiplier=issue.current_debt_multiplier,
            reported_by=issue.reported_by,
            created_at=issue.created_at,
        ))
    
    return IssueListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/summary", response_model=IssueSummary)
def get_issue_summary(
    db: Session = Depends(get_db),
    ward_id: Optional[int] = None,
):
    """
    Get summary statistics for issues.
    """
    query = db.query(Issue)
    
    if ward_id:
        query = query.join(Asset).filter(Asset.ward_id == ward_id)
    
    all_issues = query.all()
    
    total_issues = len(all_issues)
    open_issues = sum(1 for i in all_issues if not i.is_resolved)
    resolved_issues = sum(1 for i in all_issues if i.is_resolved)
    overdue_issues = sum(1 for i in all_issues if i.is_overdue)
    critical_issues = sum(1 for i in all_issues if not i.is_resolved and i.severity == IssueSeverity.CRITICAL)
    
    total_debt = sum(i.current_debt_amount for i in all_issues if not i.is_resolved)
    
    delay_days = [i.current_delay_days for i in all_issues if i.current_delay_days > 0]
    avg_delay = sum(delay_days) / len(delay_days) if delay_days else 0
    
    return IssueSummary(
        total_issues=total_issues,
        open_issues=open_issues,
        resolved_issues=resolved_issues,
        overdue_issues=overdue_issues,
        critical_issues=critical_issues,
        total_debt=total_debt,
        avg_delay_days=avg_delay,
    )


@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a single issue by ID.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    return IssueResponse(
        id=issue.id,
        issue_code=issue.issue_code,
        title=issue.title,
        description=issue.description,
        asset_id=issue.asset_id,
        category=issue.category.value,
        severity=issue.severity.value,
        estimated_repair_cost=issue.estimated_repair_cost,
        actual_repair_cost=issue.actual_repair_cost,
        report_date=issue.report_date,
        expected_fix_date=issue.expected_fix_date,
        resolution_date=issue.resolution_date,
        is_resolved=issue.is_resolved,
        is_overdue=issue.is_overdue,
        days_open=issue.days_open,
        current_delay_days=issue.current_delay_days,
        current_debt_amount=issue.current_debt_amount,
        current_debt_multiplier=issue.current_debt_multiplier,
        reported_by=issue.reported_by,
        created_at=issue.created_at,
    )


@router.post("", response_model=IssueResponse, status_code=201)
def create_issue(
    issue_in: IssueCreate,
    db: Session = Depends(get_db),
):
    """
    Report a new maintenance issue.
    """
    # Verify asset exists
    asset = db.query(Asset).filter(Asset.id == issue_in.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Generate issue code if not provided
    issue_code = issue_in.issue_code or f"ISS-{uuid.uuid4().hex[:8].upper()}"
    
    # Check for duplicate code
    existing = db.query(Issue).filter(Issue.issue_code == issue_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Issue code already exists")
    
    # Set report date
    report_date = issue_in.report_date or datetime.utcnow()
    
    # Calculate expected fix date based on SLA
    sla_days = get_sla_days(asset.asset_type.value)
    expected_fix_date = report_date + timedelta(days=sla_days)
    
    # Use asset's base cost if not specified
    estimated_cost = issue_in.estimated_repair_cost or asset.base_repair_cost
    
    # Map enums
    try:
        category_enum = IssueCategory(issue_in.category.value)
    except ValueError:
        category_enum = IssueCategory.OTHER
    
    try:
        severity_enum = IssueSeverity(issue_in.severity.value)
    except ValueError:
        severity_enum = IssueSeverity.MEDIUM
    
    issue = Issue(
        issue_code=issue_code,
        title=issue_in.title,
        description=issue_in.description,
        asset_id=issue_in.asset_id,
        category=category_enum,
        severity=severity_enum,
        estimated_repair_cost=estimated_cost,
        report_date=report_date,
        expected_fix_date=expected_fix_date,
        reported_by=issue_in.reported_by,
        reporter_contact=issue_in.reporter_contact,
    )
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    # Calculate initial debt (should be 0 if within SLA)
    debt_service = DebtService(db)
    debt_result = debt_service.calculate_issue_debt(issue)
    debt_service.update_issue_debt_tracking(issue, debt_result)
    db.commit()
    db.refresh(issue)
    
    return IssueResponse(
        id=issue.id,
        issue_code=issue.issue_code,
        title=issue.title,
        description=issue.description,
        asset_id=issue.asset_id,
        category=issue.category.value,
        severity=issue.severity.value,
        estimated_repair_cost=issue.estimated_repair_cost,
        actual_repair_cost=issue.actual_repair_cost,
        report_date=issue.report_date,
        expected_fix_date=issue.expected_fix_date,
        resolution_date=issue.resolution_date,
        is_resolved=issue.is_resolved,
        is_overdue=issue.is_overdue,
        days_open=issue.days_open,
        current_delay_days=issue.current_delay_days,
        current_debt_amount=issue.current_debt_amount,
        current_debt_multiplier=issue.current_debt_multiplier,
        reported_by=issue.reported_by,
        created_at=issue.created_at,
    )


@router.put("/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: int,
    issue_in: IssueUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing issue.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    if issue.is_resolved:
        raise HTTPException(status_code=400, detail="Cannot update resolved issue")
    
    # Update fields
    update_data = issue_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "category" and value:
            value = IssueCategory(value.value)
        elif field == "severity" and value:
            value = IssueSeverity(value.value)
        setattr(issue, field, value)
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    # Recalculate debt
    debt_service = DebtService(db)
    debt_result = debt_service.calculate_issue_debt(issue)
    debt_service.update_issue_debt_tracking(issue, debt_result)
    db.commit()
    db.refresh(issue)
    
    return IssueResponse(
        id=issue.id,
        issue_code=issue.issue_code,
        title=issue.title,
        description=issue.description,
        asset_id=issue.asset_id,
        category=issue.category.value,
        severity=issue.severity.value,
        estimated_repair_cost=issue.estimated_repair_cost,
        actual_repair_cost=issue.actual_repair_cost,
        report_date=issue.report_date,
        expected_fix_date=issue.expected_fix_date,
        resolution_date=issue.resolution_date,
        is_resolved=issue.is_resolved,
        is_overdue=issue.is_overdue,
        days_open=issue.days_open,
        current_delay_days=issue.current_delay_days,
        current_debt_amount=issue.current_debt_amount,
        current_debt_multiplier=issue.current_debt_multiplier,
        reported_by=issue.reported_by,
        created_at=issue.created_at,
    )


@router.patch("/{issue_id}/resolve", response_model=IssueResponse)
def resolve_issue(
    issue_id: int,
    resolve_in: IssueResolve,
    db: Session = Depends(get_db),
):
    """
    Mark an issue as resolved.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    if issue.is_resolved:
        raise HTTPException(status_code=400, detail="Issue is already resolved")
    
    # Resolve the issue
    issue.resolve(
        notes=resolve_in.resolution_notes,
        actual_cost=resolve_in.actual_repair_cost
    )
    
    # Update asset's last maintenance date
    asset = issue.asset
    asset.last_maintenance_date = datetime.utcnow()
    
    db.add(issue)
    db.add(asset)
    db.commit()
    db.refresh(issue)
    
    return IssueResponse(
        id=issue.id,
        issue_code=issue.issue_code,
        title=issue.title,
        description=issue.description,
        asset_id=issue.asset_id,
        category=issue.category.value,
        severity=issue.severity.value,
        estimated_repair_cost=issue.estimated_repair_cost,
        actual_repair_cost=issue.actual_repair_cost,
        report_date=issue.report_date,
        expected_fix_date=issue.expected_fix_date,
        resolution_date=issue.resolution_date,
        is_resolved=issue.is_resolved,
        is_overdue=False,  # Resolved, so not overdue
        days_open=issue.days_open,
        current_delay_days=issue.current_delay_days,
        current_debt_amount=issue.current_debt_amount,
        current_debt_multiplier=issue.current_debt_multiplier,
        reported_by=issue.reported_by,
        created_at=issue.created_at,
    )


@router.delete("/{issue_id}", status_code=204)
def delete_issue(
    issue_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete an issue.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    db.delete(issue)
    db.commit()
    return None
