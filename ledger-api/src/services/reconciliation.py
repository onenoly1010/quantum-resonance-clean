"""
Reconciliation service for account balance verification and tracking.
"""
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from src.models.models import ReconciliationLog, LedgerTransaction, LogicalAccount
from src.schemas.schemas import ReconciliationLogCreate, ReconciliationLogUpdate


class ReconciliationService:
    """Service for handling account reconciliation operations."""
    
    @staticmethod
    def calculate_account_balance(db: Session, account_id: UUID) -> Decimal:
        """
        Calculate the current balance for an account.
        Credits increase balance, debits decrease it.
        
        Args:
            db: Database session
            account_id: UUID of the account
            
        Returns:
            Current account balance
        """
        from sqlalchemy import case, func
        
        # Use database aggregation for better performance
        result = db.query(
            func.sum(
                case(
                    (LedgerTransaction.transaction_type == 'credit', LedgerTransaction.amount),
                    else_=-LedgerTransaction.amount
                )
            )
        ).filter(
            LedgerTransaction.account_id == account_id
        ).scalar()
        
        return result if result is not None else Decimal("0")
    
    @staticmethod
    def create_reconciliation(
        db: Session,
        reconciliation_data: ReconciliationLogCreate,
        auto_calculate_actual: bool = True
    ) -> ReconciliationLog:
        """
        Create a new reconciliation log entry.
        
        Args:
            db: Database session
            reconciliation_data: Reconciliation data
            auto_calculate_actual: Whether to auto-calculate actual balance
            
        Returns:
            Created reconciliation log
        """
        # Check if account exists
        account = db.query(LogicalAccount).filter(
            LogicalAccount.id == reconciliation_data.account_id
        ).first()
        
        if not account:
            raise ValueError(f"Account {reconciliation_data.account_id} not found")
        
        # Auto-calculate actual balance if requested
        actual_balance = reconciliation_data.actual_balance
        if auto_calculate_actual:
            actual_balance = ReconciliationService.calculate_account_balance(
                db, reconciliation_data.account_id
            )
        
        # Determine status based on variance
        variance = actual_balance - reconciliation_data.expected_balance
        status = reconciliation_data.status
        
        if abs(variance) < Decimal("0.01"):  # Within 1 cent
            status = "matched"
        elif status == "pending":
            status = "variance"
        
        # Create reconciliation log
        reconciliation_entry = ReconciliationLog(
            account_id=reconciliation_data.account_id,
            reconciliation_date=reconciliation_data.reconciliation_date,
            expected_balance=reconciliation_data.expected_balance,
            actual_balance=actual_balance,
            status=status,
            notes=reconciliation_data.notes,
            reconciled_by=reconciliation_data.reconciled_by
        )
        
        db.add(reconciliation_entry)
        db.commit()
        db.refresh(reconciliation_entry)
        
        return reconciliation_entry
    
    @staticmethod
    def update_reconciliation(
        db: Session,
        reconciliation_id: UUID,
        reconciliation_data: ReconciliationLogUpdate
    ) -> ReconciliationLog:
        """
        Update a reconciliation log entry.
        
        Args:
            db: Database session
            reconciliation_id: UUID of the reconciliation log
            reconciliation_data: Updated reconciliation data
            
        Returns:
            Updated reconciliation log
        """
        reconciliation_entry = db.query(ReconciliationLog).filter(
            ReconciliationLog.id == reconciliation_id
        ).first()
        
        if not reconciliation_entry:
            raise ValueError(f"Reconciliation log {reconciliation_id} not found")
        
        # Update fields if provided
        if reconciliation_data.status is not None:
            reconciliation_entry.status = reconciliation_data.status
            
            # Set resolved_at if status is resolved
            if reconciliation_data.status == "resolved":
                reconciliation_entry.resolved_at = datetime.utcnow()
        
        if reconciliation_data.notes is not None:
            reconciliation_entry.notes = reconciliation_data.notes
        
        if reconciliation_data.resolved_at is not None:
            reconciliation_entry.resolved_at = reconciliation_data.resolved_at
        
        db.commit()
        db.refresh(reconciliation_entry)
        
        return reconciliation_entry
    
    @staticmethod
    def get_variance_reconciliations(
        db: Session,
        account_id: Optional[UUID] = None
    ) -> list[ReconciliationLog]:
        """
        Get all reconciliation logs with variances.
        
        Args:
            db: Database session
            account_id: Optional account ID to filter by
            
        Returns:
            List of reconciliation logs with variance status
        """
        query = db.query(ReconciliationLog).filter(
            ReconciliationLog.status == "variance"
        )
        
        if account_id:
            query = query.filter(ReconciliationLog.account_id == account_id)
        
        return query.order_by(ReconciliationLog.reconciliation_date.desc()).all()
