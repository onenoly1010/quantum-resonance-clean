"""
Pydantic schemas for request/response validation
Defines data transfer objects for API endpoints
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# Logical Account Schemas
class LogicalAccountBase(BaseModel):
    """Base schema for logical account"""
    account_code: str = Field(..., max_length=50)
    account_name: str = Field(..., max_length=255)
    account_type: str = Field(..., pattern="^(asset|liability|equity|revenue|expense)$")
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="active", pattern="^(active|inactive|archived)$")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class LogicalAccountCreate(LogicalAccountBase):
    """Schema for creating a logical account"""
    created_by: Optional[str] = None


class LogicalAccountUpdate(BaseModel):
    """Schema for updating a logical account"""
    account_name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, pattern="^(active|inactive|archived)$")
    metadata: Optional[Dict[str, Any]] = None
    updated_by: Optional[str] = None


class LogicalAccountResponse(LogicalAccountBase):
    """Schema for logical account response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True


# Ledger Transaction Schemas
class LedgerTransactionBase(BaseModel):
    """Base schema for ledger transaction"""
    transaction_ref: str = Field(..., max_length=100)
    transaction_date: Optional[datetime] = None
    description: str
    debit_account_id: UUID
    credit_account_id: UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="pending", pattern="^(pending|posted|reversed|cancelled)$")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('debit_account_id', 'credit_account_id')
    def validate_different_accounts(cls, v, values):
        """Ensure debit and credit accounts are different"""
        if 'debit_account_id' in values and v == values['debit_account_id']:
            raise ValueError('Debit and credit accounts must be different')
        return v


class LedgerTransactionCreate(LedgerTransactionBase):
    """Schema for creating a ledger transaction"""
    created_by: Optional[str] = None


class LedgerTransactionUpdate(BaseModel):
    """Schema for updating a ledger transaction"""
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|posted|reversed|cancelled)$")
    metadata: Optional[Dict[str, Any]] = None
    updated_by: Optional[str] = None


class LedgerTransactionResponse(LedgerTransactionBase):
    """Schema for ledger transaction response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True


# Allocation Rule Schemas
class AllocationDestination(BaseModel):
    """Schema for allocation destination in allocation logic"""
    destination_account_id: str
    percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    amount: Optional[Decimal] = Field(None, ge=0)
    
    @validator('percentage', 'amount')
    def validate_percentage_or_amount(cls, v, values):
        """Ensure either percentage or amount is provided, but not both"""
        if 'percentage' in values and values.get('percentage') and v:
            raise ValueError('Cannot specify both percentage and amount')
        return v


class AllocationRuleBase(BaseModel):
    """Base schema for allocation rule"""
    rule_name: str = Field(..., max_length=255)
    rule_description: Optional[str] = None
    source_account_id: UUID
    allocation_logic: List[AllocationDestination]
    priority: int = Field(default=0)
    is_active: bool = Field(default=True)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AllocationRuleCreate(AllocationRuleBase):
    """Schema for creating an allocation rule"""
    created_by: Optional[str] = None


class AllocationRuleUpdate(BaseModel):
    """Schema for updating an allocation rule"""
    rule_description: Optional[str] = None
    allocation_logic: Optional[List[AllocationDestination]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    effective_to: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    updated_by: Optional[str] = None


class AllocationRuleResponse(AllocationRuleBase):
    """Schema for allocation rule response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True


# Audit Log Schemas
class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry"""
    user_id: str
    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AuditLogResponse(AuditLogCreate):
    """Schema for audit log response"""
    id: UUID
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Reconciliation Log Schemas
class ReconciliationLogBase(BaseModel):
    """Base schema for reconciliation log"""
    account_id: UUID
    reconciliation_type: str
    expected_balance: Decimal = Field(..., decimal_places=2)
    actual_balance: Decimal = Field(..., decimal_places=2)
    status: str = Field(default="pending", pattern="^(pending|matched|unmatched|reviewed)$")
    notes: Optional[str] = None
    reconciled_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ReconciliationLogCreate(ReconciliationLogBase):
    """Schema for creating a reconciliation log entry"""
    pass


class ReconciliationLogUpdate(BaseModel):
    """Schema for updating a reconciliation log entry"""
    status: Optional[str] = Field(None, pattern="^(pending|matched|unmatched|reviewed)$")
    notes: Optional[str] = None
    reconciled_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ReconciliationLogResponse(ReconciliationLogBase):
    """Schema for reconciliation log response"""
    id: UUID
    reconciliation_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Account Balance Schema
class AccountBalanceResponse(BaseModel):
    """Schema for account balance response"""
    account_id: UUID
    account_code: str
    account_name: str
    account_type: str
    total_debits: Decimal
    total_credits: Decimal
    balance: Decimal
    
    class Config:
        from_attributes = True
