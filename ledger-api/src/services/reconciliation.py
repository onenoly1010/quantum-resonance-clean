"""Reconciliation service for account reconciliation."""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.models import (
    Account, Transaction, TransactionLine, Reconciliation
)
from ..config import settings


class ReconciliationService:
    """Service for handling account reconciliation."""
    
    def __init__(self, db: Session):
        """Initialize reconciliation service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def calculate_ledger_balance(
        self,
        account_id: UUID,
        as_of_date: Optional[date] = None
    ) -> Decimal:
        """
        Calculate the ledger balance for an account.
        
        Args:
            account_id: Account ID
            as_of_date: Calculate balance as of this date (None for current)
        
        Returns:
            Current ledger balance
        """
        # Get account to determine type
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Build query for transaction lines
        query = self.db.query(
            func.sum(
                func.case(
                    (TransactionLine.line_type == "DEBIT", TransactionLine.amount),
                    else_=-TransactionLine.amount
                )
            )
        ).join(Transaction).filter(
            TransactionLine.account_id == account_id,
            Transaction.status == "POSTED"
        )
        
        # Filter by date if provided
        if as_of_date:
            query = query.filter(Transaction.transaction_date <= as_of_date)
        
        net_balance = query.scalar() or Decimal("0")
        
        # Adjust sign based on account type
        # For ASSET and EXPENSE accounts, positive balance = debit balance
        # For LIABILITY, EQUITY, and REVENUE accounts, positive balance = credit balance
        if account.account_type in ("LIABILITY", "EQUITY", "REVENUE"):
            net_balance = -net_balance
        
        return net_balance
    
    def create_reconciliation(
        self,
        account_id: UUID,
        reconciliation_date: date,
        statement_balance: Decimal,
        notes: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Reconciliation:
        """
        Create a new reconciliation record.
        
        Args:
            account_id: Account to reconcile
            reconciliation_date: Date of reconciliation
            statement_balance: Balance from bank/external statement
            notes: Optional notes
            user_id: User performing reconciliation
        
        Returns:
            Created reconciliation record
        """
        # Calculate ledger balance
        ledger_balance = self.calculate_ledger_balance(account_id, reconciliation_date)
        
        # Create reconciliation
        reconciliation = Reconciliation(
            account_id=account_id,
            reconciliation_date=reconciliation_date,
            statement_balance=statement_balance,
            ledger_balance=ledger_balance,
            status="PENDING",
            notes=notes,
            metadata={"created_by_user": user_id}
        )
        
        self.db.add(reconciliation)
        self.db.commit()
        self.db.refresh(reconciliation)
        
        # Auto-reconcile if within threshold
        if settings.AUTO_RECONCILE:
            difference = abs(statement_balance - ledger_balance)
            if difference <= Decimal(str(settings.RECONCILIATION_THRESHOLD)):
                self.complete_reconciliation(reconciliation.id, user_id)
        
        return reconciliation
    
    def complete_reconciliation(
        self,
        reconciliation_id: UUID,
        user_id: Optional[str] = None
    ) -> Reconciliation:
        """
        Mark a reconciliation as completed.
        
        Args:
            reconciliation_id: Reconciliation ID
            user_id: User completing reconciliation
        
        Returns:
            Updated reconciliation record
        """
        from datetime import datetime
        
        reconciliation = self.db.query(Reconciliation).filter(
            Reconciliation.id == reconciliation_id
        ).first()
        
        if not reconciliation:
            raise ValueError(f"Reconciliation {reconciliation_id} not found")
        
        reconciliation.status = "COMPLETED"
        reconciliation.reconciled_by = user_id
        reconciliation.reconciled_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(reconciliation)
        
        return reconciliation
    
    def get_unreconciled_transactions(
        self,
        account_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Transaction]:
        """
        Get unreconciled transactions for an account.
        
        Args:
            account_id: Account ID
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            List of unreconciled transactions
        """
        query = self.db.query(Transaction).join(TransactionLine).filter(
            TransactionLine.account_id == account_id,
            Transaction.status.in_(["POSTED"]),
            ~Transaction.status.in_(["RECONCILED"])
        )
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        return query.distinct().all()
    
    def mark_transactions_reconciled(
        self,
        transaction_ids: List[UUID]
    ) -> int:
        """
        Mark transactions as reconciled.
        
        Args:
            transaction_ids: List of transaction IDs to mark
        
        Returns:
            Number of transactions updated
        """
        count = self.db.query(Transaction).filter(
            Transaction.id.in_(transaction_ids)
        ).update(
            {"status": "RECONCILED"},
            synchronize_session=False
        )
        
        self.db.commit()
        return count
    
    def get_reconciliation_summary(
        self,
        account_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get reconciliation summary for an account.
        
        Args:
            account_id: Account ID
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            Summary dictionary with reconciliation statistics
        """
        # Get account
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Get current balance
        current_balance = self.calculate_ledger_balance(account_id)
        
        # Get unreconciled transactions
        unreconciled = self.get_unreconciled_transactions(
            account_id, start_date, end_date
        )
        
        # Get recent reconciliations
        rec_query = self.db.query(Reconciliation).filter(
            Reconciliation.account_id == account_id
        )
        if start_date:
            rec_query = rec_query.filter(Reconciliation.reconciliation_date >= start_date)
        if end_date:
            rec_query = rec_query.filter(Reconciliation.reconciliation_date <= end_date)
        
        reconciliations = rec_query.order_by(
            Reconciliation.reconciliation_date.desc()
        ).limit(10).all()
        
        # Calculate unreconciled amount
        unreconciled_amount = Decimal("0")
        for txn in unreconciled:
            for line in txn.lines:
                if line.account_id == account_id:
                    if line.line_type == "DEBIT":
                        unreconciled_amount += line.amount
                    else:
                        unreconciled_amount -= line.amount
        
        return {
            "account_id": account_id,
            "account_code": account.account_code,
            "account_name": account.account_name,
            "current_balance": float(current_balance),
            "unreconciled_transaction_count": len(unreconciled),
            "unreconciled_amount": float(unreconciled_amount),
            "recent_reconciliations": [
                {
                    "id": str(rec.id),
                    "date": rec.reconciliation_date.isoformat(),
                    "statement_balance": float(rec.statement_balance),
                    "ledger_balance": float(rec.ledger_balance),
                    "difference": float(rec.statement_balance - rec.ledger_balance),
                    "status": rec.status
                }
                for rec in reconciliations
            ]
        }
