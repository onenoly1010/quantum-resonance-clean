"""
Allocation service for managing fund allocation rules and execution.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from src.models.models import AllocationRule, LedgerTransaction, LogicalAccount
from src.schemas.schemas import AllocationRuleCreate, AllocationRuleUpdate


class AllocationService:
    """Service for handling allocation rules and fund distribution."""
    
    @staticmethod
    def validate_allocation_config(allocation_config: List[Dict]) -> bool:
        """
        Validate that allocation percentages sum to 100.
        
        Args:
            allocation_config: List of allocation configurations
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        total_percentage = sum(
            Decimal(str(config.get("percentage", 0))) 
            for config in allocation_config
        )
        
        if total_percentage != Decimal("100"):
            raise ValueError(
                f"Allocation percentages must sum to 100, got {total_percentage}"
            )
        
        return True
    
    @staticmethod
    def create_allocation_rule(
        db: Session,
        rule_data: AllocationRuleCreate
    ) -> AllocationRule:
        """
        Create a new allocation rule.
        
        Args:
            db: Database session
            rule_data: Allocation rule creation data
            
        Returns:
            Created allocation rule
        """
        # Validate allocation config
        allocation_config_dicts = [config.model_dump() for config in rule_data.allocation_config]
        AllocationService.validate_allocation_config(allocation_config_dicts)
        
        # Check if source account exists
        source_account = db.query(LogicalAccount).filter(
            LogicalAccount.id == rule_data.source_account_id
        ).first()
        
        if not source_account:
            raise ValueError(f"Source account {rule_data.source_account_id} not found")
        
        # Check if all destination accounts exist
        for config in rule_data.allocation_config:
            dest_account = db.query(LogicalAccount).filter(
                LogicalAccount.id == config.destination_account_id
            ).first()
            if not dest_account:
                raise ValueError(
                    f"Destination account {config.destination_account_id} not found"
                )
        
        # Create allocation rule
        db_rule = AllocationRule(
            rule_name=rule_data.rule_name,
            source_account_id=rule_data.source_account_id,
            allocation_config=allocation_config_dicts,
            is_active=rule_data.is_active,
            effective_from=rule_data.effective_from or datetime.utcnow(),
            effective_to=rule_data.effective_to
        )
        
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        
        return db_rule
    
    @staticmethod
    def update_allocation_rule(
        db: Session,
        rule_id: UUID,
        rule_data: AllocationRuleUpdate
    ) -> AllocationRule:
        """
        Update an existing allocation rule.
        
        Args:
            db: Database session
            rule_id: UUID of the rule to update
            rule_data: Updated rule data
            
        Returns:
            Updated allocation rule
        """
        db_rule = db.query(AllocationRule).filter(AllocationRule.id == rule_id).first()
        
        if not db_rule:
            raise ValueError(f"Allocation rule {rule_id} not found")
        
        # Update fields if provided
        if rule_data.rule_name is not None:
            db_rule.rule_name = rule_data.rule_name
        
        if rule_data.allocation_config is not None:
            allocation_config_dicts = [config.model_dump() for config in rule_data.allocation_config]
            AllocationService.validate_allocation_config(allocation_config_dicts)
            db_rule.allocation_config = allocation_config_dicts
        
        if rule_data.is_active is not None:
            db_rule.is_active = rule_data.is_active
        
        if rule_data.effective_to is not None:
            db_rule.effective_to = rule_data.effective_to
        
        db.commit()
        db.refresh(db_rule)
        
        return db_rule
    
    @staticmethod
    def execute_allocation(
        db: Session,
        rule_id: UUID,
        amount: Decimal,
        reference_id: Optional[str] = None
    ) -> List[LedgerTransaction]:
        """
        Execute an allocation rule for a given amount.
        
        Args:
            db: Database session
            rule_id: UUID of the allocation rule
            amount: Total amount to allocate
            reference_id: Optional reference ID for tracking
            
        Returns:
            List of created ledger transactions
        """
        # Get allocation rule
        db_rule = db.query(AllocationRule).filter(
            AllocationRule.id == rule_id,
            AllocationRule.is_active == True
        ).first()
        
        if not db_rule:
            raise ValueError(f"Active allocation rule {rule_id} not found")
        
        # Sort allocations by priority
        sorted_allocations = sorted(
            db_rule.allocation_config,
            key=lambda x: x.get("priority", 999)
        )
        
        transactions = []
        
        # Create debit transaction from source account
        source_transaction = LedgerTransaction(
            account_id=db_rule.source_account_id,
            amount=amount,
            transaction_type="debit",
            reference_id=reference_id,
            description=f"Allocation from rule: {db_rule.rule_name}",
            metadata={"allocation_rule_id": str(rule_id)}
        )
        db.add(source_transaction)
        transactions.append(source_transaction)
        
        # Create credit transactions for each destination
        for config in sorted_allocations:
            allocation_amount = (amount * Decimal(str(config["percentage"]))) / Decimal("100")
            
            dest_transaction = LedgerTransaction(
                account_id=UUID(config["destination_account_id"]),
                amount=allocation_amount,
                transaction_type="credit",
                reference_id=reference_id,
                description=f"Allocation to {config['percentage']}% from {db_rule.rule_name}",
                metadata={
                    "allocation_rule_id": str(rule_id),
                    "percentage": str(config["percentage"]),
                    "priority": config.get("priority", 999)
                }
            )
            db.add(dest_transaction)
            transactions.append(dest_transaction)
        
        db.commit()
        
        # Refresh all transactions
        for txn in transactions:
            db.refresh(txn)
        
        return transactions
