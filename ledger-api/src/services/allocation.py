"""
Allocation Engine Service

Handles automatic transaction splitting based on allocation rules.
Ensures atomicity and rule validation.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from decimal import Decimal
import uuid
from datetime import datetime

from ..models.allocation_rule import AllocationRule
from ..models.ledger_transaction import LedgerTransaction
from ..models.logical_account import LogicalAccount
from ..schemas.allocation_rule import AllocationRuleItem


class AllocationEngineError(Exception):
    """Base exception for allocation engine errors"""
    pass


class AllocationRuleNotFoundError(AllocationEngineError):
    """Raised when allocation rule is not found"""
    pass


class AllocationValidationError(AllocationEngineError):
    """Raised when allocation validation fails"""
    pass


class AllocationEngine:
    """
    Allocation Engine - Splits transactions according to rules
    
    Features:
    - Validates allocation rules (sum = 100%)
    - Creates allocation transactions atomically
    - Links allocations to parent transaction
    - Updates account balances
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_allocation_rule(self, rule_name: Optional[str] = None) -> Optional[AllocationRule]:
        """
        Get active allocation rule by name, or the default active rule
        
        Args:
            rule_name: Optional rule name. If None, returns first active rule.
            
        Returns:
            AllocationRule if found, None otherwise
        """
        query = select(AllocationRule).where(AllocationRule.active == True)
        
        if rule_name:
            query = query.where(AllocationRule.name == rule_name)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def validate_allocation_rules(self, rules: List[Dict[str, Any]]) -> None:
        """
        Validate allocation rules
        
        Args:
            rules: List of allocation rule dictionaries
            
        Raises:
            AllocationValidationError: If validation fails
        """
        if not rules:
            raise AllocationValidationError("Allocation rules cannot be empty")
        
        # Validate percentage sum
        total_percentage = sum(Decimal(str(rule.get("percentage", 0))) for rule in rules)
        
        if abs(total_percentage - Decimal("100.0")) > Decimal("0.01"):
            raise AllocationValidationError(
                f"Allocation percentages must sum to 100.0, got {total_percentage}"
            )
        
        # Validate all rules have required fields
        for idx, rule in enumerate(rules):
            if "destination_account_id" not in rule:
                raise AllocationValidationError(
                    f"Rule {idx} missing 'destination_account_id'"
                )
            if "percentage" not in rule:
                raise AllocationValidationError(
                    f"Rule {idx} missing 'percentage'"
                )
            
            # Validate percentage range
            percentage = Decimal(str(rule["percentage"]))
            if percentage < 0 or percentage > 100:
                raise AllocationValidationError(
                    f"Rule {idx} percentage must be between 0 and 100, got {percentage}"
                )

    async def validate_destination_accounts(self, rules: List[Dict[str, Any]]) -> None:
        """
        Validate that all destination accounts exist
        
        Args:
            rules: List of allocation rule dictionaries
            
        Raises:
            AllocationValidationError: If any account doesn't exist
        """
        account_ids = [uuid.UUID(rule["destination_account_id"]) for rule in rules]
        
        query = select(LogicalAccount.id).where(LogicalAccount.id.in_(account_ids))
        result = await self.db.execute(query)
        existing_ids = {row[0] for row in result.all()}
        
        missing_ids = set(account_ids) - existing_ids
        if missing_ids:
            raise AllocationValidationError(
                f"Destination accounts not found: {missing_ids}"
            )

    async def create_allocations(
        self,
        parent_transaction: LedgerTransaction,
        allocation_rule: Optional[AllocationRule] = None,
        rule_name: Optional[str] = None
    ) -> List[LedgerTransaction]:
        """
        Create allocation transactions for a parent transaction
        
        Args:
            parent_transaction: The parent transaction to allocate
            allocation_rule: Optional pre-fetched allocation rule
            rule_name: Optional rule name to use
            
        Returns:
            List of created allocation transactions
            
        Raises:
            AllocationEngineError: If allocation fails
        """
        # Get allocation rule
        if allocation_rule is None:
            allocation_rule = await self.get_active_allocation_rule(rule_name)
            
        if allocation_rule is None:
            raise AllocationRuleNotFoundError(
                f"No active allocation rule found{f' with name {rule_name}' if rule_name else ''}"
            )
        
        # Validate rules
        rules = allocation_rule.rules
        if not isinstance(rules, list):
            raise AllocationValidationError("Allocation rules must be a list")
        
        self.validate_allocation_rules(rules)
        await self.validate_destination_accounts(rules)
        
        # Create allocation transactions
        allocations = []
        parent_amount = parent_transaction.amount
        
        for rule in rules:
            percentage = Decimal(str(rule["percentage"]))
            allocation_amount = (parent_amount * percentage / Decimal("100")).quantize(
                Decimal("0.000000000001")  # 12 decimal places
            )
            
            allocation = LedgerTransaction(
                type="ALLOCATION",
                amount=allocation_amount,
                currency=parent_transaction.currency,
                status="COMPLETED",
                logical_account_id=uuid.UUID(rule["destination_account_id"]),
                parent_transaction_id=parent_transaction.id,
                description=f"Allocation: {rule.get('description', 'Auto-allocated')} ({percentage}%)",
                transaction_metadata={
                    "allocation_rule_id": str(allocation_rule.id),
                    "allocation_rule_name": allocation_rule.name,
                    "allocation_percentage": str(percentage),
                    "parent_transaction_id": str(parent_transaction.id),
                }
            )
            
            self.db.add(allocation)
            allocations.append(allocation)
        
        # Flush to get IDs but don't commit yet (caller handles transaction)
        await self.db.flush()
        
        # Update account balances
        for allocation in allocations:
            account_query = select(LogicalAccount).where(
                LogicalAccount.id == allocation.logical_account_id
            )
            account_result = await self.db.execute(account_query)
            account = account_result.scalar_one()
            account.balance += allocation.amount
        
        return allocations

    async def apply_allocation_to_transaction(
        self,
        transaction: LedgerTransaction,
        rule_name: Optional[str] = None
    ) -> List[LedgerTransaction]:
        """
        Apply allocation rules to a completed transaction atomically
        
        This is the main entry point for automatic allocation.
        Called when a transaction status changes to COMPLETED.
        
        Args:
            transaction: The transaction to allocate
            rule_name: Optional specific rule name to use
            
        Returns:
            List of created allocation transactions
        """
        if transaction.status != "COMPLETED":
            raise AllocationValidationError(
                "Can only allocate completed transactions"
            )
        
        # Check if allocations already exist
        existing_allocations_query = select(LedgerTransaction).where(
            LedgerTransaction.parent_transaction_id == transaction.id
        )
        existing_result = await self.db.execute(existing_allocations_query)
        existing_allocations = existing_result.scalars().all()
        
        if existing_allocations:
            raise AllocationValidationError(
                f"Transaction {transaction.id} already has allocations"
            )
        
        # Create allocations within the current transaction
        allocations = await self.create_allocations(
            parent_transaction=transaction,
            rule_name=rule_name
        )
        
        return allocations
