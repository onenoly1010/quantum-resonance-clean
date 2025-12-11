"""
Treasury API Routes

Endpoints for treasury status and reconciliation
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from decimal import Decimal

from ..db.session import get_db
from ..models.logical_account import LogicalAccount
from ..schemas.reconciliation import ReconciliationCreate, ReconciliationResponse
from ..services.reconciliation import ReconciliationService, ReconciliationError
from ..deps.auth import get_current_user, require_admin_or_operator, TokenPayload
from ..hooks.audit import get_audit_logger, AuditLogger, AuditAction


router = APIRouter(prefix="/api/v1/treasury", tags=["treasury"])


@router.get("/status")
async def get_treasury_status(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get treasury status - all accounts with balances
    
    Returns account information with current balances.
    Requires authentication.
    """
    # Query all accounts with their balances
    query = select(LogicalAccount).order_by(LogicalAccount.type, LogicalAccount.name)
    result = await db.execute(query)
    accounts = result.scalars().all()
    
    # Group by account type
    accounts_by_type = {}
    total_assets = Decimal("0")
    total_liabilities = Decimal("0")
    
    for account in accounts:
        account_type = account.type
        if account_type not in accounts_by_type:
            accounts_by_type[account_type] = []
        
        accounts_by_type[account_type].append({
            "id": str(account.id),
            "name": account.name,
            "balance": str(account.balance),
            "metadata": account.metadata,
        })
        
        # Calculate totals
        if account_type == "ASSET":
            total_assets += account.balance
        elif account_type == "LIABILITY":
            total_liabilities += account.balance
    
    net_worth = total_assets - total_liabilities
    
    return {
        "accounts_by_type": accounts_by_type,
        "summary": {
            "total_assets": str(total_assets),
            "total_liabilities": str(total_liabilities),
            "net_worth": str(net_worth),
            "account_count": len(accounts),
        }
    }


@router.post("/reconcile", response_model=ReconciliationResponse, status_code=status.HTTP_201_CREATED)
async def reconcile_account(
    reconciliation_data: ReconciliationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_admin_or_operator),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """
    Reconcile an account with external balance
    
    Compares internal ledger balance with external source (blockchain, bank, etc)
    and creates a reconciliation log entry.
    
    Requires admin or operator role.
    """
    try:
        reconciliation_service = ReconciliationService(db)
        
        reconciliation = await reconciliation_service.create_reconciliation_log(
            account_id=reconciliation_data.logical_account_id,
            external_balance=reconciliation_data.external_balance,
            currency=reconciliation_data.currency,
        )
        
        await db.commit()
        await db.refresh(reconciliation)
        
        # Log audit entry
        await audit.log_from_request(
            action=AuditAction.CREATE_RECONCILIATION,
            request=request,
            user=user,
            target_id=reconciliation.id,
            target_type="reconciliation_log",
            details={
                "account_id": str(reconciliation.logical_account_id),
                "external_balance": str(reconciliation.external_balance),
                "internal_balance": str(reconciliation.internal_balance),
                "discrepancy": str(reconciliation.discrepancy),
            }
        )
        
        return reconciliation
    
    except ReconciliationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/reconciliations", response_model=List[ReconciliationResponse])
async def list_reconciliations(
    skip: int = 0,
    limit: int = 100,
    resolved: bool = False,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """
    List reconciliation logs
    
    Query parameters:
    - skip: Pagination offset (default: 0)
    - limit: Number of results (default: 100)
    - resolved: Show only resolved/unresolved (default: False = unresolved)
    
    Requires authentication.
    """
    from ..models.reconciliation_log import ReconciliationLog
    
    query = select(ReconciliationLog).where(
        ReconciliationLog.resolved == resolved
    ).order_by(ReconciliationLog.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    reconciliations = result.scalars().all()
    
    return list(reconciliations)


@router.post("/reconciliations/{reconciliation_id}/resolve", response_model=ReconciliationResponse)
async def resolve_reconciliation(
    reconciliation_id: str,
    request: Request,
    notes: str,
    create_correction: bool = False,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_admin_or_operator),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """
    Resolve a reconciliation manually or with correction transaction
    
    Query parameters:
    - notes: Required notes explaining the resolution
    - create_correction: Whether to create a correction transaction (default: False)
    
    Requires admin or operator role.
    """
    import uuid as uuid_lib
    
    try:
        reconciliation_service = ReconciliationService(db)
        reconciliation_uuid = uuid_lib.UUID(reconciliation_id)
        
        if create_correction:
            # Create correction transaction to resolve discrepancy
            from ..models.reconciliation_log import ReconciliationLog
            query = select(ReconciliationLog).where(ReconciliationLog.id == reconciliation_uuid)
            result = await db.execute(query)
            reconciliation = result.scalar_one_or_none()
            
            if reconciliation is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Reconciliation {reconciliation_id} not found"
                )
            
            await reconciliation_service.create_correction_transaction(
                reconciliation=reconciliation,
                approved_by=user.sub,
                notes=notes
            )
            
            await db.commit()
            await db.refresh(reconciliation)
            
            # Log audit entry
            await audit.log_from_request(
                action=AuditAction.CREATE_CORRECTION,
                request=request,
                user=user,
                target_id=reconciliation.id,
                target_type="reconciliation_log",
                details={"notes": notes, "correction_created": True}
            )
        else:
            # Manually resolve without correction
            reconciliation = await reconciliation_service.resolve_reconciliation_manually(
                reconciliation_id=reconciliation_uuid,
                resolved_by=user.sub,
                notes=notes
            )
            
            await db.commit()
            await db.refresh(reconciliation)
            
            # Log audit entry
            await audit.log_from_request(
                action=AuditAction.RESOLVE_RECONCILIATION,
                request=request,
                user=user,
                target_id=reconciliation.id,
                target_type="reconciliation_log",
                details={"notes": notes, "manual_resolution": True}
            )
        
        return reconciliation
    
    except ReconciliationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
