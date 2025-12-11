"""
Allocation Rules API Routes

CRUD endpoints for allocation rules (admin-protected)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from ..db.session import get_db
from ..models.allocation_rule import AllocationRule
from ..schemas.allocation_rule import (
    AllocationRuleCreate,
    AllocationRuleResponse,
    AllocationRuleUpdate,
)
from ..deps.auth import require_admin, TokenPayload
from ..hooks.audit import get_audit_logger, AuditLogger, AuditAction


router = APIRouter(prefix="/api/v1/allocation-rules", tags=["allocation-rules"])


@router.get("", response_model=List[AllocationRuleResponse])
async def list_allocation_rules(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_admin),
):
    """
    List allocation rules
    
    Query parameters:
    - skip: Pagination offset (default: 0)
    - limit: Number of results (default: 100)
    - active_only: Show only active rules (default: False)
    
    Requires admin role.
    """
    query = select(AllocationRule).order_by(AllocationRule.created_at.desc())
    
    if active_only:
        query = query.where(AllocationRule.active == True)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return list(rules)


@router.post("", response_model=AllocationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation_rule(
    rule_data: AllocationRuleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_admin),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """
    Create a new allocation rule
    
    The rule's percentages must sum to exactly 100.0.
    
    Requires admin role.
    """
    # Check if rule with same name exists
    existing_query = select(AllocationRule).where(AllocationRule.name == rule_data.name)
    existing_result = await db.execute(existing_query)
    existing_rule = existing_result.scalar_one_or_none()
    
    if existing_rule:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Allocation rule with name '{rule_data.name}' already exists"
        )
    
    # Validate destination accounts exist
    from ..models.logical_account import LogicalAccount
    from ..services.allocation import AllocationEngine
    
    allocation_engine = AllocationEngine(db)
    
    # Convert Pydantic models to dicts for validation
    rules_dict = [rule.model_dump() for rule in rule_data.rules]
    
    try:
        allocation_engine.validate_allocation_rules(rules_dict)
        await allocation_engine.validate_destination_accounts(rules_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Create allocation rule
    rule = AllocationRule(
        name=rule_data.name,
        rules=rules_dict,
        active=rule_data.active,
        description=rule_data.description,
        created_by=rule_data.created_by or user.sub,
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    # Log audit entry
    await audit.log_from_request(
        action=AuditAction.CREATE_ALLOCATION_RULE,
        request=request,
        user=user,
        target_id=rule.id,
        target_type="allocation_rule",
        details={
            "name": rule.name,
            "rule_count": len(rule_data.rules),
            "active": rule.active,
        }
    )
    
    return rule


@router.get("/{rule_id}", response_model=AllocationRuleResponse)
async def get_allocation_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_admin),
):
    """
    Get a specific allocation rule by ID
    
    Requires admin role.
    """
    query = select(AllocationRule).where(AllocationRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule {rule_id} not found"
        )
    
    return rule


@router.put("/{rule_id}", response_model=AllocationRuleResponse)
async def update_allocation_rule(
    rule_id: uuid.UUID,
    update_data: AllocationRuleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_admin),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """
    Update an allocation rule
    
    Requires admin role.
    """
    query = select(AllocationRule).where(AllocationRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule {rule_id} not found"
        )
    
    # Validate rules if provided
    if update_data.rules is not None:
        from ..services.allocation import AllocationEngine
        
        allocation_engine = AllocationEngine(db)
        rules_dict = [r.model_dump() for r in update_data.rules]
        
        try:
            allocation_engine.validate_allocation_rules(rules_dict)
            await allocation_engine.validate_destination_accounts(rules_dict)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Convert rules to dict if present
    if "rules" in update_dict and update_dict["rules"] is not None:
        update_dict["rules"] = [r.model_dump() for r in update_data.rules]
    
    for field, value in update_dict.items():
        setattr(rule, field, value)
    
    await db.commit()
    await db.refresh(rule)
    
    # Log audit entry
    await audit.log_from_request(
        action=AuditAction.UPDATE_ALLOCATION_RULE,
        request=request,
        user=user,
        target_id=rule.id,
        target_type="allocation_rule",
        details=update_dict
    )
    
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allocation_rule(
    rule_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_admin),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """
    Delete an allocation rule
    
    Requires admin role.
    """
    query = select(AllocationRule).where(AllocationRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule {rule_id} not found"
        )
    
    # Log audit entry before deletion
    await audit.log_from_request(
        action=AuditAction.DELETE_ALLOCATION_RULE,
        request=request,
        user=user,
        target_id=rule.id,
        target_type="allocation_rule",
        details={"name": rule.name}
    )
    
    await db.delete(rule)
    await db.commit()
    
    return None
