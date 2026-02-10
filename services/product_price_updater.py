"""
Servicio de Actualización Automática de Precios

Actualiza el campo 'price' de los productos basándose en:
- price_usd (precio de referencia, ej: 80)
- Moneda base de la empresa
- Tasas de cambio actuales

Lógica de cálculo:
- VES como base: price = price_usd * tasa_USD (ej: 80 * 344.50 = 27,560)
- USD como base: price = price_usd (ej: 80 USD)
- Otra moneda: price = price_usd * (tasa_base / tasa_USD)
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from models import Product
from models.currency_config import Currency

logger = logging.getLogger(__name__)


class ProductPriceUpdater:
    """Actualiza automáticamente precios de productos cuando cambian las tasas o moneda base."""

    # Tasa USD por defecto (BCV oficial)
    DEFAULT_USD_RATE = Decimal("344.50")

    @staticmethod
    def get_base_currency(db: Session, company_id: int) -> Optional[Currency]:
        """Obtiene la moneda base de la empresa."""
        return db.query(Currency).filter(
            Currency.company_id == company_id,
            Currency.is_base_currency == True
        ).first()

    @staticmethod
    def get_currency_by_code(db: Session, company_id: int, code: str) -> Optional[Currency]:
        """Obtiene una moneda por su código."""
        return db.query(Currency).filter(
            Currency.company_id == company_id,
            Currency.code == code,
            Currency.is_active == True
        ).first()

    @staticmethod
    def get_usd_rate(db: Session, company_id: int) -> Decimal:
        """Obtiene la tasa de cambio actual de USD."""
        usd = ProductPriceUpdater.get_currency_by_code(db, company_id, "USD")
        if usd and usd.exchange_rate:
            return Decimal(str(usd.exchange_rate))
        return ProductPriceUpdater.DEFAULT_USD_RATE

    @staticmethod
    def calculate_price_from_reference(
        price_usd: Decimal,
        base_currency_code: str,
        usd_rate: Decimal,
        base_rate: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calcula el precio local basado en el precio de referencia (price_usd).

        Args:
            price_usd: Precio de referencia (ej: 80)
            base_currency_code: Código de moneda base (VES, USD, EUR, etc.)
            usd_rate: Tasa de USD (respecto a VES)
            base_rate: Tasa de moneda base (si no es VES ni USD)

        Returns:
            Decimal: Precio calculado

        Ejemplos:
            - VES: 80 * 344.50 = 27,560
            - USD: 80
            - EUR: 80 * (401.35 / 344.50) = 93.19
        """
        if not price_usd or price_usd == 0:
            return Decimal("0")

        if base_currency_code == "VES":
            # USD → VES: multiplicar por tasa USD
            return (price_usd * usd_rate).quantize(Decimal("0.01"))

        elif base_currency_code == "USD":
            # Ya está en USD
            return price_usd.quantize(Decimal("0.01"))

        else:
            # Otra moneda: convertir vía USD
            if not base_rate or base_rate == 0:
                logger.warning(f"Tasa inválida para {base_currency_code}, usando USD")
                return price_usd.quantize(Decimal("0.01"))

            converted = price_usd * (base_rate / usd_rate)
            return converted.quantize(Decimal("0.01"))

    @staticmethod
    def update_all_products(
        db: Session,
        company_id: int,
        product_id: Optional[int] = None
    ) -> Dict:
        """
        Actualiza los precios de todos los productos de la empresa.

        Args:
            db: Sesión de base de datos
            company_id: ID de empresa
            product_id: ID de producto específico (opcional)

        Returns:
            Dict con estadísticas
        """
        # 1. Obtener configuración
        base_currency = ProductPriceUpdater.get_base_currency(db, company_id)
        if not base_currency:
            return {
                "success": False,
                "error": "No hay moneda base configurada",
                "updated": 0
            }

        usd_rate = ProductPriceUpdater.get_usd_rate(db, company_id)

        logger.info(
            f"Actualizando precios: base={base_currency.code}, "
            f"tasa_USD={usd_rate}, tasa_base={base_currency.exchange_rate}"
        )

        # 2. Obtener productos
        query = db.query(Product).filter(
            Product.company_id == company_id,
            Product.price_usd.isnot(None),
            Product.price_usd > 0
        )

        if product_id:
            query = query.filter(Product.id == product_id)

        products = query.all()

        # 3. Actualizar cada producto
        updated = 0
        errors = []

        for product in products:
            try:
                new_price = ProductPriceUpdater.calculate_price_from_reference(
                    price_usd=Decimal(str(product.price_usd)),
                    base_currency_code=base_currency.code,
                    usd_rate=usd_rate,
                    base_rate=Decimal(str(base_currency.exchange_rate)) if base_currency.exchange_rate else None
                )

                product.price = float(new_price)
                updated += 1

                logger.debug(
                    f"Producto {product.id}: {product.price_usd} → {new_price} {base_currency.code}"
                )

            except Exception as e:
                logger.error(f"Error actualizando producto {product.id}: {e}")
                errors.append({"product_id": product.id, "error": str(e)})

        # 4. Guardar cambios
        try:
            db.commit()
            logger.info(f"Actualización completada: {updated} productos")

            return {
                "success": True,
                "updated": updated,
                "errors": errors,
                "base_currency": base_currency.code,
                "usd_rate": float(usd_rate)
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error guardando: {e}")
            return {
                "success": False,
                "error": str(e),
                "updated": 0
            }

    @staticmethod
    def update_on_currency_change(
        db: Session,
        company_id: int,
        currency_id: int
    ) -> Dict:
        """
        Se ejecuta cuando cambia una moneda (tasa o moneda base).

        Este método se llama desde el endpoint de currencies.
        """
        logger.info(f"Cambio en moneda {currency_id}, actualizando precios...")
        return ProductPriceUpdater.update_all_products(db, company_id)
