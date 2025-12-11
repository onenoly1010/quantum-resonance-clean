"""Transaction routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..db import get_db
from ..models.models import Transaction, TransactionLine
from ..schemas.schemas import (
    TransactionCreate, TransactionUpdate, TransactionResponse,
    MessageResponse
)
from ..deps import get_current_user
from ..hooks import get_audit_hook


router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    request: Request,
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new transaction with lines.
    
    The transaction must be balanced (total debits = total credits).
    """
    # Generate transaction number
    from datetime import date
    today = date.today()
    count = db.query(Transaction).filter(
        Transaction.transaction_date == today
    ).count()
    
    transaction_number = f"TXN-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    
    # Create transaction
    transaction = Transaction(
        transaction_number=transaction_number,
        transaction_date=transaction_data.transaction_date,
        description=transaction_data.description,
        reference_number=transaction_data.reference_number,
        status="PENDING",
        created_by=current_user.get("user_id"),
        metadata=transaction_data.metadata
    )
    
    db.add(transaction)
    db.flush()
    
    # Create transaction lines
    for line_data in transaction_data.lines:
        line = TransactionLine(
            transaction_id=transaction.id,
            account_id=line_data.account_id,
            line_type=line_data.line_type,
            amount=line_data.amount,
            currency=line_data.currency,
            description=line_data.description,
            metadata=line_data.metadata
        )
        db.add(line)
    
    db.commit()
    db.refresh(transaction)
    
    # Audit log
    audit = get_audit_hook(db, request)
    audit.log_create(
        table_name="transactions",
        record_id=transaction.id,
        user_id=current_user.get("user_id"),
        data={"transaction_number": transaction_number}
    )
    
    return transaction


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific transaction by ID."""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    return transaction


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List transactions with optional filtering."""
    query = db.query(Transaction)
    
    if status_filter:
        query = query.filter(Transaction.status == status_filter)
    
    transactions = query.order_by(
        Transaction.transaction_date.desc(),
        Transaction.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return transactions


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    request: Request,
    transaction_id: UUID,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a transaction."""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    # Can't update posted transactions
    if transaction.status == "POSTED" and transaction_data.status != "VOID":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update posted transaction"
        )
    
    # Store old data for audit
    old_data = {
        "description": transaction.description,
        "status": transaction.status
    }
    
    # Update fields
    if transaction_data.description is not None:
        transaction.description = transaction_data.description
    if transaction_data.status is not None:
        transaction.status = transaction_data.status
        if transaction_data.status == "POSTED":
            transaction.posted_at = datetime.now()
    if transaction_data.metadata is not None:
        transaction.metadata = transaction_data.metadata
    
    db.commit()
    db.refresh(transaction)
    
    # Audit log
    audit = get_audit_hook(db, request)
    audit.log_update(
        table_name="transactions",
        record_id=transaction.id,
        user_id=current_user.get("user_id"),
        old_data=old_data,
        new_data={
            "description": transaction.description,
            "status": transaction.status
        }
    )
    
    return transaction


@router.post("/{transaction_id}/post", response_model=TransactionResponse)
async def post_transaction(
    request: Request,
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Post a transaction (make it permanent)."""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    if transaction.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only post pending transactions, current status: {transaction.status}"
        )
    
    transaction.status = "POSTED"
    transaction.posted_at = datetime.now()
    
    db.commit()
    db.refresh(transaction)
    
    # Audit log
    audit = get_audit_hook(db, request)
    audit.log_update(
        table_name="transactions",
        record_id=transaction.id,
        user_id=current_user.get("user_id"),
        old_data={"status": "PENDING"},
        new_data={"status": "POSTED"}
    )
    
    return transaction


@router.delete("/{transaction_id}", response_model=MessageResponse)
async def delete_transaction(
    request: Request,
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a transaction (only if not posted)."""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    if transaction.status == "POSTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete posted transaction. Void it instead."
        )
    
    # Audit log before deletion
    audit = get_audit_hook(db, request)
    audit.log_delete(
        table_name="transactions",
        record_id=transaction.id,
        user_id=current_user.get("user_id"),
        data={"transaction_number": transaction.transaction_number}
    )
    
    db.delete(transaction)
    db.commit()
    
    return MessageResponse(
        message=f"Transaction {transaction_id} deleted successfully"
    )
