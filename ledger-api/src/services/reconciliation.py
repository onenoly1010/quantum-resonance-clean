from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.models import LogicalAccount, ReconciliationLog
import uuid


async def reconcile_account(
    session: AsyncSession,
    logical_account_id: uuid.UUID,
    external_balance: Decimal
) -> ReconciliationLog:
    """
    Reconcile a logical account with an external balance.
    
    Args:
        session: Database session
        logical_account_id: ID of the logical account
        external_balance: The external balance to reconcile against
        
    Returns:
        ReconciliationLog entry
        
    Raises:
        ValueError: If account not found
    """
    # Fetch the logical account
    result = await session.execute(
        select(LogicalAccount).where(LogicalAccount.id == logical_account_id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise ValueError(f"Logical account {logical_account_id} not found")
    
    # Compute discrepancy
    ledger_balance = Decimal(str(account.balance))
    external_balance = Decimal(str(external_balance))
    discrepancy = ledger_balance - external_balance
    
    # Create reconciliation log entry
    reconciliation = ReconciliationLog(
        logical_account_id=logical_account_id,
        ledger_balance=ledger_balance,
        external_balance=external_balance,
        discrepancy=discrepancy
    )
    
    session.add(reconciliation)
    await session.flush()
    
    return reconciliation
