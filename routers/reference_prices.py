"""
API Endpoints para Precios de Referencia (REF)

Sistema multi-moneda para Venezuela con contexto económico inflacionario.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from decimal import Decimal

from database import get_db
from models import User
from auth import verify_token
from services.reference_price_service import ReferencePriceService

router = APIRouter(prefix="/api/v1/reference-prices", tags=["💵 Precios de Referencia (REF)"])


# ==================== MODELOS PYDANTIC ====================

class ReferencePriceResponse(BaseModel):
    """Respuesta con precio de referencia"""
    product_id: int
    product_name: str
    price_reference: Optional[float]
    reference_currency: str
    available: bool
    price_legacy: Optional[float] = None


class ReferencePriceSummaryResponse(BaseModel):
    """Resumen de precio REF + precio VES calculado"""
    product_id: int
    product_name: str
    price_reference: Optional[float]
    price_ves: Optional[float]
    reference_currency: str
    exchange_rate: Optional[float]
    has_reference_price: bool


class InvoiceItemRequest(BaseModel):
    """Request para calcular item de factura"""
    product_id: int
    quantity: int
    price_reference_override: Optional[float] = None


class InvoiceCalculationRequest(BaseModel):
    """Request para cálculo completo de factura"""
    items: List[InvoiceItemRequest]
    customer_id: Optional[int] = None
    payment_method: str = 'transferencia'
    manual_exchange_rate: Optional[float] = None
    discount_percentage: Optional[float] = None


class InvoiceItemCalculation(BaseModel):
    """Item de factura calculado"""
    product_id: int
    product_name: str
    quantity: int
    unit_price_reference: float
    unit_price_target: float
    subtotal_reference: float
    subtotal_target: float
    exchange_rate: float
    rate_date: date
    rate_source: str
    iva_percentage: float
    iva_amount: float
    igtf_percentage: float
    igtf_amount: float
    igtf_exempt: bool
    total_item: float


class InvoiceTotalsResponse(BaseModel):
    """Totales de factura calculada"""
    reference_currency: str
    payment_currency: str
    items: List[InvoiceItemCalculation]
    subtotal_reference: float
    subtotal_target: float
    iva_amount: float
    igtf_amount: float
    discount_amount: float
    total_amount: float
    exchange_rate: Optional[float]
    rate_date: Optional[date]
    rate_source: Optional[str]


# ==================== ENDPOINTS ====================

@router.get("/products/{product_id}/reference-price", response_model=ReferencePriceResponse)
def get_product_reference_price(
    product_id: int,
    reference_currency: str = Query("USD", description="Moneda de referencia (default: USD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Obtiene el precio de referencia de un producto.

    El precio de referencia es el precio oficial en moneda estable (USD).
    Este es el precio que se usa como base para todas las conversiones.

    Ejemplo:
        GET /api/v1/reference-prices/products/123/reference-price

    Response:
        {
            "product_id": 123,
            "product_name": "Laptop HP",
            "price_reference": 800.00,
            "reference_currency": "USD",
            "available": true
        }
    """
    service = ReferencePriceService(db, current_user.company_id)

    try:
        result = service.get_product_reference_price(product_id, reference_currency)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} not found"
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting reference price: {str(e)}"
        )


@router.get("/products/summary", response_model=List[ReferencePriceSummaryResponse])
def get_products_reference_summary(
    product_ids: str = Query(..., description="Comma-separated product IDs (ej: 1,2,3)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Obtiene resumen de precios REF para múltiples productos.

    Incluye el precio REF (USD) y el precio en VES calculado
    con la tasa BCV del día.

    Ejemplo:
        GET /api/v1/reference-prices/products/summary?product_ids=1,2,3

    Response:
        [
            {
                "product_id": 1,
                "product_name": "Laptop HP",
                "price_reference": 800.00,
                "price_ves": 275605.60,
                "reference_currency": "USD",
                "exchange_rate": 344.507,
                "has_reference_price": true
            }
        ]
    """
    service = ReferencePriceService(db, current_user.company_id)

    try:
        # Parsear product_ids
        ids_list = [int(id.strip()) for id in product_ids.split(',')]

        result = service.get_reference_price_summary(ids_list)
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid product_ids format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting products summary: {str(e)}"
        )


@router.post("/invoices/calculate-item", response_model=InvoiceItemCalculation)
def calculate_invoice_item(
    item: InvoiceItemRequest,
    payment_method: str = Query('transferencia', description="Método de pago"),
    manual_exchange_rate: Optional[float] = Query(None, description="Tasa manual opcional"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Calcula un item de factura usando precio de referencia.

    Implementa la lógica completa:
    1. Obtiene precio REF del producto (USD)
    2. Convierte a VES usando tasa BCV del día
    3. Calcula IVA (16%) sobre monto en VES
    4. Calcula IGTF (3%) si no es efectivo

    Ejemplo:
        POST /api/v1/reference-prices/invoices/calculate-item?payment_method=transferencia

    Body:
        {
            "product_id": 1,
            "quantity": 2,
            "price_reference_override": 850.00  // Opcional
        }
    """
    service = ReferencePriceService(db, current_user.company_id)

    try:
        result = service.calculate_invoice_item_with_reference(
            product_id=item.product_id,
            quantity=item.quantity,
            price_reference_override=(
                Decimal(str(item.price_reference_override))
                if item.price_reference_override else None
            ),
            payment_method=payment_method,
            manual_exchange_rate=manual_exchange_rate
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating invoice item: {str(e)}"
        )


@router.post("/invoices/calculate-totals", response_model=InvoiceTotalsResponse)
def calculate_invoice_totals(
    request: InvoiceCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Calcula los totales de una factura completa usando precios de referencia.

    Este es el endpoint principal para crear facturas con precios REF.
    Realiza todos los cálculos necesarios incluyendo IVA e IGTF.

    Ejemplo:
        POST /api/v1/reference-prices/invoices/calculate-totals

    Body:
        {
            "items": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 1}
            ],
            "payment_method": "transferencia",
            "manual_exchange_rate": null,
            "discount_percentage": 10.0
        }

    Response:
        {
            "reference_currency": "USD",
            "payment_currency": "VES",
            "items": [...],
            "subtotal_reference": 2400.00,
            "subtotal_target": 826816.80,
            "iva_amount": 132290.69,
            "igtf_amount": 28793.25,
            "total_amount": 962810.74,
            "exchange_rate": 344.507
        }
    """
    service = ReferencePriceService(db, current_user.company_id)

    try:
        # Convertir items a formato correcto
        items_data = []
        for item in request.items:
            item_dict = {
                "product_id": item.product_id,
                "quantity": item.quantity
            }
            if item.price_reference_override:
                item_dict["price_reference_override"] = item.price_reference_override
            items_data.append(item_dict)

        result = service.calculate_invoice_totals_with_reference(
            items=items_data,
            customer_id=request.customer_id,
            payment_method=request.payment_method,
            manual_exchange_rate=request.manual_exchange_rate,
            discount_percentage=request.discount_percentage
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating invoice totals: {str(e)}"
        )
