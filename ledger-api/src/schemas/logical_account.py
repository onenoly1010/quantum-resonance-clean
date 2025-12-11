"""Logical Account Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import uuid


class LogicalAccountBase(BaseModel):
    """Base schema for Logical Account"""
    name: str = Field(..., description="Unique account name")
    type: str = Field(..., description="Account type: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LogicalAccountCreate(LogicalAccountBase):
    """Schema for creating a Logical Account"""
    pass


class LogicalAccountUpdate(BaseModel):
    """Schema for updating a Logical Account"""
    name: Optional[str] = Field(None, description="Account name")
    type: Optional[str] = Field(None, description="Account type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")


class LogicalAccountResponse(LogicalAccountBase):
    """Schema for Logical Account response"""
    id: uuid.UUID
    balance: Decimal = Field(..., description="Current account balance")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Custom validation to handle account_metadata -> metadata mapping"""
        if hasattr(obj, 'account_metadata'):
            # Create a dict with the correct field names
            data = {
                'id': obj.id,
                'name': obj.name,
                'type': obj.type,
                'metadata': obj.account_metadata,
                'balance': obj.balance,
                'created_at': obj.created_at,
                'updated_at': obj.updated_at,
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)
