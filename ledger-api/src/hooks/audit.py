"""Audit hooks for tracking changes"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import uuid
from datetime import datetime, timezone

from models.models import AuditLog


class AuditHook:
    """Hook for creating audit log entries"""
    
    @staticmethod
    def log_change(
        db: Session,
        entity_type: str,
        entity_id: str,
        action: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        changed_by: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log a change to the audit log.
        
        Args:
            db: Database session
            entity_type: Type of entity being changed (e.g., "transaction", "account")
            entity_id: ID of the entity
            action: Action performed (e.g., "CREATE", "UPDATE", "DELETE")
            old_value: Previous value (for updates/deletes)
            new_value: New value (for creates/updates)
            changed_by: User who made the change
            ip_address: IP address of the user
            user_agent: User agent string
            metadata: Additional metadata
            
        Returns:
            Created AuditLog entry
        """
        audit_entry = AuditLog(
            audit_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            changed_at=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        
        return audit_entry
    
    @staticmethod
    def log_transaction_create(
        db: Session,
        transaction_id: str,
        transaction_data: Dict[str, Any],
        created_by: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Log creation of a ledger transaction.
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            transaction_data: Transaction data
            created_by: User who created the transaction
            ip_address: IP address of the user
            
        Returns:
            Created AuditLog entry
        """
        return AuditHook.log_change(
            db=db,
            entity_type="transaction",
            entity_id=transaction_id,
            action="CREATE",
            new_value=transaction_data,
            changed_by=created_by,
            ip_address=ip_address,
            metadata={"source": "ledger_api"}
        )
    
    @staticmethod
    def log_allocation_rule_change(
        db: Session,
        rule_id: str,
        action: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        changed_by: Optional[str] = None
    ) -> AuditLog:
        """
        Log changes to allocation rules.
        
        Args:
            db: Database session
            rule_id: Rule ID
            action: Action performed
            old_value: Previous value
            new_value: New value
            changed_by: User who made the change
            
        Returns:
            Created AuditLog entry
        """
        return AuditHook.log_change(
            db=db,
            entity_type="allocation_rule",
            entity_id=rule_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            metadata={"source": "ledger_api"}
        )
    
    @staticmethod
    def log_account_change(
        db: Session,
        account_id: str,
        action: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        changed_by: Optional[str] = None
    ) -> AuditLog:
        """
        Log changes to accounts.
        
        Args:
            db: Database session
            account_id: Account ID
            action: Action performed
            old_value: Previous value
            new_value: New value
            changed_by: User who made the change
            
        Returns:
            Created AuditLog entry
        """
        return AuditHook.log_change(
            db=db,
            entity_type="account",
            entity_id=account_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            metadata={"source": "ledger_api"}
        )


def obfuscate_sensitive_data(data: Dict[str, Any], sensitive_fields: list = None) -> Dict[str, Any]:
    """
    Obfuscate sensitive fields in data before logging.
    
    Args:
        data: Data to obfuscate
        sensitive_fields: List of field names to obfuscate
        
    Returns:
        Data with obfuscated sensitive fields
    """
    if sensitive_fields is None:
        sensitive_fields = ["wallet_address", "private_key", "secret", "password", "token"]
    
    obfuscated = data.copy()
    for field in sensitive_fields:
        if field in obfuscated and obfuscated[field]:
            value = str(obfuscated[field])
            if len(value) > 8:
                # Keep first 4 and last 3 characters, obfuscate the rest
                obfuscated[field] = f"{value[:4]}...{value[-3:]}"
            else:
                obfuscated[field] = "***"
    
    return obfuscated
