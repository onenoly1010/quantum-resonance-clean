"""
Reconciliation service
Handles reconciliation of account balances
"""
from typing import List, Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from models.models import ReconciliationLog, LogicalAccount, LedgerTransaction
from schemas.schemas import ReconciliationLogCreate
import logging

logger = logging.getLogger(__name__)


class ReconciliationService:
    """Service for managing account reconciliation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_account_balance(self, account_id: UUID) -> Decimal:
        """
        Calculate current balance for an account
        
        Args:
            account_id: Account UUID
            
        Returns:
            Current balance as Decimal
        """
        # Sum debits
        total_debits = (
            self.db.query(func.coalesce(func.sum(LedgerTransaction.amount), 0))
            .filter(
                LedgerTransaction.debit_account_id == account_id,
                LedgerTransaction.status == "posted"
            )
            .scalar()
        ) or Decimal("0")
        
        # Sum credits
        total_credits = (
            self.db.query(func.coalesce(func.sum(LedgerTransaction.amount), 0))
            .filter(
                LedgerTransaction.credit_account_id == account_id,
                LedgerTransaction.status == "posted"
            )
            .scalar()
        ) or Decimal("0")
        
        # Balance = Debits - Credits (for asset and expense accounts)
        # For liability, equity, revenue: Credits - Debits
        balance = Decimal(str(total_debits)) - Decimal(str(total_credits))
        
        return balance
    
    def reconcile_account(
        self,
        account_id: UUID,
        expected_balance: Decimal,
        reconciliation_type: str = "manual",
        reconciled_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ReconciliationLog:
        """
        Perform reconciliation for an account
        
        Args:
            account_id: Account UUID to reconcile
            expected_balance: Expected balance from external source
            reconciliation_type: Type of reconciliation
            reconciled_by: User performing reconciliation
            notes: Optional notes
            
        Returns:
            Created reconciliation log entry
        """
        # Get actual balance
        actual_balance = self.get_account_balance(account_id)
        
        # Determine status
        difference = abs(actual_balance - expected_balance)
        tolerance = Decimal("0.01")  # 1 cent tolerance
        
        if difference <= tolerance:
            status = "matched"
        else:
            status = "unmatched"
        
        # Create reconciliation log
        recon_log = ReconciliationLog(
            account_id=account_id,
            reconciliation_type=reconciliation_type,
            expected_balance=expected_balance,
            actual_balance=actual_balance,
            status=status,
            notes=notes,
            reconciled_by=reconciled_by,
            metadata={
                "difference": str(difference),
                "tolerance": str(tolerance)
            }
        )
        
        self.db.add(recon_log)
        self.db.commit()
        self.db.refresh(recon_log)
        
        logger.info(
            f"Reconciliation completed for account {account_id}: "
            f"Expected={expected_balance}, Actual={actual_balance}, Status={status}"
        )
        
        return recon_log
    
    def get_reconciliation_history(
        self,
        account_id: UUID,
        limit: int = 100
    ) -> List[ReconciliationLog]:
        """
        Get reconciliation history for an account
        
        Args:
            account_id: Account UUID
            limit: Maximum number of records to return
            
        Returns:
            List of reconciliation log entries
        """
        return (
            self.db.query(ReconciliationLog)
            .filter(ReconciliationLog.account_id == account_id)
            .order_by(ReconciliationLog.reconciliation_date.desc())
            .limit(limit)
            .all()
        )
    
    def get_unmatched_reconciliations(self) -> List[ReconciliationLog]:
        """
        Get all unmatched reconciliations
        
        Returns:
            List of unmatched reconciliation log entries
        """
        return (
            self.db.query(ReconciliationLog)
            .filter(ReconciliationLog.status == "unmatched")
            .order_by(ReconciliationLog.reconciliation_date.desc())
            .all()
        )
    
    def mark_as_reviewed(
        self,
        reconciliation_id: UUID,
        reviewed_by: str,
        notes: Optional[str] = None
    ) -> ReconciliationLog:
        """
        Mark a reconciliation as reviewed
        
        Args:
            reconciliation_id: Reconciliation log UUID
            reviewed_by: User reviewing the reconciliation
            notes: Optional review notes
            
        Returns:
            Updated reconciliation log entry
        """
        recon_log = (
            self.db.query(ReconciliationLog)
            .filter(ReconciliationLog.id == reconciliation_id)
            .first()
        )
        
        if not recon_log:
            raise ValueError(f"Reconciliation {reconciliation_id} not found")
        
        recon_log.status = "reviewed"
        recon_log.reconciled_by = reviewed_by
        
        if notes:
            existing_notes = recon_log.notes or ""
            recon_log.notes = f"{existing_notes}\n[Reviewed] {notes}" if existing_notes else f"[Reviewed] {notes}"
        
        self.db.commit()
        self.db.refresh(recon_log)
        
        logger.info(f"Reconciliation {reconciliation_id} marked as reviewed by {reviewed_by}")
        
        return recon_log
    
    def get_all_account_balances(self) -> List[dict]:
        """
        Get balances for all active accounts
        
        Returns:
            List of dictionaries with account balance information
        """
        accounts = (
            self.db.query(LogicalAccount)
            .filter(LogicalAccount.status == "active")
            .all()
        )
        
        balances = []
        for account in accounts:
            balance = self.get_account_balance(account.id)
            balances.append({
                "account_id": account.id,
                "account_code": account.account_code,
                "account_name": account.account_name,
                "account_type": account.account_type,
                "balance": balance,
                "currency": account.currency
            })
        
        return balances
