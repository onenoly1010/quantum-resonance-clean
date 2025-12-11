"""Allocation rules management routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from db.session import get_db
from models.models import AllocationRule, LogicalAccount
from schemas.schemas import (
    AllocationRuleCreate,
    AllocationRuleUpdate,
    AllocationRuleResponse
)
from deps.auth import get_current_user, require_guardian_role, get_optional_user
from hooks.audit import AuditHook

router = APIRouter(prefix="/api/v1/allocation-rules", tags=["allocation-rules"])


@router.post("/", response_model=AllocationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation_rule(
    rule: AllocationRuleCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_guardian_role)
):
    """
    Create a new allocation rule.
    
    Requires guardian role authorization.
    """
    # Verify source account exists
    source_account = db.query(LogicalAccount).filter(
        LogicalAccount.account_id == rule.source_account_id
    ).first()
    
    if not source_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source account not found: {rule.source_account_id}"
        )
    
    # Verify all destination accounts exist
    for allocation in rule.allocation_config:
        dest_account = db.query(LogicalAccount).filter(
            LogicalAccount.account_id == allocation.destination_account_id
        ).first()
        if not dest_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Destination account not found: {allocation.destination_account_id}"
            )
    
    # Convert allocation config to dict format for JSONB
    allocation_config = [
        {
            "destination_account_id": a.destination_account_id,
            "percentage": a.percentage,
            "condition": a.condition
        }
        for a in rule.allocation_config
    ]
    
    # Create allocation rule
    db_rule = AllocationRule(
        rule_id=f"RULE-{uuid.uuid4().hex[:12].upper()}",
        rule_name=rule.rule_name,
        source_account_id=rule.source_account_id,
        allocation_config=allocation_config,
        is_active=rule.is_active,
        priority=rule.priority,
        effective_from=rule.effective_from or datetime.utcnow(),
        effective_to=rule.effective_to,
        created_by=current_user
    )
    
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    # Log to audit
    AuditHook.log_allocation_rule_change(
        db=db,
        rule_id=db_rule.rule_id,
        action="CREATE",
        new_value={
            "rule_name": rule.rule_name,
            "source_account_id": rule.source_account_id,
            "allocation_config": allocation_config
        },
        changed_by=current_user
    )
    
    return db_rule


@router.get("/", response_model=List[AllocationRuleResponse])
async def list_allocation_rules(
    source_account_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    List allocation rules with optional filtering.
    
    Authentication is optional for read operations.
    """
    query = db.query(AllocationRule)
    
    if source_account_id:
        query = query.filter(AllocationRule.source_account_id == source_account_id)
    if is_active is not None:
        query = query.filter(AllocationRule.is_active == is_active)
    
    query = query.order_by(AllocationRule.priority.desc(), AllocationRule.created_at.desc())
    
    return query.all()


@router.get("/{rule_id}", response_model=AllocationRuleResponse)
async def get_allocation_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Get details of a specific allocation rule.
    
    Authentication is optional for read operations.
    """
    rule = db.query(AllocationRule).filter(
        AllocationRule.rule_id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule not found: {rule_id}"
        )
    
    return rule


@router.put("/{rule_id}", response_model=AllocationRuleResponse)
async def update_allocation_rule(
    rule_id: str,
    rule_update: AllocationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_guardian_role)
):
    """
    Update an allocation rule.
    
    Requires guardian role authorization.
    """
    # Get existing rule
    db_rule = db.query(AllocationRule).filter(
        AllocationRule.rule_id == rule_id
    ).first()
    
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule not found: {rule_id}"
        )
    
    # Store old values for audit
    old_value = {
        "rule_name": db_rule.rule_name,
        "allocation_config": db_rule.allocation_config,
        "is_active": db_rule.is_active,
        "priority": db_rule.priority
    }
    
    # Update fields
    if rule_update.rule_name is not None:
        db_rule.rule_name = rule_update.rule_name
    if rule_update.allocation_config is not None:
        # Validate destination accounts exist
        for allocation in rule_update.allocation_config:
            dest_account = db.query(LogicalAccount).filter(
                LogicalAccount.account_id == allocation.destination_account_id
            ).first()
            if not dest_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination account not found: {allocation.destination_account_id}"
                )
        
        # Convert to dict format
        db_rule.allocation_config = [
            {
                "destination_account_id": a.destination_account_id,
                "percentage": a.percentage,
                "condition": a.condition
            }
            for a in rule_update.allocation_config
        ]
    if rule_update.is_active is not None:
        db_rule.is_active = rule_update.is_active
    if rule_update.priority is not None:
        db_rule.priority = rule_update.priority
    if rule_update.effective_to is not None:
        db_rule.effective_to = rule_update.effective_to
    
    db_rule.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_rule)
    
    # Log to audit
    AuditHook.log_allocation_rule_change(
        db=db,
        rule_id=rule_id,
        action="UPDATE",
        old_value=old_value,
        new_value={
            "rule_name": db_rule.rule_name,
            "allocation_config": db_rule.allocation_config,
            "is_active": db_rule.is_active,
            "priority": db_rule.priority
        },
        changed_by=current_user
    )
    
    return db_rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allocation_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_guardian_role)
):
    """
    Delete (deactivate) an allocation rule.
    
    Requires guardian role authorization.
    Note: This performs a soft delete by setting is_active to False.
    """
    db_rule = db.query(AllocationRule).filter(
        AllocationRule.rule_id == rule_id
    ).first()
    
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule not found: {rule_id}"
        )
    
    # Soft delete
    old_value = {
        "rule_name": db_rule.rule_name,
        "is_active": db_rule.is_active
    }
    
    db_rule.is_active = False
    db_rule.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Log to audit
    AuditHook.log_allocation_rule_change(
        db=db,
        rule_id=rule_id,
        action="DELETE",
        old_value=old_value,
        new_value={"is_active": False},
        changed_by=current_user
    )
    
    return None
