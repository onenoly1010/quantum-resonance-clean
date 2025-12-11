import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from src.models.models import Base, LogicalAccount, LedgerTransaction, AllocationRule
from src.services.allocation import apply_allocation_rules
import uuid


@pytest_asyncio.fixture
async def async_session():
    """Create an in-memory SQLite database for testing."""
    # Create in-memory SQLite engine with async support
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    AsyncTestingSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with AsyncTestingSessionLocal() as session:
        yield session
    
    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
async def test_allocation_engine(async_session):
    """
    Test the allocation engine with a sample transaction.
    Creates two accounts, an allocation rule, and verifies allocations.
    """
    # Create two destination accounts
    account1_id = uuid.uuid4()
    account2_id = uuid.uuid4()
    
    account1 = LogicalAccount(
        id=account1_id,
        name="Development Fund",
        account_type="OPERATIONAL",
        balance=Decimal("0"),
        currency="PI"
    )
    account2 = LogicalAccount(
        id=account2_id,
        name="Community Fund",
        account_type="OPERATIONAL",
        balance=Decimal("0"),
        currency="PI"
    )
    
    async_session.add(account1)
    async_session.add(account2)
    await async_session.flush()
    
    # Create allocation rule (60% to account1, 40% to account2)
    rule = AllocationRule(
        name="Default Allocation",
        rule_data={
            "allocations": [
                {"logical_account_id": str(account1_id), "percent": "60"},
                {"logical_account_id": str(account2_id), "percent": "40"}
            ]
        },
        active=True
    )
    async_session.add(rule)
    await async_session.flush()
    
    # Create parent transaction (deposit of 100 PI)
    parent_tx = LedgerTransaction(
        transaction_type="DEPOSIT",
        amount=Decimal("100"),
        currency="PI",
        status="COMPLETED"
    )
    async_session.add(parent_tx)
    await async_session.flush()
    
    # Apply allocation rules
    allocations = await apply_allocation_rules(async_session, parent_tx)
    await async_session.commit()
    
    # Verify two allocation transactions were created
    assert len(allocations) == 2
    
    # Verify allocation amounts (60 and 40)
    allocation_amounts = sorted([float(alloc.amount) for alloc in allocations])
    assert allocation_amounts[0] == 40.0
    assert allocation_amounts[1] == 60.0
    
    # Verify all allocations have correct type and status
    for alloc in allocations:
        assert alloc.transaction_type == "ALLOCATION"
        assert alloc.status == "COMPLETED"
        assert alloc.parent_transaction_id == parent_tx.id
    
    # Refresh accounts and verify balances were updated
    await async_session.refresh(account1)
    await async_session.refresh(account2)
    
    assert float(account1.balance) == 60.0
    assert float(account2.balance) == 40.0
    
    print("✓ Allocation engine test passed")


@pytest.mark.asyncio
async def test_allocation_rule_validation(async_session):
    """
    Test that allocation rules with invalid percentages are rejected.
    """
    # Create a rule with percentages that don't sum to 100
    account1_id = uuid.uuid4()
    account2_id = uuid.uuid4()
    
    account1 = LogicalAccount(
        id=account1_id,
        name="Test Account 1",
        account_type="OPERATIONAL",
        balance=Decimal("0"),
        currency="PI"
    )
    account2 = LogicalAccount(
        id=account2_id,
        name="Test Account 2",
        account_type="OPERATIONAL",
        balance=Decimal("0"),
        currency="PI"
    )
    
    async_session.add(account1)
    async_session.add(account2)
    await async_session.flush()
    
    # Create allocation rule with invalid percentages (70% + 40% = 110%)
    rule = AllocationRule(
        name="Invalid Allocation",
        rule_data={
            "allocations": [
                {"logical_account_id": str(account1_id), "percent": "70"},
                {"logical_account_id": str(account2_id), "percent": "40"}
            ]
        },
        active=True
    )
    async_session.add(rule)
    await async_session.flush()
    
    # Create parent transaction
    parent_tx = LedgerTransaction(
        transaction_type="DEPOSIT",
        amount=Decimal("100"),
        currency="PI",
        status="COMPLETED"
    )
    async_session.add(parent_tx)
    await async_session.flush()
    
    # Apply allocation rules should raise ValueError
    with pytest.raises(ValueError, match="Total allocation percentage must equal 100"):
        await apply_allocation_rules(async_session, parent_tx)
    
    print("✓ Allocation validation test passed")
