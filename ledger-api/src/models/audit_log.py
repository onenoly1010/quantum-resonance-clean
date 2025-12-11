"""Audit Log Model"""
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from ..db.session import Base


class AuditLog(Base):
    """
    Audit Log - Comprehensive audit trail
    
    Records all operations for compliance, debugging, and security monitoring.
    Tracks who did what, when, and to which resource.
    """
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(Text, nullable=False, index=True)
    actor = Column(Text, nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    target_type = Column(Text, nullable=True, index=True)
    audit_details = Column("details", JSON().with_variant(JSONB, "postgresql"), default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    ip_address = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', actor='{self.actor}', created_at={self.created_at})>"
