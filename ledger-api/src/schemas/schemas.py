"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ============= Account Schemas =============

class AccountBase(BaseModel):
    """Base schema for account"""
    account_id: str = Field(..., max_length=100)
    account_name: str = Field(..., max_length=255)
    account_type: str = Field(..., pattern="^(ASSET|LIABILITY|EQUITY|REVENUE|EXPENSE)$")
    parent_account_id: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AccountCreate(AccountBase):
    """Schema for creating an account"""
    pass


class AccountUpdate(BaseModel):
    """Schema for updating an account"""
    account_name: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class AccountResponse(AccountBase):
    """Schema for account response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= Transaction Schemas =============

class TransactionBase(BaseModel):
    """Base schema for transaction"""
    account_id: str = Field(..., max_length=100)
    transaction_type: str = Field(..., pattern="^(DEBIT|CREDIT)$")
    amount: Decimal = Field(..., ge=0, decimal_places=8)
    currency: str = Field(default="USD", max_length=10)
    description: Optional[str] = None
    reference_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction"""
    pass


class DoubleEntryTransactionCreate(BaseModel):
    """Schema for creating a double-entry transaction"""
    debit_account_id: str
    credit_account_id: str
    amount: Decimal = Field(..., ge=0, decimal_places=8)
    currency: str = Field(default="USD", max_length=10)
    description: Optional[str] = None
    reference_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TransactionResponse(TransactionBase):
    """Schema for transaction response"""
    id: int
    transaction_id: str
    batch_id: Optional[str] = None
    source_system: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============= Allocation Rule Schemas =============

class AllocationDestination(BaseModel):
    """Schema for allocation destination"""
    destination_account_id: str
    percentage: float = Field(..., ge=0, le=100)
    condition: Optional[str] = None


class AllocationRuleBase(BaseModel):
    """Base schema for allocation rule"""
    rule_name: str = Field(..., max_length=255)
    source_account_id: str = Field(..., max_length=100)
    allocation_config: List[AllocationDestination]
    is_active: bool = True
    priority: int = Field(default=0)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    
    @field_validator('allocation_config')
    @classmethod
    def validate_total_percentage(cls, v):
        """Validate that total percentage equals 100"""
        total = sum(dest.percentage for dest in v)
        if abs(total - 100.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Total allocation percentage must equal 100%, got {total}%")
        return v


class AllocationRuleCreate(AllocationRuleBase):
    """Schema for creating allocation rule"""
    pass


class AllocationRuleUpdate(BaseModel):
    """Schema for updating allocation rule"""
    rule_name: Optional[str] = None
    allocation_config: Optional[List[AllocationDestination]] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    effective_to: Optional[datetime] = None


class AllocationRuleResponse(AllocationRuleBase):
    """Schema for allocation rule response"""
    id: int
    rule_id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============= Treasury Schemas =============

class TreasuryBalanceResponse(BaseModel):
    """Schema for treasury balance response"""
    account_id: str
    account_name: str
    balance: Decimal
    currency: str
    last_updated: datetime


class AllocationRequest(BaseModel):
    """Schema for allocation request"""
    amount: Decimal = Field(..., ge=0, decimal_places=8)
    source_account_id: str
    rule_id: Optional[str] = None
    description: Optional[str] = None


class AllocationResponse(BaseModel):
    """Schema for allocation response"""
    batch_id: str
    source_account_id: str
    total_amount: Decimal
    allocations: List[Dict[str, Any]]
    created_at: datetime


# ============= Reconciliation Schemas =============

class ReconciliationResponse(BaseModel):
    """Schema for reconciliation response"""
    reconciliation_id: str
    reconciliation_type: str
    account_id: Optional[str]
    start_time: datetime
    end_time: datetime
    status: str
    total_records: int
    matched_records: int
    unmatched_records: int
    discrepancies: List[Dict[str, Any]]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


# ============= Audit Schemas =============

class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    audit_id: str
    entity_type: str
    entity_id: str
    action: str
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    changed_by: Optional[str]
    changed_at: datetime
    
    class Config:
        from_attributes = True
