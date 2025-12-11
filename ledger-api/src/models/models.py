"""
SQLAlchemy models for Ledger API.
Defines database tables and relationships.
"""
from sqlalchemy import (
    Column, String, Text, Boolean, DECIMAL, 
    ForeignKey, CheckConstraint, Index, TIMESTAMP, Computed, TypeDecorator
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB, INET
from sqlalchemy.types import CHAR, TEXT
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid as uuid_lib
import json
from decimal import Decimal
from src.db.session import Base



# Cross-database type decorators
class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_GUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value) if isinstance(value, uuid_lib.UUID) else value
        else:
            if isinstance(value, uuid_lib.UUID):
                return str(value)
            else:
                return str(uuid_lib.UUID(value)) if value else None

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, uuid_lib.UUID):
                return value
            else:
                return uuid_lib.UUID(value)


class JSON(TypeDecorator):
    """Platform-independent JSON type.
    Uses PostgreSQL's JSONB type, otherwise uses TEXT, storing as JSON-encoded strings.
    """
    impl = TEXT
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_JSONB())
        else:
            return dialect.type_descriptor(TEXT())

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        else:
            if value is not None:
                # Custom JSON encoder to handle UUID and Decimal
                return json.dumps(value, default=self._json_serializer)
            return value

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        else:
            if value is not None:
                return json.loads(value)
            return value
    
    @staticmethod
    def _json_serializer(obj):
        """Custom JSON serializer for objects not serializable by default."""
        if isinstance(obj, uuid_lib.UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class LogicalAccount(Base):
    """Logical account model for different account types."""
    __tablename__ = "logical_accounts"
    
    id = Column(GUID(), primary_key=True, default=uuid_lib.uuid4)
    account_name = Column(String(255), nullable=False, unique=True)
    account_type = Column(String(50), nullable=False)
    description = Column(Text)
    extra_metadata = Column(JSON, default={})
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
    
    id = Column(GUID(), primary_key=True, default=uuid_lib.uuid4)
    transaction_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    account_id = Column(GUID(), ForeignKey("logical_accounts.id"), nullable=False)
    amount = Column(DECIMAL(20, 8), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    transaction_type = Column(String(50), nullable=False)
    reference_id = Column(String(255))
    description = Column(Text)
    extra_metadata = Column(JSON, default={})
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
    
    id = Column(GUID(), primary_key=True, default=uuid_lib.uuid4)
    rule_name = Column(String(255), nullable=False, unique=True)
    source_account_id = Column(GUID(), ForeignKey("logical_accounts.id"), nullable=False)
    allocation_config = Column(JSON, nullable=False)
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
    
    id = Column(GUID(), primary_key=True, default=uuid_lib.uuid4)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(GUID(), nullable=False)
    action = Column(String(50), nullable=False)
    user_id = Column(String(255))
    changes = Column(JSON)
    ip_address = Column(String(45))
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
    
    id = Column(GUID(), primary_key=True, default=uuid_lib.uuid4)
    account_id = Column(GUID(), ForeignKey("logical_accounts.id"), nullable=False)
    reconciliation_date = Column(TIMESTAMP(timezone=True), nullable=False)
    expected_balance = Column(DECIMAL(20, 8), nullable=False)
    actual_balance = Column(DECIMAL(20, 8), nullable=False)
    variance = Column(DECIMAL(20, 8), Computed('actual_balance - expected_balance'))
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


class WorkflowPatch(Base):
    """Workflow patch model for automated patch management."""
    __tablename__ = "workflow_patches"
    
    id = Column(GUID(), primary_key=True, default=uuid_lib.uuid4)
    patch_name = Column(String(255), nullable=False)
    patch_version = Column(String(50), nullable=False)
    patch_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    target_workflow = Column(String(255), nullable=False)
    issue_identified = Column(Text, nullable=False)
    patch_content = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default='pending')
    severity = Column(String(50), nullable=False)
    created_by = Column(String(255), default='WorkflowPatchAgent')
    reviewed_by = Column(String(255))
    approved_by = Column(String(255))
    test_results = Column(JSON)
    deployment_config = Column(JSON)
    rollback_config = Column(JSON)
    impact_report = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    tested_at = Column(TIMESTAMP(timezone=True))
    deployed_at = Column(TIMESTAMP(timezone=True))
    rolled_back_at = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        CheckConstraint(
            "patch_type IN ('bug_fix', 'performance', 'security', 'feature', 'refactor')",
            name="check_patch_type"
        ),
        CheckConstraint(
            "status IN ('pending', 'testing', 'tested', 'approved', 'deployed', 'failed', 'rolled_back')",
            name="check_patch_status"
        ),
        CheckConstraint(
            "severity IN ('critical', 'high', 'medium', 'low')",
            name="check_patch_severity"
        ),
        Index("idx_workflow_patches_status", "status"),
        Index("idx_workflow_patches_target_workflow", "target_workflow"),
        Index("idx_workflow_patches_created_at", "created_at"),
    )


class WorkflowAnalysis(Base):
    """Workflow analysis model for tracking workflow health and issues."""
    __tablename__ = "workflow_analysis"
    
    id = Column(GUID(), primary_key=True, default=uuid_lib.uuid4)
    workflow_name = Column(String(255), nullable=False)
    analysis_type = Column(String(50), nullable=False)
    findings = Column(JSON, nullable=False)
    metrics = Column(JSON)
    recommendations = Column(JSON)
    severity = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default='new')
    analyzed_by = Column(String(255), default='WorkflowPatchAgent')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    addressed_at = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        CheckConstraint(
            "analysis_type IN ('security', 'performance', 'efficiency', 'compatibility', 'quality')",
            name="check_analysis_type"
        ),
        CheckConstraint(
            "severity IN ('critical', 'high', 'medium', 'low', 'info')",
            name="check_analysis_severity"
        ),
        CheckConstraint(
            "status IN ('new', 'in_progress', 'addressed', 'ignored')",
            name="check_analysis_status"
        ),
        Index("idx_workflow_analysis_workflow_name", "workflow_name"),
        Index("idx_workflow_analysis_status", "status"),
        Index("idx_workflow_analysis_severity", "severity"),
    )
