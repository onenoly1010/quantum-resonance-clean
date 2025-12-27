"""
Transaction routes for ledger API.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from src.db.session import get_db
from src.models.models import LedgerTransaction, LogicalAccount
from src.schemas.schemas import LedgerTransactionCreate, LedgerTransactionResponse
from src.deps.auth import get_current_user
from src.hooks.audit import AuditLogger

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=LedgerTransactionResponse, status_code=201)
def create_transaction(
    transaction: LedgerTransactionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new ledger transaction.
    Requires authentication.
    """
    # Verify account exists
    account_record = db.query(LogicalAccount).filter(
        LogicalAccount.id == transaction.account_id
    ).first()
    
    if not account_record:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Create transaction
    transaction_record = LedgerTransaction(
        account_id=transaction.account_id,
        amount=transaction.amount,
        currency=transaction.currency,
        transaction_type=transaction.transaction_type,
        reference_id=transaction.reference_id,
        description=transaction.description,
        custom_metadata=transaction.metadata,
        transaction_date=transaction.transaction_date or datetime.utcnow()
    )
    
    db.add(transaction_record)
    db.commit()
    db.refresh(transaction_record)
    
    # Log audit trail
    AuditLogger.log_create(
        db=db,
        entity_type="LedgerTransaction",
        entity_id=transaction_record.id,
        entity_data={
            "account_id": str(transaction.account_id),
            "amount": str(transaction.amount),
            "transaction_type": transaction.transaction_type
        },
        user_id=current_user,
        request=request
    )
    
    return transaction_record


@router.get("", response_model=List[LedgerTransactionResponse])
def list_transactions(
    account_id: Optional[UUID] = Query(None, description="Filter by account ID"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    List ledger transactions with optional filtering.
    Requires authentication.
    """
    query = db.query(LedgerTransaction)
    
    if account_id:
        query = query.filter(LedgerTransaction.account_id == account_id)
    
    if transaction_type:
        query = query.filter(LedgerTransaction.transaction_type == transaction_type)
    
    transactions = query.order_by(
        LedgerTransaction.transaction_date.desc()
    ).offset(skip).limit(limit).all()
    
    return transactions


@router.get("/{transaction_id}", response_model=LedgerTransactionResponse)
def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get a specific transaction by ID.
    Requires authentication.
    """
    transaction = db.query(LedgerTransaction).filter(
        LedgerTransaction.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction


@router.get("/account/{account_id}", response_model=List[LedgerTransactionResponse])
def get_account_transactions(
    account_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get all transactions for a specific account.
    Requires authentication.
    """
    # Verify account exists
    account_record = db.query(LogicalAccount).filter(
        LogicalAccount.id == account_id
    ).first()
    
    if not account_record:
        raise HTTPException(status_code=404, detail="Account not found")
    
    transactions = db.query(LedgerTransaction).filter(
        LedgerTransaction.account_id == account_id
    ).order_by(
        LedgerTransaction.transaction_date.desc()
    ).offset(skip).limit(limit).all()
    
    return transactions
