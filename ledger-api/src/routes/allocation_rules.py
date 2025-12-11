"""
Allocation rules routes for managing fund allocation.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from src.db.session import get_db
from src.models.models import AllocationRule
from src.schemas.schemas import (
    AllocationRuleCreate,
    AllocationRuleUpdate,
    AllocationRuleResponse,
    LedgerTransactionResponse
)
from src.deps.auth import get_current_user, require_admin
from src.hooks.audit import AuditLogger
from src.services.allocation import AllocationService

router = APIRouter(prefix="/allocation-rules", tags=["Allocation Rules"])


@router.get("", response_model=List[AllocationRuleResponse])
def list_allocation_rules(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    List all allocation rules.
    Requires authentication.
    """
    query = db.query(AllocationRule)
    
    if is_active is not None:
        query = query.filter(AllocationRule.is_active == is_active)
    
    rules = query.order_by(AllocationRule.rule_name).offset(skip).limit(limit).all()
    
    return rules


@router.post("", response_model=AllocationRuleResponse, status_code=201)
def create_allocation_rule(
    rule: AllocationRuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin)
):
    """
    Create a new allocation rule.
    Requires admin authentication.
    """
    try:
        db_rule = AllocationService.create_allocation_rule(db, rule)
        
        # Log audit trail
        AuditLogger.log_create(
            db=db,
            entity_type="AllocationRule",
            entity_id=db_rule.id,
            entity_data={
                "rule_name": rule.rule_name,
                "source_account_id": str(rule.source_account_id),
                "allocation_count": len(rule.allocation_config)
            },
            user_id=current_user,
            request=request
        )
        
        return db_rule
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rule_id}", response_model=AllocationRuleResponse)
def get_allocation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get a specific allocation rule by ID.
    Requires authentication.
    """
    rule = db.query(AllocationRule).filter(
        AllocationRule.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Allocation rule not found")
    
    return rule


@router.put("/{rule_id}", response_model=AllocationRuleResponse)
def update_allocation_rule(
    rule_id: UUID,
    rule_update: AllocationRuleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin)
):
    """
    Update an allocation rule.
    Requires admin authentication.
    """
    try:
        # Get old data for audit
        db_rule = db.query(AllocationRule).filter(
            AllocationRule.id == rule_id
        ).first()
        
        if not db_rule:
            raise HTTPException(status_code=404, detail="Allocation rule not found")
        
        old_data = {
            "rule_name": db_rule.rule_name,
            "is_active": db_rule.is_active
        }
        
        # Update rule
        db_rule = AllocationService.update_allocation_rule(db, rule_id, rule_update)
        
        # Log audit trail
        new_data = {
            "rule_name": db_rule.rule_name,
            "is_active": db_rule.is_active
        }
        
        AuditLogger.log_update(
            db=db,
            entity_type="AllocationRule",
            entity_id=db_rule.id,
            old_data=old_data,
            new_data=new_data,
            user_id=current_user,
            request=request
        )
        
        return db_rule
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{rule_id}/execute", response_model=List[LedgerTransactionResponse])
def execute_allocation_rule(
    rule_id: UUID,
    amount: Decimal = Query(..., description="Amount to allocate", gt=0),
    reference_id: Optional[str] = Query(None, description="Reference ID for tracking"),
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin)
):
    """
    Execute an allocation rule for a given amount.
    Creates transactions according to the allocation configuration.
    Requires admin authentication.
    """
    try:
        transactions = AllocationService.execute_allocation(
            db, rule_id, amount, reference_id
        )
        
        # Log audit trail for execution
        AuditLogger.log_action(
            db=db,
            entity_type="AllocationRule",
            entity_id=rule_id,
            action="update",
            user_id=current_user,
            changes={
                "executed": True,
                "amount": str(amount),
                "transaction_count": len(transactions)
            },
            request=request
        )
        
        return transactions
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
