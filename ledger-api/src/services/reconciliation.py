"""
Reconciliation Service

Handles comparing internal ledger balances with external sources
and creating reconciliation records.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from decimal import Decimal
import uuid
from datetime import datetime

from ..models.reconciliation_log import ReconciliationLog
from ..models.logical_account import LogicalAccount
from ..models.ledger_transaction import LedgerTransaction


class ReconciliationError(Exception):
    """Base exception for reconciliation errors"""
    pass


class AccountNotFoundError(ReconciliationError):
    """Raised when account is not found"""
    pass


class ReconciliationService:
    """
    Reconciliation Service - Compares external and internal balances
    
    Features:
    - Fetches current internal balance from ledger
    - Compares with external balance (blockchain, bank, etc)
    - Logs discrepancies
    - Optionally creates correction transactions
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_account_balance(self, account_id: uuid.UUID) -> Decimal:
        """
        Get current balance for an account
        
        Args:
            account_id: Account UUID
            
        Returns:
            Current balance
            
        Raises:
            AccountNotFoundError: If account doesn't exist
        """
        query = select(LogicalAccount).where(LogicalAccount.id == account_id)
        result = await self.db.execute(query)
        account = result.scalar_one_or_none()
        
        if account is None:
            raise AccountNotFoundError(f"Account {account_id} not found")
        
        return account.balance

    async def create_reconciliation_log(
        self,
        account_id: uuid.UUID,
        external_balance: Decimal,
        currency: str = "USD"
    ) -> ReconciliationLog:
        """
        Create a reconciliation log entry
        
        Args:
            account_id: Account to reconcile
            external_balance: Balance from external source
            currency: Currency code
            
        Returns:
            Created ReconciliationLog
            
        Raises:
            AccountNotFoundError: If account doesn't exist
        """
        # Get current internal balance
        internal_balance = await self.get_account_balance(account_id)
        
        # Calculate discrepancy (external - internal)
        discrepancy = external_balance - internal_balance
        
        # Create reconciliation log
        reconciliation = ReconciliationLog(
            logical_account_id=account_id,
            external_balance=external_balance,
            internal_balance=internal_balance,
            discrepancy=discrepancy,
            currency=currency,
            resolved=abs(discrepancy) < Decimal("0.000001"),  # Auto-resolve if negligible
        )
        
        self.db.add(reconciliation)
        await self.db.flush()
        
        return reconciliation

    async def create_correction_transaction(
        self,
        reconciliation: ReconciliationLog,
        approved_by: str,
        notes: Optional[str] = None
    ) -> LedgerTransaction:
        """
        Create a correction transaction to resolve a discrepancy
        
        Args:
            reconciliation: ReconciliationLog to correct
            approved_by: User approving the correction
            notes: Optional notes about the correction
            
        Returns:
            Created correction transaction
            
        Raises:
            ReconciliationError: If reconciliation is already resolved or has no discrepancy
        """
        if reconciliation.resolved:
            raise ReconciliationError(
                f"Reconciliation {reconciliation.id} is already resolved"
            )
        
        if abs(reconciliation.discrepancy) < Decimal("0.000001"):
            raise ReconciliationError(
                "Reconciliation has no significant discrepancy to correct"
            )
        
        # Create correction transaction
        correction = LedgerTransaction(
            type="CORRECTION",
            amount=abs(reconciliation.discrepancy),
            currency=reconciliation.currency,
            status="COMPLETED",
            logical_account_id=reconciliation.logical_account_id,
            description=f"Reconciliation correction - {notes or 'Balance adjustment'}",
            metadata={
                "reconciliation_id": str(reconciliation.id),
                "approved_by": approved_by,
                "external_balance": str(reconciliation.external_balance),
                "internal_balance": str(reconciliation.internal_balance),
                "discrepancy": str(reconciliation.discrepancy),
            }
        )
        
        self.db.add(correction)
        await self.db.flush()
        
        # Update account balance based on discrepancy direction
        account_query = select(LogicalAccount).where(
            LogicalAccount.id == reconciliation.logical_account_id
        )
        account_result = await self.db.execute(account_query)
        account = account_result.scalar_one()
        
        # If discrepancy is positive, external > internal, so add to internal
        # If discrepancy is negative, external < internal, so subtract from internal
        account.balance += reconciliation.discrepancy
        
        # Mark reconciliation as resolved
        reconciliation.resolved = True
        reconciliation.resolved_at = datetime.utcnow()
        reconciliation.resolved_by = approved_by
        reconciliation.resolution_notes = notes
        reconciliation.correction_transaction_id = correction.id
        
        return correction

    async def get_unresolved_reconciliations(
        self,
        account_id: Optional[uuid.UUID] = None,
        limit: int = 100
    ) -> list[ReconciliationLog]:
        """
        Get unresolved reconciliation logs
        
        Args:
            account_id: Optional account filter
            limit: Maximum number of records to return
            
        Returns:
            List of unresolved ReconciliationLog entries
        """
        query = select(ReconciliationLog).where(
            ReconciliationLog.resolved == False
        ).order_by(ReconciliationLog.created_at.desc()).limit(limit)
        
        if account_id:
            query = query.where(ReconciliationLog.logical_account_id == account_id)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def resolve_reconciliation_manually(
        self,
        reconciliation_id: uuid.UUID,
        resolved_by: str,
        notes: str
    ) -> ReconciliationLog:
        """
        Manually mark a reconciliation as resolved without creating correction transaction
        
        Args:
            reconciliation_id: Reconciliation to resolve
            resolved_by: User resolving the reconciliation
            notes: Notes explaining the resolution
            
        Returns:
            Updated ReconciliationLog
            
        Raises:
            ReconciliationError: If reconciliation not found or already resolved
        """
        query = select(ReconciliationLog).where(ReconciliationLog.id == reconciliation_id)
        result = await self.db.execute(query)
        reconciliation = result.scalar_one_or_none()
        
        if reconciliation is None:
            raise ReconciliationError(f"Reconciliation {reconciliation_id} not found")
        
        if reconciliation.resolved:
            raise ReconciliationError(f"Reconciliation {reconciliation_id} is already resolved")
        
        reconciliation.resolved = True
        reconciliation.resolved_at = datetime.utcnow()
        reconciliation.resolved_by = resolved_by
        reconciliation.resolution_notes = notes
        
        await self.db.flush()
        
        return reconciliation
