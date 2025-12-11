from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.session import get_db
from src.schemas.schemas import AllocationRuleCreate, AllocationRuleRead
from src.models.models import AllocationRule
from src.deps.auth import require_guardian_role
from src.hooks.audit import write_audit
from typing import List

router = APIRouter(prefix="/api/v1/allocation_rules", tags=["allocation_rules"])


@router.get("/", response_model=List[AllocationRuleRead])
async def list_allocation_rules(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    List allocation rules.
    
    Args:
        active_only: If true, only return active rules
        db: Database session
        
    Returns:
        List of allocation rules
    """
    query = select(AllocationRule).order_by(AllocationRule.created_at.desc())
    
    if active_only:
        query = query.where(AllocationRule.active == True)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return rules


@router.post("/", response_model=AllocationRuleRead, status_code=201)
async def create_allocation_rule(
    rule: AllocationRuleCreate,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_guardian_role)
):
    """
    Create a new allocation rule. Requires guardian role.
    
    Args:
        rule: Allocation rule data
        db: Database session
        actor: Current actor (must have guardian role)
        
    Returns:
        Created allocation rule
    """
    # Validate that percentages sum to 100 (already done by Pydantic)
    # Convert allocations to JSONB format
    rule_data = {
        "allocations": [
            {
                "logical_account_id": str(item.logical_account_id),
                "percent": str(item.percent)
            }
            for item in rule.allocations
        ]
    }
    
    # Create allocation rule
    allocation_rule = AllocationRule(
        name=rule.name,
        rule_data=rule_data,
        active=rule.active
    )
    
    db.add(allocation_rule)
    await db.flush()
    
    # Write audit log
    await write_audit(
        db,
        action="CREATE_ALLOCATION_RULE",
        actor=actor.get("sub", "unknown"),
        target_id=allocation_rule.id,
        details={"name": rule.name, "active": rule.active}
    )
    
    await db.commit()
    await db.refresh(allocation_rule)
    
    return allocation_rule
