#!/usr/bin/env python3
"""
Demo: Sistema Multi-Moneda Escalable
Muestra todas las características implementadas
"""

from decimal import Decimal
from datetime import datetime

# Core - Provider Pattern
from core.exchange_rate_providers import (
    ExchangeRateManager,
    ExchangeRateProviderFactory
)

# Services
from services.currency_conversion_service import (
    CurrencyConversionService,
    CurrencyAmount
)
from services.tax_engine import TaxEngine, TaxType
from services.transaction_service import MultiCurrencyTransactionService

# Schemas
from schemas.transaction_schemas import (
    CreateTransactionRequest,
    TransactionItem,
    PaymentMethod
)


def print_separator(title: str):
    """Imprime separador visual"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_providers():
    """Demo: Provider Pattern para Exchange Rates"""
    print_separator("1. PROVIDER PATTERN - Exchange Rates")

    # Crear manager con fallback chain
    print("Creando ExchangeRateManager con fallback: Mock -> BCV -> Binance")
    manager = ExchangeRateManager(['mock', 'bcv', 'binance'])

    # Obtener tasa
    rate = manager.get_rate("USD", "VES")
    print(f"\n✅ Tasa USD -> VES: {rate}")

    # Ver estado de proveedores
    status = manager.get_providers_status()
    print(f"\n📊 Estado de proveedores:")
    for provider, available in status.items():
        icon = "✅" if available else "❌"
        print(f"   {icon} {provider}: {'Disponible' if available else 'No disponible'}")


def demo_currency_conversion():
    """Demo: Servicio de Conversión de Monedas"""
    print_separator("2. SERVICIO DE CONVERSIÓN - Lógica Agnóstica")

    # Crear manager
    manager = ExchangeRateManager(['mock'])

    # Crear monto agnóstico (no hay "precio en dólares")
    print("Creando monto agnóstico:")
    price = CurrencyAmount(amount=Decimal("100"), currency="USD")
    print(f"   💵 Monto original: {price}")

    # Convertir a VES
    print("\nConvirtiendo a VES...")
    ves_price = price.convert_to("VES", manager)
    print(f"   💰 Monto convertido: {ves_price}")

    # Ver estadísticas de caché
    stats = CurrencyConversionService.get_cache_stats()
    print(f"\n📈 Estadísticas de caché:")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Tasa de aciertos: {stats['hit_rate']:.2%}")


def demo_tax_engine():
    """Demo: Motor de Impuestos Dinámico"""
    print_separator("3. MOTOR DE IMPUESTOS - Configurable y Extensible")

    # Crear motor
    tax_engine = TaxEngine()

    # Calcular IVA
    print("Calculando IVA (16%) para Bs 10,000:")
    iva_calc = tax_engine.calculate_tax(
        amount=Decimal("10000"),
        currency="VES",
        tax_type=TaxType.IVA
    )

    if iva_calc:
        print(f"   💳 IVA: Bs {iva_calc.tax_amount} ({iva_calc.rate}%)")

    # Calcular IGTF para USD
    print("\nCalculando IGTF (3%) para $1,500 USD:")
    igtf_calc = tax_engine.calculate_tax(
        amount=Decimal("1500"),
        currency="USD",
        tax_type=TaxType.IGTF
    )

    if igtf_calc:
        print(f"   💳 IGTF: ${igtf_calc.tax_amount} ({igtf_calc.rate}%)")

    # Calcular todos los impuestos
    print("\nCalculando TODOS los impuestos para $1,200 USD:")
    all_taxes = tax_engine.calculate_all_taxes(
        amount=Decimal("1200"),
        currency="USD"
    )

    total_tax = sum(t.tax_amount for t in all_taxes)
    print(f"   💳 Total impuestos: ${total_tax}")
    for tax in all_taxes:
        print(f"      - {tax.tax_name}: ${tax.tax_amount} ({tax.rate}%)")


def demo_transaction():
    """Demo: Transacción Multi-Moneda Completa"""
    print_separator("4. TRANSACCIÓN MULTI-MONEDA - Integración Completa")

    # Crear manager y engine
    manager = ExchangeRateManager(['mock'])
    tax_engine = TaxEngine()

    # Crear servicio (sin BD para demo)
    service = MultiCurrencyTransactionService(
        db=None,
        rate_manager=manager,
        tax_engine=tax_engine
    )

    # Crear request con items en diferentes monedas
    print("Creando factura con:")
    print("   - 2 Laptops @ $500 USD c/u")
    print("   - 1 Mouse @ Bs 740 VES")
    print("   - Moneda base: VES")
    print("   - Método de pago: Transferencia")

    request = CreateTransactionRequest(
        base_currency="VES",
        customer_id=1,
        warehouse_id=1,
        payment_method=PaymentMethod.TRANSFER,
        items=[
            TransactionItem(
                product_id=1,
                quantity=2,
                price_amount=Decimal("500"),
                price_currency="USD",
                is_tax_exempt=False
            ),
            TransactionItem(
                product_id=2,
                quantity=1,
                price_amount=Decimal("740"),
                price_currency="VES",
                is_tax_exempt=False
            )
        ]
    )

    # Calcular manualmente (sin persistir en BD)
    print("\n📊 Cálculos:")

    # Subtotal items
    subtotal_usd = Decimal("500") * 2  # $1000 USD
    subtotal_ves = Decimal("740") * 1   # Bs 740

    print(f"   Subtotal USD: ${subtotal_usd}")
    print(f"   Subtotal VES: Bs {subtotal_ves}")

    # Convertir USD a VES
    conversion = CurrencyConversionService.convert(
        amount=subtotal_usd,
        from_currency="USD",
        to_currency="VES",
        rate_manager=manager
    )

    print(f"\n💱 Conversión: ${subtotal_usd} → Bs {conversion.converted_amount}")
    print(f"   Tasa usada: {conversion.rate_used} (proveedor: {conversion.provider})")

    # Total en moneda base
    total_base = conversion.converted_amount + subtotal_ves
    print(f"\n💰 Total base: Bs {total_base}")

    # Calcular impuestos
    taxes = service._calculate_taxes(
        amount=total_base,
        currency="VES",
        payment_method=PaymentMethod.TRANSFER
    )

    total_tax = sum(t.tax_amount for t in taxes)
    print(f"\n💳 Impuestos calculados: {len(taxes)} impuestos")
    for tax in taxes:
        print(f"   - {tax.tax_name}: Bs {tax.tax_amount} ({tax.rate}%)")

    # Total final
    final_total = total_base + total_tax
    print(f"\n✅ TOTAL FINAL: Bs {final_total}")


def demo_snapshots():
    """Demo: Inmutabilidad de Snapshots"""
    print_separator("5. SNAPSHOTS INMUTABLES - Auditoría")

    print("Estructura de snapshot:")
    snapshot = {
        "transaction_type": "invoice",
        "transaction_id": 12345,
        "amount_original": {
            "amount": "1000.00",
            "currency": "USD"
        },
        "amount_base": {
            "amount": "36500.00",
            "currency": "VES"
        },
        "exchange_rate": {
            "rate": "36.500000",
            "date": datetime.now().isoformat(),
            "provider": "bcv"
        },
        "taxes_snapshot": {
            "iva": {
                "rate": 16.0,
                "taxable_amount": 36500.00,
                "tax_amount": 5840.00,
                "rule_id": "iva_estandar"
            },
            "igtf": {
                "rate": 3.0,
                "taxable_amount": 42340.00,
                "tax_amount": 1270.20,
                "rule_id": "igtf_divisas"
            }
        },
        "metadata": {
            "customer_id": 100,
            "warehouse_id": 5,
            "payment_method": "transfer",
            "user_id": 10
        },
        "created_at": datetime.now().isoformat(),
        "is_finalized": True
    }

    import json
    print(json.dumps(snapshot, indent=2, default=str))

    print("\n✅ Características del snapshot:")
    print("   • Inmutable: is_finalized = True")
    print("   • Auditoría completa: tasas, impuestos, usuario")
    print("   • Reconstrucción exacta de la transacción")
    print("   • Precisión Decimal en todos los montos")


def main():
    """Ejecuta todas las demos"""
    print("\n" + "🚀" * 35)
    print("  DEMO: ARQUITECTURA MULTI-MONEDA ESCALABLE")
    print("🚀" * 35)

    try:
        # 1. Provider Pattern
        demo_providers()

        # 2. Servicio de Conversión
        demo_currency_conversion()

        # 3. Motor de Impuestos
        demo_tax_engine()

        # 4. Transacción Completa
        demo_transaction()

        # 5. Snapshots
        demo_snapshots()

        # Resumen
        print_separator("✅ CARACTERÍSTICAS IMPLEMENTADAS")
        print("""
   ✅ Provider Pattern - BCV, Binance, Mock con fallback automático
   ✅ Precios Agnósticos - CurrencyAmount(amount, currency)
   ✅ Motor de Impuestos Dinámico - Configurable sin código
   ✅ Snapshots Inmutables - Auditoría completa de transacciones
   ✅ Caché Inteligente - Reducción de llamadas a proveedores
   ✅ Precisión Decimal - Cálculos financieros exactos
   ✅ Tipado Estático - Pydantic + Mypy ready
   ✅ Escalabilidad - Agregar monedas/impuestos sin tocar lógica
        """)

        print("=" * 70)
        print("  🎉 SISTEMA LISTO PARA PRODUCCIÓN")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
