from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from decimal import Decimal
from uuid import UUID
from datetime import datetime


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    transaction_type: str
    amount: Decimal
    currency: str = "PI"
    status: str = "PENDING"
    logical_account_id: Optional[UUID] = None
    parent_transaction_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


class TransactionRead(BaseModel):
    """Schema for reading transaction data."""
    id: UUID
    transaction_type: str
    amount: Decimal
    currency: str
    status: str
    logical_account_id: Optional[UUID]
    parent_transaction_id: Optional[UUID]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class AllocationRuleItem(BaseModel):
    """Schema for a single allocation rule item."""
    logical_account_id: UUID
    percent: Decimal
    
    @validator('percent')
    def validate_percent(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Percent must be between 0 and 100')
        return v


class AllocationRuleCreate(BaseModel):
    """Schema for creating allocation rules."""
    name: str
    allocations: List[AllocationRuleItem]
    active: bool = True
    
    @validator('allocations')
    def validate_total_percent(cls, v):
        total = sum(item.percent for item in v)
        if total != 100:
            raise ValueError(f'Total percent must equal 100, got {total}')
        return v


class AllocationRuleRead(BaseModel):
    """Schema for reading allocation rule data."""
    id: UUID
    name: str
    rule_data: Dict[str, Any]
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class LogicalAccountRead(BaseModel):
    """Schema for reading logical account data."""
    id: UUID
    name: str
    account_type: str
    balance: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class ReconciliationCreate(BaseModel):
    """Schema for creating a reconciliation."""
    logical_account_id: UUID
    external_balance: Decimal


class ReconciliationRead(BaseModel):
    """Schema for reading reconciliation data."""
    id: UUID
    logical_account_id: UUID
    ledger_balance: Decimal
    external_balance: Decimal
    discrepancy: Decimal
    reconciled_at: datetime
    
    class Config:
        orm_mode = True
