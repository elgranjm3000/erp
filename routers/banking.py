"""
Router de Conciliación Bancaria Multimoneda
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
from auth import verify_token
from models import User
import crud.banking as banking_crud

router = APIRouter(prefix="/api/v1/banking", tags=["Conciliación Bancaria"])

# ==================== CUENTAS BANCARIAS ====================

@router.post("/accounts")
def create_bank_account(
    account_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """Crear cuenta bancaria"""
    return banking_crud.create_bank_account(
        db=db,
        account_data=account_data,
        company_id=current_user.company_id,
        user_id=current_user.id
    )

@router.get("/accounts")
def list_bank_accounts(
    currency_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """Listar cuentas bancarias"""
    return banking_crud.get_bank_accounts(
        db=db,
        company_id=current_user.company_id,
        currency_id=currency_id
    )

# ==================== TRANSACCIONES ====================

@router.post("/transactions")
def create_bank_transaction(
    transaction_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """Crear transacción bancaria"""
    return banking_crud.create_bank_transaction(
        db=db,
        transaction_data=transaction_data,
        company_id=current_user.company_id,
        user_id=current_user.id
    )

# ==================== SALDO CONSOLIDADO ====================

@router.get("/balance/consolidated")
def get_consolidated_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Obtiene saldo consolidado por moneda.

    Retorna:
    - Balances agrupados por moneda
    - Total convertido a moneda base
    - Lista de cuentas por moneda
    """
    return banking_crud.get_consolidated_balance(
        db=db,
        company_id=current_user.company_id
    )
