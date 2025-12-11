"""
SQLAlchemy models for Ledger API.
Defines database tables and relationships.
"""
from sqlalchemy import (
    Column, String, Text, Boolean, DECIMAL, 
    ForeignKey, CheckConstraint, Index, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from src.db.session import Base


class LogicalAccount(Base):
    """Logical account model for different account types."""
    __tablename__ = "logical_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_name = Column(String(255), nullable=False, unique=True)
    account_type = Column(String(50), nullable=False)
    description = Column(Text)
    metadata = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    transactions = relationship("LedgerTransaction", back_populates="account")
    allocation_rules = relationship("AllocationRule", back_populates="source_account")
    reconciliation_logs = relationship("ReconciliationLog", back_populates="account")
    
    __table_args__ = (
        CheckConstraint(
            "account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')",
            name="check_account_type"
        ),
    )


class LedgerTransaction(Base):
    """Ledger transaction model for all financial transactions."""
    __tablename__ = "ledger_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    account_id = Column(UUID(as_uuid=True), ForeignKey("logical_accounts.id"), nullable=False)
    amount = Column(DECIMAL(20, 8), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    transaction_type = Column(String(50), nullable=False)
    reference_id = Column(String(255))
    description = Column(Text)
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("LogicalAccount", back_populates="transactions")
    
    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('debit', 'credit')",
            name="check_transaction_type"
        ),
        Index("idx_ledger_transactions_account_id", "account_id"),
        Index("idx_ledger_transactions_transaction_date", "transaction_date"),
        Index("idx_ledger_transactions_reference_id", "reference_id"),
    )


class AllocationRule(Base):
    """Allocation rule model for automated fund distribution."""
    __tablename__ = "allocation_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(255), nullable=False, unique=True)
    source_account_id = Column(UUID(as_uuid=True), ForeignKey("logical_accounts.id"), nullable=False)
    allocation_config = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    effective_from = Column(TIMESTAMP(timezone=True), server_default=func.now())
    effective_to = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    source_account = relationship("LogicalAccount", back_populates="allocation_rules")
    
    __table_args__ = (
        Index("idx_allocation_rules_source_account_id", "source_account_id"),
        Index("idx_allocation_rules_is_active", "is_active"),
    )


class AuditLog(Base):
    """Audit log model for tracking all system changes."""
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(50), nullable=False)
    user_id = Column(String(255))
    changes = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint(
            "action IN ('create', 'update', 'delete', 'read')",
            name="check_action_type"
        ),
        Index("idx_audit_log_entity_type_id", "entity_type", "entity_id"),
        Index("idx_audit_log_timestamp", "timestamp"),
    )


class ReconciliationLog(Base):
    """Reconciliation log model for account balance verification."""
    __tablename__ = "reconciliation_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("logical_accounts.id"), nullable=False)
    reconciliation_date = Column(TIMESTAMP(timezone=True), nullable=False)
    expected_balance = Column(DECIMAL(20, 8), nullable=False)
    actual_balance = Column(DECIMAL(20, 8), nullable=False)
    # variance is a computed column in the database: GENERATED ALWAYS AS (actual_balance - expected_balance) STORED
    status = Column(String(50), nullable=False)
    notes = Column(Text)
    reconciled_by = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    resolved_at = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    account = relationship("LogicalAccount", back_populates="reconciliation_logs")
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'matched', 'variance', 'resolved')",
            name="check_reconciliation_status"
        ),
        Index("idx_reconciliation_log_account_id", "account_id"),
        Index("idx_reconciliation_log_status", "status"),
    )
