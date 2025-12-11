"""Audit logging hooks."""

from typing import Optional, Any, Dict
from uuid import UUID
from fastapi import Request
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.models import AuditLog


class AuditHook:
    """Audit logging hook for tracking all database operations."""
    
    def __init__(self, db: Session, request: Optional[Request] = None):
        """
        Initialize audit hook.
        
        Args:
            db: Database session
            request: Optional FastAPI request for context
        """
        self.db = db
        self.request = request
    
    def log(
        self,
        table_name: str,
        record_id: UUID,
        action: str,
        user_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log an audit event.
        
        Args:
            table_name: Name of the table affected
            record_id: ID of the record affected
            action: Action performed (CREATE, UPDATE, DELETE, READ)
            user_id: User who performed the action
            changes: Dictionary of changes made
        
        Returns:
            Created audit log entry
        """
        # Extract request context if available
        ip_address = None
        user_agent = None
        
        if self.request:
            # Get IP address
            ip_address = self.request.client.host if self.request.client else None
            
            # Get user agent
            user_agent = self.request.headers.get("user-agent")
        
        # Create audit log entry
        audit_entry = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            user_id=user_id,
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(audit_entry)
        self.db.commit()
        
        return audit_entry
    
    def log_create(
        self,
        table_name: str,
        record_id: UUID,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log a CREATE action."""
        return self.log(
            table_name=table_name,
            record_id=record_id,
            action="CREATE",
            user_id=user_id,
            changes={"created": data} if data else None
        )
    
    def log_update(
        self,
        table_name: str,
        record_id: UUID,
        user_id: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log an UPDATE action."""
        changes = {}
        if old_data and new_data:
            changes = {
                "old": old_data,
                "new": new_data,
                "changed_fields": list(set(new_data.keys()) - set(old_data.keys()) | 
                                     {k for k in old_data.keys() if old_data.get(k) != new_data.get(k)})
            }
        
        return self.log(
            table_name=table_name,
            record_id=record_id,
            action="UPDATE",
            user_id=user_id,
            changes=changes
        )
    
    def log_delete(
        self,
        table_name: str,
        record_id: UUID,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log a DELETE action."""
        return self.log(
            table_name=table_name,
            record_id=record_id,
            action="DELETE",
            user_id=user_id,
            changes={"deleted": data} if data else None
        )
    
    def log_read(
        self,
        table_name: str,
        record_id: UUID,
        user_id: Optional[str] = None
    ) -> AuditLog:
        """Log a READ action (for sensitive data)."""
        return self.log(
            table_name=table_name,
            record_id=record_id,
            action="READ",
            user_id=user_id
        )


def get_audit_hook(db: Session, request: Optional[Request] = None) -> AuditHook:
    """
    Factory function to create audit hook.
    
    Args:
        db: Database session
        request: Optional FastAPI request
    
    Returns:
        AuditHook instance
    """
    return AuditHook(db, request)
