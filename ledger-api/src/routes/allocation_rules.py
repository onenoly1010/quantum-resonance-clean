"""Allocation rules routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..db import get_db
from ..models.models import AllocationRule
from ..schemas.schemas import (
    AllocationRuleCreate, AllocationRuleUpdate, AllocationRuleResponse,
    MessageResponse
)
from ..deps import get_current_user, require_role
from ..hooks import get_audit_hook
from ..services import AllocationService


router = APIRouter(prefix="/api/v1/allocation-rules", tags=["allocation-rules"])


@router.post("/", response_model=AllocationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation_rule(
    request: Request,
    rule_data: AllocationRuleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("allocation_manager"))
):
    """Create a new allocation rule."""
    # Validate allocation rules
    allocation_service = AllocationService(db)
    
    try:
        # Convert Pydantic models to dict for validation
        rules_dict = [item.model_dump() for item in rule_data.rules]
        allocation_service.validate_allocation_rules(rules_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Create allocation rule
    allocation_rule = AllocationRule(
        rule_name=rule_data.rule_name,
        source_account_id=rule_data.source_account_id,
        rules=rules_dict,
        priority=rule_data.priority,
        created_by=current_user.get("user_id"),
        metadata=rule_data.metadata
    )
    
    db.add(allocation_rule)
    db.commit()
    db.refresh(allocation_rule)
    
    # Audit log
    audit = get_audit_hook(db, request)
    audit.log_create(
        table_name="allocation_rules",
        record_id=allocation_rule.id,
        user_id=current_user.get("user_id"),
        data={"rule_name": rule_data.rule_name}
    )
    
    return allocation_rule


@router.get("/{rule_id}", response_model=AllocationRuleResponse)
async def get_allocation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific allocation rule."""
    rule = db.query(AllocationRule).filter(
        AllocationRule.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule {rule_id} not found"
        )
    
    return rule


@router.get("/", response_model=List[AllocationRuleResponse])
async def list_allocation_rules(
    is_active: Optional[bool] = None,
    source_account_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List allocation rules with optional filtering."""
    query = db.query(AllocationRule)
    
    if is_active is not None:
        query = query.filter(AllocationRule.is_active == is_active)
    if source_account_id:
        query = query.filter(AllocationRule.source_account_id == source_account_id)
    
    rules = query.order_by(AllocationRule.priority, AllocationRule.created_at).all()
    return rules


@router.patch("/{rule_id}", response_model=AllocationRuleResponse)
async def update_allocation_rule(
    request: Request,
    rule_id: UUID,
    rule_data: AllocationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("allocation_manager"))
):
    """Update an allocation rule."""
    rule = db.query(AllocationRule).filter(
        AllocationRule.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule {rule_id} not found"
        )
    
    # Store old data
    old_data = {
        "rule_name": rule.rule_name,
        "is_active": rule.is_active,
        "priority": rule.priority
    }
    
    # Validate new rules if provided
    if rule_data.rules is not None:
        allocation_service = AllocationService(db)
        try:
            rules_dict = [item.model_dump() for item in rule_data.rules]
            allocation_service.validate_allocation_rules(rules_dict)
            rule.rules = rules_dict
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    # Update other fields
    if rule_data.rule_name is not None:
        rule.rule_name = rule_data.rule_name
    if rule_data.is_active is not None:
        rule.is_active = rule_data.is_active
    if rule_data.priority is not None:
        rule.priority = rule_data.priority
    if rule_data.metadata is not None:
        rule.metadata = rule_data.metadata
    
    db.commit()
    db.refresh(rule)
    
    # Audit log
    audit = get_audit_hook(db, request)
    audit.log_update(
        table_name="allocation_rules",
        record_id=rule.id,
        user_id=current_user.get("user_id"),
        old_data=old_data,
        new_data={
            "rule_name": rule.rule_name,
            "is_active": rule.is_active,
            "priority": rule.priority
        }
    )
    
    return rule


@router.delete("/{rule_id}", response_model=MessageResponse)
async def delete_allocation_rule(
    request: Request,
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("allocation_manager"))
):
    """Delete an allocation rule."""
    rule = db.query(AllocationRule).filter(
        AllocationRule.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule {rule_id} not found"
        )
    
    # Audit log before deletion
    audit = get_audit_hook(db, request)
    audit.log_delete(
        table_name="allocation_rules",
        record_id=rule.id,
        user_id=current_user.get("user_id"),
        data={"rule_name": rule.rule_name}
    )
    
    db.delete(rule)
    db.commit()
    
    return MessageResponse(
        message=f"Allocation rule {rule_id} deleted successfully"
    )


@router.post("/{rule_id}/apply")
async def apply_allocation_rule(
    request: Request,
    rule_id: UUID,
    source_transaction_id: UUID,
    amount: float,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("allocation_manager"))
):
    """
    Apply an allocation rule to distribute an amount.
    
    This will calculate the allocation but not create transactions.
    Use POST /allocate endpoint to create actual transactions.
    """
    allocation_service = AllocationService(db)
    
    try:
        from decimal import Decimal
        allocations = allocation_service.apply_allocation_rule(
            rule_id=rule_id,
            source_transaction_id=source_transaction_id,
            amount=Decimal(str(amount))
        )
        
        # Convert Decimal to float for JSON serialization
        for allocation in allocations:
            allocation["amount"] = float(allocation["amount"])
            allocation["account_id"] = str(allocation["account_id"])
        
        return {
            "rule_id": str(rule_id),
            "source_transaction_id": str(source_transaction_id),
            "total_amount": amount,
            "allocations": allocations
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/allocate", response_model=MessageResponse)
async def create_allocation_transactions(
    request: Request,
    source_account_id: UUID,
    allocations: List[dict],
    description: str = "Automatic allocation",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("allocation_manager"))
):
    """
    Create transactions based on allocation results.
    
    This endpoint creates actual ledger transactions for the allocations.
    """
    allocation_service = AllocationService(db)
    
    try:
        # Convert amounts to Decimal
        for allocation in allocations:
            from decimal import Decimal
            allocation["amount"] = Decimal(str(allocation["amount"]))
            if isinstance(allocation["account_id"], str):
                allocation["account_id"] = UUID(allocation["account_id"])
        
        transaction_ids = allocation_service.create_allocation_transactions(
            source_account_id=source_account_id,
            allocations=allocations,
            description=description
        )
        
        # Audit log
        audit = get_audit_hook(db, request)
        audit.log_create(
            table_name="transactions",
            record_id=UUID('00000000-0000-0000-0000-000000000000'),  # Bulk operation
            user_id=current_user.get("user_id"),
            data={"allocation_count": len(transaction_ids)}
        )
        
        return MessageResponse(
            message=f"Created {len(transaction_ids)} allocation transactions",
            detail={"transaction_ids": [str(tid) for tid in transaction_ids]}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
