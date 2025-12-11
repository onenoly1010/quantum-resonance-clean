from decimal import Decimal, ROUND_DOWN
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.models.models import LedgerTransaction, AllocationRule, LogicalAccount
from typing import List
import uuid


async def apply_allocation_rules(session: AsyncSession, parent_tx: LedgerTransaction) -> List[LedgerTransaction]:
    """
    Apply allocation rules to a completed transaction.
    
    Args:
        session: Database session
        parent_tx: The parent transaction to allocate from
        
    Returns:
        List of created allocation transactions
        
    Raises:
        ValueError: If no active rule found or percentages don't sum to 100
    """
    # Load the first active allocation rule
    result = await session.execute(
        select(AllocationRule).where(AllocationRule.active == True).limit(1)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise ValueError("No active allocation rule found")
    
    # Extract allocation items from rule_data
    allocations = rule.rule_data.get("allocations", [])
    
    if not allocations:
        raise ValueError("Allocation rule has no allocations defined")
    
    # Validate total percentage equals 100
    total_percent = sum(Decimal(str(item["percent"])) for item in allocations)
    if total_percent != 100:
        raise ValueError(f"Total allocation percentage must equal 100, got {total_percent}")
    
    # Compute allocations with proper rounding
    parent_amount = Decimal(str(parent_tx.amount))
    allocated_transactions = []
    total_allocated = Decimal("0")
    
    # Create allocation transactions for all except the last
    for i, allocation_item in enumerate(allocations[:-1]):
        percent = Decimal(str(allocation_item["percent"]))
        amount = (parent_amount * percent / 100).quantize(Decimal("0.000000000001"), rounding=ROUND_DOWN)
        total_allocated += amount
        
        # Create allocation transaction
        allocation_tx = LedgerTransaction(
            transaction_type="ALLOCATION",
            amount=amount,
            currency=parent_tx.currency,
            status="COMPLETED",
            logical_account_id=uuid.UUID(allocation_item["logical_account_id"]),
            parent_transaction_id=parent_tx.id,
            metadata={"allocation_rule_id": str(rule.id), "percent": str(percent)}
        )
        session.add(allocation_tx)
        allocated_transactions.append(allocation_tx)
        
        # Update logical account balance
        await session.execute(
            update(LogicalAccount)
            .where(LogicalAccount.id == uuid.UUID(allocation_item["logical_account_id"]))
            .values(balance=LogicalAccount.balance + amount)
        )
    
    # Last allocation gets the remaining difference to handle rounding
    last_allocation = allocations[-1]
    last_amount = parent_amount - total_allocated
    last_percent = Decimal(str(last_allocation["percent"]))
    
    allocation_tx = LedgerTransaction(
        transaction_type="ALLOCATION",
        amount=last_amount,
        currency=parent_tx.currency,
        status="COMPLETED",
        logical_account_id=uuid.UUID(last_allocation["logical_account_id"]),
        parent_transaction_id=parent_tx.id,
        metadata={"allocation_rule_id": str(rule.id), "percent": str(last_percent)}
    )
    session.add(allocation_tx)
    allocated_transactions.append(allocation_tx)
    
    # Update logical account balance for last allocation
    await session.execute(
        update(LogicalAccount)
        .where(LogicalAccount.id == uuid.UUID(last_allocation["logical_account_id"]))
        .values(balance=LogicalAccount.balance + last_amount)
    )
    
    await session.flush()
    
    return allocated_transactions
