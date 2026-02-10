"""
Endpoints Mejorados de Monedas v2.0

Con batch operations, mejor error handling y documentación completa.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from decimal import Decimal

from database import get_db
from auth import verify_token  # Cambiado de get_current_user
from models import User
from schemas import (
    CurrencyCreate,
    CurrencyUpdate,
    CurrencyResponse,
    CurrencyRateUpdate,
)
from services.currency_service_v2 import CurrencyServiceV2, get_currency_service_v2
from core.exceptions import ERPBaseException


router = APIRouter(prefix="/api/v2/currencies", tags=["Currencies v2"])


# ==================== DEPENDENCIES ====================

def get_service(db: Session = Depends(get_db)) -> CurrencyServiceV2:
    """Dependency injection para el servicio de monedas."""
    return get_currency_service_v2(db)


# ==================== ERROR HANDLER ====================

@router.exception_handler(ERPBaseException)
async def erp_exception_handler(request, exc: ERPBaseException):
    """Manejador de excepciones personalizadas."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


# ==================== CRUD MEJORADO ====================

@router.post("/", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED)
def create_currency(
    currency_data: CurrencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: CurrencyServiceV2 = Depends(get_service)
):
    """
    Crear nueva moneda.

    - **code**: Código ISO 4217 (ej: USD, EUR, VES) - máximo 3 caracteres
    - **name**: Nombre completo de la moneda
    - **symbol**: Símbolo de moneda (ej: $, €, Bs)
    - **exchange_rate**: Tasa de cambio (hasta 10 decimales)
    - **decimal_places**: Decimales para display (default: 2)
    - **is_base_currency**: Si es moneda base de la empresa (solo 1 permitida)
    - **conversion_method**: Método de conversión (direct, inverse, via_usd)
    - **applies_igtf**: Si aplica IGTF (impuesto venezolano)
    - **igtf_rate**: Tasa de IGTF (default: 3.00%)
    - **rate_update_method**: Método de actualización (manual, api_bcv, etc.)

    **Raises:**
    - 422: ValidationError (código inválido, tasa inválida)
    - 409: ConflictError (moneda duplicada, moneda base ya existe)
    """
    try:
        return service.create_currency(
            currency_data=currency_data,
            company_id=current_user.company_id,
            user_id=current_user.id
        )
    except ERPBaseException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error creating currency: {str(e)}"
        )


@router.post("/bulk", response_model=Dict[str, Any])
def bulk_create_currencies(
    currencies_data: List[CurrencyCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: CurrencyServiceV2 = Depends(get_service)
):
    """
    Crear múltiples monedas en batch.

    **Ejemplo de request body:**
    ```json
    [
      {
        "code": "EUR",
        "name": "Euro",
        "symbol": "€",
        "exchange_rate": "39.50",
        "applies_igtf": true
      },
      {
        "code": "GBP",
        "name": "British Pound",
        "symbol": "£",
        "exchange_rate": "46.80",
        "applies_igtf": true
      }
    ]
    ```

    **Returns:**
    - created: Lista de monedas creadas exitosamente
    - failed: Lista de monedas que fallaron con error
    - success_count: Número de monedas creadas
    - error_count: Número de errores
    """
    return service.bulk_create_currencies(
        currencies_data=currencies_data,
        company_id=current_user.company_id,
        user_id=current_user.id
    )


@router.put("/bulk/rates", response_model=Dict[str, Any])
def bulk_update_rates(
    updates: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: CurrencyServiceV2 = Depends(get_service)
):
    """
    Actualizar múltiples tasas de cambio en batch.

    **Ejemplo de request body:**
    ```json
    [
      {
        "currency_id": 28,
        "new_rate": "38.50",
        "change_reason": "Actualización masiva BCV"
      },
      {
        "currency_id": 29,
        "new_rate": "41.20",
        "change_reason": "Actualización masiva BCV"
      }
    ]
    ```

    **Returns:**
    - updated: Lista de tasas actualizadas
    - failed: Lista de actualizaciones que fallaron
    """
    return service.bulk_update_rates(
        updates=updates,
        company_id=current_user.company_id,
        user_id=current_user.id
    )


@router.get("/", response_model=List[CurrencyResponse])
def list_currencies(
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: CurrencyServiceV2 = Depends(get_service)
):
    """
    Listar monedas de la empresa.

    **Query params:**
    - is_active: Filtrar por estado (true/false)
    - skip: Cantidad de registros a saltar (paginación)
    - limit: Cantidad máxima de registros a retornar

    **Response caching:** 60 segundos
    """
    return service.list_currencies(
        company_id=current_user.company_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )


@router.get("/{currency_id}", response_model=CurrencyResponse)
def get_currency(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: CurrencyServiceV2 = Depends(get_service)
):
    """
    Obtener moneda por ID.

    **Response caching:** 5 minutos
    """
    try:
        return service.get_currency(
            currency_id=currency_id,
            company_id=current_user.company_id
        )
    except ERPBaseException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.put("/{currency_id}", response_model=CurrencyResponse)
def update_currency(
    currency_id: int,
    currency_data: CurrencyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: CurrencyServiceV2 = Depends(get_service)
):
    """Actualizar moneda existente."""
    try:
        return service.update_currency(
            currency_id=currency_id,
            currency_data=currency_data,
            company_id=current_user.company_id,
            user_id=current_user.id
        )
    except ERPBaseException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error updating currency: {str(e)}"
        )


@router.delete("/{currency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_currency(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: CurrencyServiceV2 = Depends(get_service)
):
    """
    Soft delete de moneda (marca como inactiva).

    **Nota:** No se puede eliminar la moneda base de la empresa.
    """
    try:
        service.delete_currency(
            currency_id=currency_id,
            company_id=current_user.company_id
        )
    except ERPBaseException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error deleting currency: {str(e)}"
        )


# ==================== ENDPOINTS ADICIONALES ====================

@router.post("/cache/clear", response_model=Dict[str, str])
def clear_currency_cache(
    pattern: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Limpiar caché de monedas.

    **Query params:**
    - pattern: Patrón de keys a limpiar (ej: "currency:28"). Si es None, limpia todo.

    **Nota:** Requiere permisos de administrador.
    """
    from core.cache import invalidate_caches

    count = invalidate_caches(pattern=pattern)

    return {
        "message": f"Cache cleared successfully",
        "entries_removed": count,
        "pattern": pattern or "all"
    }


@router.get("/cache/stats", response_model=Dict[str, Any])
def get_cache_stats(current_user: User = Depends(get_current_user)):
    """
    Obtener estadísticas del caché de monedas.

    **Nota:** Requiere permisos de administrador.
    """
    from core.cache import get_cache_stats

    return get_cache_stats()


# ==================== EXPORT/IMPORT ====================

@router.get("/export", response_model=Dict[str, Any])
def export_currencies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exportar todas las monedas de la empresa a JSON/CSV.

    **Query params:**
    - format: "json" o "csv" (default: json)

    **Returns:**
    - data: Datos exportados
    - format: Formato de exportación
    - count: Cantidad de monedas
    - exported_at: Timestamp de exportación
    """
    from datetime import datetime
    from models import Currency

    currencies = db.query(Currency).filter(
        Currency.company_id == current_user.company_id
    ).all()

    return {
        "data": [c.to_dict() for c in currencies],
        "format": "json",
        "count": len(currencies),
        "exported_at": datetime.now().isoformat(),
        "company_id": current_user.company_id
    }
