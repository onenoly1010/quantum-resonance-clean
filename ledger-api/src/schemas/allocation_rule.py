"""Allocation Rule Schemas"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid


class AllocationRuleItem(BaseModel):
    """Schema for a single allocation rule item"""
    destination_account_id: uuid.UUID = Field(..., description="Destination account UUID")
    percentage: Decimal = Field(..., ge=0, le=100, description="Allocation percentage (0-100)")
    description: Optional[str] = Field(None, description="Description of this allocation")


class AllocationRuleBase(BaseModel):
    """Base schema for Allocation Rule"""
    name: str = Field(..., description="Unique rule name")
    rules: List[AllocationRuleItem] = Field(..., description="List of allocation rules")
    active: bool = Field(default=True, description="Whether the rule is active")
    description: Optional[str] = Field(None, description="Rule description")

    @field_validator('rules')
    @classmethod
    def validate_percentages_sum_to_100(cls, v: List[AllocationRuleItem]) -> List[AllocationRuleItem]:
        """Validate that all percentages sum to exactly 100"""
        total = sum(item.percentage for item in v)
        if abs(total - Decimal('100.0')) > Decimal('0.01'):  # Allow small floating point errors
            raise ValueError(f"Allocation percentages must sum to 100.0, got {total}")
        return v


class AllocationRuleCreate(AllocationRuleBase):
    """Schema for creating an Allocation Rule"""
    created_by: Optional[str] = Field(None, description="User creating the rule")


class AllocationRuleUpdate(BaseModel):
    """Schema for updating an Allocation Rule"""
    name: Optional[str] = Field(None, description="Rule name")
    rules: Optional[List[AllocationRuleItem]] = Field(None, description="Allocation rules")
    active: Optional[bool] = Field(None, description="Active status")
    description: Optional[str] = Field(None, description="Description")

    @field_validator('rules')
    @classmethod
    def validate_percentages_sum_to_100(cls, v: Optional[List[AllocationRuleItem]]) -> Optional[List[AllocationRuleItem]]:
        """Validate that all percentages sum to exactly 100"""
        if v is None:
            return v
        total = sum(item.percentage for item in v)
        if abs(total - Decimal('100.0')) > Decimal('0.01'):
            raise ValueError(f"Allocation percentages must sum to 100.0, got {total}")
        return v


class AllocationRuleResponse(AllocationRuleBase):
    """Schema for Allocation Rule response"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    model_config = ConfigDict(from_attributes=True)
