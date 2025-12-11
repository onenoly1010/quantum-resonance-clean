from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import AuditLog
from typing import Optional, Dict, Any
import uuid


async def write_audit(
    session: AsyncSession,
    action: str,
    actor: str,
    target_id: Optional[uuid.UUID] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Write an audit log entry.
    
    Args:
        session: Database session
        action: Action being performed (e.g., "CREATE_TRANSACTION")
        actor: Actor performing the action (username or system)
        target_id: Optional ID of the target resource
        details: Optional additional details as JSONB
        
    Returns:
        Created AuditLog entry
    """
    audit_entry = AuditLog(
        action=action,
        actor=actor,
        target_id=target_id,
        details=details
    )
    
    session.add(audit_entry)
    await session.flush()
    
    return audit_entry
