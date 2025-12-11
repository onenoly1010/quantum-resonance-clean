"""Reconciliation Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid


class ReconciliationCreate(BaseModel):
    """Schema for creating a reconciliation record"""
    logical_account_id: uuid.UUID = Field(..., description="Account to reconcile")
    external_balance: Decimal = Field(..., description="External balance (from blockchain, bank, etc)")
    currency: str = Field(default="USD", description="Currency code")


class ReconciliationResponse(BaseModel):
    """Schema for reconciliation response"""
    id: uuid.UUID
    logical_account_id: uuid.UUID
    external_balance: Decimal
    internal_balance: Decimal
    discrepancy: Decimal
    currency: str
    created_at: datetime
    resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolution_notes: Optional[str]
    correction_transaction_id: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)
