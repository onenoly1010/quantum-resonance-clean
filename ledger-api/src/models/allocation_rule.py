"""Allocation Rule Model"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from ..db.session import Base


class AllocationRule(Base):
    """
    Allocation Rule - Automatic transaction splitting configuration
    
    Defines rules for how transactions should be split across multiple accounts.
    Rules are stored as JSONB array: [{"destination_account_id": "uuid", "percentage": 60.0, "description": "..."}]
    """
    __tablename__ = "allocation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, unique=True, index=True)
    rules = Column(
        JSONB,
        nullable=False,
        comment="JSONB array of allocation rules with destination_account_id, percentage, and description"
    )
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<AllocationRule(id={self.id}, name='{self.name}', active={self.active})>"
