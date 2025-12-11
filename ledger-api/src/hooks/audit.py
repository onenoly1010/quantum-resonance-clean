"""
Audit Logging Hook

Provides utilities to write audit log entries for CRUD operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import uuid
from fastapi import Request

from ..models.audit_log import AuditLog
from ..deps.auth import TokenPayload


class AuditLogger:
    """
    Audit Logger - Records operations for compliance and debugging
    
    Features:
    - Automatic actor extraction from JWT
    - Captures IP address and user agent
    - Stores operation details as JSONB
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        actor: str,
        target_id: Optional[uuid.UUID] = None,
        target_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry
        
        Args:
            action: Action performed (e.g., "CREATE_TRANSACTION", "UPDATE_ALLOCATION_RULE")
            actor: User or system performing the action
            target_id: Optional UUID of the target resource
            target_type: Optional type of the target resource
            details: Optional additional details as dictionary
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            
        Returns:
            Created AuditLog entry
        """
        audit_entry = AuditLog(
            action=action,
            actor=actor,
            target_id=target_id,
            target_type=target_type,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        self.db.add(audit_entry)
        await self.db.flush()
        
        return audit_entry

    async def log_from_request(
        self,
        action: str,
        request: Request,
        user: Optional[TokenPayload] = None,
        target_id: Optional[uuid.UUID] = None,
        target_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Create audit log entry from FastAPI request
        
        Args:
            action: Action performed
            request: FastAPI Request object
            user: Optional authenticated user
            target_id: Optional target resource ID
            target_type: Optional target resource type
            details: Optional additional details
            
        Returns:
            Created AuditLog entry
        """
        actor = user.sub if user else "anonymous"
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        return await self.log(
            action=action,
            actor=actor,
            target_id=target_id,
            target_type=target_type,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )


async def get_audit_logger(db: AsyncSession) -> AuditLogger:
    """
    Dependency to get audit logger
    
    Usage:
        @app.post("/items")
        async def create_item(
            db: AsyncSession = Depends(get_db),
            audit: AuditLogger = Depends(get_audit_logger),
            user: TokenPayload = Depends(get_current_user)
        ):
            item = create_item_logic()
            await audit.log("CREATE_ITEM", user.sub, target_id=item.id, target_type="item")
            return item
    """
    return AuditLogger(db)


# Common audit action constants
class AuditAction:
    """Common audit action names"""
    
    # Transaction actions
    CREATE_TRANSACTION = "CREATE_TRANSACTION"
    UPDATE_TRANSACTION = "UPDATE_TRANSACTION"
    DELETE_TRANSACTION = "DELETE_TRANSACTION"
    
    # Account actions
    CREATE_ACCOUNT = "CREATE_ACCOUNT"
    UPDATE_ACCOUNT = "UPDATE_ACCOUNT"
    DELETE_ACCOUNT = "DELETE_ACCOUNT"
    
    # Allocation rule actions
    CREATE_ALLOCATION_RULE = "CREATE_ALLOCATION_RULE"
    UPDATE_ALLOCATION_RULE = "UPDATE_ALLOCATION_RULE"
    DELETE_ALLOCATION_RULE = "DELETE_ALLOCATION_RULE"
    ACTIVATE_ALLOCATION_RULE = "ACTIVATE_ALLOCATION_RULE"
    DEACTIVATE_ALLOCATION_RULE = "DEACTIVATE_ALLOCATION_RULE"
    
    # Reconciliation actions
    CREATE_RECONCILIATION = "CREATE_RECONCILIATION"
    RESOLVE_RECONCILIATION = "RESOLVE_RECONCILIATION"
    CREATE_CORRECTION = "CREATE_CORRECTION"
    
    # System actions
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    FAILED_AUTH = "FAILED_AUTH"
