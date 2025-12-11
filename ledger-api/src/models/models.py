"""
SQLAlchemy models for Ledger API
Defines database models for all entities
"""
from sqlalchemy import Column, String, Integer, Boolean, Numeric, DateTime, CheckConstraint, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.session import Base
import uuid


class LogicalAccount(Base):
    """Model for logical accounts"""
    __tablename__ = "logical_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_code = Column(String(50), unique=True, nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False, index=True)
    currency = Column(String(3), nullable=False, default='USD')
    status = Column(String(20), nullable=False, default='active', index=True)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(255))
    updated_by = Column(String(255))
    
    __table_args__ = (
        CheckConstraint("account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')", name='check_account_type'),
        CheckConstraint("status IN ('active', 'inactive', 'archived')", name='check_status'),
    )
    
    # Relationships
    debit_transactions = relationship("LedgerTransaction", foreign_keys="LedgerTransaction.debit_account_id", back_populates="debit_account")
    credit_transactions = relationship("LedgerTransaction", foreign_keys="LedgerTransaction.credit_account_id", back_populates="credit_account")
    allocation_rules = relationship("AllocationRule", back_populates="source_account")
    reconciliation_logs = relationship("ReconciliationLog", back_populates="account")


class LedgerTransaction(Base):
    """Model for ledger transactions"""
    __tablename__ = "ledger_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_ref = Column(String(100), unique=True, nullable=False, index=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    description = Column(Text, nullable=False)
    debit_account_id = Column(UUID(as_uuid=True), ForeignKey('logical_accounts.id'), nullable=False, index=True)
    credit_account_id = Column(UUID(as_uuid=True), ForeignKey('logical_accounts.id'), nullable=False, index=True)
    amount = Column(Numeric(20, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    status = Column(String(20), nullable=False, default='pending', index=True)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(255))
    updated_by = Column(String(255))
    
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_amount_positive'),
        CheckConstraint("status IN ('pending', 'posted', 'reversed', 'cancelled')", name='check_transaction_status'),
        CheckConstraint('debit_account_id != credit_account_id', name='check_different_accounts'),
    )
    
    # Relationships
    debit_account = relationship("LogicalAccount", foreign_keys=[debit_account_id], back_populates="debit_transactions")
    credit_account = relationship("LogicalAccount", foreign_keys=[credit_account_id], back_populates="credit_transactions")


class AllocationRule(Base):
    """Model for allocation rules"""
    __tablename__ = "allocation_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(255), unique=True, nullable=False)
    rule_description = Column(Text)
    source_account_id = Column(UUID(as_uuid=True), ForeignKey('logical_accounts.id'), nullable=False, index=True)
    allocation_logic = Column(JSONB, nullable=False)
    priority = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    effective_from = Column(DateTime(timezone=True), server_default=func.now())
    effective_to = Column(DateTime(timezone=True))
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(255))
    updated_by = Column(String(255))
    
    # Relationships
    source_account = relationship("LogicalAccount", back_populates="allocation_rules")


class AuditLog(Base):
    """Model for audit log - immutable"""
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), index=True)
    changes = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    metadata = Column(JSONB, default={})
    
    __table_args__ = (
        Index('idx_audit_entity_composite', 'entity_type', 'entity_id'),
    )


class ReconciliationLog(Base):
    """Model for reconciliation log"""
    __tablename__ = "reconciliation_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reconciliation_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey('logical_accounts.id'), nullable=False, index=True)
    reconciliation_type = Column(String(50), nullable=False)
    expected_balance = Column(Numeric(20, 2), nullable=False)
    actual_balance = Column(Numeric(20, 2), nullable=False)
    status = Column(String(20), nullable=False, default='pending', index=True)
    notes = Column(Text)
    reconciled_by = Column(String(255))
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'matched', 'unmatched', 'reviewed')", name='check_reconciliation_status'),
    )
    
    # Relationships
    account = relationship("LogicalAccount", back_populates="reconciliation_logs")
