"""SQLAlchemy models for the Ledger API."""

from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, 
    Numeric, Date, ForeignKey, Text, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..db.session import Base


class Account(Base):
    """Chart of accounts model."""
    
    __tablename__ = "accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_code = Column(String(50), unique=True, nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False, index=True)
    parent_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    currency = Column(String(3), default="USD")
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSONB, default={})
    
    # Relationships
    parent = relationship("Account", remote_side=[id], backref="children")
    transaction_lines = relationship("TransactionLine", back_populates="account")
    treasury_accounts = relationship("TreasuryAccount", back_populates="account")
    reconciliations = relationship("Reconciliation", back_populates="account")
    
    __table_args__ = (
        CheckConstraint(
            "account_type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')",
            name="check_account_type"
        ),
    )


class Transaction(Base):
    """Transaction header model."""
    
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_number = Column(String(100), unique=True, nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    description = Column(Text)
    reference_number = Column(String(100))
    status = Column(String(50), default="PENDING", index=True)
    created_by = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    posted_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, default={})
    
    # Relationships
    lines = relationship("TransactionLine", back_populates="transaction", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'POSTED', 'VOID', 'RECONCILED')",
            name="check_transaction_status"
        ),
    )


class TransactionLine(Base):
    """Transaction line (journal entry) model."""
    
    __tablename__ = "transaction_lines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True)
    line_type = Column(String(10), nullable=False, index=True)
    amount = Column(Numeric(20, 4), nullable=False)
    currency = Column(String(3), default="USD")
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSONB, default={})
    
    # Relationships
    transaction = relationship("Transaction", back_populates="lines")
    account = relationship("Account", back_populates="transaction_lines")
    
    __table_args__ = (
        CheckConstraint("line_type IN ('DEBIT', 'CREDIT')", name="check_line_type"),
        CheckConstraint("amount >= 0", name="check_amount_positive"),
    )


class AllocationRule(Base):
    """Allocation rule model."""
    
    __tablename__ = "allocation_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(255), nullable=False)
    source_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True, index=True)
    rules = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=0, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(255))
    metadata = Column(JSONB, default={})
    
    __table_args__ = (
        CheckConstraint("jsonb_typeof(rules) = 'array'", name="check_rules_array"),
    )


class TreasuryAccount(Base):
    """Treasury account model."""
    
    __tablename__ = "treasury_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True)
    treasury_type = Column(String(50), nullable=False, index=True)
    balance = Column(Numeric(20, 4), default=0)
    currency = Column(String(3), default="USD")
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSONB, default={})
    
    # Relationships
    account = relationship("Account", back_populates="treasury_accounts")
    
    __table_args__ = (
        CheckConstraint(
            "treasury_type IN ('MAIN', 'RESERVE', 'OPERATIONAL', 'ESCROW')",
            name="check_treasury_type"
        ),
    )


class Reconciliation(Base):
    """Reconciliation model."""
    
    __tablename__ = "reconciliations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True)
    reconciliation_date = Column(Date, nullable=False, index=True)
    statement_balance = Column(Numeric(20, 4), nullable=False)
    ledger_balance = Column(Numeric(20, 4), nullable=False)
    status = Column(String(50), default="PENDING", index=True)
    reconciled_by = Column(String(255))
    reconciled_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSONB, default={})
    
    # Relationships
    account = relationship("Account", back_populates="reconciliations")
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED')",
            name="check_reconciliation_status"
        ),
    )


class AuditLog(Base):
    """Audit log model."""
    
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_name = Column(String(100), nullable=False)
    record_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(50), nullable=False, index=True)
    user_id = Column(String(255), index=True)
    changes = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    __table_args__ = (
        CheckConstraint(
            "action IN ('CREATE', 'UPDATE', 'DELETE', 'READ')",
            name="check_audit_action"
        ),
        Index("idx_audit_table_record", "table_name", "record_id"),
    )
