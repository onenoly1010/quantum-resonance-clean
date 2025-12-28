"""
Treasury routes for logical account management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from src.db.session import get_db
from src.models.models import LogicalAccount
from src.schemas.schemas import (
    LogicalAccountCreate, 
    LogicalAccountUpdate, 
    LogicalAccountResponse,
    AccountBalanceResponse
)
from src.deps.auth import get_current_user, require_admin
from src.hooks.audit import AuditLogger
from src.services.reconciliation import ReconciliationService

router = APIRouter(prefix="/treasury", tags=["Treasury"])


@router.get("/accounts", response_model=List[LogicalAccountResponse])
def list_accounts(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    List all logical accounts.
    Requires authentication.
    """
    query = db.query(LogicalAccount)
    
    if is_active is not None:
        query = query.filter(LogicalAccount.is_active == is_active)
    
    if account_type:
        query = query.filter(LogicalAccount.account_type == account_type)
    
    accounts = query.order_by(LogicalAccount.account_name).offset(skip).limit(limit).all()
    
    return accounts


@router.post("/accounts", response_model=LogicalAccountResponse, status_code=201)
def create_account(
    account: LogicalAccountCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin)
):
    """
    Create a new logical account.
    Requires admin authentication.
    """
    # Check if account name already exists
    existing_account = db.query(LogicalAccount).filter(
        LogicalAccount.account_name == account.account_name
    ).first()
    
    if existing_account:
        raise HTTPException(
            status_code=400, 
            detail=f"Account with name '{account.account_name}' already exists"
        )
    
    # Create account
    account_record = LogicalAccount(
        account_name=account.account_name,
        account_type=account.account_type,
        description=account.description,
        custom_metadata=account.metadata,
        is_active=account.is_active
    )
    
    db.add(account_record)
    db.commit()
    db.refresh(account_record)
    
    # Log audit trail
    AuditLogger.log_create(
        db=db,
        entity_type="LogicalAccount",
        entity_id=account_record.id,
        entity_data={
            "account_name": account.account_name,
            "account_type": account.account_type
        },
        user_id=current_user,
        request=request
    )
    
    return account_record


@router.get("/accounts/{account_id}", response_model=LogicalAccountResponse)
def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get a specific logical account by ID.
    Requires authentication.
    """
    account = db.query(LogicalAccount).filter(
        LogicalAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account


@router.put("/accounts/{account_id}", response_model=LogicalAccountResponse)
def update_account(
    account_id: UUID,
    account_update: LogicalAccountUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin)
):
    """
    Update a logical account.
    Requires admin authentication.
    """
    account_record = db.query(LogicalAccount).filter(
        LogicalAccount.id == account_id
    ).first()
    
    if not account_record:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Store old data for audit
    old_data = {
        "account_name": account_record.account_name,
        "account_type": account_record.account_type,
        "is_active": account_record.is_active
    }
    
    # Update fields
    if account_update.account_name is not None:
        account_record.account_name = account_update.account_name
    
    if account_update.account_type is not None:
        account_record.account_type = account_update.account_type
    
    if account_update.description is not None:
        account_record.description = account_update.description
    
    if account_update.metadata is not None:
        account_record.custom_metadata = account_update.metadata
    
    if account_update.is_active is not None:
        account_record.is_active = account_update.is_active
    
    db.commit()
    db.refresh(account_record)
    
    # Log audit trail
    new_data = {
        "account_name": account_record.account_name,
        "account_type": account_record.account_type,
        "is_active": account_record.is_active
    }
    
    AuditLogger.log_update(
        db=db,
        entity_type="LogicalAccount",
        entity_id=account_record.id,
        old_data=old_data,
        new_data=new_data,
        user_id=current_user,
        request=request
    )
    
    return account_record


@router.get("/balance/{account_id}", response_model=AccountBalanceResponse)
def get_account_balance(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get the current balance for an account.
    Requires authentication.
    """
    account_record = db.query(LogicalAccount).filter(
        LogicalAccount.id == account_id
    ).first()
    
    if not account_record:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Calculate balance
    balance = ReconciliationService.calculate_account_balance(db, account_id)
    
    # Get last transaction date
    from src.models.models import LedgerTransaction
    last_transaction = db.query(LedgerTransaction).filter(
        LedgerTransaction.account_id == account_id
    ).order_by(LedgerTransaction.transaction_date.desc()).first()
    
    last_transaction_date = None
    if last_transaction:
        last_transaction_date = last_transaction.transaction_date
    
    return AccountBalanceResponse(
        account_id=account_id,
        account_name=account_record.account_name,
        balance=balance,
        currency="USD",
        last_transaction_date=last_transaction_date
    )
