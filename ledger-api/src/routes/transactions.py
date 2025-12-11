"""
Transaction routes
Endpoints for managing ledger transactions
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from db.session import get_db
from models.models import LedgerTransaction
from schemas.schemas import (
    LedgerTransactionCreate,
    LedgerTransactionUpdate,
    LedgerTransactionResponse
)
from deps.auth import get_current_user
from hooks.audit import AuditLogger, get_audit_logger
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])


@router.post("/", response_model=LedgerTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: LedgerTransactionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Create a new ledger transaction
    
    Args:
        transaction: Transaction data
        request: FastAPI request
        db: Database session
        current_user: Current authenticated user
        audit_logger: Audit logger instance
        
    Returns:
        Created transaction
    """
    # Set created_by to current user
    transaction_data = transaction.model_dump()
    transaction_data['created_by'] = current_user
    
    # Create transaction
    db_transaction = LedgerTransaction(**transaction_data)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    # Log to audit
    audit_logger.log_create(
        user_id=current_user,
        entity_type="ledger_transaction",
        entity_id=db_transaction.id,
        entity_data=transaction_data,
        request=request
    )
    
    logger.info(f"Transaction created: {db_transaction.transaction_ref}")
    
    return db_transaction


@router.get("/", response_model=List[LedgerTransactionResponse])
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    List ledger transactions with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status_filter: Filter by transaction status
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of transactions
    """
    query = db.query(LedgerTransaction)
    
    if status_filter:
        query = query.filter(LedgerTransaction.status == status_filter)
    
    transactions = query.offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(transactions)} transactions")
    
    return transactions


@router.get("/{transaction_id}", response_model=LedgerTransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get a specific transaction by ID
    
    Args:
        transaction_id: Transaction UUID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Transaction details
        
    Raises:
        HTTPException: If transaction not found
    """
    transaction = db.query(LedgerTransaction).filter(
        LedgerTransaction.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    return transaction


@router.put("/{transaction_id}", response_model=LedgerTransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    transaction_update: LedgerTransactionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Update a transaction
    
    Args:
        transaction_id: Transaction UUID
        transaction_update: Updated transaction data
        request: FastAPI request
        db: Database session
        current_user: Current authenticated user
        audit_logger: Audit logger instance
        
    Returns:
        Updated transaction
        
    Raises:
        HTTPException: If transaction not found
    """
    # Get existing transaction
    db_transaction = db.query(LedgerTransaction).filter(
        LedgerTransaction.id == transaction_id
    ).first()
    
    if not db_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    # Store old data for audit
    old_data = {
        "description": db_transaction.description,
        "status": db_transaction.status,
        "metadata": db_transaction.metadata
    }
    
    # Update fields
    update_data = transaction_update.model_dump(exclude_unset=True)
    update_data['updated_by'] = current_user
    
    for field, value in update_data.items():
        setattr(db_transaction, field, value)
    
    db.commit()
    db.refresh(db_transaction)
    
    # Log to audit
    new_data = {
        "description": db_transaction.description,
        "status": db_transaction.status,
        "metadata": db_transaction.metadata
    }
    
    audit_logger.log_update(
        user_id=current_user,
        entity_type="ledger_transaction",
        entity_id=db_transaction.id,
        old_data=old_data,
        new_data=new_data,
        request=request
    )
    
    logger.info(f"Transaction updated: {db_transaction.transaction_ref}")
    
    return db_transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Delete a transaction (soft delete by setting status to 'cancelled')
    
    Args:
        transaction_id: Transaction UUID
        request: FastAPI request
        db: Database session
        current_user: Current authenticated user
        audit_logger: Audit logger instance
        
    Raises:
        HTTPException: If transaction not found
    """
    db_transaction = db.query(LedgerTransaction).filter(
        LedgerTransaction.id == transaction_id
    ).first()
    
    if not db_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    # Soft delete by setting status to cancelled
    db_transaction.status = 'cancelled'
    db_transaction.updated_by = current_user
    db.commit()
    
    # Log to audit
    audit_logger.log_delete(
        user_id=current_user,
        entity_type="ledger_transaction",
        entity_id=db_transaction.id,
        entity_data={"transaction_ref": db_transaction.transaction_ref},
        request=request
    )
    
    logger.info(f"Transaction deleted: {db_transaction.transaction_ref}")
