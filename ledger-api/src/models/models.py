"""SQLAlchemy models for Ledger API"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Numeric, DateTime, Text,
    ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.session import Base


class LogicalAccount(Base):
    """Chart of accounts for the ledger system"""
    
    __tablename__ = "logical_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(100), unique=True, nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)
    parent_account_id = Column(String(100), ForeignKey("logical_accounts.account_id", ondelete="SET NULL"))
    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = relationship("LedgerTransaction", back_populates="account")
    allocation_rules = relationship("AllocationRule", back_populates="source_account")
    
    __table_args__ = (
        CheckConstraint(
            "account_type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')",
            name="check_account_type"
        ),
        Index("idx_logical_accounts_type", "account_type"),
        Index("idx_logical_accounts_parent", "parent_account_id"),
    )


class LedgerTransaction(Base):
    """All ledger transactions with double-entry bookkeeping"""
    
    __tablename__ = "ledger_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    account_id = Column(String(100), ForeignKey("logical_accounts.account_id", ondelete="RESTRICT"), nullable=False)
    transaction_type = Column(String(10), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    currency = Column(String(10), default="USD")
    description = Column(Text)
    reference_id = Column(String(100), index=True)
    batch_id = Column(String(100), index=True)
    source_system = Column(String(50))
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    created_by = Column(String(100))
    
    # Relationships
    account = relationship("LogicalAccount", back_populates="transactions")
    
    __table_args__ = (
        CheckConstraint("transaction_type IN ('DEBIT', 'CREDIT')", name="check_transaction_type"),
        CheckConstraint("amount >= 0", name="check_amount_positive"),
    )


class AllocationRule(Base):
    """Automated allocation rules configuration"""
    
    __tablename__ = "allocation_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(100), unique=True, nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    source_account_id = Column(String(100), ForeignKey("logical_accounts.account_id", ondelete="RESTRICT"), nullable=False)
    allocation_config = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=0, index=True)
    effective_from = Column(DateTime(timezone=True), default=datetime.utcnow)
    effective_to = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    
    # Relationships
    source_account = relationship("LogicalAccount", back_populates="allocation_rules")


class AuditLog(Base):
    """Complete audit trail of all system changes"""
    
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String(100), unique=True, nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False, index=True)
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    changed_by = Column(String(100), index=True)
    changed_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    metadata = Column(JSONB, default={})
    
    __table_args__ = (
        Index("idx_audit_log_entity", "entity_type", "entity_id"),
    )


class ReconciliationLog(Base):
    """Reconciliation history and results"""
    
    __tablename__ = "reconciliation_log"
    
    id = Column(Integer, primary_key=True, index=True)
    reconciliation_id = Column(String(100), unique=True, nullable=False, index=True)
    reconciliation_type = Column(String(50), nullable=False)
    account_id = Column(String(100), ForeignKey("logical_accounts.account_id", ondelete="SET NULL"))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    total_records = Column(Integer, default=0)
    matched_records = Column(Integer, default=0)
    unmatched_records = Column(Integer, default=0)
    discrepancies = Column(JSONB, default=[])
    error_message = Column(Text)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    __table_args__ = (
        CheckConstraint("status IN ('SUCCESS', 'FAILED', 'PARTIAL')", name="check_status"),
    )
