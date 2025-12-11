"""
Audit logging hooks for tracking all system changes.
"""
from fastapi import Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID
from src.models.models import AuditLog


class AuditLogger:
    """Helper class for creating audit log entries."""
    
    @staticmethod
    def log_action(
        db: Session,
        entity_type: str,
        entity_id: UUID,
        action: str,
        user_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Create an audit log entry.
        
        Args:
            db: Database session
            entity_type: Type of entity (e.g., 'LogicalAccount', 'LedgerTransaction')
            entity_id: UUID of the entity
            action: Action performed ('create', 'update', 'delete', 'read')
            user_id: Optional user ID performing the action
            changes: Optional dictionary of changes made
            request: Optional FastAPI request object for IP and user agent
            
        Returns:
            Created audit log entry
        """
        ip_address = None
        user_agent = None
        
        if request:
            # Get client IP address
            if hasattr(request, 'client') and request.client:
                ip_address = request.client.host
            
            # Get user agent
            user_agent = request.headers.get('user-agent')
        
        audit_entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        
        return audit_entry
    
    @staticmethod
    def log_create(
        db: Session,
        entity_type: str,
        entity_id: UUID,
        entity_data: Dict[str, Any],
        user_id: Optional[str] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log entity creation."""
        return AuditLogger.log_action(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            action="create",
            user_id=user_id,
            changes={"created": entity_data},
            request=request
        )
    
    @staticmethod
    def log_update(
        db: Session,
        entity_type: str,
        entity_id: UUID,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        user_id: Optional[str] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log entity update."""
        changes = {
            "old": old_data,
            "new": new_data
        }
        
        return AuditLogger.log_action(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            action="update",
            user_id=user_id,
            changes=changes,
            request=request
        )
    
    @staticmethod
    def log_delete(
        db: Session,
        entity_type: str,
        entity_id: UUID,
        entity_data: Dict[str, Any],
        user_id: Optional[str] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log entity deletion."""
        return AuditLogger.log_action(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            action="delete",
            user_id=user_id,
            changes={"deleted": entity_data},
            request=request
        )
    
    @staticmethod
    def log_read(
        db: Session,
        entity_type: str,
        entity_id: UUID,
        user_id: Optional[str] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log entity read access (for sensitive data)."""
        return AuditLogger.log_action(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            action="read",
            user_id=user_id,
            request=request
        )
