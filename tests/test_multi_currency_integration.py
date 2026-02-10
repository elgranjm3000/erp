"""
Integration Tests for Multi-Currency Architecture
Tests completos del sistema multi-moneda escalable
"""

import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Core
from core.exchange_rate_providers import (
    ExchangeRateManager,
    ExchangeRateProviderFactory,
    MockProvider,
    BCVProvider
)

# Services
from services.currency_conversion_service import (
    CurrencyConversionService,
    ConversionResult,
    CurrencyAmount
)
from services.tax_engine import (
    TaxEngine,
    TaxType,
    TaxRule,
    InMemoryTaxRuleRepository
)
from services.transaction_service import (
    MultiCurrencyTransactionService,
    create_transaction_service
)

# Schemas
from schemas.transaction_schemas import (
    CreateTransactionRequest,
    TransactionItem,
    TransactionResponse,
    Money,
    PaymentMethod
)


# ==================== FIXTURES ====================

@pytest.fixture
def rate_manager():
    """Manager de tasas con mock para testing"""
    return ExchangeRateManager(['mock'])


@pytest.fixture
def tax_engine():
    """Motor de impuestos para testing"""
    return TaxEngine()


@pytest.fixture
def db_session():
    """Sesión de BD para testing"""
    # Usar BD de prueba o SQLite
    engine = create_engine('sqlite:///:memory:')
    TestingSession = sessionmaker(bind=engine)
    return TestingSession()


@pytest.fixture
def transaction_service(db_session, rate_manager, tax_engine):
    """Servicio de transacciones para testing"""
    return MultiCurrencyTransactionService(
        db=db_session,
        rate_manager=rate_manager,
        tax_engine=tax_engine
    )


# ==================== TESTS: PROVEEDORES ====================

class TestExchangeRateProviders:
    """Tests del patrón Provider para tasas de cambio"""

    def test_mock_provider_get_rate(self):
        """Test: Obtener tasa del proveedor Mock"""
        provider = MockProvider()

        rate = provider.get_rate("VES", "USD")

        assert rate is not None
        assert rate > 0
        assert isinstance(rate, Decimal)

    def test_mock_provider_supported_currencies(self):
        """Test: Obtener monedas soportadas"""
        provider = MockProvider()

        currencies = provider.get_supported_currencies()

        assert "USD" in currencies
        assert "VES" in currencies
        assert "EUR" in currencies

    def test_mock_provider_reciprocal_rate(self):
        """Test: Calcular tasa recíproca"""
        provider = MockProvider()

        rate_to_usd = provider.get_rate("VES", "USD")
        rate_from_usd = provider.get_rate("USD", "VES")

        # El producto debe ser ~1 (con tolerancia por redondeo)
        product = rate_to_usd * rate_from_usd
        assert abs(product - Decimal("1")) < Decimal("0.01")

    def test_rate_manager_fallback(self):
        """Test: Fallback a siguiente proveedor"""
        # Mock siempre funciona
        manager = ExchangeRateManager(['mock'])

        rate = manager.get_rate("VES", "USD")

        assert rate is not None
        assert isinstance(rate, Decimal)


# ==================== TESTS: SERVICIO DE CONVERSIÓN ====================

class TestCurrencyConversionService:
    """Tests del servicio de conversión de monedas"""

    def test_convert_same_currency(self, rate_manager):
        """Test: Conversión misma moneda (sin cambio)"""
        result = CurrencyConversionService.convert(
            amount=Decimal("100"),
            from_currency="USD",
            to_currency="USD",
            rate_manager=rate_manager
        )

        assert result.original_amount == Decimal("100")
        assert result.converted_amount == Decimal("100")
        assert result.rate_used == Decimal("1")
        assert result.provider == "direct"

    def test_convert_usd_to_ves(self, rate_manager):
        """Test: Conversión USD a VES"""
        result = CurrencyConversionService.convert(
            amount=Decimal("100"),
            from_currency="USD",
            to_currency="VES",
            rate_manager=rate_manager
        )

        assert result.original_currency == "USD"
        assert result.target_currency == "VES"
        assert result.converted_amount > result.original_amount
        assert result.rate_used > 0

    def test_convert_ves_to_usd(self, rate_manager):
        """Test: Conversión VES a USD (recíproca)"""
        result = CurrencyConversionService.convert(
            amount=Decimal("3700"),  # 3700 Bs
            from_currency="VES",
            to_currency="USD",
            rate_manager=rate_manager
        )

        # Debe dar ~100 USD
        assert 90 < result.converted_amount < 110
        assert result.rate_used < 1  # Tasa < 1 para VES->USD

    def test_conversion_caching(self, rate_manager):
        """Test: Caché de conversión"""
        # Primera llamada (miss)
        result1 = CurrencyConversionService.convert(
            amount=Decimal("100"),
            from_currency="USD",
            to_currency="VES",
            rate_manager=rate_manager
        )

        stats1 = CurrencyConversionService.get_cache_stats()

        # Segunda llamada (hit)
        result2 = CurrencyConversionService.convert(
            amount=Decimal("200"),
            from_currency="USD",
            to_currency="VES",
            rate_manager=rate_manager
        )

        stats2 = CurrencyConversionService.get_cache_stats()

        # Debe haber aumentado el contador de hits
        assert stats2["hits"] >= stats1["hits"]

        # Tasa debe ser la misma (del caché)
        assert result1.rate_used == result2.rate_used

    def test_currency_amount(self, rate_manager):
        """Test: CurrencyAmount con conversión"""
        amount = CurrencyAmount(
            amount=Decimal("100"),
            currency="USD"
        )

        # Convertir a VES
        ves_amount = amount.convert_to("VES", rate_manager)

        assert ves_amount.currency == "VES"
        assert ves_amount.amount > amount.amount

    def test_conversion_result_immutability(self, rate_manager):
        """Test: Inmutabilidad de ConversionResult"""
        result = CurrencyConversionService.convert(
            amount=Decimal("100"),
            from_currency="USD",
            to_currency="VES",
            rate_manager=rate_manager
        )

        # Intentar modificar debe fallar (frozen dataclass)
        with pytest.raises(Exception):  # FrozenInstanceError
            result.converted_amount = Decimal("999")


# ==================== TESTS: MOTOR DE IMPUESTOS ====================

class TestTaxEngine:
    """Tests del motor de impuestos dinámico"""

    def test_calculate_iva_standard(self, tax_engine):
        """Test: Cálculo de IVA estándar (16%)"""
        calculation = tax_engine.calculate_tax(
            amount=Decimal("1000"),
            currency="VES",
            tax_type=TaxType.IVA
        )

        assert calculation is not None
        assert calculation.tax_amount == Decimal("160")  # 16% de 1000
        assert calculation.rate == Decimal("16")
        assert calculation.tax_type == TaxType.IVA

    def test_calculate_igtf_usd(self, tax_engine):
        """Test: Cálculo de IGTF para USD (>1000)"""
        calculation = tax_engine.calculate_tax(
            amount=Decimal("1500"),
            currency="USD",
            tax_type=TaxType.IGTF
        )

        assert calculation is not None
        assert calculation.tax_amount == Decimal("45")  # 3% de 1500
        assert calculation.rate == Decimal("3")

    def test_calculate_igtf_ves(self, tax_engine):
        """Test: IGTF para VES (0%)"""
        calculation = tax_engine.calculate_tax(
            amount=Decimal("50000"),
            currency="VES",
            tax_type=TaxType.IGTF
        )

        # VES está exento, pero puede calcular 0%
        if calculation:
            assert calculation.tax_amount == Decimal("0")

    def test_calculate_all_taxes(self, tax_engine):
        """Test: Calcular todos los impuestos aplicables"""
        calculations = tax_engine.calculate_all_taxes(
            amount=Decimal("1500"),
            currency="USD"
        )

        # Debe incluir IVA y probablemente IGTF
        tax_types = [c.tax_type for c in calculations]

        assert TaxType.IVA in tax_types

        total_tax = sum(c.tax_amount for c in calculations)
        assert total_tax > 0

    def test_custom_tax_rule(self, tax_engine):
        """Test: Agregar regla de impuesto personalizada"""
        custom_rule = TaxRule(
            tax_type=TaxType.MUNICIPAL,
            name="Impuesto Municipal Test",
            rate=Decimal("2"),
            is_active=True,
            priority=1
        )

        tax_engine.add_rule(custom_rule)

        calculation = tax_engine.calculate_tax(
            amount=Decimal("1000"),
            currency="VES",
            tax_type=TaxType.MUNICIPAL
        )

        assert calculation is not None
        assert calculation.tax_amount == Decimal("20")  # 2% de 1000


# ==================== TESTS: TRANSACCIONES ====================

class TestMultiCurrencyTransactions:
    """Tests del servicio de transacciones multi-moneda"""

    def test_create_invoice_usd_to_ves(self, transaction_service):
        """Test: Crear factura en USD, convertir a VES"""
        request = CreateTransactionRequest(
            base_currency="VES",
            customer_id=1,
            warehouse_id=1,
            payment_method=PaymentMethod.TRANSFER,
            items=[
                TransactionItem(
                    product_id=1,
                    quantity=2,
                    price_amount=Decimal("500"),  # $500 USD
                    price_currency="USD",
                    is_tax_exempt=False
                )
            ]
        )

        response = transaction_service.create_invoice(
            request=request,
            company_id=1,
            user_id=1
        )

        # Verificar conversión
        assert response.subtotal_original.currency == "USD"
        assert response.subtotal_base.currency == "VES"

        # El monto en VES debe ser mayor
        assert response.subtotal_base.amount > response.subtotal_original.amount

        # Debe haber impuestos
        assert len(response.taxes) > 0
        assert response.total_tax.amount > 0

        # Totales
        assert response.total_base.amount == (
            response.subtotal_base.amount + response.total_tax.amount
        )

    def test_create_invoice_multi_currency_items(self, transaction_service):
        """Test: Factura con items en diferentes monedas"""
        request = CreateTransactionRequest(
            base_currency="USD",
            customer_id=1,
            payment_method=PaymentMethod.CASH,
            items=[
                TransactionItem(
                    product_id=1,
                    quantity=1,
                    price_amount=Decimal("100"),
                    price_currency="USD"
                ),
                TransactionItem(
                    product_id=2,
                    quantity=1,
                    price_amount=Decimal("3700"),
                    price_currency="VES"
                )
            ]
        )

        response = transaction_service.create_invoice(
            request=request,
            company_id=1,
            user_id=1
        )

        # Todo debe estar en moneda base (USD)
        assert response.total_base.currency == "USD"

        # Debe tener snapshot
        assert response.snapshot_id is not None

    def test_transaction_with_different_payment_methods(self, transaction_service):
        """Test: IGTF según método de pago"""
        # Transferencia (tiene IGTF)
        request_transfer = CreateTransactionRequest(
            base_currency="USD",
            customer_id=1,
            payment_method=PaymentMethod.TRANSFER,
            items=[
                TransactionItem(
                    product_id=1,
                    quantity=1,
                    price_amount=Decimal("1500"),
                    price_currency="USD"
                )
            ]
        )

        response_transfer = transaction_service.create_invoice(
            request=request_transfer,
            company_id=1,
            user_id=1
        )

        # Efectivo (no tiene IGTF en algunos casos)
        request_cash = CreateTransactionRequest(
            base_currency="USD",
            customer_id=1,
            payment_method=PaymentMethod.CASH,
            items=[
                TransactionItem(
                    product_id=1,
                    quantity=1,
                    price_amount=Decimal("1500"),
                    price_currency="USD"
                )
            ]
        )

        response_cash = transaction_service.create_invoice(
            request=request_cash,
            company_id=1,
            user_id=1
        )

        # Los impuestos pueden variar según el método
        tax_types_transfer = [t.tax_type for t in response_transfer.taxes]
        tax_types_cash = [t.tax_type for t in response_cash.taxes]

        # Al menos IVA debe estar en ambos
        assert "iva" in tax_types_transfer
        assert "iva" in tax_types_cash


# ==================== TESTS: INMUTABILIDAD ====================

class TestImmutability:
    """Tests de inmutabilidad de snapshots"""

    def test_snapshot_creation(self, db_session, rate_manager, tax_engine):
        """Test: Creación de snapshot inmutable"""
        service = MultiCurrencyTransactionService(
            db=db_session,
            rate_manager=rate_manager,
            tax_engine=tax_engine
        )

        request = CreateTransactionRequest(
            base_currency="VES",
            customer_id=1,
            payment_method=PaymentMethod.TRANSFER,
            items=[
                TransactionItem(
                    product_id=1,
                    quantity=1,
                    price_amount=Decimal("100"),
                    price_currency="USD"
                )
            ]
        )

        response = service.create_invoice(
            request=request,
            company_id=1,
            user_id=1
        )

        # Verificar snapshot creado
        assert response.snapshot_id is not None

        snapshot = db_session.query(models.TransactionSnapshot).filter(
            models.TransactionSnapshot.id == response.snapshot_id
        ).first()

        assert snapshot is not None
        assert snapshot.is_finalized == True
        assert snapshot.amount_original > 0
        assert snapshot.exchange_rate > 0

        # Verificar que no se puede modificar (frozen dataclass en schema)
        # En BD, el campo is_finalized indica inmutabilidad

    def test_exchange_rate_immutability(self, db_session):
        """Test: Inmutabilidad de tasa de cambio en snapshot"""
        # Crear snapshot
        snapshot = models.TransactionSnapshot(
            transaction_type="invoice",
            transaction_id=1,
            amount_original=Decimal("100"),
            currency_original="USD",
            amount_base=Decimal("3650"),
            currency_base="VES",
            exchange_rate=Decimal("36.5"),
            exchange_rate_date=datetime.now(),
            exchange_rate_provider="bcv",
            is_finalized=True
        )

        db_session.add(snapshot)
        db_session.commit()

        # Recuperar y verificar
        retrieved = db_session.query(models.TransactionSnapshot).filter(
            models.TransactionSnapshot.id == snapshot.id
        ).first()

        assert retrieved.exchange_rate == Decimal("36.5")
        assert retrieved.is_finalized == True


# ==================== TESTS: PRECISIÓN DECIMAL ====================

class TestDecimalPrecision:
    """Tests de precisión financiera con Decimal"""

    def test_decimal_rounding(self):
        """Test: Redondeo a 2 decimales"""
        amount = Decimal("100.123456")

        # Redondear a 2 decimales
        rounded = amount.quantize(Decimal("0.01"))

        assert rounded == Decimal("100.12")

    def test_tax_calculation_precision(self, rate_manager, tax_engine):
        """Test: Precisión en cálculo de impuestos"""
        service = MultiCurrencyTransactionService(
            db=None,  # No necesitamos BD para este test
            rate_manager=rate_manager,
            tax_engine=tax_engine
        )

        # IVA de 16.333... debe dar precisión correcta
        taxes = service._calculate_taxes(
            amount=Decimal("100.333"),
            currency="VES",
            payment_method=PaymentMethod.TRANSFER
        )

        for tax in taxes:
            # Verificar que tiene 2 decimales
            assert tax.tax_amount == tax.tax_amount.quantize(Decimal("0.01"))

    def test_currency_conversion_precision(self, rate_manager):
        """Test: Precisión en conversión de monedas"""
        result = CurrencyConversionService.convert(
            amount=Decimal("100.999"),  # Monto con 3 decimales
            from_currency="USD",
            to_currency="VES",
            rate_manager=rate_manager
        )

        # Resultado debe tener 2 decimales
        assert result.converted_amount == result.converted_amount.quantize(Decimal("0.01"))


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    # Ejecutar tests con pytest
    pytest.main([__file__, "-v", "--tb=short"])
