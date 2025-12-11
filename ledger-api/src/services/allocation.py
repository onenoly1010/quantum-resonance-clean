"""
Allocation service
Handles allocation logic for transactions based on rules
"""
from typing import List, Dict, Any
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from models.models import AllocationRule, LedgerTransaction, LogicalAccount
from schemas.schemas import AllocationDestination
import logging

logger = logging.getLogger(__name__)


class AllocationService:
    """Service for managing transaction allocations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_rules_for_account(self, account_id: UUID) -> List[AllocationRule]:
        """
        Get all active allocation rules for a source account
        
        Args:
            account_id: Source account UUID
            
        Returns:
            List of active allocation rules ordered by priority
        """
        return (
            self.db.query(AllocationRule)
            .filter(
                AllocationRule.source_account_id == account_id,
                AllocationRule.is_active == True
            )
            .order_by(AllocationRule.priority.desc())
            .all()
        )
    
    def apply_allocation_rule(
        self,
        rule: AllocationRule,
        source_amount: Decimal,
        transaction_ref_prefix: str,
        description: str,
        created_by: str = "system"
    ) -> List[LedgerTransaction]:
        """
        Apply an allocation rule to create transactions
        
        Args:
            rule: Allocation rule to apply
            source_amount: Amount to allocate
            transaction_ref_prefix: Prefix for transaction references
            description: Description for transactions
            created_by: User creating the transactions
            
        Returns:
            List of created ledger transactions
        """
        transactions = []
        allocation_logic = rule.allocation_logic
        
        # Validate allocation logic format
        if not isinstance(allocation_logic, list):
            logger.error(f"Invalid allocation logic format for rule {rule.id}")
            raise ValueError("Allocation logic must be a list")
        
        # Calculate allocations
        allocations = self._calculate_allocations(allocation_logic, source_amount)
        
        # Create transactions for each allocation
        for idx, allocation in enumerate(allocations):
            destination_account_id = UUID(allocation["destination_account_id"])
            amount = allocation["amount"]
            
            # Verify destination account exists
            dest_account = self.db.query(LogicalAccount).filter(
                LogicalAccount.id == destination_account_id
            ).first()
            
            if not dest_account:
                logger.warning(f"Destination account {destination_account_id} not found")
                continue
            
            # Create transaction
            transaction = LedgerTransaction(
                transaction_ref=f"{transaction_ref_prefix}-{rule.rule_name}-{idx+1}",
                description=f"{description} - {rule.rule_name}",
                debit_account_id=destination_account_id,
                credit_account_id=rule.source_account_id,
                amount=amount,
                status="posted",
                created_by=created_by,
                metadata={
                    "allocation_rule_id": str(rule.id),
                    "allocation_rule_name": rule.rule_name
                }
            )
            
            self.db.add(transaction)
            transactions.append(transaction)
        
        self.db.commit()
        logger.info(f"Created {len(transactions)} transactions for rule {rule.rule_name}")
        
        return transactions
    
    def _calculate_allocations(
        self,
        allocation_logic: List[Dict[str, Any]],
        total_amount: Decimal
    ) -> List[Dict[str, Any]]:
        """
        Calculate allocation amounts based on logic
        
        Args:
            allocation_logic: List of allocation destinations with percentages or amounts
            total_amount: Total amount to allocate
            
        Returns:
            List of allocations with calculated amounts
        """
        allocations = []
        remaining_amount = total_amount
        
        for rule in allocation_logic:
            destination_account_id = rule.get("destination_account_id")
            
            if not destination_account_id:
                logger.warning("Missing destination_account_id in allocation rule")
                continue
            
            # Calculate amount based on percentage or fixed amount
            if "percentage" in rule and rule["percentage"] is not None:
                percentage = Decimal(str(rule["percentage"]))
                amount = (total_amount * percentage / Decimal("100")).quantize(Decimal("0.01"))
            elif "amount" in rule and rule["amount"] is not None:
                amount = Decimal(str(rule["amount"]))
            else:
                logger.warning(f"No percentage or amount specified for {destination_account_id}")
                continue
            
            # Ensure we don't allocate more than available
            if amount > remaining_amount:
                logger.warning(f"Allocation amount {amount} exceeds remaining {remaining_amount}")
                amount = remaining_amount
            
            allocations.append({
                "destination_account_id": destination_account_id,
                "amount": amount
            })
            
            remaining_amount -= amount
            
            if remaining_amount <= 0:
                break
        
        # Log if there's remaining amount
        if remaining_amount > 0:
            logger.info(f"Remaining unallocated amount: {remaining_amount}")
        
        return allocations
    
    def validate_allocation_logic(self, allocation_logic: List[Dict[str, Any]]) -> bool:
        """
        Validate allocation logic structure
        
        Args:
            allocation_logic: List of allocation rules to validate
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        if not isinstance(allocation_logic, list) or len(allocation_logic) == 0:
            raise ValueError("Allocation logic must be a non-empty list")
        
        total_percentage = Decimal("0")
        
        for idx, rule in enumerate(allocation_logic):
            if not isinstance(rule, dict):
                raise ValueError(f"Rule {idx} must be a dictionary")
            
            if "destination_account_id" not in rule:
                raise ValueError(f"Rule {idx} missing destination_account_id")
            
            # Validate that either percentage or amount is provided
            has_percentage = "percentage" in rule and rule["percentage"] is not None
            has_amount = "amount" in rule and rule["amount"] is not None
            
            if not has_percentage and not has_amount:
                raise ValueError(f"Rule {idx} must specify either percentage or amount")
            
            if has_percentage and has_amount:
                raise ValueError(f"Rule {idx} cannot specify both percentage and amount")
            
            # Track total percentage
            if has_percentage:
                percentage = Decimal(str(rule["percentage"]))
                if percentage < 0 or percentage > 100:
                    raise ValueError(f"Rule {idx} percentage must be between 0 and 100")
                total_percentage += percentage
        
        # Warn if total percentage exceeds 100%
        if total_percentage > Decimal("100"):
            logger.warning(f"Total allocation percentage {total_percentage}% exceeds 100%")
        
        return True
