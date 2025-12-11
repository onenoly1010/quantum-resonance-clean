from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.session import get_db
from src.schemas.schemas import TransactionCreate, TransactionRead
from src.models.models import LedgerTransaction
from src.services.allocation import apply_allocation_rules
from src.hooks.audit import write_audit
from typing import List

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionRead, status_code=201)
async def create_transaction(
    transaction: TransactionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new transaction. If status is COMPLETED, allocation rules are applied.
    
    Args:
        transaction: Transaction data
        db: Database session
        
    Returns:
        Created transaction
    """
    # Create transaction
    tx = LedgerTransaction(
        transaction_type=transaction.transaction_type,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        logical_account_id=transaction.logical_account_id,
        parent_transaction_id=transaction.parent_transaction_id,
        metadata=transaction.metadata
    )
    
    db.add(tx)
    await db.flush()
    
    # Apply allocation rules if transaction is completed
    if transaction.status.upper() == "COMPLETED":
        try:
            await apply_allocation_rules(db, tx)
        except ValueError as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    # Write audit log
    await write_audit(
        db,
        action="CREATE_TRANSACTION",
        actor="system",
        target_id=tx.id,
        details={"type": transaction.transaction_type, "amount": str(transaction.amount)}
    )
    
    await db.commit()
    await db.refresh(tx)
    
    return tx


@router.get("/", response_model=List[TransactionRead])
async def list_transactions(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List transactions with pagination.
    
    Args:
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session
        
    Returns:
        List of transactions
    """
    result = await db.execute(
        select(LedgerTransaction)
        .order_by(LedgerTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()
    
    return transactions
