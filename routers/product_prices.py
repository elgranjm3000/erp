"""
Router para Gestión de Precios de Productos por Moneda
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from database import get_db
from auth import verify_token
from models import User

from services.product_price_updater import ProductPriceUpdater

router = APIRouter(prefix="/api/v1/product-prices", tags=["Precios de Productos"])

# ==================== ACTUALIZACIÓN AUTOMÁTICA ====================

@router.post("/auto-update")
def trigger_price_update(
    currency_id: int = Query(..., description="ID de moneda que cambió (USD, EUR)"),
    old_rate: Decimal = Query(..., description="Tasa anterior"),
    new_rate: Decimal = Query(..., description="Tasa nueva"),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    Actualiza automáticamente precios VES después de un cambio de tasa.
    """
    updater = ProductPriceUpdater(db)

    results = updater.update_prices_after_rate_change(
        company_id=current_user.company_id,
        currency_id=currency_id,
        old_rate=old_rate,
        new_rate=new_rate,
        user_id=current_user.id
    )

    return results

# ==================== HISTORIAL DE PRECIOS ====================

@router.get("/history/{product_id}")
def get_price_history(
    product_id: int,
    currency_id: int = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """Obtiene historial de cambios de precio de un producto."""
    from models.product_price_history import ProductPriceHistory

    query = db.query(ProductPriceHistory).filter(
        ProductPriceHistory.product_id == product_id,
        ProductPriceHistory.company_id == current_user.company_id
    )

    if currency_id:
        query = query.filter(ProductPriceHistory.currency_id == currency_id)

    history = query.order_by(
        ProductPriceHistory.changed_at.desc()
    ).limit(limit).all()

    return [
        {
            "id": h.id,
            "currency_id": h.currency_id,
            "old_price": float(h.old_price),
            "new_price": float(h.new_price),
            "difference": float(h.price_difference),
            "variation_percent": float(h.price_variation_percent) if h.price_variation_percent else None,
            "change_type": h.change_type,
            "change_source": h.change_source,
            "change_reason": h.change_reason,
            "changed_at": h.changed_at.isoformat(),
            "changed_by": h.changed_by
        }
        for h in history
    ]
