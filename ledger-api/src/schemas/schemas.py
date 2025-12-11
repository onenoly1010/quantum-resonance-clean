"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# Logical Account Schemas
class LogicalAccountBase(BaseModel):
    """Base schema for logical account."""
    account_name: str = Field(..., max_length=255)
    account_type: str = Field(..., pattern="^(asset|liability|equity|revenue|expense)$")
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class LogicalAccountCreate(LogicalAccountBase):
    """Schema for creating a logical account."""
    pass


class LogicalAccountUpdate(BaseModel):
    """Schema for updating a logical account."""
    account_name: Optional[str] = Field(None, max_length=255)
    account_type: Optional[str] = Field(None, pattern="^(asset|liability|equity|revenue|expense)$")
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class LogicalAccountResponse(LogicalAccountBase):
    """Schema for logical account response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Ledger Transaction Schemas
class LedgerTransactionBase(BaseModel):
    """Base schema for ledger transaction."""
    account_id: UUID
    amount: Decimal = Field(..., max_digits=20, decimal_places=8)
    currency: str = Field(default="USD", max_length=10)
    transaction_type: str = Field(..., pattern="^(debit|credit)$")
    reference_id: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LedgerTransactionCreate(LedgerTransactionBase):
    """Schema for creating a ledger transaction."""
    transaction_date: Optional[datetime] = None


class LedgerTransactionResponse(LedgerTransactionBase):
    """Schema for ledger transaction response."""
    id: UUID
    transaction_date: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Allocation Rule Schemas
class AllocationConfig(BaseModel):
    """Schema for allocation configuration item."""
    destination_account_id: UUID
    percentage: Decimal = Field(..., max_digits=5, decimal_places=2, ge=0, le=100)
    priority: int = Field(..., ge=1)


class AllocationRuleBase(BaseModel):
    """Base schema for allocation rule."""
    rule_name: str = Field(..., max_length=255)
    source_account_id: UUID
    allocation_config: List[AllocationConfig]
    is_active: bool = True
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class AllocationRuleCreate(AllocationRuleBase):
    """Schema for creating an allocation rule."""
    pass


class AllocationRuleUpdate(BaseModel):
    """Schema for updating an allocation rule."""
    rule_name: Optional[str] = Field(None, max_length=255)
    allocation_config: Optional[List[AllocationConfig]] = None
    is_active: Optional[bool] = None
    effective_to: Optional[datetime] = None


class AllocationRuleResponse(AllocationRuleBase):
    """Schema for allocation rule response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Audit Log Schemas
class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""
    entity_type: str = Field(..., max_length=100)
    entity_id: UUID
    action: str = Field(..., pattern="^(create|update|delete|read)$")
    user_id: Optional[str] = Field(None, max_length=255)
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogResponse(AuditLogCreate):
    """Schema for audit log response."""
    id: UUID
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Reconciliation Log Schemas
class ReconciliationLogBase(BaseModel):
    """Base schema for reconciliation log."""
    account_id: UUID
    reconciliation_date: datetime
    expected_balance: Decimal = Field(..., max_digits=20, decimal_places=8)
    actual_balance: Decimal = Field(..., max_digits=20, decimal_places=8)
    status: str = Field(..., pattern="^(pending|matched|variance|resolved)$")
    notes: Optional[str] = None
    reconciled_by: Optional[str] = Field(None, max_length=255)


class ReconciliationLogCreate(ReconciliationLogBase):
    """Schema for creating a reconciliation log."""
    pass


class ReconciliationLogUpdate(BaseModel):
    """Schema for updating a reconciliation log."""
    status: Optional[str] = Field(None, pattern="^(pending|matched|variance|resolved)$")
    notes: Optional[str] = None
    resolved_at: Optional[datetime] = None


class ReconciliationLogResponse(ReconciliationLogBase):
    """Schema for reconciliation log response."""
    id: UUID
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Balance Response Schema
class AccountBalanceResponse(BaseModel):
    """Schema for account balance response."""
    account_id: UUID
    account_name: str
    balance: Decimal
    currency: str = "USD"
    last_transaction_date: Optional[datetime] = None
