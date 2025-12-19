"""Transaction management routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from db.session import get_db
from models.models import LedgerTransaction, LogicalAccount
from schemas.schemas import (
    TransactionCreate, 
    TransactionResponse, 
    DoubleEntryTransactionCreate
)
from deps.auth import get_current_user, get_optional_user
from hooks.audit import AuditHook
from services.allocation import AllocationService

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new ledger transaction.
    
    If status equals COMPLETED (case-insensitive), triggers allocation engine.
    Requires authentication.
    """
    # Verify account exists
    account = db.query(LogicalAccount).filter(
        LogicalAccount.account_id == transaction.account_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found: {transaction.account_id}"
        )
    
    try:
        # Create transaction
        db_transaction = LedgerTransaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
            account_id=transaction.account_id,
            transaction_type=transaction.transaction_type,
            amount=transaction.amount,
            currency=transaction.currency,
            description=transaction.description,
            reference_id=transaction.reference_id,
            metadata=transaction.metadata,
            created_by=current_user,
            source_system="api"
        )
        
        db.add(db_transaction)
        db.flush()  # Flush to get transaction ID but don't commit yet
        
        # If status is COMPLETED, trigger allocation engine within same transaction
        if transaction.status and transaction.status.upper() == "COMPLETED":
            allocation_service = AllocationService(db)
            try:
                allocation_service.execute_allocation(
                    amount=transaction.amount,
                    source_account_id=transaction.account_id,
                    description=f"Auto-allocation for transaction {db_transaction.transaction_id}",
                    created_by=current_user
                )
            except ValueError as e:
                # Rollback if allocation fails
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Allocation failed: {str(e)}"
                )
        
        # Commit transaction (includes allocation if triggered)
        db.commit()
        db.refresh(db_transaction)
        
        # Log to audit
        AuditHook.log_transaction_create(
            db=db,
            transaction_id=db_transaction.transaction_id,
            transaction_data={
                "account_id": transaction.account_id,
                "type": transaction.transaction_type,
                "amount": str(transaction.amount),
                "currency": transaction.currency,
                "status": transaction.status
            },
            created_by=current_user
        )
        
        return db_transaction
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction creation failed: {str(e)}"
        )


@router.post("/double-entry", response_model=List[TransactionResponse], status_code=status.HTTP_201_CREATED)
async def create_double_entry_transaction(
    transaction: DoubleEntryTransactionCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a double-entry transaction (debit and credit).
    
    This is the preferred method for creating balanced ledger entries.
    Requires authentication.
    """
    # Verify both accounts exist
    debit_account = db.query(LogicalAccount).filter(
        LogicalAccount.account_id == transaction.debit_account_id
    ).first()
    credit_account = db.query(LogicalAccount).filter(
        LogicalAccount.account_id == transaction.credit_account_id
    ).first()
    
    if not debit_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debit account not found: {transaction.debit_account_id}"
        )
    if not credit_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit account not found: {transaction.credit_account_id}"
        )
    
    # Generate batch ID for this transaction pair
    batch_id = f"BATCH-{uuid.uuid4().hex[:12].upper()}"
    
    # Create debit transaction
    debit_txn = LedgerTransaction(
        transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
        account_id=transaction.debit_account_id,
        transaction_type="DEBIT",
        amount=transaction.amount,
        currency=transaction.currency,
        description=transaction.description,
        reference_id=transaction.reference_id,
        batch_id=batch_id,
        metadata=transaction.metadata,
        created_by=current_user,
        source_system="api"
    )
    
    # Create credit transaction
    credit_txn = LedgerTransaction(
        transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
        account_id=transaction.credit_account_id,
        transaction_type="CREDIT",
        amount=transaction.amount,
        currency=transaction.currency,
        description=transaction.description,
        reference_id=transaction.reference_id,
        batch_id=batch_id,
        metadata=transaction.metadata,
        created_by=current_user,
        source_system="api"
    )
    
    db.add(debit_txn)
    db.add(credit_txn)
    db.commit()
    db.refresh(debit_txn)
    db.refresh(credit_txn)
    
    # Log to audit
    AuditHook.log_change(
        db=db,
        entity_type="transaction",
        entity_id=batch_id,
        action="CREATE_DOUBLE_ENTRY",
        new_value={
            "debit_account": transaction.debit_account_id,
            "credit_account": transaction.credit_account_id,
            "amount": str(transaction.amount),
            "currency": transaction.currency
        },
        changed_by=current_user
    )
    
    return [debit_txn, credit_txn]


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    account_id: Optional[str] = None,
    batch_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    List ledger transactions with optional filtering.
    
    Authentication is optional for read operations.
    """
    query = db.query(LedgerTransaction)
    
    if account_id:
        query = query.filter(LedgerTransaction.account_id == account_id)
    if batch_id:
        query = query.filter(LedgerTransaction.batch_id == batch_id)
    
    query = query.order_by(LedgerTransaction.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    return query.all()


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Get details of a specific transaction.
    
    Authentication is optional for read operations.
    """
    transaction = db.query(LedgerTransaction).filter(
        LedgerTransaction.transaction_id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction not found: {transaction_id}"
        )
    
    return transaction
