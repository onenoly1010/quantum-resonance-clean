"""
Treasury routes
Endpoints for managing logical accounts and balances
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from db.session import get_db
from models.models import LogicalAccount
from schemas.schemas import (
    LogicalAccountCreate,
    LogicalAccountUpdate,
    LogicalAccountResponse,
    AccountBalanceResponse
)
from deps.auth import get_current_user
from hooks.audit import AuditLogger, get_audit_logger
from services.reconciliation import ReconciliationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/treasury", tags=["Treasury"])


@router.post("/accounts", response_model=LogicalAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: LogicalAccountCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Create a new logical account
    
    Args:
        account: Account data
        request: FastAPI request
        db: Database session
        current_user: Current authenticated user
        audit_logger: Audit logger instance
        
    Returns:
        Created account
    """
    # Check if account code already exists
    existing = db.query(LogicalAccount).filter(
        LogicalAccount.account_code == account.account_code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account with code {account.account_code} already exists"
        )
    
    # Set created_by to current user
    account_data = account.model_dump()
    account_data['created_by'] = current_user
    
    # Create account
    db_account = LogicalAccount(**account_data)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    # Log to audit
    audit_logger.log_create(
        user_id=current_user,
        entity_type="logical_account",
        entity_id=db_account.id,
        entity_data=account_data,
        request=request
    )
    
    logger.info(f"Account created: {db_account.account_code}")
    
    return db_account


@router.get("/accounts", response_model=List[LogicalAccountResponse])
async def list_accounts(
    skip: int = 0,
    limit: int = 100,
    account_type: str = None,
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    List logical accounts with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        account_type: Filter by account type
        status_filter: Filter by account status
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of accounts
    """
    query = db.query(LogicalAccount)
    
    if account_type:
        query = query.filter(LogicalAccount.account_type == account_type)
    
    if status_filter:
        query = query.filter(LogicalAccount.status == status_filter)
    
    accounts = query.offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(accounts)} accounts")
    
    return accounts


@router.get("/accounts/{account_id}", response_model=LogicalAccountResponse)
async def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get a specific account by ID
    
    Args:
        account_id: Account UUID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Account details
        
    Raises:
        HTTPException: If account not found
    """
    account = db.query(LogicalAccount).filter(
        LogicalAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    
    return account


@router.put("/accounts/{account_id}", response_model=LogicalAccountResponse)
async def update_account(
    account_id: UUID,
    account_update: LogicalAccountUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Update an account
    
    Args:
        account_id: Account UUID
        account_update: Updated account data
        request: FastAPI request
        db: Database session
        current_user: Current authenticated user
        audit_logger: Audit logger instance
        
    Returns:
        Updated account
        
    Raises:
        HTTPException: If account not found
    """
    # Get existing account
    db_account = db.query(LogicalAccount).filter(
        LogicalAccount.id == account_id
    ).first()
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    
    # Store old data for audit
    old_data = {
        "account_name": db_account.account_name,
        "status": db_account.status,
        "metadata": db_account.metadata
    }
    
    # Update fields
    update_data = account_update.model_dump(exclude_unset=True)
    update_data['updated_by'] = current_user
    
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.commit()
    db.refresh(db_account)
    
    # Log to audit
    new_data = {
        "account_name": db_account.account_name,
        "status": db_account.status,
        "metadata": db_account.metadata
    }
    
    audit_logger.log_update(
        user_id=current_user,
        entity_type="logical_account",
        entity_id=db_account.id,
        old_data=old_data,
        new_data=new_data,
        request=request
    )
    
    logger.info(f"Account updated: {db_account.account_code}")
    
    return db_account


@router.get("/balances", response_model=List[dict])
async def get_balances(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get balances for all active accounts
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of account balances
    """
    recon_service = ReconciliationService(db)
    balances = recon_service.get_all_account_balances()
    
    logger.info(f"Retrieved balances for {len(balances)} accounts")
    
    return balances


@router.get("/balances/{account_id}")
async def get_account_balance(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get balance for a specific account
    
    Args:
        account_id: Account UUID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Account balance
        
    Raises:
        HTTPException: If account not found
    """
    # Verify account exists
    account = db.query(LogicalAccount).filter(
        LogicalAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    
    # Get balance
    recon_service = ReconciliationService(db)
    balance = recon_service.get_account_balance(account_id)
    
    return {
        "account_id": account_id,
        "account_code": account.account_code,
        "account_name": account.account_name,
        "balance": balance,
        "currency": account.currency
    }
