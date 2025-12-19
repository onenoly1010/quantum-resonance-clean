"""Treasury management routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from db.session import get_db
from models.models import LogicalAccount, ReconciliationLog
from schemas.schemas import (
    TreasuryBalanceResponse,
    AllocationRequest,
    AllocationResponse,
    ReconciliationRequest,
    ReconciliationSimpleResponse
)
from services.allocation import AllocationService
from services.reconciliation import ReconciliationService
from deps.auth import get_current_user, require_guardian_role, get_optional_user

router = APIRouter(prefix="/api/v1/treasury", tags=["treasury"])


@router.get("/balance", response_model=List[TreasuryBalanceResponse])
@router.get("/status", response_model=List[TreasuryBalanceResponse])  # Alias for PR requirements
async def get_treasury_balance(
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Get balances for all treasury accounts.
    
    Authentication is optional for read operations.
    """
    # Get allocation service
    allocation_service = AllocationService(db)
    
    # Get all active accounts
    accounts = db.query(LogicalAccount).filter(
        LogicalAccount.is_active.is_(True)
    ).all()
    
    balances = []
    for account in accounts:
        balance = allocation_service.get_account_balance(account.account_id)
        balances.append(TreasuryBalanceResponse(
            account_id=account.account_id,
            account_name=account.account_name,
            balance=balance,
            currency="USD",
            last_updated=datetime.now(timezone.utc)
        ))
    
    return balances


@router.get("/balance/{account_id}", response_model=TreasuryBalanceResponse)
async def get_account_balance(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Get balance for a specific account.
    
    Authentication is optional for read operations.
    """
    # Verify account exists
    account = db.query(LogicalAccount).filter(
        LogicalAccount.account_id == account_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found: {account_id}"
        )
    
    # Get balance
    allocation_service = AllocationService(db)
    balance = allocation_service.get_account_balance(account_id)
    
    return TreasuryBalanceResponse(
        account_id=account.account_id,
        account_name=account.account_name,
        balance=balance,
        currency="USD",
        last_updated=datetime.now(timezone.utc)
    )


@router.post("/allocate", response_model=AllocationResponse)
async def trigger_allocation(
    request: AllocationRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_guardian_role)
):
    """
    Trigger allocation from a source account.
    
    This endpoint requires guardian role authorization.
    """
    # Verify source account exists
    account = db.query(LogicalAccount).filter(
        LogicalAccount.account_id == request.source_account_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source account not found: {request.source_account_id}"
        )
    
    # Execute allocation
    allocation_service = AllocationService(db)
    
    try:
        result = allocation_service.execute_allocation(
            amount=request.amount,
            source_account_id=request.source_account_id,
            rule_id=request.rule_id,
            description=request.description,
            created_by=current_user
        )
        
        return AllocationResponse(
            batch_id=result["batch_id"],
            source_account_id=result["source_account_id"],
            total_amount=result["total_amount"],
            allocations=result["allocations"],
            created_at=result["created_at"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Allocation failed: {str(e)}"
        )


@router.get("/report")
async def get_treasury_report(
    db: Session = Depends(get_db),
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Generate a comprehensive treasury report.
    
    Authentication is optional for read operations.
    """
    recon_service = ReconciliationService(db)
    
    # Get all active accounts
    accounts = db.query(LogicalAccount).filter(
        LogicalAccount.is_active.is_(True)
    ).all()
    
    report = {
        "generated_at": datetime.now(timezone.utc),
        "total_accounts": len(accounts),
        "accounts": []
    }
    
    total_assets = Decimal("0")
    total_liabilities = Decimal("0")
    total_equity = Decimal("0")
    
    for account in accounts:
        balance_info = recon_service.get_account_balance(account.account_id)
        
        account_data = {
            "account_id": account.account_id,
            "account_name": account.account_name,
            "account_type": account.account_type,
            "balance": float(balance_info["balance"]),
            "transaction_count": balance_info["transaction_count"],
            "last_transaction": balance_info["last_transaction"]
        }
        
        report["accounts"].append(account_data)
        
        # Accumulate totals by account type
        if account.account_type == "ASSET":
            total_assets += balance_info["balance"]
        elif account.account_type == "LIABILITY":
            total_liabilities += balance_info["balance"]
        elif account.account_type == "EQUITY":
            total_equity += balance_info["balance"]
    
    report["summary"] = {
        "total_assets": float(total_assets),
        "total_liabilities": float(total_liabilities),
        "total_equity": float(total_equity),
        "net_position": float(total_assets - total_liabilities)
    }
    
    return report


@router.post("/reconcile", response_model=ReconciliationSimpleResponse)
async def reconcile_account(
    request: ReconciliationRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_guardian_role)
):
    """
    Reconcile a logical account with external balance.
    
    Requires guardian role authorization.
    Computes discrepancy = external_balance - internal_balance.
    """
    # Verify account exists
    account = db.query(LogicalAccount).filter(
        LogicalAccount.account_id == request.logical_account_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found: {request.logical_account_id}"
        )
    
    # Get internal balance using reconciliation service
    recon_service = ReconciliationService(db)
    balance_info = recon_service.get_account_balance(request.logical_account_id)
    internal_balance = balance_info["balance"]
    
    # Compute discrepancy
    discrepancy = request.external_balance - internal_balance
    
    # Create reconciliation log entry
    recon_log = ReconciliationLog(
        reconciliation_id=f"RECON-{uuid.uuid4().hex[:12].upper()}",
        reconciliation_type="external_reconciliation",
        account_id=request.logical_account_id,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        status="SUCCESS",
        total_records=balance_info["transaction_count"],
        matched_records=balance_info["transaction_count"] if abs(discrepancy) < Decimal("0.01") else 0,
        unmatched_records=balance_info["transaction_count"] if abs(discrepancy) >= Decimal("0.01") else 0,
        discrepancies=[{
            "type": "balance_mismatch",
            "internal_balance": float(internal_balance),
            "external_balance": float(request.external_balance),
            "discrepancy": float(discrepancy)
        }] if abs(discrepancy) >= Decimal("0.01") else [],
        metadata={
            "reconciled_by": current_user,
            "external_balance": float(request.external_balance),
            "internal_balance": float(internal_balance)
        }
    )
    
    db.add(recon_log)
    db.commit()
    db.refresh(recon_log)
    
    return ReconciliationSimpleResponse(
        reconciliation_id=recon_log.reconciliation_id,
        discrepancy=discrepancy
    )
