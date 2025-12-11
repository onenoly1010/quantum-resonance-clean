"""
Tests for Allocation Engine

Tests allocation rule validation, transaction splitting, and atomicity
"""
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
import uuid

from src.db.session import Base
from src.models.logical_account import LogicalAccount
from src.models.ledger_transaction import LedgerTransaction
from src.models.allocation_rule import AllocationRule
from src.services.allocation import (
    AllocationEngine,
    AllocationValidationError,
    AllocationRuleNotFoundError,
)


# Test database URL - SQLite in-memory for unit tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def sample_accounts(db_session):
    """Create sample logical accounts for testing"""
    accounts = [
        LogicalAccount(name="Operations", type="EXPENSE", balance=Decimal("0")),
        LogicalAccount(name="Development", type="EXPENSE", balance=Decimal("0")),
        LogicalAccount(name="Reserve", type="ASSET", balance=Decimal("0")),
        LogicalAccount(name="Treasury", type="ASSET", balance=Decimal("1000")),
    ]
    
    for account in accounts:
        db_session.add(account)
    
    await db_session.commit()
    
    # Refresh to get IDs
    for account in accounts:
        await db_session.refresh(account)
    
    return accounts


@pytest.fixture
async def sample_allocation_rule(db_session, sample_accounts):
    """Create sample allocation rule"""
    rule = AllocationRule(
        name="Revenue Split",
        active=True,
        rules=[
            {
                "destination_account_id": str(sample_accounts[0].id),
                "percentage": 60.0,
                "description": "Operations"
            },
            {
                "destination_account_id": str(sample_accounts[1].id),
                "percentage": 30.0,
                "description": "Development"
            },
            {
                "destination_account_id": str(sample_accounts[2].id),
                "percentage": 10.0,
                "description": "Reserve"
            },
        ]
    )
    
    db_session.add(rule)
    await db_session.commit()
    await db_session.refresh(rule)
    
    return rule


@pytest.mark.asyncio
async def test_validate_allocation_rules_valid(db_session):
    """Test validation of valid allocation rules"""
    engine = AllocationEngine(db_session)
    
    rules = [
        {"destination_account_id": str(uuid.uuid4()), "percentage": 50.0},
        {"destination_account_id": str(uuid.uuid4()), "percentage": 30.0},
        {"destination_account_id": str(uuid.uuid4()), "percentage": 20.0},
    ]
    
    # Should not raise exception
    engine.validate_allocation_rules(rules)


@pytest.mark.asyncio
async def test_validate_allocation_rules_invalid_sum(db_session):
    """Test validation fails when percentages don't sum to 100"""
    engine = AllocationEngine(db_session)
    
    rules = [
        {"destination_account_id": str(uuid.uuid4()), "percentage": 50.0},
        {"destination_account_id": str(uuid.uuid4()), "percentage": 30.0},
    ]
    
    with pytest.raises(AllocationValidationError, match="must sum to 100.0"):
        engine.validate_allocation_rules(rules)


@pytest.mark.asyncio
async def test_validate_allocation_rules_missing_fields(db_session):
    """Test validation fails when required fields are missing"""
    engine = AllocationEngine(db_session)
    
    rules = [
        {"percentage": 100.0},  # Missing destination_account_id
    ]
    
    with pytest.raises(AllocationValidationError, match="missing 'destination_account_id'"):
        engine.validate_allocation_rules(rules)


@pytest.mark.asyncio
async def test_validate_destination_accounts_exist(db_session, sample_accounts):
    """Test validation of destination accounts"""
    engine = AllocationEngine(db_session)
    
    rules = [
        {"destination_account_id": str(sample_accounts[0].id), "percentage": 100.0},
    ]
    
    # Should not raise exception
    await engine.validate_destination_accounts(rules)


@pytest.mark.asyncio
async def test_validate_destination_accounts_not_found(db_session):
    """Test validation fails when destination account doesn't exist"""
    engine = AllocationEngine(db_session)
    
    fake_id = uuid.uuid4()
    rules = [
        {"destination_account_id": str(fake_id), "percentage": 100.0},
    ]
    
    with pytest.raises(AllocationValidationError, match="not found"):
        await engine.validate_destination_accounts(rules)


@pytest.mark.asyncio
async def test_create_allocations(db_session, sample_accounts, sample_allocation_rule):
    """Test creating allocation transactions"""
    engine = AllocationEngine(db_session)
    
    # Create parent transaction
    parent_transaction = LedgerTransaction(
        type="DEPOSIT",
        amount=Decimal("1000.00"),
        currency="USD",
        status="COMPLETED",
        logical_account_id=sample_accounts[3].id,  # Treasury
    )
    
    db_session.add(parent_transaction)
    await db_session.commit()
    await db_session.refresh(parent_transaction)
    
    # Create allocations
    allocations = await engine.create_allocations(
        parent_transaction=parent_transaction,
        allocation_rule=sample_allocation_rule
    )
    
    await db_session.commit()
    
    # Verify allocations were created
    assert len(allocations) == 3
    
    # Verify allocation amounts
    assert allocations[0].amount == Decimal("600.00")  # 60%
    assert allocations[1].amount == Decimal("300.00")  # 30%
    assert allocations[2].amount == Decimal("100.00")  # 10%
    
    # Verify all are ALLOCATION type
    for allocation in allocations:
        assert allocation.type == "ALLOCATION"
        assert allocation.status == "COMPLETED"
        assert allocation.parent_transaction_id == parent_transaction.id


@pytest.mark.asyncio
async def test_allocation_updates_account_balances(db_session, sample_accounts, sample_allocation_rule):
    """Test that allocations update account balances correctly"""
    engine = AllocationEngine(db_session)
    
    # Record initial balances
    initial_balances = {acc.id: acc.balance for acc in sample_accounts}
    
    # Create parent transaction
    parent_transaction = LedgerTransaction(
        type="DEPOSIT",
        amount=Decimal("1000.00"),
        currency="USD",
        status="COMPLETED",
    )
    
    db_session.add(parent_transaction)
    await db_session.commit()
    await db_session.refresh(parent_transaction)
    
    # Create allocations
    allocations = await engine.create_allocations(
        parent_transaction=parent_transaction,
        allocation_rule=sample_allocation_rule
    )
    
    await db_session.commit()
    
    # Refresh accounts to get updated balances
    for account in sample_accounts:
        await db_session.refresh(account)
    
    # Verify balances were updated
    assert sample_accounts[0].balance == initial_balances[sample_accounts[0].id] + Decimal("600.00")
    assert sample_accounts[1].balance == initial_balances[sample_accounts[1].id] + Decimal("300.00")
    assert sample_accounts[2].balance == initial_balances[sample_accounts[2].id] + Decimal("100.00")


@pytest.mark.asyncio
async def test_apply_allocation_to_transaction(db_session, sample_accounts, sample_allocation_rule):
    """Test applying allocation to a completed transaction"""
    engine = AllocationEngine(db_session)
    
    # Create completed transaction
    transaction = LedgerTransaction(
        type="DEPOSIT",
        amount=Decimal("500.00"),
        currency="USD",
        status="COMPLETED",
    )
    
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    
    # Apply allocation
    allocations = await engine.apply_allocation_to_transaction(transaction)
    
    await db_session.commit()
    
    # Verify allocations were created
    assert len(allocations) == 3
    
    # Verify total allocation equals parent amount
    total_allocated = sum(a.amount for a in allocations)
    assert total_allocated == Decimal("500.00")


@pytest.mark.asyncio
async def test_apply_allocation_fails_for_non_completed_transaction(db_session, sample_allocation_rule):
    """Test that allocation fails for non-completed transactions"""
    engine = AllocationEngine(db_session)
    
    # Create pending transaction
    transaction = LedgerTransaction(
        type="DEPOSIT",
        amount=Decimal("500.00"),
        currency="USD",
        status="PENDING",
    )
    
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    
    # Should raise validation error
    with pytest.raises(AllocationValidationError, match="Can only allocate completed transactions"):
        await engine.apply_allocation_to_transaction(transaction)


@pytest.mark.asyncio
async def test_apply_allocation_fails_if_already_allocated(db_session, sample_accounts, sample_allocation_rule):
    """Test that allocation fails if transaction already has allocations"""
    engine = AllocationEngine(db_session)
    
    # Create completed transaction
    transaction = LedgerTransaction(
        type="DEPOSIT",
        amount=Decimal("500.00"),
        currency="USD",
        status="COMPLETED",
    )
    
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    
    # Apply allocation first time
    await engine.apply_allocation_to_transaction(transaction)
    await db_session.commit()
    
    # Try to apply again - should fail
    with pytest.raises(AllocationValidationError, match="already has allocations"):
        await engine.apply_allocation_to_transaction(transaction)


@pytest.mark.asyncio
async def test_no_active_allocation_rule(db_session):
    """Test that allocation fails when no active rule exists"""
    engine = AllocationEngine(db_session)
    
    # Create completed transaction
    transaction = LedgerTransaction(
        type="DEPOSIT",
        amount=Decimal("500.00"),
        currency="USD",
        status="COMPLETED",
    )
    
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    
    # Should raise error - no active rules
    with pytest.raises(AllocationRuleNotFoundError, match="No active allocation rule found"):
        await engine.apply_allocation_to_transaction(transaction)


@pytest.mark.asyncio
async def test_allocation_atomicity(db_session, sample_accounts):
    """Test that allocations are atomic - all succeed or all fail"""
    engine = AllocationEngine(db_session)
    
    # Create rule with invalid destination account (will fail)
    bad_rule = AllocationRule(
        name="Bad Rule",
        active=True,
        rules=[
            {
                "destination_account_id": str(uuid.uuid4()),  # Non-existent account
                "percentage": 100.0,
                "description": "Invalid"
            },
        ]
    )
    
    db_session.add(bad_rule)
    await db_session.commit()
    await db_session.refresh(bad_rule)
    
    # Create transaction
    transaction = LedgerTransaction(
        type="DEPOSIT",
        amount=Decimal("500.00"),
        currency="USD",
        status="COMPLETED",
    )
    
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    
    # Store transaction ID before potential expiration
    transaction_id = transaction.id
    
    # Try to create allocations - should fail
    with pytest.raises(AllocationValidationError):
        await engine.create_allocations(
            parent_transaction=transaction,
            allocation_rule=bad_rule
        )
    
    # Rollback the session
    await db_session.rollback()
    
    # Verify no allocations were created using the stored ID
    query = select(LedgerTransaction).where(
        LedgerTransaction.parent_transaction_id == transaction_id
    )
    result = await db_session.execute(query)
    allocations = result.scalars().all()
    
    assert len(allocations) == 0
