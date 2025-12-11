"""
Audit logging hooks
Provides automatic audit logging for operations
"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from models.models import AuditLog
from fastapi import Request
import logging

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logging utility"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        changes: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Create an audit log entry
        
        Args:
            user_id: User performing the action
            action: Action performed (e.g., 'create', 'update', 'delete')
            entity_type: Type of entity (e.g., 'transaction', 'account')
            entity_id: ID of the affected entity
            changes: Dictionary of changes made
            request: FastAPI request object (for IP and user agent)
            metadata: Additional metadata
            
        Returns:
            Created audit log entry
        """
        # Extract request information
        ip_address = None
        user_agent = None
        
        if request:
            # Get client IP
            if hasattr(request, 'client') and request.client:
                ip_address = request.client.host
            
            # Get user agent
            user_agent = request.headers.get('user-agent')
        
        # Create audit log entry
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        self.db.add(audit_entry)
        self.db.commit()
        
        logger.info(
            f"Audit log created: user={user_id}, action={action}, "
            f"entity_type={entity_type}, entity_id={entity_id}"
        )
        
        return audit_entry
    
    def log_create(
        self,
        user_id: str,
        entity_type: str,
        entity_id: UUID,
        entity_data: Dict[str, Any],
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log a create operation"""
        return self.log(
            user_id=user_id,
            action="create",
            entity_type=entity_type,
            entity_id=entity_id,
            changes={"created": entity_data},
            request=request
        )
    
    def log_update(
        self,
        user_id: str,
        entity_type: str,
        entity_id: UUID,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log an update operation"""
        # Calculate what changed
        changes = {
            "before": old_data,
            "after": new_data
        }
        
        return self.log(
            user_id=user_id,
            action="update",
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            request=request
        )
    
    def log_delete(
        self,
        user_id: str,
        entity_type: str,
        entity_id: UUID,
        entity_data: Dict[str, Any],
        request: Optional[Request] = None
    ) -> AuditLog:
        """Log a delete operation"""
        return self.log(
            user_id=user_id,
            action="delete",
            entity_type=entity_type,
            entity_id=entity_id,
            changes={"deleted": entity_data},
            request=request
        )
    
    def log_read(
        self,
        user_id: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        request: Optional[Request] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log a read operation"""
        return self.log(
            user_id=user_id,
            action="read",
            entity_type=entity_type,
            entity_id=entity_id,
            request=request,
            metadata=metadata
        )


def get_audit_logger(db: Session) -> AuditLogger:
    """
    Dependency to get audit logger instance
    
    Usage: audit_logger: AuditLogger = Depends(get_audit_logger)
    """
    return AuditLogger(db)
