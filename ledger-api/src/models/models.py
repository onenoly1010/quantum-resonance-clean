from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, TIMESTAMP, text, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid as uuid_lib

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses String(36), storing as stringified hex values.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid_lib.UUID):
                return str(uuid_lib.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid_lib.UUID):
                value = uuid_lib.UUID(value)
            return value


class JSON(TypeDecorator):
    """Platform-independent JSON type.
    Uses PostgreSQL's JSONB type, otherwise uses String, storing as JSON text.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB)
        else:
            import json
            # For SQLite, use TEXT
            from sqlalchemy import Text
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            import json
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            import json
            return json.loads(value)


class LogicalAccount(Base):
    """Logical account model for tracking balances."""
    __tablename__ = "logical_accounts"
    
    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    account_type = Column(String(50), nullable=False)
    balance = Column(Numeric(30, 12), nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="PI")
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class LedgerTransaction(Base):
    """Ledger transaction model for tracking all financial movements."""
    __tablename__ = "ledger_transactions"
    
    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Numeric(30, 12), nullable=False)
    currency = Column(String(10), nullable=False, default="PI")
    status = Column(String(50), nullable=False, default="PENDING")
    logical_account_id = Column(GUID, ForeignKey("logical_accounts.id"))
    parent_transaction_id = Column(GUID, ForeignKey("ledger_transactions.id"))
    tx_metadata = Column("metadata", JSON)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AllocationRule(Base):
    """Allocation rule model for defining how funds are distributed."""
    __tablename__ = "allocation_rules"
    
    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4)
    name = Column(String(255), nullable=False)
    rule_data = Column(JSON, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Audit log model for tracking all system actions."""
    __tablename__ = "audit_log"
    
    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4)
    action = Column(String(100), nullable=False)
    actor = Column(String(255), nullable=False)
    target_id = Column(GUID)
    details = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)


class ReconciliationLog(Base):
    """Reconciliation log model for tracking balance verifications."""
    __tablename__ = "reconciliation_log"
    
    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4)
    logical_account_id = Column(GUID, ForeignKey("logical_accounts.id"), nullable=False)
    ledger_balance = Column(Numeric(30, 12), nullable=False)
    external_balance = Column(Numeric(30, 12), nullable=False)
    discrepancy = Column(Numeric(30, 12), nullable=False)
    reconciled_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
