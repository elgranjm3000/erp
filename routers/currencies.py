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


@router.get("/currencies/{currency_id}/exchange-rates", response_model=List[schemas.ExchangeRateHistory])
def get_exchange_rate_history(
    currency_id: int,
    from_currency_id: int = None,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Obtener historial de tasas de cambio de una moneda.

    Parámetros:
    - currency_id: Moneda destino
    - from_currency_id: Moneda origen (opcional, default = moneda base de la empresa)
    - limit: Cantidad máxima de registros

    Ejemplo: GET /api/v1/currencies/2/exchange-rates?from_currency_id=1&limit=50
    Retorna el historial de USD -> VES
    """
    # Verificar que la moneda pertenezca a la empresa
    currency = crud.get_currency_by_id_and_company(
        db=db,
        currency_id=currency_id,
        company_id=current_user.company_id
    )

    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")

    # Determinar moneda origen
    if from_currency_id is None:
        # Usar moneda base de la empresa
        base_currency = crud.CurrencyService.get_base_currency(db, current_user.company_id)
        if not base_currency:
            raise HTTPException(
                status_code=400,
                detail="Company has no base currency configured"
            )
        from_currency_id = base_currency.id
    else:
        # Verificar que la moneda origen pertenezca a la empresa
        from_currency = crud.get_currency_by_id_and_company(
            db=db,
            currency_id=from_currency_id,
            company_id=current_user.company_id
        )
        if not from_currency:
            raise HTTPException(status_code=404, detail="From currency not found")

    # Obtener historial
    history = db.query(models.ExchangeRateHistory).filter(
        models.ExchangeRateHistory.company_id == current_user.company_id,
        models.ExchangeRateHistory.from_currency_id == from_currency_id,
        models.ExchangeRateHistory.to_currency_id == currency_id
    ).order_by(
        models.ExchangeRateHistory.recorded_at.desc()
    ).limit(limit).all()

    return history


@router.post("/currencies/exchange-rates", response_model=schemas.ExchangeRateHistory)
def record_exchange_rate(
    rate_data: schemas.ExchangeRateHistoryCreate,
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(get_db)
):
    """
    Registrar manualmente una tasa de cambio en el historial.

    Útil para:
    - Actualizar tasas diarias desde un API externo
    - Registrar tasas históricas
    - Corregir tasas incorrectas

    Ejemplo:
    {
        "from_currency_id": 1,  # USD
        "to_currency_id": 2,    # VES
        "rate": 36.5,
        "recorded_at": "2026-01-15T10:00:00"
    }
    """
    # Verificar que ambas monedas pertenezcan a la empresa
    from_currency = crud.get_currency_by_id_and_company(
        db=db,
        currency_id=rate_data.from_currency_id,
        company_id=current_user.company_id
    )

    if not from_currency:
        raise HTTPException(status_code=404, detail="From currency not found")

    to_currency = crud.get_currency_by_id_and_company(
        db=db,
        currency_id=rate_data.to_currency_id,
        company_id=current_user.company_id
    )

    if not to_currency:
        raise HTTPException(status_code=404, detail="To currency not found")

    # Registrar tasa
    exchange_rate = crud.CurrencyService.record_exchange_rate(
        db=db,
        company_id=current_user.company_id,
        from_currency_id=rate_data.from_currency_id,
        to_currency_id=rate_data.to_currency_id,
        rate=rate_data.rate,
        recorded_at=rate_data.recorded_at
    )

    return exchange_rate


@router.get("/currencies/rate-at-date")
def get_exchange_rate_at_date(
    from_currency_id: int,
    to_currency_id: int,
    date: str,  # Formato ISO: 2026-01-15
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Obtener la tasa de cambio vigente en una fecha específica.

    Útil para:
    - Saber cuánto valía una moneda en el pasado
    - Recalcular montos históricos

    Ejemplo: GET /api/v1/currencies/rate-at-date?from_currency_id=1&to_currency_id=2&date=2026-01-15
    """
    from datetime import datetime

    # Verificar que ambas monedas pertenezcan a la empresa
    from_currency = crud.get_currency_by_id_and_company(
        db=db,
        currency_id=from_currency_id,
        company_id=current_user.company_id
    )

    if not from_currency:
        raise HTTPException(status_code=404, detail="From currency not found")

    to_currency = crud.get_currency_by_id_and_company(
        db=db,
        currency_id=to_currency_id,
        company_id=current_user.company_id
    )

    if not to_currency:
        raise HTTPException(status_code=404, detail="To currency not found")

    # Parsear fecha
    try:
        query_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format: YYYY-MM-DD")

    # Obtener tasa en esa fecha
    rate_record = crud.CurrencyService.get_exchange_rate_at_date(
        db=db,
        company_id=current_user.company_id,
        from_currency_id=from_currency_id,
        to_currency_id=to_currency_id,
        date=query_date
    )

    if not rate_record:
        raise HTTPException(
            status_code=404,
            detail=f"No exchange rate found for {from_currency.code} -> {to_currency.code} on {date}"
        )

    return {
        "from_currency": from_currency.code,
        "to_currency": to_currency.code,
        "rate": rate_record.rate,
        "rate_date": rate_record.recorded_at,
        "query_date": date
    }

