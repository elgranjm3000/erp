"""
Servicio de Precios de Referencia (REF) para Venezuela

Contexto Económico:
- Los productos en Venezuela se cotizan en USD (moneda estable)
- Las ventas se realizan en VES (Bolívares) usando tasa BCV del día
- Es crucial mantener un registro histórico de las conversiones
- IVA (16%) se calcula sobre el precio en VES
- IGTF (3%) solo aplica a pagos electrónicos

Autor: Arquitecto Senior
Especialidad: Sistemas Multi-moneda para Economías Inflacionarias
"""

import logging
from typing import Dict, List, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session

from models import Product
from services.daily_rate_service import DailyRateService

logger = logging.getLogger(__name__)


class ReferencePriceService:
    """
    Servicio para gestión de precios de referencia en contextos inflacionarios.

    Principios de diseño:
    1. Single Source of Truth: precio_usd como referencia única
    2. Trazabilidad completa: cada conversión está registrada
    3. Precisión financiera: Decimal con 2 decimales
    4. Idempotencia: mismas entradas = mismas salidas
    """

    # Constantes para Venezuela
    VES_CODE = "VES"
    USD_CODE = "USD"
    DEFAULT_IGTF_PERCENTAGE = 3.0
    DEFAULT_IVA_PERCENTAGE = 16.0

    # Métodos de pago exentos de IGTF
    IGTF_EXEMPT_METHODS = ['efectivo', 'cash']

    def __init__(self, db: Session, company_id: int):
        """
        Inicializa el servicio de precios de referencia.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
        """
        self.db = db
        self.company_id = company_id
        self.rate_service = DailyRateService(db, company_id)

        # Precisión para cálculos financieros (2 decimales)
        self.quantize = Decimal('0.01')

    def get_product_reference_price(
        self,
        product_id: int,
        reference_currency: str = USD_CODE
    ) -> Optional[Dict[str, any]]:
        """
        Obtiene el precio de referencia de un producto.

        El precio de referencia es el precio "oficial" del producto
        en la moneda estable (generalmente USD).

        Args:
            product_id: ID del producto
            reference_currency: Moneda de referencia (default: USD)

        Returns:
            Dict con:
                - product_id
                - price_reference: Precio en moneda de referencia
                - reference_currency: Código de moneda de referencia
                - available: True si tiene precio de referencia
        """
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.company_id == self.company_id
        ).first()

        if not product:
            logger.error(f"Product {product_id} not found for company {self.company_id}")
            return None

        # Obtener precio de referencia (price_usd)
        price_ref = None
        if reference_currency == self.USD_CODE and product.price_usd is not None:
            price_ref = Decimal(str(product.price_usd))

        return {
            "product_id": product_id,
            "product_name": product.name,
            "price_reference": price_ref,
            "reference_currency": reference_currency,
            "available": price_ref is not None,
            "price_legacy": Decimal(str(product.price)) if product.price else None
        }

    def calculate_price_from_reference(
        self,
        reference_price: Decimal,
        target_currency: str,
        rate_date: Optional[date] = None,
        manual_rate: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Convierte un precio de referencia a moneda local.

        Este es el método core del sistema. Convierte el precio REF
        (en USD) a la moneda de pago (VES) usando la tasa BCV.

        Args:
            reference_price: Precio en moneda de referencia (USD)
            target_currency: Moneda destino (VES)
            rate_date: Fecha de la tasa a usar (default: hoy)
            manual_rate: Tasa manual opcional para override

        Returns:
            Dict con:
                - price_reference: Precio original en USD
                - price_target: Precio convertido en VES
                - exchange_rate: Tasa usada
                - rate_date: Fecha de la tasa
                - rate_source: 'BCV' o 'MANUAL'
        """
        if reference_price is None:
            raise ValueError("Reference price cannot be None")

        # Obtener tasa de cambio
        if manual_rate is not None:
            exchange_rate = Decimal(str(manual_rate))
            rate_source = "MANUAL"
            used_date = rate_date or date.today()
        else:
            daily_rate = self.rate_service.get_today_rate(
                self.USD_CODE,
                target_currency
            )

            if not daily_rate:
                raise ValueError(
                    f"No rate available for {self.USD_CODE} → {target_currency}. "
                    f"Please sync BCV rates or provide manual_rate."
                )

            exchange_rate = Decimal(str(daily_rate.exchange_rate))
            rate_source = daily_rate.source
            used_date = daily_rate.rate_date

        # Calcular precio en moneda destino
        price_target = (reference_price * exchange_rate).quantize(self.quantize)

        return {
            "price_reference": reference_price.quantize(self.quantize),
            "price_target": price_target,
            "exchange_rate": exchange_rate.quantize(self.quantize),
            "rate_date": used_date,
            "rate_source": rate_source
        }

    def calculate_invoice_item_with_reference(
        self,
        product_id: int,
        quantity: int,
        price_reference_override: Optional[Decimal] = None,
        payment_method: str = 'transferencia',
        manual_exchange_rate: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Calcula el precio de un item de factura usando precio de referencia.

        Este método implementa la lógica completa de conversión para
        un item de factura en Venezuela:

        1. Obtiene precio REF del producto (USD)
        2. Convierte a VES usando tasa BCV del día
        3. Calcula subtotal en ambas monedas
        4. Calcula IVA (16%) sobre el monto en VES
        5. Calcula IGTF (3%) si aplica

        Args:
            product_id: ID del producto
            quantity: Cantidad
            price_reference_override: Override del precio REF (opcional)
            payment_method: Método de pago ('efectivo', 'transferencia', etc.)
            manual_exchange_rate: Tasa manual opcional

        Returns:
            Dict con toda la información del item calculado
        """
        # 1. Obtener precio de referencia
        product_info = self.get_product_reference_price(product_id)
        if not product_info or not product_info['available']:
            raise ValueError(
                f"Product {product_id} does not have a reference price. "
                f"Please set price_usd before creating invoices."
            )

        price_ref = price_reference_override or product_info['price_reference']

        # 2. Convertir a VES
        conversion = self.calculate_price_from_reference(
            reference_price=price_ref,
            target_currency=self.VES_CODE,
            manual_rate=manual_exchange_rate
        )

        # 3. Calcular subtotales
        subtotal_ref = (price_ref * quantity).quantize(self.quantize)
        subtotal_target = (conversion['price_target'] * quantity).quantize(self.quantize)

        # 4. Calcular IVA (16% sobre monto en VES)
        iva_amount = (subtotal_target * Decimal(str(self.DEFAULT_IVA_PERCENTAGE)) / 100).quantize(self.quantize)

        # 5. Calcular IGTF (3% solo si NO es efectivo)
        igtf_exempt = payment_method.lower() in self.IGTF_EXEMPT_METHODS
        igtf_percentage = Decimal(str(self.DEFAULT_IGTF_PERCENTAGE))

        if igtf_exempt:
            igtf_amount = Decimal('0').quantize(self.quantize)
        else:
            # IGTF se calcula sobre el subtotal + IVA
            base_igtf = subtotal_target + iva_amount
            igtf_amount = (base_igtf * igtf_percentage / 100).quantize(self.quantize)

        # 6. Total del item
        total_item = subtotal_target + iva_amount + igtf_amount

        return {
            "product_id": product_id,
            "product_name": product_info['product_name'],
            "quantity": quantity,
            # Precios unitarios
            "unit_price_reference": price_ref.quantize(self.quantize),
            "unit_price_target": conversion['price_target'],
            # Subtotales
            "subtotal_reference": subtotal_ref,
            "subtotal_target": subtotal_target,
            # Tasa de cambio
            "exchange_rate": conversion['exchange_rate'],
            "rate_date": conversion['rate_date'],
            "rate_source": conversion['rate_source'],
            # Impuestos
            "iva_percentage": self.DEFAULT_IVA_PERCENTAGE,
            "iva_amount": iva_amount,
            "igtf_percentage": self.DEFAULT_IGTF_PERCENTAGE if not igtf_exempt else 0,
            "igtf_amount": igtf_amount,
            "igtf_exempt": igtf_exempt,
            # Total
            "total_item": total_item.quantize(self.quantize)
        }

    def calculate_invoice_totals_with_reference(
        self,
        items: List[Dict[str, any]],
        customer_id: Optional[int] = None,
        payment_method: str = 'transferencia',
        manual_exchange_rate: Optional[float] = None,
        discount_percentage: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Calcula los totales de una factura completa usando precios de referencia.

        Args:
            items: Lista de items con formato:
                {
                    "product_id": int,
                    "quantity": int,
                    "price_reference_override": Decimal (opcional)
                }
            customer_id: ID del cliente (opcional)
            payment_method: Método de pago
            manual_exchange_rate: Tasa manual (opcional)
            discount_percentage: Descuento global (opcional)

        Returns:
            Dict con todos los totales de la factura desglosados
        """
        if not items:
            raise ValueError("Items list cannot be empty")

        calculated_items = []
        totals = {
            "reference_currency": self.USD_CODE,
            "payment_currency": self.VES_CODE,
            "items": [],
            # Totales en moneda de referencia (USD)
            "subtotal_reference": Decimal('0'),
            # Totales en moneda de pago (VES)
            "subtotal_target": Decimal('0'),
            "iva_amount": Decimal('0'),
            "igtf_amount": Decimal('0'),
            "discount_amount": Decimal('0'),
            "total_amount": Decimal('0'),
            # Info de tasas
            "exchange_rate": None,
            "rate_date": None,
            "rate_source": None
        }

        # Calcular cada item
        for item in items:
            calculated = self.calculate_invoice_item_with_reference(
                product_id=item['product_id'],
                quantity=item['quantity'],
                price_reference_override=item.get('price_reference_override'),
                payment_method=payment_method,
                manual_exchange_rate=manual_exchange_rate
            )

            calculated_items.append(calculated)
            totals['items'].append(calculated)

            # Acumular totales
            totals['subtotal_reference'] += Decimal(str(calculated['subtotal_reference']))
            totals['subtotal_target'] += Decimal(str(calculated['subtotal_target']))
            totals['iva_amount'] += Decimal(str(calculated['iva_amount']))
            totals['igtf_amount'] += Decimal(str(calculated['igtf_amount']))

        # Guardar info de tasa (todos los items usan la misma)
        if calculated_items:
            totals['exchange_rate'] = calculated_items[0]['exchange_rate']
            totals['rate_date'] = calculated_items[0]['rate_date']
            totals['rate_source'] = calculated_items[0]['rate_source']

        # Calcular descuento si aplica
        if discount_percentage:
            discount_percentage = Decimal(str(discount_percentage))
            # Descuento sobre subtotal target (antes de IVA)
            totals['discount_amount'] = (
                totals['subtotal_target'] * discount_percentage / 100
            ).quantize(self.quantize)

        # Calcular total
        totals['total_amount'] = (
            totals['subtotal_target'] +
            totals['iva_amount'] +
            totals['igtf_amount'] -
            totals['discount_amount']
        ).quantize(self.quantize)

        # Redondear todos los totales
        for key in ['subtotal_reference', 'subtotal_target', 'iva_amount',
                    'igtf_amount', 'discount_amount', 'total_amount']:
            totals[key] = totals[key].quantize(self.quantize)

        return totals

    def get_reference_price_summary(
        self,
        product_ids: List[int]
    ) -> List[Dict[str, any]]:
        """
        Obtiene un resumen de precios de referencia para múltiples productos.

        Útil para mostrar en frontend el precio REF y el precio en VES
        calculado con la tasa del día.

        Args:
            product_ids: Lista de IDs de productos

        Returns:
            Lista de dicts con información de precio REF
        """
        summary = []

        # Obtener tasa del día una sola vez
        daily_rate = self.rate_service.get_today_rate(
            self.USD_CODE,
            self.VES_CODE
        )

        exchange_rate = Decimal(str(daily_rate.exchange_rate)) if daily_rate else None

        for product_id in product_ids:
            product_info = self.get_product_reference_price(product_id)
            if not product_info:
                continue

            price_ref = product_info['price_reference']
            price_ves = None

            if price_ref and exchange_rate:
                price_ves = (price_ref * exchange_rate).quantize(self.quantize)

            summary.append({
                "product_id": product_info['product_id'],
                "product_name": product_info['product_name'],
                "price_reference": price_ref,
                "price_ves": price_ves,
                "reference_currency": self.USD_CODE,
                "exchange_rate": exchange_rate,
                "has_reference_price": product_info['available']
            })

        return summary
