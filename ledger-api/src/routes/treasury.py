"""Treasury routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from ..db import get_db
from ..models.models import TreasuryAccount, Account
from ..schemas.schemas import (
    TreasuryAccountCreate, TreasuryAccountUpdate, TreasuryAccountResponse,
    MessageResponse
)
from ..deps import get_current_user, require_role
from ..hooks import get_audit_hook
from ..services import ReconciliationService


router = APIRouter(prefix="/api/v1/treasury", tags=["treasury"])


@router.post("/accounts", response_model=TreasuryAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_treasury_account(
    request: Request,
    treasury_data: TreasuryAccountCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("treasury_manager"))
):
    """Create a new treasury account."""
    # Verify account exists
    account = db.query(Account).filter(Account.id == treasury_data.account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {treasury_data.account_id} not found"
        )
    
    # Create treasury account
    treasury = TreasuryAccount(
        account_id=treasury_data.account_id,
        treasury_type=treasury_data.treasury_type,
        currency=treasury_data.currency,
        balance=Decimal("0"),
        metadata=treasury_data.metadata
    )
    
    db.add(treasury)
    db.commit()
    db.refresh(treasury)
    
    # Audit log
    audit = get_audit_hook(db, request)
    audit.log_create(
        table_name="treasury_accounts",
        record_id=treasury.id,
        user_id=current_user.get("user_id"),
        data={"account_id": str(treasury_data.account_id)}
    )
    
    return treasury


@router.get("/accounts/{treasury_id}", response_model=TreasuryAccountResponse)
async def get_treasury_account(
    treasury_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific treasury account."""
    treasury = db.query(TreasuryAccount).filter(
        TreasuryAccount.id == treasury_id
    ).first()
    
    if not treasury:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Treasury account {treasury_id} not found"
        )
    
    return treasury


@router.get("/accounts", response_model=List[TreasuryAccountResponse])
async def list_treasury_accounts(
    treasury_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List treasury accounts with optional filtering."""
    query = db.query(TreasuryAccount)
    
    if treasury_type:
        query = query.filter(TreasuryAccount.treasury_type == treasury_type)
    if is_active is not None:
        query = query.filter(TreasuryAccount.is_active == is_active)
    
    accounts = query.order_by(TreasuryAccount.treasury_type).all()
    return accounts


@router.get("/balance")
async def get_total_balance(
    currency: str = "USD",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get total treasury balance across all active accounts."""
    from sqlalchemy import func
    
    total = db.query(
        func.sum(TreasuryAccount.balance)
    ).filter(
        TreasuryAccount.is_active == True,
        TreasuryAccount.currency == currency
    ).scalar() or Decimal("0")
    
    # Get breakdown by type
    breakdown = db.query(
        TreasuryAccount.treasury_type,
        func.sum(TreasuryAccount.balance).label("total")
    ).filter(
        TreasuryAccount.is_active == True,
        TreasuryAccount.currency == currency
    ).group_by(TreasuryAccount.treasury_type).all()
    
    return {
        "currency": currency,
        "total_balance": float(total),
        "breakdown": [
            {"type": item[0], "balance": float(item[1])}
            for item in breakdown
        ]
    }


@router.get("/balance/{account_id}")
async def get_treasury_balance_by_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get calculated balance for a treasury account from ledger."""
    # Use reconciliation service to calculate actual balance
    recon_service = ReconciliationService(db)
    
    try:
        ledger_balance = recon_service.calculate_ledger_balance(account_id)
        
        # Get treasury account record
        treasury = db.query(TreasuryAccount).filter(
            TreasuryAccount.account_id == account_id
        ).first()
        
        return {
            "account_id": str(account_id),
            "ledger_balance": float(ledger_balance),
            "treasury_balance": float(treasury.balance) if treasury else 0,
            "difference": float(ledger_balance - (treasury.balance if treasury else 0))
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/accounts/{treasury_id}", response_model=TreasuryAccountResponse)
async def update_treasury_account(
    request: Request,
    treasury_id: UUID,
    treasury_data: TreasuryAccountUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("treasury_manager"))
):
    """Update a treasury account."""
    treasury = db.query(TreasuryAccount).filter(
        TreasuryAccount.id == treasury_id
    ).first()
    
    if not treasury:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Treasury account {treasury_id} not found"
        )
    
    # Store old data
    old_data = {
        "is_active": treasury.is_active
    }
    
    # Update fields
    if treasury_data.is_active is not None:
        treasury.is_active = treasury_data.is_active
    if treasury_data.metadata is not None:
        treasury.metadata = treasury_data.metadata
    
    db.commit()
    db.refresh(treasury)
    
    # Audit log
    audit = get_audit_hook(db, request)
    audit.log_update(
        table_name="treasury_accounts",
        record_id=treasury.id,
        user_id=current_user.get("user_id"),
        old_data=old_data,
        new_data={"is_active": treasury.is_active}
    )
    
    return treasury


@router.post("/sync-balances", response_model=MessageResponse)
async def sync_treasury_balances(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("treasury_manager"))
):
    """Synchronize treasury balances with ledger balances."""
    recon_service = ReconciliationService(db)
    
    treasuries = db.query(TreasuryAccount).filter(
        TreasuryAccount.is_active == True
    ).all()
    
    updated_count = 0
    
    for treasury in treasuries:
        try:
            ledger_balance = recon_service.calculate_ledger_balance(treasury.account_id)
            treasury.balance = ledger_balance
            updated_count += 1
        except ValueError:
            # Skip accounts that don't exist or have issues
            continue
    
    db.commit()
    
    # Audit log
    audit = get_audit_hook(db, request)
    audit.log_update(
        table_name="treasury_accounts",
        record_id=UUID('00000000-0000-0000-0000-000000000000'),  # Bulk operation
        user_id=current_user.get("user_id"),
        old_data={},
        new_data={"sync_count": updated_count}
    )
    
    return MessageResponse(
        message=f"Successfully synchronized {updated_count} treasury accounts"
    )
