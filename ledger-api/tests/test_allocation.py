"""Tests for allocation service."""

import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import date

from src.services.allocation import AllocationService
from src.models.models import Account, AllocationRule, Transaction, TransactionLine
from src.db.session import SessionLocal


@pytest.fixture
def db_session():
    """Create a test database session."""
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_accounts(db_session):
    """Create test accounts."""
    accounts = []
    
    # Source account
    source = Account(
        account_code="TEST-SRC",
        account_name="Test Source Account",
        account_type="ASSET",
        is_active=True
    )
    db_session.add(source)
    accounts.append(source)
    
    # Destination accounts
    for i in range(3):
        dest = Account(
            account_code=f"TEST-DEST-{i+1}",
            account_name=f"Test Destination {i+1}",
            account_type="ASSET",
            is_active=True
        )
        db_session.add(dest)
        accounts.append(dest)
    
    db_session.commit()
    
    for acc in accounts:
        db_session.refresh(acc)
    
    return accounts


@pytest.fixture
def allocation_service(db_session):
    """Create allocation service instance."""
    return AllocationService(db_session)


class TestAllocationRuleValidation:
    """Test allocation rule validation."""
    
    def test_validate_percentage_allocation(self, allocation_service):
        """Test validation of percentage-based allocation."""
        rules = [
            {"destination_account_id": str(uuid4()), "percentage": 50},
            {"destination_account_id": str(uuid4()), "percentage": 50}
        ]
        
        assert allocation_service.validate_allocation_rules(rules) is True
    
    def test_validate_amount_allocation(self, allocation_service):
        """Test validation of fixed amount allocation."""
        rules = [
            {"destination_account_id": str(uuid4()), "amount": 100},
            {"destination_account_id": str(uuid4()), "amount": 200}
        ]
        
        assert allocation_service.validate_allocation_rules(rules) is True
    
    def test_validate_empty_rules(self, allocation_service):
        """Test validation fails with empty rules."""
        with pytest.raises(ValueError, match="At least one allocation rule is required"):
            allocation_service.validate_allocation_rules([])
    
    def test_validate_missing_destination(self, allocation_service):
        """Test validation fails without destination account."""
        rules = [{"percentage": 100}]
        
        with pytest.raises(ValueError, match="destination_account_id"):
            allocation_service.validate_allocation_rules(rules)
    
    def test_validate_percentage_over_100(self, allocation_service):
        """Test validation fails when total percentage exceeds 100."""
        rules = [
            {"destination_account_id": str(uuid4()), "percentage": 60},
            {"destination_account_id": str(uuid4()), "percentage": 60}
        ]
        
        with pytest.raises(ValueError, match="exceeds 100%"):
            allocation_service.validate_allocation_rules(rules)
    
    def test_validate_negative_percentage(self, allocation_service):
        """Test validation fails with negative percentage."""
        rules = [
            {"destination_account_id": str(uuid4()), "percentage": -10}
        ]
        
        with pytest.raises(ValueError, match="between 0 and 100"):
            allocation_service.validate_allocation_rules(rules)
    
    def test_validate_negative_amount(self, allocation_service):
        """Test validation fails with negative amount."""
        rules = [
            {"destination_account_id": str(uuid4()), "amount": -100}
        ]
        
        with pytest.raises(ValueError, match="non-negative"):
            allocation_service.validate_allocation_rules(rules)


class TestAllocationRuleApplication:
    """Test applying allocation rules."""
    
    def test_apply_percentage_rule(self, db_session, allocation_service, test_accounts):
        """Test applying a percentage-based allocation rule."""
        source, dest1, dest2, dest3 = test_accounts
        
        # Create allocation rule
        rule = AllocationRule(
            rule_name="Test 50/50 Split",
            source_account_id=source.id,
            rules=[
                {"destination_account_id": str(dest1.id), "percentage": 50, "priority": 1},
                {"destination_account_id": str(dest2.id), "percentage": 50, "priority": 2}
            ],
            is_active=True
        )
        db_session.add(rule)
        db_session.commit()
        db_session.refresh(rule)
        
        # Apply rule
        allocations = allocation_service.apply_allocation_rule(
            rule_id=rule.id,
            source_transaction_id=uuid4(),
            amount=Decimal("1000.00")
        )
        
        assert len(allocations) == 2
        assert allocations[0]["amount"] == Decimal("500.00")
        assert allocations[1]["amount"] == Decimal("500.00")
    
    def test_apply_uneven_percentage_rule(self, db_session, allocation_service, test_accounts):
        """Test applying an uneven percentage split."""
        source, dest1, dest2, dest3 = test_accounts
        
        rule = AllocationRule(
            rule_name="Test 60/30/10 Split",
            rules=[
                {"destination_account_id": str(dest1.id), "percentage": 60, "priority": 1},
                {"destination_account_id": str(dest2.id), "percentage": 30, "priority": 2},
                {"destination_account_id": str(dest3.id), "percentage": 10, "priority": 3}
            ],
            is_active=True
        )
        db_session.add(rule)
        db_session.commit()
        db_session.refresh(rule)
        
        allocations = allocation_service.apply_allocation_rule(
            rule_id=rule.id,
            source_transaction_id=uuid4(),
            amount=Decimal("1000.00")
        )
        
        assert len(allocations) == 3
        assert allocations[0]["amount"] == Decimal("600.00")
        assert allocations[1]["amount"] == Decimal("300.00")
        assert allocations[2]["amount"] == Decimal("100.00")
    
    def test_apply_rule_with_rounding(self, db_session, allocation_service, test_accounts):
        """Test allocation with amounts that require rounding."""
        source, dest1, dest2, dest3 = test_accounts
        
        rule = AllocationRule(
            rule_name="Test Rounding",
            rules=[
                {"destination_account_id": str(dest1.id), "percentage": 33.33, "priority": 1},
                {"destination_account_id": str(dest2.id), "percentage": 33.33, "priority": 2},
                {"destination_account_id": str(dest3.id), "percentage": 33.34, "priority": 3}
            ],
            is_active=True
        )
        db_session.add(rule)
        db_session.commit()
        db_session.refresh(rule)
        
        allocations = allocation_service.apply_allocation_rule(
            rule_id=rule.id,
            source_transaction_id=uuid4(),
            amount=Decimal("100.00")
        )
        
        assert len(allocations) == 3
        # Total should equal original amount
        total = sum(a["amount"] for a in allocations)
        assert total == Decimal("100.00")
    
    def test_apply_inactive_rule_fails(self, db_session, allocation_service, test_accounts):
        """Test that applying an inactive rule fails."""
        source, dest1, dest2, dest3 = test_accounts
        
        rule = AllocationRule(
            rule_name="Inactive Rule",
            rules=[
                {"destination_account_id": str(dest1.id), "percentage": 100, "priority": 1}
            ],
            is_active=False  # Inactive
        )
        db_session.add(rule)
        db_session.commit()
        db_session.refresh(rule)
        
        with pytest.raises(ValueError, match="not found or inactive"):
            allocation_service.apply_allocation_rule(
                rule_id=rule.id,
                source_transaction_id=uuid4(),
                amount=Decimal("1000.00")
            )


class TestAllocationTransactionCreation:
    """Test creating transactions from allocations."""
    
    def test_create_allocation_transactions(self, db_session, allocation_service, test_accounts):
        """Test creating ledger transactions from allocation results."""
        source, dest1, dest2, dest3 = test_accounts
        
        allocations = [
            {
                "account_id": dest1.id,
                "account_code": dest1.account_code,
                "account_name": dest1.account_name,
                "amount": Decimal("500.00"),
                "priority": 1
            },
            {
                "account_id": dest2.id,
                "account_code": dest2.account_code,
                "account_name": dest2.account_name,
                "amount": Decimal("500.00"),
                "priority": 2
            }
        ]
        
        transaction_ids = allocation_service.create_allocation_transactions(
            source_account_id=source.id,
            allocations=allocations,
            description="Test allocation"
        )
        
        assert len(transaction_ids) == 2
        
        # Verify transactions were created
        for txn_id in transaction_ids:
            txn = db_session.query(Transaction).filter(Transaction.id == txn_id).first()
            assert txn is not None
            assert txn.status == "POSTED"
            assert len(txn.lines) == 2  # One debit, one credit
            
            # Verify transaction is balanced
            debit_total = sum(
                line.amount for line in txn.lines if line.line_type == "DEBIT"
            )
            credit_total = sum(
                line.amount for line in txn.lines if line.line_type == "CREDIT"
            )
            assert debit_total == credit_total


class TestGetActiveRules:
    """Test getting active allocation rules."""
    
    def test_get_active_rules_for_account(self, db_session, allocation_service, test_accounts):
        """Test retrieving active rules for a specific account."""
        source, dest1, dest2, dest3 = test_accounts
        
        # Create multiple rules
        rule1 = AllocationRule(
            rule_name="Rule 1",
            source_account_id=source.id,
            rules=[{"destination_account_id": str(dest1.id), "percentage": 100, "priority": 1}],
            is_active=True,
            priority=1
        )
        rule2 = AllocationRule(
            rule_name="Rule 2",
            source_account_id=source.id,
            rules=[{"destination_account_id": str(dest2.id), "percentage": 100, "priority": 1}],
            is_active=True,
            priority=2
        )
        rule3 = AllocationRule(
            rule_name="Inactive Rule",
            source_account_id=source.id,
            rules=[{"destination_account_id": str(dest3.id), "percentage": 100, "priority": 1}],
            is_active=False,
            priority=3
        )
        
        db_session.add_all([rule1, rule2, rule3])
        db_session.commit()
        
        active_rules = allocation_service.get_active_rules_for_account(source.id)
        
        assert len(active_rules) == 2  # Only active rules
        assert active_rules[0].rule_name == "Rule 1"
        assert active_rules[1].rule_name == "Rule 2"
