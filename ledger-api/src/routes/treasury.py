from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.session import get_db
from src.schemas.schemas import LogicalAccountRead, ReconciliationCreate, ReconciliationRead
from src.models.models import LogicalAccount
from src.services.reconciliation import reconcile_account
from src.deps.auth import require_guardian_role
from src.hooks.audit import write_audit
from typing import List

router = APIRouter(prefix="/api/v1/treasury", tags=["treasury"])


@router.get("/status", response_model=List[LogicalAccountRead])
async def get_treasury_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current status of all logical accounts.
    
    Args:
        db: Database session
        
    Returns:
        List of logical accounts with balances
    """
    result = await db.execute(
        select(LogicalAccount).order_by(LogicalAccount.name)
    )
    accounts = result.scalars().all()
    
    return accounts


@router.post("/reconcile", response_model=ReconciliationRead)
async def reconcile_treasury(
    reconciliation: ReconciliationCreate,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_guardian_role)
):
    """
    Reconcile a logical account with an external balance.
    Requires guardian role.
    
    Args:
        reconciliation: Reconciliation data
        db: Database session
        actor: Current actor (must have guardian role)
        
    Returns:
        Reconciliation log entry
    """
    try:
        reconciliation_log = await reconcile_account(
            db,
            reconciliation.logical_account_id,
            reconciliation.external_balance
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Write audit log
    await write_audit(
        db,
        action="RECONCILE_ACCOUNT",
        actor=actor.get("sub", "unknown"),
        target_id=reconciliation.logical_account_id,
        details={
            "external_balance": str(reconciliation.external_balance),
            "discrepancy": str(reconciliation_log.discrepancy)
        }
    )
    
    await db.commit()
    await db.refresh(reconciliation_log)
    
    return reconciliation_log
