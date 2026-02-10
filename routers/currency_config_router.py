"""
API Router - Gestión de Monedas con Lógica Venezolana
Endpoints para CRUD, actualización de tasas, historial e IGTF
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from database import get_db
from auth import verify_token
from models import User

from models.currency_config import Currency, CurrencyRateHistory, IGTFConfig
# Importar schemas desde el archivo en lugar del paquete
from schemas import (
    CurrencyCreate,
    CurrencyUpdate,
    CurrencyResponse,
    CurrencyRateUpdate,
    CurrencyRateHistoryResponse,
    IGTFConfigCreate,
    IGTFConfigResponse,
    ISO_4217_CURRENCIES,
    ConversionMethod,
    CurrencyConversionRequest,
    IGTFCalculationRequest
)
from services.currency_business_service import CurrencyService, CurrencyBusinessLogic
from services.product_price_updater import ProductPriceUpdater


router = APIRouter(prefix="/api/v1/currencies", tags=["Monedas"])


# ==================== ENDPOINTS: CRUD DE MONEDAS ====================

@router.post("/", response_model=CurrencyResponse)
def create_currency(
    currency_data: CurrencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Crea una nueva moneda con validación ISO 4217.

    - Valida código ISO 4217
    - Calcula automáticamente el factor de conversión
    - Configura IGTF según tipo de moneda
    - Verifica que solo haya una moneda base por empresa

    Ejemplo:
    ```json
    {
        "code": "USD",
        "name": "US Dollar",
        "symbol": "$",
        "exchange_rate": "36.5000000000",
        "decimal_places": 2,
        "is_base_currency": false,
        "conversion_method": "direct",
        "applies_igtf": true,
        "igtf_rate": "3.00",
        "igtf_min_amount": "1000.00",
        "rate_update_method": "api_bcv",
        "rate_source_url": "https://www.bcv.org.ve"
    }
    ```
    """
    service = CurrencyService(db)

    try:
        currency = service.create_currency(
            currency_data=currency_data,
            company_id=current_user.company_id,
            user_id=current_user.id
        )

        return currency

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating currency: {str(e)}")


@router.get("/", response_model=List[CurrencyResponse])
def list_currencies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """Lista todas las monedas de la empresa con filtros"""
    query = db.query(Currency).filter(
        Currency.company_id == current_user.company_id
    )

    if is_active is not None:
        query = query.filter(Currency.is_active == is_active)

    currencies = query.order_by(Currency.code).offset(skip).limit(limit).all()

    return currencies


# ==================== IMPORTANT: SPECIFIC ROUTES MUST COME BEFORE PARAMETERIZED ONES ====================

# ==================== ENDPOINTS: CONVERSIÓN ====================

@router.get("/convert")
def convert_currency(
    from_currency: str = Query(..., min_length=3, max_length=3),
    to_currency: str = Query(..., min_length=3, max_length=3),
    amount: Decimal = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Convierte un monto entre monedas usando tasas configuradas.

    Args:
        from_currency: Moneda origen (ej: USD)
        to_currency: Moneda destino (ej: VES)
        amount: Monto a convertir

    Returns:
        JSON con:
        - original_amount, original_currency
        - converted_amount, target_currency
        - exchange_rate_used
        - conversion_method
        - rate_metadata

    Ejemplo:
        GET /api/v1/currencies/convert?from_currency=USD&to_currency=VES&amount=100
    """
    service = CurrencyService(db)

    try:
        rate, metadata = service.get_exchange_rate_with_metadata(
            from_currency=from_currency,
            to_currency=to_currency,
            company_id=current_user.company_id
        )

        # Convertir
        logic = CurrencyBusinessLogic()
        # Ensure rate is Decimal for the conversion
        from decimal import Decimal
        rate_decimal = Decimal(str(rate)) if not isinstance(rate, Decimal) else rate
        converted, rate_used, method = logic.convert_currency(
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate_decimal,
            method=metadata.get("method", "direct")
        )

        return {
            "original_amount": float(amount),
            "original_currency": from_currency.upper(),
            "converted_amount": float(converted),
            "target_currency": to_currency.upper(),
            "exchange_rate_used": float(rate_used),
            "conversion_method": method,
            "rate_metadata": metadata
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ENDPOINTS: FACTORES DE CONVERSIÓN ====================

@router.get("/factors")
def list_conversion_factors(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Lista todas las monedas con sus factores de conversión.

    Retorna tabla con:
    - Código de moneda
    - Nombre
    - Tasa actual
    - Método de conversión
    - Factor de conversión
    - Aplica IGTF
    """
    currencies = db.query(Currency).filter(
        Currency.company_id == current_user.company_id,
        Currency.is_active == True
    ).all()

    factors = []

    for currency in currencies:
        logic = CurrencyBusinessLogic()
        factor, method = logic.calculate_conversion_factor(
            code=currency.code,
            rate=currency.exchange_rate,
            method=ConversionMethod(currency.conversion_method) if currency.conversion_method else None
        )

        factors.append({
            "code": currency.code,
            "name": currency.name,
            "symbol": currency.symbol,
            "exchange_rate": float(currency.exchange_rate),
            "conversion_method": currency.conversion_method,
            "conversion_factor": float(factor) if factor else None,
            "is_base": currency.is_base_currency,
            "applies_igtf": currency.applies_igtf,
            "igtf_rate": float(currency.igtf_rate) if currency.igtf_rate else None,
            "decimal_places": currency.decimal_places
        })

    return factors


# ==================== ENDPOINTS: IGTF ====================

@router.get("/igtf/config", response_model=List[IGTFConfigResponse])
def list_igtf_configs(
    currency_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """Lista configuraciones de IGTF de la empresa"""
    service = CurrencyService(db)

    configs = service.get_igtf_config(
        company_id=current_user.company_id,
        currency_id=currency_id
    )

    return configs


@router.post("/igtf/config", response_model=IGTFConfigResponse)
def create_igtf_config(
    config_data: IGTFConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Crea configuración personalizada de IGTF para una moneda.

    Útil para empresas con régimen especial de IGTF.

    Ejemplo:
    ```json
    {
        "company_id": 1,
        "currency_id": 2,
        "is_special_contributor": true,
        "igtf_rate": "3.00",
        "min_amount_local": "1000.00",
        "min_amount_foreign": "100.00",
        "exempt_transactions": ["pago_nomina", "pago_proveedores"],
        "applicable_payment_methods": ["transfer", "credit_card"]
    }
    ```
    """
    # Verificar que la moneda pertenezca a la empresa
    currency = db.query(Currency).filter(
        Currency.id == config_data.currency_id,
        Currency.company_id == config_data.company_id
    ).first()

    if not currency:
        raise HTTPException(
            status_code=404,
            detail="Moneda no encontrada en la empresa"
        )

    # Crear configuración
    igtf_config = IGTFConfig(
        company_id=config_data.company_id,
        currency_id=config_data.currency_id,
        is_special_contributor=config_data.is_special_contributor,
        igtf_rate=config_data.igtf_rate,
        min_amount_local=config_data.min_amount_local,
        min_amount_foreign=config_data.min_amount_foreign,
        is_exempt=config_data.is_exempt,
        exempt_transactions=str(config_data.exempt_transactions) if config_data.exempt_transactions else None,
        applicable_payment_methods=str(config_data.applicable_payment_methods) if config_data.applicable_payment_methods else None,
        valid_from=config_data.valid_from,
        valid_until=config_data.valid_until,
        created_by=current_user.id,
        notes=config_data.notes
    )

    db.add(igtf_config)
    db.commit()
    db.refresh(igtf_config)

    return igtf_config


@router.post("/igtf/calculate")
def calculate_igtf(
    amount: Decimal = Query(..., gt=0, decimal_places=2),
    currency_id: int = Query(..., gt=0),
    payment_method: str = Query("transfer"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Calcula el IGTF para un monto según configuración vigente.

    Args:
        amount: Monto en moneda extranjera
        currency_id: ID de moneda
        payment_method: Método de pago (transfer, cash, etc.)

    Returns:
        JSON con:
        - igtf_amount: Monto de IGTF calculado
        - igtf_applied: Si se aplicó IGTF
        - metadata: Información de configuración usada

    Ejemplo:
        POST /api/v1/currencies/igtf/calculate?amount=1500&currency_id=2
    """
    service = CurrencyService(db)

    try:
        igtf_amount, applied, metadata = service.calculate_igtf_for_transaction(
            amount=amount,
            currency_id=currency_id,
            company_id=current_user.company_id,
            payment_method=payment_method
        )

        return {
            "original_amount": float(amount),
            "igtf_amount": float(igtf_amount),
            "igtf_applied": applied,
            "total_with_igtf": float(amount + igtf_amount),
            "metadata": metadata
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ENDPOINTS: VALIDACIÓN ====================

@router.post("/validate/iso-4217")
def validate_iso_code(
    code: str = Query(..., min_length=3, max_length=3)
):
    """
    Valida un código ISO 4217.

    Retorna:
        - valid: Si es válido
        - currency_name: Nombre oficial (si existe)
        - message: Mensaje de error o confirmación

    Ejemplo:
        POST /api/v1/currencies/validate/iso-4217?code=USD
    """
    logic = CurrencyBusinessLogic()
    is_valid, error_msg = logic.validate_iso_4217(code)

    if is_valid:
        # ISO_4217_CURRENCIES ya está importado al nivel del módulo
        currency_name = ISO_4217_CURRENCIES.get(code.upper(), "Desconocido")

        return {
            "valid": True,
            "code": code.upper(),
            "currency_name": currency_name,
            "message": f"Código {code.upper()} válido según ISO 4217"
        }
    else:
        return {
            "valid": False,
            "code": code.upper(),
            "currency_name": None,
            "message": error_msg
        }


# ==================== ENDPOINTS: CRUD CON PARÁMETROS (DEBEN IR AL FINAL) ====================

@router.get("/{currency_id:int}", response_model=CurrencyResponse)
def get_currency(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """Obtiene detalles de una moneda específica"""
    currency = db.query(Currency).filter(
        Currency.id == currency_id,
        Currency.company_id == current_user.company_id
    ).first()

    if not currency:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")

    return currency


@router.put("/{currency_id:int}", response_model=CurrencyResponse)
def update_currency(
    currency_id: int,
    currency_data: CurrencyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """Actualiza datos de una moneda (excepto tasa, usar endpoint específico)"""
    currency = db.query(Currency).filter(
        Currency.id == currency_id,
        Currency.company_id == current_user.company_id
    ).first()

    if not currency:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")

    # Actualizar campos permitidos
    update_data = currency_data.dict(exclude_unset=True)

    # No permitir modificar ciertos campos críticos
    protected_fields = {'code', 'is_base_currency', 'company_id'}
    for field in protected_fields:
        if field in update_data:
            del update_data[field]

    for key, value in update_data.items():
        setattr(currency, key, value)

    currency.updated_by = current_user.id
    currency.updated_at = datetime.now()

    db.commit()
    db.refresh(currency)

    return currency


@router.delete("/{currency_id:int}")
def delete_currency(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Elimina una moneda (soft delete: is_active=False)

    NO permite eliminar:
    - Moneda base
    - Monedas con historial de transacciones
    """
    currency = db.query(Currency).filter(
        Currency.id == currency_id,
        Currency.company_id == current_user.company_id
    ).first()

    if not currency:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")

    if currency.is_base_currency:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar moneda base. "
                 "Configura otra como base primero."
        )

    # Soft delete
    currency.is_active = False
    currency.updated_by = current_user.id
    currency.updated_at = datetime.now()

    db.commit()

    return {"detail": f"Moneda {currency.code} desactivada correctamente"}


# ==================== ENDPOINTS: TASAS DE CAMBIO ====================

@router.put("/{currency_id:int}/rate", response_model=CurrencyResponse)
def update_currency_rate(
    currency_id: int,
    rate_update: CurrencyRateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token),
    user_ip: str = None
):
    """
    Actualiza la tasa de cambio con REGISTRO HISTÓRICO COMPLETO.

    Genera automáticamente un registro en CurrencyRateHistory con:
    - Valor anterior y nuevo
    - Diferencia y variación porcentual
    - Usuario que realizó el cambio
    - IP address
    - Razón del cambio
    - Timestamp exacto

    Ejemplo:
    ```json
    {
        "new_rate": "37.5000000000",
        "change_reason": "Actualización diaria BCV",
        "change_type": "automatic_api",
        "change_source": "api_bcv"
    }
    ```
    """
    service = CurrencyService(db)

    try:
        currency = service.update_currency_rate(
            currency_id=currency_id,
            rate_update=rate_update,
            company_id=current_user.company_id,
            user_id=current_user.id,
            user_ip=user_ip
        )

        # ✅ Actualizar precios de productos automáticamente
        try:
            price_update_result = ProductPriceUpdater.update_on_currency_change(
                db=db,
                company_id=current_user.company_id,
                currency_id=currency_id
            )
            if price_update_result.get("success"):
                print(f"✅ Precios actualizados: {price_update_result.get('updated')} productos")
            else:
                print(f"⚠️ Error actualizando precios: {price_update_result.get('error')}")
        except Exception as e:
            print(f"⚠️ Error en actualización automática de precios: {e}")

        return currency

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating rate: {str(e)}")


@router.post("/{currency_id:int}/set-base-currency", response_model=CurrencyResponse)
def set_base_currency(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Establece una moneda como la moneda base de la empresa.

    Importante:
    - Desactiva la moneda base anterior (si existe)
    - Activa la nueva moneda base
    - Solo puede haber una moneda base por empresa

    Args:
        currency_id: ID de la moneda que será la nueva base

    Returns:
        La moneda actualizada

    Raises:
        404: Si la moneda no existe
        400: Si la moneda no pertenece a la empresa
    """
    # Verificar que la moneda existe y pertenece a la empresa
    new_base = db.query(Currency).filter(
        Currency.id == currency_id,
        Currency.company_id == current_user.company_id
    ).first()

    if not new_base:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")

    # Buscar la moneda base actual
    current_base = db.query(Currency).filter(
        Currency.company_id == current_user.company_id,
        Currency.is_base_currency == True
    ).first()

    # Si ya es la moneda base, no hacer nada
    if new_base.is_base_currency:
        return new_base

    # Iniciar transacción
    try:
        # Desactivar la moneda base anterior
        if current_base:
            current_base.is_base_currency = False
            current_base.updated_by = current_user.id
            current_base.updated_at = datetime.now()

        # Establecer la nueva moneda base
        new_base.is_base_currency = True
        new_base.is_active = True
        new_base.updated_by = current_user.id
        new_base.updated_at = datetime.now()

        db.commit()
        db.refresh(new_base)

        # ✅ Actualizar precios de productos automáticamente
        try:
            price_update_result = ProductPriceUpdater.update_on_currency_change(
                db=db,
                company_id=current_user.company_id,
                currency_id=currency_id
            )
            if price_update_result.get("success"):
                print(f"✅ Precios actualizados: {price_update_result.get('updated')} productos")
            else:
                print(f"⚠️ Error actualizando precios: {price_update_result.get('error')}")
        except Exception as e:
            print(f"⚠️ Error en actualización automática de precios: {e}")

        return new_base

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al establecer moneda base: {str(e)}")


@router.get("/{currency_id:int}/rate/history", response_model=List[CurrencyRateHistoryResponse])
def get_currency_rate_history(
    currency_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Obtiene historial de cambios de tasa de una moneda.

    Retorna lista ordenada por fecha descendente (más reciente primero).

    Cada registro incluye:
    - old_rate: Tasa anterior
    - new_rate: Tasa nueva
    - rate_difference: Diferencia absoluta
    - rate_variation_percent: Variación porcentual
    - changed_by: Usuario que hizo el cambio
    - change_type: Tipo de cambio
    - changed_at: Timestamp exacto
    - change_reason: Razón del cambio
    """
    service = CurrencyService(db)

    try:
        history = service.get_currency_history(
            currency_id=currency_id,
            company_id=current_user.company_id,
            limit=limit
        )

        return history

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{currency_id:int}/statistics")
def get_currency_statistics(
    currency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Obtiene estadísticas completas de una moneda.

    Incluye:
    - Tasa actual
    - Total de cambios históricos
    - Último cambio
    - Variación promedio
    - Variación máxima/mínima
    - Configuración de IGTF
    - Timestamps de creación/actualización
    """
    service = CurrencyService(db)

    try:
        stats = service.get_currency_statistics(
            company_id=current_user.company_id,
            currency_id=currency_id
        )

        return stats

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== ENDPOINTS: ACTUALIZACIÓN BCV ====================

@router.post("/bcv/update")
def trigger_bcv_update(
    force_update: bool = Query(False, description="Forzar actualización aunque el cache sea válido"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Dispara la actualización automática de tasas BCV.

    Actualiza todas las monedas configuradas con rate_update_method='api_bcv'.
    Genera historial completo de cambios en CurrencyRateHistory.

    Returns:
        JSON con resultado de la actualización (actualizadas, fallidas, omitidas)
    """
    from services.bcv_rate_updater import BCVRateUpdater

    updater = BCVRateUpdater(db, current_user.company_id)

    results = updater.update_bcv_currencies(
        user_id=current_user.id,
        force_update=force_update
    )

    return results


@router.get("/bcv/status")
def get_bcv_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Obtiene el estado del provider BCV.

    Incluye:
    - Disponibilidad del servicio
    - Última actualización
    - Tasas en caché
    - Monedas soportadas
    """
    from services.bcv_rate_updater import BCVRateUpdater

    updater = BCVRateUpdater(db, current_user.company_id)

    return updater.get_bcv_status()


# ==================== ENDPOINTS ADICIONALES PARA FRONTEND ====================
# Estos endpoints complementan los existentes para compatibilidad con frontend

@router.post("/convert")
def convert_currency_post(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Convierte un monto entre monedas usando método POST (compatible con frontend).
    
    Equivalente a GET /convert pero acepta JSON body.
    
    Args:
        request: JSON con from_currency, to_currency, amount
    
    Ejemplo:
        POST /api/v1/currencies/convert
        {
            "from_currency": "USD",
            "to_currency": "EUR", 
            "amount": 100
        }
    """
    from decimal import Decimal
    from schemas import CurrencyConversionRequest
    
    # Validar request
    try:
        conv_request = CurrencyConversionRequest(**request)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    
    service = CurrencyService(db)
    
    try:
        rate, metadata = service.get_exchange_rate_with_metadata(
            from_currency=conv_request.from_currency,
            to_currency=conv_request.to_currency,
            company_id=current_user.company_id
        )
        
        # Convertir
        logic = CurrencyBusinessLogic()
        rate_decimal = Decimal(str(rate)) if not isinstance(rate, Decimal) else rate
        converted, rate_used, method = logic.convert_to_base_currency(
            amount=conv_request.amount,
            from_currency=conv_request.from_currency,
            rate=rate_decimal,
            base_currency=conv_request.to_currency
        )
        
        return {
            "original_amount": float(conv_request.amount),
            "original_currency": conv_request.from_currency.upper(),
            "converted_amount": float(converted),
            "target_currency": conv_request.to_currency.upper(),
            "exchange_rate_used": float(rate_used),
            "conversion_method": method,
            "rate_metadata": metadata
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculate-igtf")
def calculate_igtf_post(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Calcula el IGTF usando método POST (compatible con frontend).
    
    Equivalente a POST /igtf/calculate pero con ruta diferente.
    
    Args:
        request: JSON con amount, currency_id, payment_method
    
    Ejemplo:
        POST /api/v1/currencies/calculate-igtf
        {
            "amount": 100,
            "currency_id": 1,
            "payment_method": "transfer"
        }
    """
    from decimal import Decimal
    from schemas import IGTFCalculationRequest
    
    # Validar request
    try:
        igtf_request = IGTFCalculationRequest(**request)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    
    service = CurrencyService(db)
    
    try:
        igtf_amount, applied, metadata = service.calculate_igtf_for_transaction(
            amount=igtf_request.amount,
            currency_id=igtf_request.currency_id,
            company_id=current_user.company_id,
            payment_method=igtf_request.payment_method
        )
        
        return {
            "original_amount": float(igtf_request.amount),
            "igtf_amount": float(igtf_amount),
            "igtf_applied": applied,
            "total_with_igtf": float(igtf_request.amount + igtf_amount),
            "metadata": metadata
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/conversion-factors")
def list_conversion_factors_alias(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Lista factores de conversión (alias para frontend).
    
    Equivalente a GET /factors pero con ruta diferente.
    """
    currencies = db.query(Currency).filter(
        Currency.company_id == current_user.company_id,
        Currency.is_active == True
    ).all()
    
    factors = []
    
    for currency in currencies:
        logic = CurrencyBusinessLogic()
        factor, method = logic.calculate_conversion_factor(
            code=currency.code,
            rate=currency.exchange_rate,
            method=ConversionMethod(currency.conversion_method) if currency.conversion_method else None
        )
        
        factors.append({
            "code": currency.code,
            "name": currency.name,
            "symbol": currency.symbol,
            "exchange_rate": float(currency.exchange_rate),
            "conversion_method": currency.conversion_method,
            "conversion_factor": float(factor) if factor else None,
            "is_base": currency.is_base_currency,
            "applies_igtf": currency.applies_igtf,
            "igtf_rate": float(currency.igtf_rate) if currency.igtf_rate else None,
            "decimal_places": currency.decimal_places
        })
    
    return factors
