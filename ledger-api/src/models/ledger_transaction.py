"""Ledger Transaction Model"""
from sqlalchemy import Column, String, DECIMAL, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..db.session import Base


class LedgerTransaction(Base):
    """
    Ledger Transaction - All financial transactions
    
    Records deposits, withdrawals, transfers, allocations, and corrections.
    Supports parent-child relationships for allocation tracking.
    """
    __tablename__ = "ledger_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    type = Column(
        Text,
        nullable=False,
        index=True,
        comment="Transaction type: DEPOSIT, WITHDRAWAL, TRANSFER, ALLOCATION, CORRECTION"
    )
    amount = Column(DECIMAL(30, 12), nullable=False)
    currency = Column(Text, nullable=False, default="USD")
    status = Column(
        Text,
        nullable=False,
        default="PENDING",
        index=True,
        comment="Transaction status: PENDING, COMPLETED, FAILED, CANCELLED"
    )
    metadata = Column(JSONB, default={}, nullable=False)
    external_tx_hash = Column(Text, nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Foreign Keys
    logical_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("logical_accounts.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )
    parent_transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ledger_transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="References parent transaction for allocations"
    )

    # Relationships
    logical_account = relationship("LogicalAccount", back_populates="transactions", foreign_keys=[logical_account_id])
    parent_transaction = relationship("LedgerTransaction", remote_side=[id], foreign_keys=[parent_transaction_id])
    allocations = relationship("LedgerTransaction", remote_side=[parent_transaction_id], foreign_keys=[parent_transaction_id])

    def __repr__(self):
        return f"<LedgerTransaction(id={self.id}, type='{self.type}', amount={self.amount}, status='{self.status}')>"
