from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import crud
import models
import schemas
from database import get_db
from models import User
from auth import verify_token, check_permission

router = APIRouter()


@router.post("/currencies", response_model=schemas.Currency)
def create_currency(
    currency: schemas.CurrencyCreate,
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(get_db)
):
    """Crear moneda para mi empresa"""
    return crud.create_currency_for_company(
        db=db,
        currency_data=currency,
        company_id=current_user.company_id
    )


@router.get("/currencies", response_model=List[schemas.Currency])
def list_currencies(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Listar monedas de mi empresa"""
    return crud.get_currencies_by_company(
        db=db,
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        active_only=active_only
    )


@router.get("/currencies/{currency_id}", response_model=schemas.Currency)
def get_currency(
    currency_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Obtener moneda específica de mi empresa"""
    return crud.get_currency_by_id_and_company(
        db=db,
        currency_id=currency_id,
        company_id=current_user.company_id
    )


@router.put("/currencies/{currency_id}", response_model=schemas.Currency)
def update_currency(
    currency_id: int,
    currency_data: schemas.CurrencyUpdate,
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(get_db)
):
    """Actualizar moneda de mi empresa"""
    return crud.update_currency_for_company(
        db=db,
        currency_id=currency_id,
        currency_data=currency_data,
        company_id=current_user.company_id
    )


@router.delete("/currencies/{currency_id}")
def delete_currency(
    currency_id: int,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(get_db)
):
    """Eliminar (desactivar) moneda de mi empresa"""
    return crud.delete_currency_for_company(
        db=db,
        currency_id=currency_id,
        company_id=current_user.company_id
    )


@router.get("/currencies/convert")
def convert_currency(
    amount: float,
    from_currency_id: int,
    to_currency_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Convertir monto de una moneda a otra usando las tasas de cambio actuales.

    Ejemplo:
    - amount: 100
    - from_currency_id: 1 (USD)
    - to_currency_id: 2 (VES)
    - Resultado: 100 * 36.5 = 3,650 Bs
    """
    # Obtener monedas
    from_currency = crud.get_currency_by_id_and_company(
        db=db,
        currency_id=from_currency_id,
        company_id=current_user.company_id
    )
    to_currency = crud.get_currency_by_id_and_company(
        db=db,
        currency_id=to_currency_id,
        company_id=current_user.company_id
    )

    # Si es la misma moneda, retornar el mismo monto
    if from_currency_id == to_currency_id:
        return {
            "amount": amount,
            "from_currency": from_currency.code,
            "to_currency": to_currency.code,
            "converted_amount": amount,
            "rate": 1.0
        }

    # Convertir usando tasas de cambio
    # Primero convertir a moneda base (si from_currency es base)
    if from_currency.is_base_currency:
        amount_in_base = amount
    else:
        amount_in_base = amount / from_currency.exchange_rate

    # Luego convertir de base a moneda destino
    if to_currency.is_base_currency:
        converted_amount = amount_in_base
    else:
        converted_amount = amount_in_base * to_currency.exchange_rate

    return {
        "amount": amount,
        "from_currency": from_currency.code,
        "to_currency": to_currency.code,
        "converted_amount": round(converted_amount, 2),
        "rate": round(to_currency.exchange_rate / from_currency.exchange_rate, 6) if not from_currency.is_base_currency else round(to_currency.exchange_rate, 6)
    }

