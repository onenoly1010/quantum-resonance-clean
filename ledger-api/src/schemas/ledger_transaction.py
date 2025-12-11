"""Ledger Transaction Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import uuid


class LedgerTransactionBase(BaseModel):
    """Base schema for Ledger Transaction"""
    type: str = Field(..., description="Transaction type: DEPOSIT, WITHDRAWAL, TRANSFER, ALLOCATION, CORRECTION")
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    description: Optional[str] = Field(None, description="Transaction description")
    external_tx_hash: Optional[str] = Field(None, description="External transaction hash/reference")
    logical_account_id: Optional[uuid.UUID] = Field(None, description="Target logical account ID")


class LedgerTransactionCreate(LedgerTransactionBase):
    """Schema for creating a Ledger Transaction"""
    pass


class LedgerTransactionUpdate(BaseModel):
    """Schema for updating a Ledger Transaction"""
    status: Optional[str] = Field(None, description="Transaction status: PENDING, COMPLETED, FAILED, CANCELLED")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    description: Optional[str] = Field(None, description="Description")


class LedgerTransactionResponse(LedgerTransactionBase):
    """Schema for Ledger Transaction response"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    status: str = Field(..., description="Transaction status")
    parent_transaction_id: Optional[uuid.UUID] = Field(None, description="Parent transaction ID for allocations")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Custom validation to handle transaction_metadata -> metadata mapping"""
        if hasattr(obj, 'transaction_metadata'):
            # Create a dict with the correct field names
            data = {
                'id': obj.id,
                'type': obj.type,
                'amount': obj.amount,
                'currency': obj.currency,
                'metadata': obj.transaction_metadata,
                'description': obj.description,
                'external_tx_hash': obj.external_tx_hash,
                'logical_account_id': obj.logical_account_id,
                'created_at': obj.created_at,
                'updated_at': obj.updated_at,
                'status': obj.status,
                'parent_transaction_id': obj.parent_transaction_id,
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)
