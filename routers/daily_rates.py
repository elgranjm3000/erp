"""
API Router - Tasas Diarias de Cambio
Endpoints para gestión de tasas históricas BCV y manuales
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

from database import get_db
from auth import verify_token
from models import User
from models.daily_rates import DailyRate

from services.daily_rate_service import DailyRateService


router = APIRouter(prefix="/api/v1/rates", tags=["Tasas de Cambio"])


# ==================== ENDPOINTS: SINCRONIZACIÓN BCV ====================

@router.post("/bcv/sync")
def sync_bcv_rates(
    force_refresh: bool = Query(False, description="Forzar actualización de cache"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Sincroniza las tasas del BCV con la base de datos.

    Obtiene las tasas oficiales del Banco Central de Venezuela
    y las guarda en el historial de tasas diarias.

    - Si ya existe tasa para hoy, la actualiza si cambió
    - Si no existe, crea una nueva tasa diaria
    - Marca la fuente como "BCV"
    - Registra el usuario que inició la sincronización

    Retorna:
        JSON con estadísticas de la sincronización
    """
    service = DailyRateService(db, current_user.company_id)

    try:
        results = service.sync_bcv_rates(
            user_id=current_user.id,
            force_refresh=force_refresh
        )

        if results.get("error"):
            raise HTTPException(status_code=500, detail=results["error"])

        return {
            "message": "BCV rates synchronized successfully",
            "stats": {
                "synced": results["total_synced"],
                "failed": results["total_failed"],
                "skipped": len(results["skipped_rates"])
            },
            "details": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing BCV rates: {str(e)}"
        )


@router.get("/bcv/status")
def get_bcv_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Obtiene el estado del servicio BCV.

    Retorna información sobre:
        - Disponibilidad del servicio BCV
        - Última actualización
        - Tasas cacheadas
        - Monedas soportadas

    Útil para verificar si el BCV está accesible
    y cuándo fue la última sincronización exitosa.
    """
    service = DailyRateService(db, current_user.company_id)

    try:
        status = service.get_bcv_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting BCV status: {str(e)}"
        )


# ==================== ENDPOINTS: CONSULTA DE TASAS ====================

@router.get("/today")
def get_today_rate(
    from_currency: str = Query(..., min_length=3, max_length=3, description="Moneda origen (ej: USD)"),
    to_currency: str = Query(..., min_length=3, max_length=3, description="Moneda destino (ej: VES)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Obtiene la tasa de cambio de hoy.

    Si no existe tasa para hoy, intenta obtenerla del BCV
    automáticamente. Si no está disponible, retorna la más reciente.

    Args:
        from_currency: Moneda origen (ej: USD)
        to_currency: Moneda destino (ej: VES)

    Returns:
        JSON con:
            - rate: Tasa de cambio
            - rate_date: Fecha de la tasa
            - source: Fuente (BCV/MANUAL)
            - inverse_rate: Tasa inversa

    Ejemplo:
        GET /api/v1/rates/today?from_currency=USD&to_currency=VES
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"🔍 /rates/today called: {from_currency} → {to_currency} | User: {current_user.username} | Company: {current_user.company_id}")

    service = DailyRateService(db, current_user.company_id)

    try:
        daily_rate = service.get_today_rate(from_currency, to_currency)

        if not daily_rate:
            logger.error(f"❌ No rate found for {from_currency} → {to_currency} | Company: {current_user.company_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No rate available for {from_currency} → {to_currency}"
            )

        logger.info(f"✅ Rate found: {daily_rate.exchange_rate} | Source: {daily_rate.source}")

        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": daily_rate.exchange_rate,
            "rate_date": daily_rate.rate_date.isoformat(),
            "source": daily_rate.source,
            "inverse_rate": daily_rate.inverse_rate,
            "is_active": daily_rate.is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in /rates/today: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting today's rate: {str(e)}"
        )


@router.get("/latest")
def get_latest_rate(
    from_currency: str = Query(..., min_length=3, max_length=3, description="Moneda origen"),
    to_currency: str = Query(..., min_length=3, max_length=3, description="Moneda destino"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Obtiene la tasa de cambio más reciente disponible.

    A diferencia de /today, este endpoint NO intenta sincronizar
    con el BCV, solo retorna la tasa más reciente guardada.

    Útil para obtener la última tasa conocida sin hacer
    solicitudes externas.
    """
    service = DailyRateService(db, current_user.company_id)

    try:
        daily_rate = service.get_latest_rate(from_currency, to_currency)

        if not daily_rate:
            raise HTTPException(
                status_code=404,
                detail=f"No rate found for {from_currency} → {to_currency}"
            )

        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": daily_rate.exchange_rate,
            "rate_date": daily_rate.rate_date.isoformat(),
            "source": daily_rate.source,
            "inverse_rate": daily_rate.inverse_rate,
            "is_active": daily_rate.is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting latest rate: {str(e)}"
        )


@router.get("/history")
def get_rate_history(
    from_currency: str = Query(..., min_length=3, max_length=3, description="Moneda origen"),
    to_currency: str = Query(..., min_length=3, max_length=3, description="Moneda destino"),
    start_date: Optional[date] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Obtiene el historial de tasas para un par de monedas.

    Retorna todas las tasas guardadas ordenadas por fecha descendente
    (más reciente primero).

    Args:
        from_currency: Moneda origen
        to_currency: Moneda destino
        start_date: Fecha inicial (opcional)
        end_date: Fecha final (opcional)
        limit: Máximo de registros a retornar

    Example:
        GET /api/v1/rates/history?from_currency=USD&to_currency=VES&limit=30
    """
    service = DailyRateService(db, current_user.company_id)

    try:
        history = service.get_rate_history(
            from_currency_code=from_currency,
            to_currency_code=to_currency,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "count": len(history),
            "rates": [
                {
                    "rate": r.exchange_rate,
                    "rate_date": r.rate_date.isoformat(),
                    "source": r.source,
                    "inverse_rate": r.inverse_rate,
                    "notes": r.notes
                }
                for r in history
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting rate history: {str(e)}"
        )


# ==================== ENDPOINTS: CONVERSIÓN ====================

@router.post("/convert")
def convert_currency(
    amount: Decimal = Query(..., gt=0, description="Monto a convertir"),
    from_currency: str = Query(..., min_length=3, max_length=3, description="Moneda origen"),
    to_currency: str = Query(..., min_length=3, max_length=3, description="Moneda destino"),
    rate_date: Optional[date] = Query(None, description="Fecha de la tasa (usar hoy si es None)"),
    manual_rate: Optional[float] = Query(None, description="Tasa manual para override"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Convierte un monto entre monedas usando tasas diarias.

    Este endpoint es el utilizado por las facturas para convertir
    de USD a VES usando la tasa BCV del día.

    Args:
        amount: Monto a convertir
        from_currency: Moneda origen
        to_currency: Moneda destino
        rate_date: Fecha de la tasa (opcional, usa hoy si es None)
        manual_rate: Tasa manual para override (opcional)

    Returns:
        JSON con:
            - original_amount, original_currency
            - converted_amount, target_currency
            - rate: Tasa utilizada
            - rate_date: Fecha de la tasa
            - source: Fuente (BCV/MANUAL)
            - inverse_rate: Tasa inversa

    Ejemplo:
        POST /api/v1/rates/convert?amount=100&from_currency=USD&to_currency=VES

        Response:
        {
            "original_amount": "100.00",
            "original_currency": "USD",
            "converted_amount": "3450.00",
            "target_currency": "VES",
            "rate": "34.50",
            "rate_date": "2025-01-17",
            "source": "BCV",
            "inverse_rate": "0.02899"
        }
    """
    service = DailyRateService(db, current_user.company_id)

    try:
        result = service.calculate_conversion(
            amount=amount,
            from_currency_code=from_currency,
            to_currency_code=to_currency,
            rate_date=rate_date,
            manual_rate=manual_rate
        )

        return {
            "original_amount": str(amount),
            "original_currency": from_currency,
            "converted_amount": str(result["converted_amount"]),
            "target_currency": to_currency,
            "rate": str(result["rate"]),
            "rate_date": result["rate_date"].isoformat(),
            "source": result["source"],
            "inverse_rate": str(result["inverse_rate"]) if result["inverse_rate"] else None
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error converting currency: {str(e)}"
        )


# ==================== ENDPOINTS: TASAS MANUALES ====================

@router.post("/manual")
def create_manual_rate(
    from_currency: str = Query(..., min_length=3, max_length=3, description="Moneda origen"),
    to_currency: str = Query(..., min_length=3, max_length=3, description="Moneda destino"),
    rate_date: date = Query(..., description="Fecha de la tasa"),
    exchange_rate: float = Query(..., gt=0, description="Tasa de cambio"),
    notes: Optional[str] = Query(None, description="Notas justificando la tasa manual"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Crea una tasa manual con override.

    Se usa cuando se necesita usar una tasa diferente a la del BCV
    para una factura específica. Se debe proporcionar una justificación
    en el campo notes.

    Args:
        from_currency: Moneda origen (ej: USD)
        to_currency: Moneda destino (ej: VES)
        rate_date: Fecha de la tasa
        exchange_rate: Tasa de cambio
        notes: Justificación de la tasa manual

    Returns:
        DailyRate creada

    Example:
        POST /api/v1/rates/manual?from_currency=USD&to_currency=VES
            &rate_date=2025-01-17&exchange_rate=35.00
            &notes=Tasa%20manual%20por%20acuerdo%20con%20cliente
    """
    service = DailyRateService(db, current_user.company_id)

    try:
        daily_rate = service.create_manual_rate(
            from_currency_code=from_currency,
            to_currency_code=to_currency,
            rate_date=rate_date,
            exchange_rate=exchange_rate,
            user_id=current_user.id,
            notes=notes
        )

        return {
            "id": daily_rate.id,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": daily_rate.exchange_rate,
            "rate_date": daily_rate.rate_date.isoformat(),
            "source": daily_rate.source,
            "notes": daily_rate.notes,
            "created_at": daily_rate.created_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating manual rate: {str(e)}"
        )
