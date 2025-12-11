"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


# Account Schemas
class AccountBase(BaseModel):
    """Base account schema."""
    account_code: str = Field(..., min_length=1, max_length=50)
    account_name: str = Field(..., min_length=1, max_length=255)
    account_type: str = Field(..., pattern="^(ASSET|LIABILITY|EQUITY|REVENUE|EXPENSE)$")
    parent_account_id: Optional[UUID] = None
    currency: str = Field(default="USD", max_length=3)
    metadata: dict = Field(default_factory=dict)


class AccountCreate(AccountBase):
    """Schema for creating an account."""
    pass


class AccountUpdate(BaseModel):
    """Schema for updating an account."""
    account_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class AccountResponse(AccountBase):
    """Schema for account response."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionLineBase(BaseModel):
    """Base transaction line schema."""
    account_id: UUID
    line_type: str = Field(..., pattern="^(DEBIT|CREDIT)$")
    amount: Decimal = Field(..., ge=0, decimal_places=4)
    currency: str = Field(default="USD", max_length=3)
    description: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class TransactionLineCreate(TransactionLineBase):
    """Schema for creating a transaction line."""
    pass


class TransactionLineResponse(TransactionLineBase):
    """Schema for transaction line response."""
    id: UUID
    transaction_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    """Base transaction schema."""
    transaction_date: date
    description: Optional[str] = None
    reference_number: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    lines: List[TransactionLineCreate] = Field(..., min_length=2)
    
    @field_validator('lines')
    @classmethod
    def validate_balanced_transaction(cls, lines: List[TransactionLineCreate]) -> List[TransactionLineCreate]:
        """Validate that debits equal credits."""
        total_debits = sum(line.amount for line in lines if line.line_type == "DEBIT")
        total_credits = sum(line.amount for line in lines if line.line_type == "CREDIT")
        
        if total_debits != total_credits:
            raise ValueError(
                f"Transaction must be balanced: debits={total_debits}, credits={total_credits}"
            )
        
        return lines


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(PENDING|POSTED|VOID|RECONCILED)$")
    metadata: Optional[dict] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    id: UUID
    transaction_number: str
    status: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    posted_at: Optional[datetime]
    lines: List[TransactionLineResponse] = []
    
    class Config:
        from_attributes = True


# Allocation Rule Schemas
class AllocationRuleItem(BaseModel):
    """Single allocation rule item."""
    destination_account_id: str = Field(..., description="Destination account ID")
    percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Allocation percentage")
    amount: Optional[Decimal] = Field(None, ge=0, description="Fixed allocation amount")
    priority: int = Field(default=1, ge=1, description="Priority order")
    
    @field_validator('percentage', 'amount')
    @classmethod
    def validate_allocation_method(cls, v, info):
        """Ensure either percentage or amount is provided, not both."""
        values = info.data
        percentage = values.get('percentage')
        amount = values.get('amount')
        
        if percentage is None and amount is None:
            raise ValueError("Either percentage or amount must be provided")
        if percentage is not None and amount is not None:
            raise ValueError("Only one of percentage or amount can be provided")
        
        return v


class AllocationRuleBase(BaseModel):
    """Base allocation rule schema."""
    rule_name: str = Field(..., min_length=1, max_length=255)
    source_account_id: Optional[UUID] = None
    rules: List[AllocationRuleItem] = Field(..., min_length=1)
    priority: int = Field(default=0, ge=0)
    metadata: dict = Field(default_factory=dict)


class AllocationRuleCreate(AllocationRuleBase):
    """Schema for creating an allocation rule."""
    pass


class AllocationRuleUpdate(BaseModel):
    """Schema for updating an allocation rule."""
    rule_name: Optional[str] = Field(None, min_length=1, max_length=255)
    rules: Optional[List[AllocationRuleItem]] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)
    metadata: Optional[dict] = None


class AllocationRuleResponse(AllocationRuleBase):
    """Schema for allocation rule response."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


# Treasury Account Schemas
class TreasuryAccountBase(BaseModel):
    """Base treasury account schema."""
    account_id: UUID
    treasury_type: str = Field(..., pattern="^(MAIN|RESERVE|OPERATIONAL|ESCROW)$")
    currency: str = Field(default="USD", max_length=3)
    metadata: dict = Field(default_factory=dict)


class TreasuryAccountCreate(TreasuryAccountBase):
    """Schema for creating a treasury account."""
    pass


class TreasuryAccountUpdate(BaseModel):
    """Schema for updating a treasury account."""
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class TreasuryAccountResponse(TreasuryAccountBase):
    """Schema for treasury account response."""
    id: UUID
    balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Reconciliation Schemas
class ReconciliationBase(BaseModel):
    """Base reconciliation schema."""
    account_id: UUID
    reconciliation_date: date
    statement_balance: Decimal = Field(..., decimal_places=4)
    ledger_balance: Decimal = Field(..., decimal_places=4)
    notes: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class ReconciliationCreate(ReconciliationBase):
    """Schema for creating a reconciliation."""
    pass


class ReconciliationUpdate(BaseModel):
    """Schema for updating a reconciliation."""
    status: Optional[str] = Field(None, pattern="^(PENDING|IN_PROGRESS|COMPLETED|FAILED)$")
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class ReconciliationResponse(ReconciliationBase):
    """Schema for reconciliation response."""
    id: UUID
    status: str
    reconciled_by: Optional[str]
    reconciled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Audit Log Schema
class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: UUID
    table_name: str
    record_id: UUID
    action: str
    user_id: Optional[str]
    changes: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Generic Response Schemas
class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[Any] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
    timestamp: datetime
