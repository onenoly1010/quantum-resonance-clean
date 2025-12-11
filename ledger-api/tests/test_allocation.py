"""Tests for allocation service"""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from db.session import Base
from models.models import LogicalAccount, AllocationRule, LedgerTransaction
from services.allocation import AllocationService


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_accounts(db_session):
    """Create sample accounts for testing"""
    accounts = [
        LogicalAccount(
            account_id="TREASURY",
            account_name="Main Treasury",
            account_type="ASSET"
        ),
        LogicalAccount(
            account_id="OPERATIONS",
            account_name="Operations Fund",
            account_type="EXPENSE"
        ),
        LogicalAccount(
            account_id="RESERVE",
            account_name="Reserve Fund",
            account_type="ASSET"
        ),
        LogicalAccount(
            account_id="DEVELOPMENT",
            account_name="Development Fund",
            account_type="EXPENSE"
        )
    ]
    
    for account in accounts:
        db_session.add(account)
    db_session.commit()
    
    return accounts


@pytest.fixture
def sample_allocation_rule(db_session, sample_accounts):
    """Create a sample allocation rule"""
    rule = AllocationRule(
        rule_id="RULE-TEST001",
        rule_name="Standard Allocation",
        source_account_id="TREASURY",
        allocation_config=[
            {
                "destination_account_id": "OPERATIONS",
                "percentage": 50.0
            },
            {
                "destination_account_id": "RESERVE",
                "percentage": 30.0
            },
            {
                "destination_account_id": "DEVELOPMENT",
                "percentage": 20.0
            }
        ],
        is_active=True,
        priority=1
    )
    
    db_session.add(rule)
    db_session.commit()
    
    return rule


class TestAllocationService:
    """Test suite for AllocationService"""
    
    def test_get_active_rules(self, db_session, sample_allocation_rule):
        """Test getting active allocation rules"""
        service = AllocationService(db_session)
        rules = service.get_active_rules("TREASURY")
        
        assert len(rules) == 1
        assert rules[0].rule_id == "RULE-TEST001"
        assert rules[0].is_active is True
    
    def test_calculate_allocations(self, db_session, sample_allocation_rule):
        """Test allocation calculation"""
        service = AllocationService(db_session)
        amount = Decimal("1000.00")
        
        allocations = service.calculate_allocations(amount, sample_allocation_rule)
        
        assert len(allocations) == 3
        assert allocations[0]["destination_account_id"] == "OPERATIONS"
        assert allocations[0]["amount"] == Decimal("500.00")
        assert allocations[1]["destination_account_id"] == "RESERVE"
        assert allocations[1]["amount"] == Decimal("300.00")
        assert allocations[2]["destination_account_id"] == "DEVELOPMENT"
        assert allocations[2]["amount"] == Decimal("200.00")
    
    def test_calculate_allocations_with_condition(self, db_session, sample_accounts):
        """Test allocation calculation with conditions"""
        rule = AllocationRule(
            rule_id="RULE-CONDITIONAL",
            rule_name="Conditional Allocation",
            source_account_id="TREASURY",
            allocation_config=[
                {
                    "destination_account_id": "OPERATIONS",
                    "percentage": 60.0,
                    "condition": "amount > 500"
                },
                {
                    "destination_account_id": "RESERVE",
                    "percentage": 40.0
                }
            ],
            is_active=True,
            priority=1
        )
        db_session.add(rule)
        db_session.commit()
        
        service = AllocationService(db_session)
        
        # Test with amount > 500 (condition met)
        allocations = service.calculate_allocations(Decimal("1000.00"), rule)
        assert len(allocations) == 2
        
        # Test with amount <= 500 (condition not met)
        allocations = service.calculate_allocations(Decimal("300.00"), rule)
        assert len(allocations) == 1
        assert allocations[0]["destination_account_id"] == "RESERVE"
    
    def test_execute_allocation(self, db_session, sample_allocation_rule):
        """Test executing an allocation"""
        service = AllocationService(db_session)
        amount = Decimal("1000.00")
        
        result = service.execute_allocation(
            amount=amount,
            source_account_id="TREASURY",
            rule_id="RULE-TEST001",
            description="Test allocation",
            created_by="test_user"
        )
        
        assert result["total_amount"] == amount
        assert result["source_account_id"] == "TREASURY"
        assert result["rule_id"] == "RULE-TEST001"
        assert len(result["allocations"]) == 3
        assert "batch_id" in result
        
        # Verify transactions were created
        transactions = db_session.query(LedgerTransaction).filter(
            LedgerTransaction.batch_id == result["batch_id"]
        ).all()
        
        # Should have 1 debit + 3 credits = 4 transactions
        assert len(transactions) == 4
        
        # Verify debit transaction
        debit_txns = [t for t in transactions if t.transaction_type == "DEBIT"]
        assert len(debit_txns) == 1
        assert debit_txns[0].account_id == "TREASURY"
        assert debit_txns[0].amount == amount
        
        # Verify credit transactions
        credit_txns = [t for t in transactions if t.transaction_type == "CREDIT"]
        assert len(credit_txns) == 3
        
        # Verify total credits equal total debits
        total_credits = sum(t.amount for t in credit_txns)
        total_debits = sum(t.amount for t in debit_txns)
        assert total_credits == total_debits
    
    def test_get_account_balance(self, db_session, sample_accounts):
        """Test getting account balance"""
        # Add some transactions
        transactions = [
            LedgerTransaction(
                transaction_id="TXN-001",
                account_id="TREASURY",
                transaction_type="CREDIT",
                amount=Decimal("1000.00"),
                currency="USD"
            ),
            LedgerTransaction(
                transaction_id="TXN-002",
                account_id="TREASURY",
                transaction_type="DEBIT",
                amount=Decimal("300.00"),
                currency="USD"
            ),
            LedgerTransaction(
                transaction_id="TXN-003",
                account_id="TREASURY",
                transaction_type="CREDIT",
                amount=Decimal("500.00"),
                currency="USD"
            )
        ]
        
        for txn in transactions:
            db_session.add(txn)
        db_session.commit()
        
        service = AllocationService(db_session)
        balance = service.get_account_balance("TREASURY")
        
        # Balance = Credits - Debits = (1000 + 500) - 300 = 1200
        assert balance == Decimal("1200.00")
    
    def test_execute_allocation_no_active_rule(self, db_session, sample_accounts):
        """Test executing allocation with no active rule"""
        service = AllocationService(db_session)
        
        with pytest.raises(ValueError, match="No active allocation rules found"):
            service.execute_allocation(
                amount=Decimal("1000.00"),
                source_account_id="TREASURY",
                created_by="test_user"
            )
    
    def test_execute_allocation_invalid_rule(self, db_session, sample_accounts):
        """Test executing allocation with invalid rule ID"""
        service = AllocationService(db_session)
        
        with pytest.raises(ValueError, match="No active allocation rule found"):
            service.execute_allocation(
                amount=Decimal("1000.00"),
                source_account_id="TREASURY",
                rule_id="INVALID-RULE",
                created_by="test_user"
            )
    
    def test_allocation_percentage_precision(self, db_session, sample_accounts):
        """Test allocation with precise percentages"""
        rule = AllocationRule(
            rule_id="RULE-PRECISE",
            rule_name="Precise Allocation",
            source_account_id="TREASURY",
            allocation_config=[
                {
                    "destination_account_id": "OPERATIONS",
                    "percentage": 33.33
                },
                {
                    "destination_account_id": "RESERVE",
                    "percentage": 33.33
                },
                {
                    "destination_account_id": "DEVELOPMENT",
                    "percentage": 33.34
                }
            ],
            is_active=True,
            priority=1
        )
        db_session.add(rule)
        db_session.commit()
        
        service = AllocationService(db_session)
        allocations = service.calculate_allocations(Decimal("1000.00"), rule)
        
        # Verify allocations sum to total
        total_allocated = sum(a["amount"] for a in allocations)
        assert total_allocated == Decimal("1000.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
