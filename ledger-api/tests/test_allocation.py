"""
Tests for allocation service
"""
import pytest
from decimal import Decimal
from uuid import uuid4
from services.allocation import AllocationService


class TestAllocationService:
    """Test cases for AllocationService"""
    
    def test_validate_allocation_logic_valid_percentage(self):
        """Test validation of valid percentage-based allocation logic"""
        allocation_logic = [
            {"destination_account_id": str(uuid4()), "percentage": 50},
            {"destination_account_id": str(uuid4()), "percentage": 30},
            {"destination_account_id": str(uuid4()), "percentage": 20}
        ]
        
        # This should not raise an exception
        service = AllocationService(None)  # Mock db
        assert service.validate_allocation_logic(allocation_logic) is True
    
    def test_validate_allocation_logic_valid_amount(self):
        """Test validation of valid amount-based allocation logic"""
        allocation_logic = [
            {"destination_account_id": str(uuid4()), "amount": 100.00},
            {"destination_account_id": str(uuid4()), "amount": 50.00}
        ]
        
        service = AllocationService(None)
        assert service.validate_allocation_logic(allocation_logic) is True
    
    def test_validate_allocation_logic_invalid_empty(self):
        """Test validation fails for empty allocation logic"""
        service = AllocationService(None)
        
        with pytest.raises(ValueError, match="must be a non-empty list"):
            service.validate_allocation_logic([])
    
    def test_validate_allocation_logic_invalid_not_list(self):
        """Test validation fails for non-list allocation logic"""
        service = AllocationService(None)
        
        with pytest.raises(ValueError, match="must be a non-empty list"):
            service.validate_allocation_logic({"key": "value"})
    
    def test_validate_allocation_logic_missing_destination(self):
        """Test validation fails when destination_account_id is missing"""
        allocation_logic = [
            {"percentage": 50}
        ]
        
        service = AllocationService(None)
        
        with pytest.raises(ValueError, match="missing destination_account_id"):
            service.validate_allocation_logic(allocation_logic)
    
    def test_validate_allocation_logic_no_percentage_or_amount(self):
        """Test validation fails when neither percentage nor amount is specified"""
        allocation_logic = [
            {"destination_account_id": str(uuid4())}
        ]
        
        service = AllocationService(None)
        
        with pytest.raises(ValueError, match="must specify either percentage or amount"):
            service.validate_allocation_logic(allocation_logic)
    
    def test_validate_allocation_logic_both_percentage_and_amount(self):
        """Test validation fails when both percentage and amount are specified"""
        allocation_logic = [
            {"destination_account_id": str(uuid4()), "percentage": 50, "amount": 100}
        ]
        
        service = AllocationService(None)
        
        with pytest.raises(ValueError, match="cannot specify both percentage and amount"):
            service.validate_allocation_logic(allocation_logic)
    
    def test_validate_allocation_logic_invalid_percentage_range(self):
        """Test validation fails for percentage outside 0-100 range"""
        allocation_logic = [
            {"destination_account_id": str(uuid4()), "percentage": 150}
        ]
        
        service = AllocationService(None)
        
        with pytest.raises(ValueError, match="percentage must be between 0 and 100"):
            service.validate_allocation_logic(allocation_logic)
    
    def test_calculate_allocations_by_percentage(self):
        """Test calculation of allocations by percentage"""
        allocation_logic = [
            {"destination_account_id": str(uuid4()), "percentage": 50},
            {"destination_account_id": str(uuid4()), "percentage": 30},
            {"destination_account_id": str(uuid4()), "percentage": 20}
        ]
        
        service = AllocationService(None)
        total_amount = Decimal("1000.00")
        
        allocations = service._calculate_allocations(allocation_logic, total_amount)
        
        assert len(allocations) == 3
        assert allocations[0]["amount"] == Decimal("500.00")
        assert allocations[1]["amount"] == Decimal("300.00")
        assert allocations[2]["amount"] == Decimal("200.00")
    
    def test_calculate_allocations_by_amount(self):
        """Test calculation of allocations by fixed amount"""
        dest1 = str(uuid4())
        dest2 = str(uuid4())
        
        allocation_logic = [
            {"destination_account_id": dest1, "amount": 100.00},
            {"destination_account_id": dest2, "amount": 50.00}
        ]
        
        service = AllocationService(None)
        total_amount = Decimal("1000.00")
        
        allocations = service._calculate_allocations(allocation_logic, total_amount)
        
        assert len(allocations) == 2
        assert allocations[0]["amount"] == Decimal("100.00")
        assert allocations[1]["amount"] == Decimal("50.00")
    
    def test_calculate_allocations_exceeds_available(self):
        """Test that allocation doesn't exceed available amount"""
        allocation_logic = [
            {"destination_account_id": str(uuid4()), "amount": 600.00},
            {"destination_account_id": str(uuid4()), "amount": 500.00}
        ]
        
        service = AllocationService(None)
        total_amount = Decimal("1000.00")
        
        allocations = service._calculate_allocations(allocation_logic, total_amount)
        
        # First allocation should get 600, second should get 400 (remaining)
        assert len(allocations) == 2
        assert allocations[0]["amount"] == Decimal("600.00")
        assert allocations[1]["amount"] == Decimal("400.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
