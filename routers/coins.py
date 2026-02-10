"""
✅ SISTEMA ESCRITORIO: Router para Gestión de Monedas (Coins)

Sistema de monedas compatible con el desktop ERP venezolano.
Basado en la estructura de PostgreSQL con soporte multiempresa.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import models
import schemas
import database
from models import User, CoinHistory
from models.currency_config import Currency
from auth import verify_token, check_permission

router = APIRouter()


# ==================== ✅ COINS (Monedas) ====================

@router.get("/coins/base")
def get_base_coin(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener la moneda base de la empresa"""
    base_coin = db.query(Currency).filter(
        Currency.company_id == current_user.company_id,
        Currency.is_base_currency == True
    ).first()

    if not base_coin:
        raise HTTPException(status_code=404, detail="No base currency found")

    return base_coin


@router.get("/coins/active")
def get_active_coins(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """
    Obtener solo las monedas activas que se muestran en browsers.

    Equivalente a: show_in_browsers = true AND is_active = true
    """
    coins = db.query(Currency).filter(
        Currency.company_id == current_user.company_id,
        Currency.show_in_browsers == True,
        Currency.is_active == True
    ).order_by(Currency.code).all()

    return coins


@router.get("/coins", response_model=List[schemas.Coin])
def read_coins(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """
    Listar todas las monedas de mi empresa.

    Retorna las monedas con los campos del sistema desktop ERP.
    """
    coins = db.query(Currency).filter(
        Currency.company_id == current_user.company_id
    ).order_by(Currency.code).offset(skip).limit(limit).all()

    return coins


@router.get("/coins/{coin_id}", response_model=schemas.Coin)
def read_coin(
    coin_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener una moneda por ID"""
    coin = db.query(Currency).filter(
        Currency.id == coin_id,
        Currency.company_id == current_user.company_id
    ).first()

    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")

    return coin


@router.post("/coins", response_model=schemas.Coin)
def create_coin(
    coin_data: schemas.CoinCreate,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(database.get_db)
):
    """
    Crear nueva moneda (coin) para la empresa.

    Campos del sistema desktop ERP:
    {
        "code": "USD",
        "description": "Dólar Americano",
        "symbol": "$",
        "sales_aliquot": 165.41,
        "buy_aliquot": 165.41,
        "factor_type": 1,
        "rounding_type": 2,
        "status": "01",
        "show_in_browsers": true,
        "value_inventory": true,
        "apply_igtf": true
    }
    """
    # Verificar que el código no existe en la empresa
    existing = db.query(Currency).filter(
        Currency.company_id == current_user.company_id,
        Currency.code == coin_data.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Coin with code {coin_data.code} already exists"
        )

    # Verificar que solo hay una moneda base
    if coin_data.factor_type == 0:  # Moneda base
        existing_base = db.query(Currency).filter(
            Currency.company_id == current_user.company_id,
            Currency.is_base_currency == True
        ).first()

        if existing_base:
            raise HTTPException(
                status_code=400,
                detail="Base currency already exists. Only one base currency per company is allowed."
            )

    # Crear moneda
    db_coin = Currency(
        company_id=current_user.company_id,
        created_by=current_user.id,
        updated_by=current_user.id,
        **coin_data.dict()
    )

    db.add(db_coin)
    db.commit()
    db.refresh(db_coin)

    return db_coin


@router.put("/coins/{coin_id}", response_model=schemas.Coin)
def update_coin(
    coin_id: int,
    coin_data: schemas.CoinUpdate,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(database.get_db)
):
    """Actualizar una moneda"""
    db_coin = db.query(Currency).filter(
        Currency.id == coin_id,
        Currency.company_id == current_user.company_id
    ).first()

    if not db_coin:
        raise HTTPException(status_code=404, detail="Coin not found")

    # Si se está cambiando a moneda base, verificar que no haya otra
    update_data = coin_data.dict(exclude_unset=True)

    if 'factor_type' in update_data and update_data['factor_type'] == 0:
        if not db_coin.is_base_currency:
            existing_base = db.query(Currency).filter(
                Currency.company_id == current_user.company_id,
                Currency.is_base_currency == True,
                Currency.id != coin_id
            ).first()

            if existing_base:
                raise HTTPException(
                    status_code=400,
                    detail="Base currency already exists. Only one base currency per company is allowed."
                )

            # Si se convierte en base, actualizar is_base_currency
            update_data['is_base_currency'] = True
    elif 'factor_type' in update_data and update_data['factor_type'] == 1:
        # Si deja de ser base
        update_data['is_base_currency'] = False

    # Actualizar campos
    for field, value in update_data.items():
        setattr(db_coin, field, value)

    db_coin.updated_by = current_user.id
    db_coin.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_coin)

    return db_coin


@router.delete("/coins/{coin_id}")
def delete_coin(
    coin_id: int,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(database.get_db)
):
    """
    Eliminar una moneda (solo admin).

    Precaución: Verificar que no esté siendo usada en productos o facturas.
    """
    db_coin = db.query(Currency).filter(
        Currency.id == coin_id,
        Currency.company_id == current_user.company_id
    ).first()

    if not db_coin:
        raise HTTPException(status_code=404, detail="Coin not found")

    # Verificar que no es la moneda base
    if db_coin.is_base_currency:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete base currency. Set another currency as base first."
        )

    db.delete(db_coin)
    db.commit()

    return {"message": "Coin deleted successfully"}


@router.put("/coins/{coin_id}/rate")
def update_coin_rate(
    coin_id: int,
    sales_aliquot: float,
    buy_aliquot: Optional[float] = None,
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """
    Actualizar la tasa de cambio de una moneda y registrar en historial.

    Este endpoint actualiza el exchange_rate y crea un registro en coin_history
    para mantener la auditoría del sistema desktop ERP.

    Ejemplo:
    PUT /coins/1/rate?sales_aliquot=170.5&buy_aliquot=170.0
    """
    db_coin = db.query(Currency).filter(
        Currency.id == coin_id,
        Currency.company_id == current_user.company_id
    ).first()

    if not db_coin:
        raise HTTPException(status_code=404, detail="Coin not found")

    # Si no se proporciona buy_aliquot, usar el mismo que sales_aliquot
    if buy_aliquot is None:
        buy_aliquot = sales_aliquot

    # Actualizar tasa
    old_rate = db_coin.exchange_rate
    db_coin.exchange_rate = sales_aliquot
    db_coin.updated_by = current_user.id
    db_coin.updated_at = datetime.utcnow()
    db_coin.last_rate_update = datetime.utcnow()

    db.commit()

    # Crear registro en coin_history (auditoría desktop ERP)
    from datetime import date, time as time_module
    now = datetime.now()
    history = CoinHistory(
        company_id=current_user.company_id,
        currency_id=coin_id,
        sales_aliquot=sales_aliquot,
        buy_aliquot=buy_aliquot,
        register_date=now.date(),
        register_hour=now.time(),
        user_id=current_user.id
    )

    db.add(history)
    db.commit()

    return {
        "message": "Rate updated successfully",
        "coin_id": coin_id,
        "old_rate": old_rate,
        "new_rate": sales_aliquot,
        "history_id": history.id
    }
