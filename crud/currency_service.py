"""
Servicio de Monedas - CurrencyService
Proporciona funcionalidades escalables para gestión de monedas, tasas de cambio
y conversión histórica de montos.
"""

from datetime import datetime
from typing import Optional, List, Dict, Tuple
from sqlalchemy import and_
from sqlalchemy.orm import Session

import models
import schemas


class CurrencyService:
    """Servicio centralizado para gestión de monedas y tasas de cambio"""

    @staticmethod
    def record_exchange_rate(
        db: Session,
        company_id: int,
        from_currency_id: int,
        to_currency_id: int,
        rate: float,
        recorded_at: Optional[datetime] = None
    ) -> models.ExchangeRateHistory:
        """
        Registrar una tasa de cambio en el historial.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
            from_currency_id: ID de moneda origen
            to_currency_id: ID de moneda destino
            rate: Tasa de cambio (1 from_currency = rate to_currency)
            recorded_at: Fecha de la tasa (default: ahora)

        Returns:
            ExchangeRateHistory: Registro creado
        """
        if recorded_at is None:
            recorded_at = datetime.utcnow()

        exchange_rate = models.ExchangeRateHistory(
            company_id=company_id,
            from_currency_id=from_currency_id,
            to_currency_id=to_currency_id,
            rate=rate,
            recorded_at=recorded_at
        )

        db.add(exchange_rate)
        db.commit()
        db.refresh(exchange_rate)

        return exchange_rate

    @staticmethod
    def get_latest_exchange_rate(
        db: Session,
        company_id: int,
        from_currency_id: int,
        to_currency_id: int
    ) -> Optional[models.ExchangeRateHistory]:
        """
        Obtener la tasa de cambio más reciente entre dos monedas.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
            from_currency_id: ID de moneda origen
            to_currency_id: ID de moneda destino

        Returns:
            ExchangeRateHistory o None si no existe
        """
        return db.query(models.ExchangeRateHistory).filter(
            models.ExchangeRateHistory.company_id == company_id,
            models.ExchangeRateHistory.from_currency_id == from_currency_id,
            models.ExchangeRateHistory.to_currency_id == to_currency_id
        ).order_by(
            models.ExchangeRateHistory.recorded_at.desc()
        ).first()

    @staticmethod
    def get_exchange_rate_at_date(
        db: Session,
        company_id: int,
        from_currency_id: int,
        to_currency_id: int,
        date: datetime
    ) -> Optional[models.ExchangeRateHistory]:
        """
        Obtener la tasa de cambio vigente en una fecha específica.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
            from_currency_id: ID de moneda origen
            to_currency_id: ID de moneda destino
            date: Fecha para buscar la tasa

        Returns:
            ExchangeRateHistory o None si no existe
        """
        return db.query(models.ExchangeRateHistory).filter(
            models.ExchangeRateHistory.company_id == company_id,
            models.ExchangeRateHistory.from_currency_id == from_currency_id,
            models.ExchangeRateHistory.to_currency_id == to_currency_id,
            models.ExchangeRateHistory.recorded_at <= date
        ).order_by(
            models.ExchangeRateHistory.recorded_at.desc()
        ).first()

    @staticmethod
    def convert_amount(
        db: Session,
        company_id: int,
        amount: float,
        from_currency_id: int,
        to_currency_id: int,
        date: Optional[datetime] = None
    ) -> Tuple[float, Optional[float]]:
        """
        Convertir un monto de una moneda a otra usando tasas históricas o actuales.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
            amount: Monto a convertir
            from_currency_id: ID de moneda origen
            to_currency_id: ID de moneda destino
            date: Fecha de la tasa a usar (None = tasa actual)

        Returns:
            Tuple[monto_convertido, tasa_usada]
        """
        # Si es la misma moneda, retornar el mismo monto
        if from_currency_id == to_currency_id:
            return amount, 1.0

        # Obtener tasa de cambio
        if date:
            rate_record = CurrencyService.get_exchange_rate_at_date(
                db, company_id, from_currency_id, to_currency_id, date
            )
        else:
            rate_record = CurrencyService.get_latest_exchange_rate(
                db, company_id, from_currency_id, to_currency_id
            )

        if not rate_record:
            raise ValueError(
                f"No exchange rate found from currency {from_currency_id} "
                f"to {to_currency_id} for date {date or 'now'}"
            )

        converted_amount = amount * rate_record.rate
        return converted_amount, rate_record.rate

    @staticmethod
    def get_base_currency(db: Session, company_id: int) -> Optional[models.Currency]:
        """
        Obtener la moneda base de una empresa.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa

        Returns:
            Currency o None si no tiene moneda base
        """
        return db.query(models.Currency).filter(
            models.Currency.company_id == company_id,
            models.Currency.is_base_currency == True,
            models.Currency.is_active == True
        ).first()

    @staticmethod
    def get_all_active_currencies(db: Session, company_id: int) -> List[models.Currency]:
        """
        Obtener todas las monedas activas de una empresa.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa

        Returns:
            List[Currency]: Lista de monedas activas
        """
        return db.query(models.Currency).filter(
            models.Currency.company_id == company_id,
            models.Currency.is_active == True
        ).order_by(models.Currency.code.asc()).all()

    @staticmethod
    def set_product_price(
        db: Session,
        product_id: int,
        currency_id: int,
        price: float,
        is_base_price: bool = False
    ) -> models.ProductPrice:
        """
        Establecer el precio de un producto en una moneda específica.
        Si ya existe, lo actualiza.

        Args:
            db: Sesión de base de datos
            product_id: ID del producto
            currency_id: ID de la moneda
            price: Precio en esa moneda
            is_base_price: Si es el precio principal del producto

        Returns:
            ProductPrice: Precio creado o actualizado
        """
        # Buscar si ya existe
        product_price = db.query(models.ProductPrice).filter(
            models.ProductPrice.product_id == product_id,
            models.ProductPrice.currency_id == currency_id
        ).first()

        if product_price:
            # Actualizar
            product_price.price = price
            product_price.is_base_price = is_base_price
            product_price.updated_at = datetime.utcnow()
        else:
            # Crear nuevo
            product_price = models.ProductPrice(
                product_id=product_id,
                currency_id=currency_id,
                price=price,
                is_base_price=is_base_price
            )
            db.add(product_price)

        db.commit()
        db.refresh(product_price)

        return product_price

    @staticmethod
    def get_product_price(
        db: Session,
        product_id: int,
        currency_id: int
    ) -> Optional[models.ProductPrice]:
        """
        Obtener el precio de un producto en una moneda específica.

        Args:
            db: Sesión de base de datos
            product_id: ID del producto
            currency_id: ID de la moneda

        Returns:
            ProductPrice o None si no existe
        """
        return db.query(models.ProductPrice).filter(
            models.ProductPrice.product_id == product_id,
            models.ProductPrice.currency_id == currency_id
        ).first()

    @staticmethod
    def get_product_prices(
        db: Session,
        product_id: int
    ) -> List[models.ProductPrice]:
        """
        Obtener todos los precios de un producto en todas las monedas.

        Args:
            db: Sesión de base de datos
            product_id: ID del producto

        Returns:
            List[ProductPrice]: Lista de precios
        """
        return db.query(models.ProductPrice).filter(
            models.ProductPrice.product_id == product_id
        ).all()

    @staticmethod
    def sync_product_prices_to_currencies(
        db: Session,
        company_id: int,
        product_id: int,
        base_price: float,
        base_currency_id: int
    ) -> List[models.ProductPrice]:
        """
        Sincronizar el precio de un producto a todas las monedas de la empresa
        usando las tasas de cambio actuales.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
            product_id: ID del producto
            base_price: Precio en moneda base
            base_currency_id: ID de la moneda base

        Returns:
            List[ProductPrice]: Lista de precios creados/actualizados
        """
        currencies = CurrencyService.get_all_active_currencies(db, company_id)
        prices = []

        for currency in currencies:
            if currency.id == base_currency_id:
                # Moneda base
                price = CurrencyService.set_product_price(
                    db, product_id, currency.id, base_price, is_base_price=True
                )
            else:
                # Convertir a esta moneda
                try:
                    converted_price, rate = CurrencyService.convert_amount(
                        db, company_id, base_price, base_currency_id, currency.id
                    )
                    price = CurrencyService.set_product_price(
                        db, product_id, currency.id, converted_price, is_base_price=False
                    )
                except ValueError:
                    # No hay tasa de cambio, saltar esta moneda
                    continue

            prices.append(price)

        return prices

    @staticmethod
    def prepare_transaction_currency_data(
        db: Session,
        company_id: int,
        currency_id: Optional[int],
        use_base_currency: bool = True
    ) -> Dict:
        """
        Preparar datos de moneda para una transacción (factura/compra).
        Si no se especifica moneda, usa la moneda base de la empresa.
        Registra la tasa de cambio actual en el historial si no existe.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
            currency_id: ID de la moneda a usar (None = base)
            use_base_currency: Si debe usar moneda base por defecto

        Returns:
            Dict con: currency_id, exchange_rate, exchange_rate_date
        """
        # Obtener moneda base
        base_currency = CurrencyService.get_base_currency(db, company_id)

        if not base_currency:
            raise ValueError("Company has no base currency configured")

        # Determinar moneda a usar
        if currency_id is None and use_base_currency:
            currency_id = base_currency.id

        # Si es la moneda base, no hay conversión
        if currency_id == base_currency.id:
            return {
                "currency_id": base_currency.id,
                "exchange_rate": 1.0,
                "exchange_rate_date": datetime.utcnow()
            }

        # Obtener o registrar tasa de cambio
        from_currencies = CurrencyService.get_all_active_currencies(db, company_id)
        target_currency = None

        for curr in from_currencies:
            if curr.id == currency_id:
                target_currency = curr
                break

        if not target_currency:
            raise ValueError(f"Currency {currency_id} not found or not active")

        # Buscar tasa más reciente
        latest_rate = CurrencyService.get_latest_exchange_rate(
            db, company_id, base_currency.id, target_currency.id
        )

        if latest_rate:
            rate = latest_rate.rate
            rate_date = latest_rate.recorded_at
        else:
            # Usar la tasa configurada en la moneda
            rate = target_currency.exchange_rate
            rate_date = datetime.utcnow()

            # Registrar en historial
            CurrencyService.record_exchange_rate(
                db, company_id, base_currency.id, target_currency.id, rate, rate_date
            )

        return {
            "currency_id": target_currency.id,
            "exchange_rate": rate,
            "exchange_rate_date": rate_date
        }

    @staticmethod
    def format_currency_amount(
        amount: float,
        currency_code: str,
        currency_symbol: str,
        decimals: int = 2
    ) -> str:
        """
        Formatear un monto con símbolo de moneda.

        Args:
            amount: Monto a formatear
            currency_code: Código de moneda (USD, VES, etc.)
            currency_symbol: Símbolo ($, Bs, €)
            decimals: Número de decimales

        Returns:
            str: Monto formateado (ej: "$100.00", "Bs 3,600.00")
        """
        formatted = f"{amount:,.{decimals}f}"

        if currency_symbol == "$":
            return f"${formatted}"
        elif currency_symbol == "€":
            return f"{formatted}€"
        else:
            return f"{currency_symbol} {formatted}"
