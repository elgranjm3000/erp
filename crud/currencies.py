# crud/currencies.py
"""
Funciones CRUD para gestión de monedas (Currency)
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from typing import List, Optional
import models
import schemas
from .base import verify_company_ownership, paginate_query


def create_currency_for_company(
    db: Session,
    currency_data: schemas.CurrencyCreate,
    company_id: int
):
    """Crear moneda para empresa específica"""

    # Verificar que la empresa exista
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Verificar que el código no exista globalmente
    existing = db.query(models.Currency).filter(
        models.Currency.code == currency_data.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Currency with code {currency_data.code} already exists"
        )

    # Si se marca como moneda base, quitar marca de otras monedas de la empresa
    if currency_data.is_base_currency:
        db.query(models.Currency).filter(
            models.Currency.company_id == company_id,
            models.Currency.is_base_currency == True
        ).update({"is_base_currency": False})

    try:
        currency = models.Currency(
            company_id=company_id,
            code=currency_data.code.upper(),
            name=currency_data.name,
            symbol=currency_data.symbol,
            exchange_rate=currency_data.exchange_rate,
            is_base_currency=currency_data.is_base_currency,
            is_active=True
        )

        db.add(currency)
        db.commit()
        db.refresh(currency)

        return currency

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating currency: {str(e)}")


def get_currencies_by_company(
    db: Session,
    company_id: int,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
):
    """Obtener monedas de una empresa"""
    query = db.query(models.Currency).filter(
        models.Currency.company_id == company_id
    )

    if active_only:
        query = query.filter(models.Currency.is_active == True)

    return paginate_query(
        query.order_by(models.Currency.code.asc()),
        skip=skip,
        limit=limit
    ).all()


def get_currency_by_id_and_company(
    db: Session,
    currency_id: int,
    company_id: int
):
    """Obtener moneda específica de una empresa"""
    return verify_company_ownership(
        db=db,
        model_class=models.Currency,
        item_id=currency_id,
        company_id=company_id,
        error_message="Currency not found in your company"
    )


def update_currency_for_company(
    db: Session,
    currency_id: int,
    currency_data: schemas.CurrencyUpdate,
    company_id: int
):
    """Actualizar moneda de una empresa"""
    currency = verify_company_ownership(
        db=db,
        model_class=models.Currency,
        item_id=currency_id,
        company_id=company_id,
        error_message="Currency not found in your company"
    )

    # Si se marca como moneda base, quitar marca de otras monedas
    if currency_data.is_base_currency and not currency.is_base_currency:
        db.query(models.Currency).filter(
            models.Currency.company_id == company_id,
            models.Currency.is_base_currency == True
        ).update({"is_base_currency": False})

    # Actualizar campos
    update_data = currency_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(currency, key):
            setattr(currency, key, value)

    db.commit()
    db.refresh(currency)
    return currency


def delete_currency_for_company(
    db: Session,
    currency_id: int,
    company_id: int
):
    """Eliminar (desactivar) moneda de una empresa"""
    currency = verify_company_ownership(
        db=db,
        model_class=models.Currency,
        item_id=currency_id,
        company_id=company_id,
        error_message="Currency not found in your company"
    )

    # No permitir eliminar moneda base
    if currency.is_base_currency:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete base currency. Set another currency as base first."
        )

    # Soft delete
    currency.is_active = False
    db.commit()

    return {"message": "Currency deactivated successfully"}
