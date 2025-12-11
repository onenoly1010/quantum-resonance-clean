"""Reconciliation Log Model"""
from sqlalchemy import Column, String, DECIMAL, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..db.session import Base


class ReconciliationLog(Base):
    """
    Reconciliation Log - External vs Internal balance tracking
    
    Compares ledger balances with external sources (e.g., blockchain, banks).
    Tracks discrepancies and their resolution.
    """
    __tablename__ = "reconciliation_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    logical_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("logical_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    external_balance = Column(DECIMAL(30, 12), nullable=False)
    internal_balance = Column(DECIMAL(30, 12), nullable=False)
    discrepancy = Column(DECIMAL(30, 12), nullable=False, comment="Calculated as external_balance - internal_balance")
    currency = Column(Text, nullable=False, default="USD")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    correction_transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ledger_transactions.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    logical_account = relationship("LogicalAccount", back_populates="reconciliations")
    correction_transaction = relationship("LedgerTransaction", foreign_keys=[correction_transaction_id])

    def __repr__(self):
        return f"<ReconciliationLog(id={self.id}, account_id={self.logical_account_id}, discrepancy={self.discrepancy}, resolved={self.resolved})>"
