"""
Transaction API Routes

Endpoints for creating and managing ledger transactions
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import uuid

from ..db.session import get_db
from ..models.ledger_transaction import LedgerTransaction
from ..models.logical_account import LogicalAccount
from ..schemas.ledger_transaction import (
    LedgerTransactionCreate,
    LedgerTransactionResponse,
    LedgerTransactionUpdate,
)
from ..services.allocation import AllocationEngine, AllocationEngineError
from ..deps.auth import get_current_user, TokenPayload, get_current_user_optional
from ..hooks.audit import get_audit_logger, AuditLogger, AuditAction


router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.post("", response_model=LedgerTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: LedgerTransactionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """
    Create a new ledger transaction
    
    When status is COMPLETED, automatically runs allocation rules
    and creates allocation transactions atomically.
    
    Requires authentication.
    """
    # Verify account exists if specified
    if transaction_data.logical_account_id:
        account_query = select(LogicalAccount).where(
            LogicalAccount.id == transaction_data.logical_account_id
        )
        account_result = await db.execute(account_query)
        account = account_result.scalar_one_or_none()
        
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Logical account {transaction_data.logical_account_id} not found"
            )
    
    # Create transaction
    transaction = LedgerTransaction(
        **transaction_data.model_dump(),
        status="PENDING",  # Always start as pending
    )
    
    db.add(transaction)
    await db.flush()
    
    # Log audit entry
    await audit.log_from_request(
        action=AuditAction.CREATE_TRANSACTION,
        request=request,
        user=user,
        target_id=transaction.id,
        target_type="ledger_transaction",
        details={
            "type": transaction.type,
            "amount": str(transaction.amount),
            "currency": transaction.currency,
        }
    )
    
    # If transaction should be completed, update status and run allocations
    if transaction_data.metadata.get("auto_complete", False):
        transaction.status = "COMPLETED"
        
        # Update account balance if account specified
        if transaction.logical_account_id:
            account.balance += transaction.amount
        
        # Run allocation rules for completed transactions
        try:
            allocation_engine = AllocationEngine(db)
            allocations = await allocation_engine.apply_allocation_to_transaction(transaction)
            
            # Log allocation creation
            await audit.log_from_request(
                action="CREATE_ALLOCATIONS",
                request=request,
                user=user,
                target_id=transaction.id,
                target_type="ledger_transaction",
                details={
                    "parent_transaction_id": str(transaction.id),
                    "allocation_count": len(allocations),
                }
            )
        except AllocationEngineError as e:
            # If allocation fails, rollback by not committing
            # Could also mark transaction as FAILED
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Allocation failed: {str(e)}"
            )
    
    await db.commit()
    await db.refresh(transaction)
    
    return transaction


@router.get("", response_model=List[LedgerTransactionResponse])
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
    account_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: Optional[TokenPayload] = Depends(get_current_user_optional),
):
    """
    List and filter ledger transactions
    
    Optional authentication - returns more details if authenticated.
    
    Query parameters:
    - skip: Pagination offset (default: 0)
    - limit: Number of results (default: 100, max: 1000)
    - status_filter: Filter by status (PENDING, COMPLETED, FAILED, CANCELLED)
    - type_filter: Filter by type (DEPOSIT, WITHDRAWAL, TRANSFER, ALLOCATION, CORRECTION)
    - account_id: Filter by logical account ID
    """
    # Build query
    query = select(LedgerTransaction).order_by(LedgerTransaction.created_at.desc())
    
    # Apply filters
    filters = []
    if status_filter:
        filters.append(LedgerTransaction.status == status_filter)
    if type_filter:
        filters.append(LedgerTransaction.type == type_filter)
    if account_id:
        filters.append(LedgerTransaction.logical_account_id == account_id)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Apply pagination
    query = query.offset(skip).limit(min(limit, 1000))
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return list(transactions)


@router.get("/{transaction_id}", response_model=LedgerTransactionResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: Optional[TokenPayload] = Depends(get_current_user_optional),
):
    """
    Get a specific transaction by ID
    
    Optional authentication.
    """
    query = select(LedgerTransaction).where(LedgerTransaction.id == transaction_id)
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    return transaction


@router.patch("/{transaction_id}", response_model=LedgerTransactionResponse)
async def update_transaction(
    transaction_id: uuid.UUID,
    update_data: LedgerTransactionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """
    Update a transaction
    
    Requires authentication.
    """
    query = select(LedgerTransaction).where(LedgerTransaction.id == transaction_id)
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(transaction, field, value)
    
    await db.commit()
    await db.refresh(transaction)
    
    # Log audit entry
    await audit.log_from_request(
        action=AuditAction.UPDATE_TRANSACTION,
        request=request,
        user=user,
        target_id=transaction.id,
        target_type="ledger_transaction",
        details=update_dict
    )
    
    return transaction
