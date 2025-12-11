"""
Allocation Rules routes
Endpoints for managing allocation rules
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from db.session import get_db
from models.models import AllocationRule
from schemas.schemas import (
    AllocationRuleCreate,
    AllocationRuleUpdate,
    AllocationRuleResponse
)
from deps.auth import get_current_user
from hooks.audit import AuditLogger, get_audit_logger
from services.allocation import AllocationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/allocation-rules", tags=["Allocation Rules"])


@router.post("/", response_model=AllocationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation_rule(
    rule: AllocationRuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Create a new allocation rule
    
    Args:
        rule: Allocation rule data
        request: FastAPI request
        db: Database session
        current_user: Current authenticated user
        audit_logger: Audit logger instance
        
    Returns:
        Created allocation rule
    """
    # Check if rule name already exists
    existing = db.query(AllocationRule).filter(
        AllocationRule.rule_name == rule.rule_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Allocation rule with name {rule.rule_name} already exists"
        )
    
    # Validate allocation logic
    allocation_service = AllocationService(db)
    try:
        allocation_logic_dict = [dest.model_dump() for dest in rule.allocation_logic]
        allocation_service.validate_allocation_logic(allocation_logic_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid allocation logic: {str(e)}"
        )
    
    # Set created_by to current user
    rule_data = rule.model_dump()
    rule_data['created_by'] = current_user
    # Convert allocation_logic to JSON-serializable format
    rule_data['allocation_logic'] = allocation_logic_dict
    
    # Create rule
    db_rule = AllocationRule(**rule_data)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    # Log to audit
    audit_logger.log_create(
        user_id=current_user,
        entity_type="allocation_rule",
        entity_id=db_rule.id,
        entity_data=rule_data,
        request=request
    )
    
    logger.info(f"Allocation rule created: {db_rule.rule_name}")
    
    return db_rule


@router.get("/", response_model=List[AllocationRuleResponse])
async def list_allocation_rules(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    List allocation rules with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of allocation rules
    """
    query = db.query(AllocationRule)
    
    if is_active is not None:
        query = query.filter(AllocationRule.is_active == is_active)
    
    rules = query.order_by(AllocationRule.priority.desc()).offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(rules)} allocation rules")
    
    return rules


@router.get("/{rule_id}", response_model=AllocationRuleResponse)
async def get_allocation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get a specific allocation rule by ID
    
    Args:
        rule_id: Allocation rule UUID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Allocation rule details
        
    Raises:
        HTTPException: If rule not found
    """
    rule = db.query(AllocationRule).filter(
        AllocationRule.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule {rule_id} not found"
        )
    
    return rule


@router.put("/{rule_id}", response_model=AllocationRuleResponse)
async def update_allocation_rule(
    rule_id: UUID,
    rule_update: AllocationRuleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Update an allocation rule
    
    Args:
        rule_id: Allocation rule UUID
        rule_update: Updated rule data
        request: FastAPI request
        db: Database session
        current_user: Current authenticated user
        audit_logger: Audit logger instance
        
    Returns:
        Updated allocation rule
        
    Raises:
        HTTPException: If rule not found
    """
    # Get existing rule
    db_rule = db.query(AllocationRule).filter(
        AllocationRule.id == rule_id
    ).first()
    
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule {rule_id} not found"
        )
    
    # Store old data for audit
    old_data = {
        "rule_description": db_rule.rule_description,
        "allocation_logic": db_rule.allocation_logic,
        "priority": db_rule.priority,
        "is_active": db_rule.is_active
    }
    
    # Validate allocation logic if provided
    update_data = rule_update.model_dump(exclude_unset=True)
    if 'allocation_logic' in update_data and update_data['allocation_logic']:
        allocation_service = AllocationService(db)
        allocation_logic_dict = [dest.model_dump() for dest in update_data['allocation_logic']]
        try:
            allocation_service.validate_allocation_logic(allocation_logic_dict)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid allocation logic: {str(e)}"
            )
        update_data['allocation_logic'] = allocation_logic_dict
    
    # Update fields
    update_data['updated_by'] = current_user
    
    for field, value in update_data.items():
        setattr(db_rule, field, value)
    
    db.commit()
    db.refresh(db_rule)
    
    # Log to audit
    new_data = {
        "rule_description": db_rule.rule_description,
        "allocation_logic": db_rule.allocation_logic,
        "priority": db_rule.priority,
        "is_active": db_rule.is_active
    }
    
    audit_logger.log_update(
        user_id=current_user,
        entity_type="allocation_rule",
        entity_id=db_rule.id,
        old_data=old_data,
        new_data=new_data,
        request=request
    )
    
    logger.info(f"Allocation rule updated: {db_rule.rule_name}")
    
    return db_rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allocation_rule(
    rule_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Delete an allocation rule (soft delete by setting is_active to False)
    
    Args:
        rule_id: Allocation rule UUID
        request: FastAPI request
        db: Database session
        current_user: Current authenticated user
        audit_logger: Audit logger instance
        
    Raises:
        HTTPException: If rule not found
    """
    db_rule = db.query(AllocationRule).filter(
        AllocationRule.id == rule_id
    ).first()
    
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allocation rule {rule_id} not found"
        )
    
    # Soft delete by setting is_active to False
    db_rule.is_active = False
    db_rule.updated_by = current_user
    db.commit()
    
    # Log to audit
    audit_logger.log_delete(
        user_id=current_user,
        entity_type="allocation_rule",
        entity_id=db_rule.id,
        entity_data={"rule_name": db_rule.rule_name},
        request=request
    )
    
    logger.info(f"Allocation rule deleted: {db_rule.rule_name}")
