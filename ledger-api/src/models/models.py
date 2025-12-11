from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class LogicalAccount(Base):
    """Logical account model for tracking balances."""
    __tablename__ = "logical_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    name = Column(String(255), nullable=False, unique=True)
    account_type = Column(String(50), nullable=False)
    balance = Column(Numeric(30, 12), nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="PI")
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))


class LedgerTransaction(Base):
    """Ledger transaction model for tracking all financial movements."""
    __tablename__ = "ledger_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Numeric(30, 12), nullable=False)
    currency = Column(String(10), nullable=False, default="PI")
    status = Column(String(50), nullable=False, default="PENDING")
    logical_account_id = Column(UUID(as_uuid=True), ForeignKey("logical_accounts.id"))
    parent_transaction_id = Column(UUID(as_uuid=True), ForeignKey("ledger_transactions.id"))
    metadata = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))


class AllocationRule(Base):
    """Allocation rule model for defining how funds are distributed."""
    __tablename__ = "allocation_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    name = Column(String(255), nullable=False)
    rule_data = Column(JSONB, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))


class AuditLog(Base):
    """Audit log model for tracking all system actions."""
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    action = Column(String(100), nullable=False)
    actor = Column(String(255), nullable=False)
    target_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))


class ReconciliationLog(Base):
    """Reconciliation log model for tracking balance verifications."""
    __tablename__ = "reconciliation_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    logical_account_id = Column(UUID(as_uuid=True), ForeignKey("logical_accounts.id"), nullable=False)
    ledger_balance = Column(Numeric(30, 12), nullable=False)
    external_balance = Column(Numeric(30, 12), nullable=False)
    discrepancy = Column(Numeric(30, 12), nullable=False)
    reconciled_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
