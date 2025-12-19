"""Reconciliation service for ledger verification"""

from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone

from models.models import ReconciliationLog, LedgerTransaction, LogicalAccount


class ReconciliationService:
    """Service for reconciling ledger entries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def reconcile_account(
        self,
        account_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> ReconciliationLog:
        """
        Reconcile a specific account for a time period.
        
        Args:
            account_id: Account to reconcile
            start_time: Start of reconciliation period
            end_time: End of reconciliation period
            
        Returns:
            ReconciliationLog with results
        """
        if not end_time:
            end_time = datetime.now(timezone.utc)
        if not start_time:
            # Default to last 30 days
            from datetime import timedelta
            start_time = end_time - timedelta(days=30)
        
        # Verify account exists
        account = self.db.query(LogicalAccount).filter(
            LogicalAccount.account_id == account_id
        ).first()
        
        if not account:
            raise ValueError(f"Account not found: {account_id}")
        
        # Get transactions in the time period
        transactions = self.db.query(LedgerTransaction).filter(
            LedgerTransaction.account_id == account_id,
            LedgerTransaction.created_at >= start_time,
            LedgerTransaction.created_at <= end_time
        ).all()
        
        # Perform reconciliation checks
        discrepancies = []
        total_records = len(transactions)
        matched_records = 0
        
        # Check for duplicate transaction IDs
        transaction_ids = [t.transaction_id for t in transactions]
        if len(transaction_ids) != len(set(transaction_ids)):
            duplicates = [tid for tid in transaction_ids if transaction_ids.count(tid) > 1]
            discrepancies.append({
                "type": "duplicate_transaction_id",
                "details": f"Duplicate transaction IDs found: {set(duplicates)}"
            })
        
        # Check for negative amounts
        negative_amounts = [t for t in transactions if t.amount < 0]
        if negative_amounts:
            discrepancies.append({
                "type": "negative_amount",
                "count": len(negative_amounts),
                "transaction_ids": [t.transaction_id for t in negative_amounts]
            })
        
        # Check for balanced batch transactions (each batch should have balanced debits/credits)
        batch_ids = set(t.batch_id for t in transactions if t.batch_id)
        for batch_id in batch_ids:
            batch_transactions = [t for t in transactions if t.batch_id == batch_id]
            debits = sum(t.amount for t in batch_transactions if t.transaction_type == "DEBIT")
            credits = sum(t.amount for t in batch_transactions if t.transaction_type == "CREDIT")
            
            if abs(debits - credits) > Decimal("0.00000001"):  # Allow tiny rounding errors
                discrepancies.append({
                    "type": "unbalanced_batch",
                    "batch_id": batch_id,
                    "debits": float(debits),
                    "credits": float(credits),
                    "difference": float(abs(debits - credits))
                })
        
        # If no discrepancies found, all records are matched
        if not discrepancies:
            matched_records = total_records
        
        # Determine status
        if not discrepancies:
            status = "SUCCESS"
        elif matched_records > 0:
            status = "PARTIAL"
        else:
            status = "FAILED"
        
        # Create reconciliation log
        recon_log = ReconciliationLog(
            reconciliation_id=f"RECON-{uuid.uuid4().hex[:12].upper()}",
            reconciliation_type="account_reconciliation",
            account_id=account_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
            total_records=total_records,
            matched_records=matched_records,
            unmatched_records=total_records - matched_records,
            discrepancies=discrepancies,
            error_message=None if status != "FAILED" else "Reconciliation failed with discrepancies"
        )
        
        self.db.add(recon_log)
        self.db.commit()
        self.db.refresh(recon_log)
        
        return recon_log
    
    def reconcile_all_accounts(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[ReconciliationLog]:
        """
        Reconcile all active accounts.
        
        Args:
            start_time: Start of reconciliation period
            end_time: End of reconciliation period
            
        Returns:
            List of ReconciliationLog entries for each account
        """
        # Get all active accounts
        accounts = self.db.query(LogicalAccount).filter(
            LogicalAccount.is_active == True
        ).all()
        
        results = []
        for account in accounts:
            try:
                recon_log = self.reconcile_account(
                    account.account_id,
                    start_time,
                    end_time
                )
                results.append(recon_log)
            except Exception as e:
                # Log error but continue with other accounts
                error_log = ReconciliationLog(
                    reconciliation_id=f"RECON-{uuid.uuid4().hex[:12].upper()}",
                    reconciliation_type="account_reconciliation",
                    account_id=account.account_id,
                    start_time=start_time or datetime.now(timezone.utc),
                    end_time=end_time or datetime.now(timezone.utc),
                    status="FAILED",
                    total_records=0,
                    matched_records=0,
                    unmatched_records=0,
                    discrepancies=[],
                    error_message=str(e)
                )
                self.db.add(error_log)
                self.db.commit()
                results.append(error_log)
        
        return results
    
    def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Calculate current account balance.
        
        Args:
            account_id: Account to calculate balance for
            
        Returns:
            Dictionary with balance details
        """
        transactions = self.db.query(LedgerTransaction).filter(
            LedgerTransaction.account_id == account_id
        ).all()
        
        total_debits = sum(t.amount for t in transactions if t.transaction_type == "DEBIT")
        total_credits = sum(t.amount for t in transactions if t.transaction_type == "CREDIT")
        
        # Net balance (credits - debits for most accounts)
        balance = total_credits - total_debits
        
        return {
            "account_id": account_id,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "balance": balance,
            "transaction_count": len(transactions),
            "last_transaction": max((t.created_at for t in transactions), default=None)
        }
