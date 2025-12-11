"""Allocation service for automated fund distribution"""

from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from models.models import AllocationRule, LedgerTransaction, LogicalAccount
from schemas.schemas import AllocationDestination


class AllocationService:
    """Service for handling automated allocation of funds"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_rules(
        self, 
        source_account_id: str,
        as_of: Optional[datetime] = None
    ) -> List[AllocationRule]:
        """
        Get active allocation rules for a source account.
        
        Args:
            source_account_id: The source account identifier
            as_of: Optional datetime to check rule effectiveness
            
        Returns:
            List of active allocation rules sorted by priority
        """
        query = self.db.query(AllocationRule).filter(
            AllocationRule.source_account_id == source_account_id,
            AllocationRule.is_active == True
        )
        
        # Filter by effective dates if as_of is provided
        if as_of:
            query = query.filter(
                AllocationRule.effective_from <= as_of,
                (AllocationRule.effective_to.is_(None)) | (AllocationRule.effective_to >= as_of)
            )
        
        # Order by priority (higher priority first)
        return query.order_by(AllocationRule.priority.desc()).all()
    
    def calculate_allocations(
        self,
        amount: Decimal,
        rule: AllocationRule
    ) -> List[Dict[str, Any]]:
        """
        Calculate allocation amounts based on rule configuration.
        
        Args:
            amount: Total amount to allocate
            rule: Allocation rule to apply
            
        Returns:
            List of allocation details with account_id and amount
        """
        allocations = []
        
        # Parse allocation config
        config = rule.allocation_config
        if isinstance(config, str):
            import json
            config = json.loads(config)
        
        for allocation_dest in config:
            dest_account_id = allocation_dest.get("destination_account_id")
            percentage = Decimal(str(allocation_dest.get("percentage", 0)))
            condition = allocation_dest.get("condition")
            
            # Evaluate condition if present (simple amount check for now)
            if condition:
                # Simple condition evaluation: "amount > 1000"
                if ">" in condition:
                    threshold = Decimal(condition.split(">")[1].strip())
                    if amount <= threshold:
                        continue
                elif "<" in condition:
                    threshold = Decimal(condition.split("<")[1].strip())
                    if amount >= threshold:
                        continue
            
            # Calculate allocation amount
            allocation_amount = (amount * percentage / Decimal("100")).quantize(Decimal("0.00000001"))
            
            allocations.append({
                "destination_account_id": dest_account_id,
                "percentage": float(percentage),
                "amount": allocation_amount
            })
        
        return allocations
    
    def execute_allocation(
        self,
        amount: Decimal,
        source_account_id: str,
        rule_id: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute allocation by creating ledger transactions.
        
        Args:
            amount: Total amount to allocate
            source_account_id: Source account for allocation
            rule_id: Optional specific rule to use
            description: Optional description for transactions
            created_by: User executing the allocation
            
        Returns:
            Dictionary with allocation details and batch_id
        """
        # Get the allocation rule
        if rule_id:
            rule = self.db.query(AllocationRule).filter(
                AllocationRule.rule_id == rule_id,
                AllocationRule.is_active == True
            ).first()
            if not rule:
                raise ValueError(f"No active allocation rule found with ID: {rule_id}")
        else:
            # Get the highest priority active rule
            rules = self.get_active_rules(source_account_id)
            if not rules:
                raise ValueError(f"No active allocation rules found for account: {source_account_id}")
            rule = rules[0]
        
        # Calculate allocations
        allocations = self.calculate_allocations(amount, rule)
        
        # Generate batch ID for this allocation
        batch_id = f"ALLOC-{uuid.uuid4().hex[:12].upper()}"
        
        # Create debit transaction from source account
        source_debit = LedgerTransaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
            account_id=source_account_id,
            transaction_type="DEBIT",
            amount=amount,
            currency="USD",
            description=description or f"Allocation via rule: {rule.rule_name}",
            batch_id=batch_id,
            source_system="allocation_engine",
            created_by=created_by,
            metadata={"rule_id": rule.rule_id, "allocation_type": "source"}
        )
        self.db.add(source_debit)
        
        # Create credit transactions for each allocation destination
        for allocation in allocations:
            dest_credit = LedgerTransaction(
                transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
                account_id=allocation["destination_account_id"],
                transaction_type="CREDIT",
                amount=allocation["amount"],
                currency="USD",
                description=description or f"Allocation from {source_account_id} ({allocation['percentage']}%)",
                batch_id=batch_id,
                source_system="allocation_engine",
                created_by=created_by,
                metadata={
                    "rule_id": rule.rule_id,
                    "allocation_type": "destination",
                    "percentage": allocation["percentage"]
                }
            )
            self.db.add(dest_credit)
        
        # Commit the transactions
        self.db.commit()
        
        return {
            "batch_id": batch_id,
            "source_account_id": source_account_id,
            "total_amount": amount,
            "rule_id": rule.rule_id,
            "rule_name": rule.rule_name,
            "allocations": allocations,
            "created_at": datetime.utcnow()
        }
    
    def get_account_balance(self, account_id: str) -> Decimal:
        """
        Calculate account balance (credits - debits for asset accounts).
        
        Args:
            account_id: The account identifier
            
        Returns:
            Current account balance
        """
        # Get all transactions for this account
        transactions = self.db.query(LedgerTransaction).filter(
            LedgerTransaction.account_id == account_id
        ).all()
        
        # Calculate balance
        credits = sum(t.amount for t in transactions if t.transaction_type == "CREDIT")
        debits = sum(t.amount for t in transactions if t.transaction_type == "DEBIT")
        
        # For most accounts, balance = credits - debits
        # (This is simplified; in a full system, account type would affect the calculation)
        balance = credits - debits
        
        return balance
