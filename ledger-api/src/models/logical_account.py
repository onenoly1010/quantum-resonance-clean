"""Logical Account Model"""
from sqlalchemy import Column, String, DECIMAL, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..db.session import Base


class LogicalAccount(Base):
    """
    Logical Account - Abstract account categories
    
    Represents categories like Treasury, Operations, Development, Reserve, etc.
    Tracks aggregate balance for all transactions in the account.
    """
    __tablename__ = "logical_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, unique=True, index=True)
    type = Column(
        Text, 
        nullable=False,
        index=True,
        comment="Account type: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE"
    )
    metadata = Column(JSONB, default={}, nullable=False)
    balance = Column(DECIMAL(30, 12), default=0, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    transactions = relationship("LedgerTransaction", back_populates="logical_account", foreign_keys="LedgerTransaction.logical_account_id")
    reconciliations = relationship("ReconciliationLog", back_populates="logical_account")

    def __repr__(self):
        return f"<LogicalAccount(id={self.id}, name='{self.name}', type='{self.type}', balance={self.balance})>"
