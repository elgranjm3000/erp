"""
Servicio de Cálculo de Facturas - Sistema Multi-Moneda Venezolano
Conversión automática USD→VES con tasas BCV y cálculo de impuestos
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

from models import Invoice, InvoiceItem, Product, Currency
from models.daily_rates import DailyRate
from services.daily_rate_service import DailyRateService


logger = logging.getLogger(__name__)


class InvoiceCalculationService:
    """
    Servicio para cálculo de facturas con conversión automática de monedas.

    Flujo venezolano:
    1. Productos tienen precios en USD (moneda de referencia)
    2. Factura se crea en VES (moneda de pago)
    3. Sistema convierte automáticamente usando tasa BCV del día
    4. Usuario puede override la tasa manualmente si es necesario
    """

    # Constantes Venezuela
    IVA_PERCENTAGE_DEFAULT = 16.0  # 16% IVA
    IGTF_PERCENTAGE_DEFAULT = 3.0  # 3% IGTF para pagos en moneda extranjera

    def __init__(self, db: Session, company_id: int):
        """
        Inicializa el servicio de cálculo de facturas.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
        """
        self.db = db
        self.company_id = company_id
        self.rate_service = DailyRateService(db, company_id)

    def calculate_invoice_preview(
        self,
        items: List[Dict[str, any]],
        customer_id: int,
        payment_method: str,
        manual_exchange_rate: Optional[float] = None,
        igtf_exempt: bool = False,
        iva_percentage: float = IVA_PERCENTAGE_DEFAULT,
        reference_currency_code: str = "USD",
        payment_currency_code: str = "VES"
    ) -> Dict[str, any]:
        """
        Calcula el preview de una factura con conversión automática.

        Args:
            items: Lista de items [{"product_id": 1, "quantity": 10}, ...]
            customer_id: ID del cliente
            payment_method: Método de pago (efectivo, transferencia, zelle, etc.)
            manual_exchange_rate: Tasa manual para override (opcional)
            igtf_exempt: Si está exento de IGTF
            iva_percentage: Porcentaje de IVA (default 16%)
            reference_currency_code: Moneda de referencia (default USD)
            payment_currency_code: Moneda de pago (default VES)

        Returns:
            Dict con el cálculo completo de la factura
        """
        try:
            # Obtener monedas
            reference_currency = self._get_currency(reference_currency_code)
            payment_currency = self._get_currency(payment_currency_code)

            if not reference_currency or not payment_currency:
                raise ValueError(f"Currencies not found: {reference_currency_code} → {payment_currency_code}")

            # Obtener tasa de cambio
            rate_info = self._get_exchange_rate(
                from_currency_code=reference_currency_code,
                to_currency_code=payment_currency_code,
                manual_rate=manual_exchange_rate
            )

            # Calcular items
            calculated_items = []
            subtotal_reference = Decimal("0")  # Subtotal en USD
            subtotal_payment = Decimal("0")  # Subtotal en VES

            for item in items:
                product_id = item.get("product_id")
                quantity = item.get("quantity", 1)

                # Obtener producto
                product = self.db.query(Product).filter(
                    Product.id == product_id,
                    Product.company_id == self.company_id
                ).first()

                if not product:
                    raise ValueError(f"Product {product_id} not found")

                # Obtener precio en moneda de referencia (USD)
                price_reference = self._get_product_price(
                    product=product,
                    currency_id=reference_currency.id
                )

                if not price_reference:
                    raise ValueError(f"Product {product_id} has no price in {reference_currency_code}")

                # Calcular totales
                item_total_reference = Decimal(str(price_reference)) * Decimal(str(quantity))
                item_total_payment = item_total_reference * rate_info["rate"]

                calculated_items.append({
                    "product_id": product_id,
                    "product_name": product.name,
                    "quantity": quantity,
                    "price_per_unit_reference": float(price_reference),
                    "price_per_unit_payment": float(Decimal(str(price_reference)) * rate_info["rate"]),
                    "total_reference": float(item_total_reference),
                    "total_payment": float(item_total_payment)
                })

                subtotal_reference += item_total_reference
                subtotal_payment += item_total_payment

            # Calcular IVA (sobre el subtotal en moneda de pago)
            iva_amount = subtotal_payment * (Decimal(str(iva_percentage)) / Decimal("100"))
            subtotal_with_iva = subtotal_payment + iva_amount

            # Calcular IGTF (3% si aplica)
            igtf_amount = Decimal("0")
            if not igtf_exempt and self._applies_igtf(payment_method, payment_currency_code):
                igtf_amount = subtotal_with_iva * (Decimal(str(self.IGTF_PERCENTAGE_DEFAULT)) / Decimal("100"))

            # Total final
            total_amount = subtotal_with_iva + igtf_amount

            return {
                "items": calculated_items,
                "reference_currency": reference_currency_code,
                "payment_currency": payment_currency_code,
                "exchange_rate": {
                    "rate": float(rate_info["rate"]),
                    "rate_date": rate_info["rate_date"].isoformat(),
                    "source": rate_info["source"],
                    "inverse_rate": float(rate_info["inverse_rate"])
                },
                "totals": {
                    "subtotal_reference": float(subtotal_reference),
                    "subtotal_payment": float(subtotal_payment),
                    "iva_percentage": iva_percentage,
                    "iva_amount": float(iva_amount),
                    "igtf_percentage": self.IGTF_PERCENTAGE_DEFAULT if not igtf_exempt else 0,
                    "igtf_amount": float(igtf_amount),
                    "igtf_exempt": igtf_exempt,
                    "total_amount": float(total_amount)
                },
                "payment_method": payment_method
            }

        except Exception as e:
            logger.error(f"Error calculating invoice preview: {e}")
            raise

    def create_invoice_with_conversion(
        self,
        items: List[Dict[str, any]],
        customer_id: int,
        payment_method: str,
        user_id: int,
        invoice_number: str,
        control_number: Optional[str] = None,
        manual_exchange_rate: Optional[float] = None,
        igtf_exempt: bool = False,
        iva_percentage: float = IVA_PERCENTAGE_DEFAULT,
        reference_currency_code: str = "USD",
        payment_currency_code: str = "VES",
        notes: Optional[str] = None,
        warehouse_id: Optional[int] = None
    ) -> Invoice:
        """
        Crea una factura con conversión automática de monedas.

        Args:
            items: Lista de items con product_id y quantity
            customer_id: ID del cliente
            payment_method: Método de pago
            user_id: ID del usuario que crea
            invoice_number: Número de factura
            control_number: Número de control (opcional)
            manual_exchange_rate: Tasa manual para override
            igtf_exempt: Exento de IGTF
            iva_percentage: Porcentaje de IVA
            reference_currency_code: Moneda de referencia (USD)
            payment_currency_code: Moneda de pago (VES)
            notes: Notas de la factura
            warehouse_id: ID del almacén (opcional)

        Returns:
            Invoice creada
        """
        try:
            # Calcular preview
            preview = self.calculate_invoice_preview(
                items=items,
                customer_id=customer_id,
                payment_method=payment_method,
                manual_exchange_rate=manual_exchange_rate,
                igtf_exempt=igtf_exempt,
                iva_percentage=iva_percentage,
                reference_currency_code=reference_currency_code,
                payment_currency_code=payment_currency_code
            )

            # Obtener monedas
            reference_currency = self._get_currency(reference_currency_code)
            payment_currency = self._get_currency(payment_currency_code)

            # Crear factura
            invoice = Invoice(
                company_id=self.company_id,
                customer_id=customer_id,
                warehouse_id=warehouse_id,
                invoice_number=invoice_number,
                control_number=control_number,
                currency_id=payment_currency.id,  # Moneda de pago (VES)
                reference_currency_id=reference_currency.id,  # Moneda de referencia (USD)
                exchange_rate=preview["totals"]["subtotal_payment"] / preview["totals"]["subtotal_reference"],
                manual_exchange_rate=manual_exchange_rate,
                date=datetime.now(),
                due_date=datetime.now(),
                payment_method=payment_method,
                transaction_type="contado" if payment_method in ["efectivo", "transferencia", "pago_movil"] else "credito",
                subtotal=preview["totals"]["subtotal_payment"],
                total_amount=preview["totals"]["total_amount"],
                total_with_taxes=preview["totals"]["total_amount"],
                iva_percentage=preview["totals"]["iva_percentage"],
                iva_amount=preview["totals"]["iva_amount"],
                igtf_percentage=preview["totals"]["igtf_percentage"],
                igtf_amount=preview["totals"]["igtf_amount"],
                igtf_exempt=igtf_exempt,
                discount=0.0,
                status="factura",
                notes=notes
            )

            self.db.add(invoice)
            self.db.flush()  # Para obtener el ID

            # Crear items de la factura
            for item_preview in preview["items"]:
                invoice_item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=item_preview["product_id"],
                    quantity=item_preview["quantity"],
                    price_per_unit=item_preview["price_per_unit_payment"],  # Precio en VES
                    total_price=item_preview["total_payment"]  # Total en VES
                )
                self.db.add(invoice_item)

            self.db.commit()
            self.db.refresh(invoice)

            logger.info(
                f"Invoice {invoice_number} created: "
                f"{preview['totals']['subtotal_reference']} {reference_currency_code} → "
                f"{preview['totals']['total_amount']} {payment_currency_code} "
                f"@ {preview['exchange_rate']['rate']}"
            )

            return invoice

        except Exception as e:
            logger.error(f"Error creating invoice with conversion: {e}")
            self.db.rollback()
            raise

    def _get_exchange_rate(
        self,
        from_currency_code: str,
        to_currency_code: str,
        manual_rate: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Obtiene la tasa de cambio para la factura.

        Args:
            from_currency_code: Moneda origen
            to_currency_code: Moneda destino
            manual_rate: Tasa manual para override

        Returns:
            Dict con rate, rate_date, source, inverse_rate
        """
        if manual_rate is not None:
            return {
                "rate": Decimal(str(manual_rate)),
                "rate_date": date.today(),
                "source": "MANUAL",
                "inverse_rate": Decimal("1") / Decimal(str(manual_rate)) if manual_rate != 0 else None
            }

        # Buscar tasa del día
        daily_rate = self.rate_service.get_today_rate(from_currency_code, to_currency_code)

        if not daily_rate:
            raise ValueError(
                f"No exchange rate available for {from_currency_code} → {to_currency_code}. "
                f"Please sync BCV rates or provide a manual rate."
            )

        return {
            "rate": Decimal(str(daily_rate.exchange_rate)),
            "rate_date": daily_rate.rate_date,
            "source": daily_rate.source,
            "inverse_rate": Decimal(str(daily_rate.inverse_rate)) if daily_rate.inverse_rate else None
        }

    def _get_currency(self, code: str) -> Optional[Currency]:
        """Obtiene una moneda por código"""
        return self.db.query(Currency).filter(
            Currency.company_id == self.company_id,
            Currency.code == code,
            Currency.is_active == True
        ).first()

    def _get_product_price(self, product: Product, currency_id: int) -> Optional[float]:
        """
        Obtiene el precio de un producto en una moneda específica.

        Args:
            product: Producto
            currency_id: ID de la moneda

        Returns:
            Precio o None si no existe
        """
        # Buscar en ProductPrice
        from models import ProductPrice
        product_price = self.db.query(ProductPrice).filter(
            ProductPrice.product_id == product.id,
            ProductPrice.currency_id == currency_id
        ).first()

        if product_price:
            return product_price.price

        # Si no hay precio específico y es USD, usar el price del producto
        usd_currency = self._get_currency("USD")
        if usd_currency and currency_id == usd_currency.id:
            return float(product.price)

        return None

    def _applies_igtf(self, payment_method: str, currency_code: str) -> bool:
        """
        Determina si aplica IGTF según el método de pago y moneda.

        El IGTF (3%) aplica cuando:
        - El pago es en moneda extranjera (USD, EUR)
        - El pago es con divisas (tarjeta de crédito extranjera, zelle, etc.)

        Args:
            payment_method: Método de pago
            currency_code: Moneda de pago

        Returns:
            True si aplica IGTF
        """
        # Si la moneda de pago es VES, no aplica IGTF
        if currency_code == "VES":
            return False

        # Métodos de pago que típicamente usan divisas
        foreign_payment_methods = ["zelle", "tarjeta_credito", "tarjeta_debito", "transferencia_internacional"]

        return payment_method.lower() in [m.lower() for m in foreign_payment_methods]
