"""
Tests for allocation service.
"""
import pytest
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.session import Base
from src.models.models import LogicalAccount, AllocationRule, LedgerTransaction
from src.services.allocation import AllocationService
from src.schemas.schemas import AllocationRuleCreate, AllocationConfig


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_accounts(db_session):
    """Create sample logical accounts for testing."""
    source_account = LogicalAccount(
        account_name="Test Source Account",
        account_type="asset",
        description="Source account for allocation tests"
    )
    
    dest_account_1 = LogicalAccount(
        account_name="Test Destination Account 1",
        account_type="asset",
        description="Destination account 1"
    )
    
    dest_account_2 = LogicalAccount(
        account_name="Test Destination Account 2",
        account_type="asset",
        description="Destination account 2"
    )
    
    db_session.add_all([source_account, dest_account_1, dest_account_2])
    db_session.commit()
    
    return {
        "source": source_account,
        "dest1": dest_account_1,
        "dest2": dest_account_2
    }


def test_validate_allocation_config_valid():
    """Test that valid allocation config passes validation."""
    config = [
        {"destination_account_id": str(uuid4()), "percentage": 60, "priority": 1},
        {"destination_account_id": str(uuid4()), "percentage": 40, "priority": 2}
    ]
    
    result = AllocationService.validate_allocation_config(config)
    assert result is True


def test_validate_allocation_config_invalid():
    """Test that invalid allocation config raises ValueError."""
    config = [
        {"destination_account_id": str(uuid4()), "percentage": 60, "priority": 1},
        {"destination_account_id": str(uuid4()), "percentage": 30, "priority": 2}
    ]
    
    with pytest.raises(ValueError) as exc_info:
        AllocationService.validate_allocation_config(config)
    
    assert "must sum to 100" in str(exc_info.value)


def test_create_allocation_rule(db_session, sample_accounts):
    """Test creating an allocation rule."""
    source = sample_accounts["source"]
    dest1 = sample_accounts["dest1"]
    dest2 = sample_accounts["dest2"]
    
    allocation_config = [
        AllocationConfig(
            destination_account_id=dest1.id,
            percentage=Decimal("70"),
            priority=1
        ),
        AllocationConfig(
            destination_account_id=dest2.id,
            percentage=Decimal("30"),
            priority=2
        )
    ]
    
    rule_data = AllocationRuleCreate(
        rule_name="Test Allocation Rule",
        source_account_id=source.id,
        allocation_config=allocation_config,
        is_active=True
    )
    
    rule = AllocationService.create_allocation_rule(db_session, rule_data)
    
    assert rule.id is not None
    assert rule.rule_name == "Test Allocation Rule"
    assert rule.source_account_id == source.id
    assert len(rule.allocation_config) == 2
    assert rule.is_active is True


def test_create_allocation_rule_invalid_source(db_session):
    """Test creating allocation rule with non-existent source account."""
    fake_source_id = uuid4()
    fake_dest_id = uuid4()
    
    allocation_config = [
        AllocationConfig(
            destination_account_id=fake_dest_id,
            percentage=Decimal("100"),
            priority=1
        )
    ]
    
    rule_data = AllocationRuleCreate(
        rule_name="Invalid Rule",
        source_account_id=fake_source_id,
        allocation_config=allocation_config,
        is_active=True
    )
    
    with pytest.raises(ValueError) as exc_info:
        AllocationService.create_allocation_rule(db_session, rule_data)
    
    assert "not found" in str(exc_info.value)


def test_execute_allocation(db_session, sample_accounts):
    """Test executing an allocation rule."""
    source = sample_accounts["source"]
    dest1 = sample_accounts["dest1"]
    dest2 = sample_accounts["dest2"]
    
    # Create allocation rule
    allocation_config = [
        AllocationConfig(
            destination_account_id=dest1.id,
            percentage=Decimal("60"),
            priority=1
        ),
        AllocationConfig(
            destination_account_id=dest2.id,
            percentage=Decimal("40"),
            priority=2
        )
    ]
    
    rule_data = AllocationRuleCreate(
        rule_name="Execute Test Rule",
        source_account_id=source.id,
        allocation_config=allocation_config,
        is_active=True
    )
    
    rule = AllocationService.create_allocation_rule(db_session, rule_data)
    
    # Execute allocation
    amount = Decimal("1000.00")
    transactions = AllocationService.execute_allocation(
        db_session, rule.id, amount, "TEST-REF-001"
    )
    
    # Should create 3 transactions: 1 debit from source, 2 credits to destinations
    assert len(transactions) == 3
    
    # Check source debit
    source_txn = [t for t in transactions if t.transaction_type == "debit"][0]
    assert source_txn.account_id == source.id
    assert source_txn.amount == amount
    assert source_txn.reference_id == "TEST-REF-001"
    
    # Check destination credits
    credit_txns = [t for t in transactions if t.transaction_type == "credit"]
    assert len(credit_txns) == 2
    
    # Check amounts
    dest1_txn = [t for t in credit_txns if t.account_id == dest1.id][0]
    dest2_txn = [t for t in credit_txns if t.account_id == dest2.id][0]
    
    assert dest1_txn.amount == Decimal("600.00")  # 60% of 1000
    assert dest2_txn.amount == Decimal("400.00")  # 40% of 1000


def test_execute_allocation_inactive_rule(db_session, sample_accounts):
    """Test executing an inactive allocation rule."""
    source = sample_accounts["source"]
    dest1 = sample_accounts["dest1"]
    
    allocation_config = [
        AllocationConfig(
            destination_account_id=dest1.id,
            percentage=Decimal("100"),
            priority=1
        )
    ]
    
    rule_data = AllocationRuleCreate(
        rule_name="Inactive Rule",
        source_account_id=source.id,
        allocation_config=allocation_config,
        is_active=False  # Inactive rule
    )
    
    rule = AllocationService.create_allocation_rule(db_session, rule_data)
    
    # Try to execute inactive rule
    with pytest.raises(ValueError) as exc_info:
        AllocationService.execute_allocation(
            db_session, rule.id, Decimal("100.00")
        )
    
    assert "not found" in str(exc_info.value)
