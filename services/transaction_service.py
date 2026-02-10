"""
Multi-Currency Transaction Service
Servicio integrado para transacciones con multi-moneda, impuestos y snapshots
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

# Nuestros servicios
from core.exchange_rate_providers import ExchangeRateManager, ExchangeRateProviderFactory
from services.currency_conversion_service import (
    CurrencyConversionService,
    ConversionResult,
    CurrencyAmount
)
from services.tax_engine import TaxEngine, TaxCalculation, TaxType

# Schemas
from schemas.transaction_schemas import (
    CreateTransactionRequest,
    TransactionResponse,
    TransactionItem,
    Money,
    ExchangeRate as ExchangeRateSchema,
    TaxCalculationSchema,
    PaymentMethod
)

# Models
import models
from models.transaction_snapshot import TransactionSnapshot


logger = logging.getLogger(__name__)


class MultiCurrencyTransactionService:
    """
    Servicio para transacciones multi-moneda con:
    - Conversión automática de monedas
    - Cálculo dinámico de impuestos
    - Snapshots inmutables
    - Precisión Decimal
    """

    def __init__(
        self,
        db: Session,
        rate_manager: Optional[ExchangeRateManager] = None,
        tax_engine: Optional[TaxEngine] = None
    ):
        """
        Inicializa el servicio.

        Args:
            db: Sesión de base de datos
            rate_manager: Manager de tasas (crea uno por defecto si es None)
            tax_engine: Motor de impuestos (crea uno por defecto si es None)
        """
        self.db = db

        # Inicializar rate manager si no se proporciona
        if rate_manager is None:
            # Usar BCV -> Binance -> Mock como fallback
            rate_manager = ExchangeRateManager(['bcv', 'binance', 'mock'])

        self.rate_manager = rate_manager

        # Inicializar tax engine si no se proporciona
        if tax_engine is None:
            tax_engine = TaxEngine()

        self.tax_engine = tax_engine

        logger.info("Multi-currency transaction service initialized")

    def create_invoice(
        self,
        request: CreateTransactionRequest,
        company_id: int,
        user_id: int
    ) -> TransactionResponse:
        """
        Crea una factura multi-moneda con conversión, impuestos y snapshot.

        Args:
            request: Request de creación
            company_id: ID de empresa
            user_id: ID de usuario

        Returns:
            TransactionResponse: Respuesta con todos los cálculos
        """
        logger.info(f"Creating multi-currency invoice for company {company_id}")

        # 1. Calcular subtotal de items
        items_subtotal = self._calculate_items_subtotal(request.items)

        # 2. Determinar moneda de pago (usar la primera item por ahora)
        payment_currency = request.items[0].price_currency

        # 3. Convertir a moneda base si es necesario
        base_currency = request.base_currency.upper()

        if payment_currency != base_currency:
            conversion = CurrencyConversionService.convert(
                amount=items_subtotal.amount,
                from_currency=payment_currency,
                to_currency=base_currency,
                rate_manager=self.rate_manager
            )
            subtotal_base = CurrencyAmount(
                amount=conversion.converted_amount,
                currency=base_currency
            )
            exchange_rate = conversion
        else:
            subtotal_base = items_subtotal
            exchange_rate = ConversionResult(
                original_amount=items_subtotal.amount,
                original_currency=payment_currency,
                converted_amount=items_subtotal.amount,
                target_currency=base_currency,
                rate_used=Decimal("1"),
                converted_at=datetime.now(),
                provider="direct"
            )

        logger.info(
            f"Subtotal: {items_subtotal.amount} {payment_currency} -> "
            f"{subtotal_base.amount} {base_currency}"
        )

        # 4. Calcular impuestos (sobre monto base)
        taxes = self._calculate_taxes(
            amount=subtotal_base.amount,
            currency=base_currency,
            payment_method=request.payment_method
        )

        total_tax_amount = sum(t.tax_amount for t in taxes)

        logger.info(f"Taxes calculated: {len(taxes)} taxes, total: {total_tax_amount} {base_currency}")

        # 5. Calcular totales
        total_base = CurrencyAmount(
            amount=subtotal_base.amount + total_tax_amount,
            currency=base_currency
        )

        # Convertir total a moneda de pago si es necesario
        if payment_currency != base_currency:
            total_conversion = CurrencyConversionService.convert(
                amount=total_base.amount,
                from_currency=base_currency,
                to_currency=payment_currency,
                rate_manager=self.rate_manager
            )
            total_original = CurrencyAmount(
                amount=total_conversion.converted_amount,
                currency=payment_currency
            )
        else:
            total_original = total_base

        # 6. Crear snapshot inmutable
        snapshot = self._create_snapshot(
            transaction_type="invoice",
            payment_amount=total_original,
            base_amount=total_base,
            exchange_rate=exchange_rate,
            taxes=taxes,
            items=request.items,
            user_id=user_id,
            transaction_metadata={
                "customer_id": request.customer_id,
                "warehouse_id": request.warehouse_id,
                "payment_method": request.payment_method.value,
                "company_id": company_id
            }
        )

        # 7. Persistir factura
        invoice = self._persist_invoice(
            request=request,
            company_id=company_id,
            user_id=user_id,
            subtotal_base=subtotal_base,
            total_base=total_base,
            taxes=taxes,
            snapshot_id=snapshot.id
        )

        logger.info(f"Invoice created with ID: {invoice.id}, snapshot ID: {snapshot.id}")

        # 8. Construir respuesta
        return TransactionResponse(
            transaction_id=invoice.id,
            transaction_type="invoice",
            subtotal_original=Money(
                amount=items_subtotal.amount,
                currency=payment_currency
            ),
            subtotal_base=Money(
                amount=subtotal_base.amount,
                currency=base_currency
            ),
            taxes=[
                TaxCalculationSchema(
                    taxable_amount=Money(amount=t.taxable_amount, currency=base_currency),
                    tax_type=t.tax_type.value,
                    tax_name=t.tax_name,
                    rate=t.rate,
                    tax_amount=Money(amount=t.tax_amount, currency=base_currency),
                    rule_id=t.rule_id,
                    calculated_at=t.calculated_at
                )
                for t in taxes
            ],
            total_tax=Money(amount=total_tax_amount, currency=base_currency),
            total_original=Money(
                amount=total_original.amount,
                currency=payment_currency
            ),
            total_base=Money(
                amount=total_base.amount,
                currency=base_currency
            ),
            exchange_rate=ExchangeRateSchema(
                from_currency=exchange_rate.original_currency,
                to_currency=exchange_rate.target_currency,
                rate=exchange_rate.rate_used,
                date=exchange_rate.converted_at,
                provider=exchange_rate.provider
            ),
            created_at=datetime.now(),
            snapshot_id=snapshot.id
        )

    def _calculate_items_subtotal(self, items: List[TransactionItem]) -> CurrencyAmount:
        """Calcula subtotal de items (suma de line totals)"""
        # Por ahora asumimos todos en misma moneda
        total = sum(item.line_total.amount for item in items)
        currency = items[0].price_currency

        return CurrencyAmount(amount=Decimal(str(total)), currency=currency)

    def _calculate_taxes(
        self,
        amount: Decimal,
        currency: str,
        payment_method: PaymentMethod
    ) -> List[TaxCalculation]:
        """Calcula impuestos aplicables"""
        # Contexto para cálculo de impuestos
        context = {
            "payment_method": payment_method.value,
        }

        # Calcular todos los impuestos aplicables
        calculations = self.tax_engine.calculate_all_taxes(
            amount=amount,
            currency=currency,
            context=context
        )

        return calculations

    def _create_snapshot(
        self,
        transaction_type: str,
        payment_amount: CurrencyAmount,
        base_amount: CurrencyAmount,
        exchange_rate: ConversionResult,
        taxes: List[TaxCalculation],
        items: List[TransactionItem],
        user_id: int,
        metadata: Dict
    ) -> TransactionSnapshot:
        """Crea snapshot inmutable de la transacción"""
        snapshot = TransactionSnapshot(
            transaction_type=transaction_type,
            transaction_id=0,  # Se actualizará después de crear la transacción
            amount_original=payment_amount.amount,
            currency_original=payment_amount.currency,
            amount_base=base_amount.amount,
            currency_base=base_amount.currency,
            exchange_rate=exchange_rate.rate_used,
            exchange_rate_date=exchange_rate.converted_at,
            exchange_rate_provider=exchange_rate.provider,
            taxes_snapshot={
                t.tax_type.value: {
                    "rate": float(t.rate),
                    "taxable_amount": float(t.taxable_amount),
                    "tax_amount": float(t.tax_amount),
                    "rule_id": t.rule_id
                }
                for t in taxes
            },
            transaction_metadata={
                **metadata,
                "items": [
                    {
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "unit_price": float(item.price_amount),
                        "currency": item.price_currency,
                        "line_total": float(item.line_total.amount)
                    }
                    for item in items
                ]
            },
            created_by=user_id,
            is_finalized=True
        )

        self.db.add(snapshot)
        self.db.flush()

        logger.info(f"Created snapshot with ID: {snapshot.id}")
        return snapshot

    def _persist_invoice(
        self,
        request: CreateTransactionRequest,
        company_id: int,
        user_id: int,
        subtotal_base: CurrencyAmount,
        total_base: CurrencyAmount,
        taxes: List[TaxCalculation],
        snapshot_id: int
    ) -> Any:
        """Persiste la factura en base de datos"""

        # Por ahora retornar un objeto mock
        # En producción, aquí persistirías en la tabla Invoice real

        class MockInvoice:
            def __init__(self):
                self.id = 1  # ID temporal

        invoice = MockInvoice()

        # Actualizar snapshot con el ID real
        snapshot = self.db.query(TransactionSnapshot).filter(
            TransactionSnapshot.id == snapshot_id
        ).first()

        if snapshot:
            snapshot.transaction_id = invoice.id
            self.db.commit()

        return invoice


# Función de conveniencia para crear el servicio
def create_transaction_service(
    db: Session,
    provider_priority: List[str] = None
) -> MultiCurrencyTransactionService:
    """
    Factory para crear el servicio de transacciones.

    Args:
        db: Sesión de base de datos
        provider_priority: Lista de proveedores de tasas en orden

    Returns:
        MultiCurrencyTransactionService: Servicio configurado
    """
    if provider_priority is None:
        # Prioridad por defecto: BCV oficial -> Paralelo (Binance) -> Mock
        provider_priority = ['bcv', 'binance', 'mock']

    rate_manager = ExchangeRateManager(provider_priority)
    tax_engine = TaxEngine()

    return MultiCurrencyTransactionService(
        db=db,
        rate_manager=rate_manager,
        tax_engine=tax_engine
    )
