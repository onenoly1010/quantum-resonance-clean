"""Allocation service for automatic transaction allocation."""

from typing import List, Dict, Any
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from ..models.models import AllocationRule, Account, Transaction, TransactionLine
from ..schemas.schemas import AllocationRuleItem


class AllocationService:
    """Service for handling transaction allocation logic."""
    
    def __init__(self, db: Session):
        """Initialize allocation service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def apply_allocation_rule(
        self,
        rule_id: UUID,
        source_transaction_id: UUID,
        amount: Decimal
    ) -> List[Dict[str, Any]]:
        """
        Apply an allocation rule to distribute an amount.
        
        Args:
            rule_id: ID of the allocation rule to apply
            source_transaction_id: ID of the source transaction
            amount: Amount to allocate
        
        Returns:
            List of allocation results with account IDs and amounts
        
        Raises:
            ValueError: If rule not found or inactive
        """
        # Get the allocation rule
        rule = self.db.query(AllocationRule).filter(
            AllocationRule.id == rule_id,
            AllocationRule.is_active == True
        ).first()
        
        if not rule:
            raise ValueError(f"Allocation rule {rule_id} not found or inactive")
        
        # Parse allocation rules
        allocations = []
        remaining_amount = amount
        
        # Sort by priority
        rule_items = sorted(rule.rules, key=lambda x: x.get("priority", 999))
        
        for item in rule_items:
            destination_account_id = item.get("destination_account_id")
            
            # Verify account exists
            account = self.db.query(Account).filter(
                Account.id == UUID(destination_account_id) if isinstance(destination_account_id, str) else destination_account_id,
                Account.is_active == True
            ).first()
            
            if not account:
                continue
            
            # Calculate allocation amount
            if "percentage" in item and item["percentage"] is not None:
                allocated_amount = (amount * Decimal(str(item["percentage"]))) / Decimal("100")
            elif "amount" in item and item["amount"] is not None:
                allocated_amount = Decimal(str(item["amount"]))
            else:
                continue
            
            # Don't exceed remaining amount
            allocated_amount = min(allocated_amount, remaining_amount)
            
            if allocated_amount > 0:
                allocations.append({
                    "account_id": account.id,
                    "account_code": account.account_code,
                    "account_name": account.account_name,
                    "amount": allocated_amount,
                    "priority": item.get("priority", 999)
                })
                
                remaining_amount -= allocated_amount
        
        # Handle rounding differences - allocate to first account
        if remaining_amount > 0 and allocations:
            allocations[0]["amount"] += remaining_amount
        
        return allocations
    
    def get_active_rules_for_account(self, account_id: UUID) -> List[AllocationRule]:
        """
        Get all active allocation rules for a specific source account.
        
        Args:
            account_id: Source account ID
        
        Returns:
            List of active allocation rules
        """
        return self.db.query(AllocationRule).filter(
            AllocationRule.source_account_id == account_id,
            AllocationRule.is_active == True
        ).order_by(AllocationRule.priority).all()
    
    def validate_allocation_rules(self, rules: List[Dict[str, Any]]) -> bool:
        """
        Validate allocation rules structure and totals.
        
        Args:
            rules: List of allocation rule items
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If validation fails
        """
        if not rules:
            raise ValueError("At least one allocation rule is required")
        
        total_percentage = Decimal("0")
        has_percentage = False
        has_amount = False
        
        for rule in rules:
            if "destination_account_id" not in rule:
                raise ValueError("Each rule must have a destination_account_id")
            
            if "percentage" in rule and rule["percentage"] is not None:
                has_percentage = True
                percentage = Decimal(str(rule["percentage"]))
                if percentage < 0 or percentage > 100:
                    raise ValueError("Percentage must be between 0 and 100")
                total_percentage += percentage
            
            if "amount" in rule and rule["amount"] is not None:
                has_amount = True
                if Decimal(str(rule["amount"])) < 0:
                    raise ValueError("Amount must be non-negative")
        
        # If using percentages, total should be <= 100
        if has_percentage and total_percentage > 100:
            raise ValueError(f"Total percentage {total_percentage} exceeds 100%")
        
        # Can't mix percentages and fixed amounts in same rule
        if has_percentage and has_amount:
            raise ValueError("Cannot mix percentage and fixed amount allocations in same rule")
        
        return True
    
    def create_allocation_transactions(
        self,
        source_account_id: UUID,
        allocations: List[Dict[str, Any]],
        description: str = "Automatic allocation"
    ) -> List[UUID]:
        """
        Create transactions based on allocation results.
        
        Args:
            source_account_id: Source account for debits
            allocations: List of allocation results
            description: Transaction description
        
        Returns:
            List of created transaction IDs
        """
        from datetime import date
        
        transaction_ids = []
        
        for allocation in allocations:
            # Create transaction with debit from source and credit to destination
            transaction = Transaction(
                transaction_number=f"ALLOC-{date.today().strftime('%Y%m%d')}-{len(transaction_ids)+1}",
                transaction_date=date.today(),
                description=description,
                status="POSTED",
                metadata={"allocation": True}
            )
            self.db.add(transaction)
            self.db.flush()
            
            # Debit source account
            debit_line = TransactionLine(
                transaction_id=transaction.id,
                account_id=source_account_id,
                line_type="DEBIT",
                amount=allocation["amount"],
                description=f"Allocation to {allocation['account_name']}"
            )
            self.db.add(debit_line)
            
            # Credit destination account
            credit_line = TransactionLine(
                transaction_id=transaction.id,
                account_id=allocation["account_id"],
                line_type="CREDIT",
                amount=allocation["amount"],
                description=f"Allocation from source"
            )
            self.db.add(credit_line)
            
            transaction_ids.append(transaction.id)
        
        self.db.commit()
        return transaction_ids
