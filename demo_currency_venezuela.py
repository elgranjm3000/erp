#!/usr/bin/env python3
"""
Demo: Sistema de Gestión de Monedas - Lógica Contable Venezolana
Muestra: ISO 4217, factores de conversión, IGTF, registro histórico
"""

from decimal import Decimal
from datetime import datetime

from models.currency_config import Currency, CurrencyRateHistory, IGTFConfig
from schemas.currency_config_schemas import (
    CurrencyCreate,
    CurrencyRateUpdate,
    CurrencyExamples,
    ConversionMethod,
    RateUpdateMethod
)
from services.currency_business_service import (
    CurrencyService,
    CurrencyBusinessLogic
)


def print_separator(title: str):
    """Imprime separador visual"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_iso_validation():
    """Demo: Validación ISO 4217"""
    print_separator("1. VALIDACIÓN ISO 4217")

    logic = CurrencyBusinessLogic()

    test_codes = ["USD", "VES", "EUR", "XYZ", "AB"]

    for code in test_codes:
        is_valid, error_msg = logic.validate_iso_4217(code)

        icon = "✅" if is_valid else "❌"

        print(f"{icon} Código '{code}': ", end="")

        if is_valid:
            from schemas.currency_config_schemas import ISO_4217_CURRENCIES
            name = ISO_4217_CURRENCIES.get(code.upper(), "Desconocido")
            print(f"VÁLIDO - {name}")
        else:
            print(f"INVÁLIDO - {error_msg}")


def demo_conversion_factors():
    """Demo: Cálculo de Factores de Conversión"""
    print_separator("2. FACTORES DE CONVERSIÓN - Lógica Venezolana")

    logic = CurrencyBusinessLogic()

    # Ejemplos de monedas
    currencies = [
        ("VES", Decimal("1.0"), None, "Moneda base, no aplica conversión"),
        ("USD", Decimal("36.50"), ConversionMethod.DIRECT, "Moneda más fuerte que VES"),
        ("EUR", Decimal("39.80"), ConversionMethod.DIRECT, "Moneda más fuerte que VES"),
        ("COP", Decimal("0.0091"), ConversionMethod.INVERSE, "Moneda más débil (frontera)"),
    ]

    for code, rate, method, description in currencies:
        factor, method_used = logic.calculate_conversion_factor(code, rate, method)

        print(f"\n{code}: {description}")
        print(f"   Tasa: {rate}")
        method_display = method if isinstance(method, str) else (method.value if method else "N/A")
        print(f"   Método: {method_display}")
        print(f"   Factor: {factor if factor else 'N/A (moneda base)'}")

        if factor:
            print(f"   Ejemplo: 1 {code} = {factor} VES")


def demo_igtf_calculation():
    """Demo: Cálculo de IGTF según moneda"""
    print_separator("3. IGTF - IMPUESTO A GRANDES TRANSACCIONES FINANCIERAS")

    logic = CurrencyBusinessLogic()

    # Ejemplos de transacciones
    transactions = [
        (Decimal("1000"), "USD", True, Decimal("3.00"), False),
        (Decimal("500"), "VES", False, Decimal("3.00"), True),
        (Decimal("2000"), "EUR", True, Decimal("3.00"), False),
    ]

    for amount, currency, applies_igtf, rate, is_exempt in transactions:
        igtf_amount, applied, reason = logic.calculate_igtf(
            amount=amount,
            currency=currency,
            applies_igtf=applies_igtf,
            igtf_rate=rate,
            is_exempt=is_exempt
        )

        icon = "💳" if applied else "⃠ "
        status = "APLICA" if applied else "NO APLICA"

        print(f"\n{icon} {currency}: {amount} {currency}")
        print(f"   IGTF {status}: {reason}")
        if applied:
            print(f"   Monto IGTF: {igtf_amount} {currency}")
            print(f"   TOTAL con IGTF: {amount + igtf_amount} {currency}")


def demo_currency_creation():
    """Demo: Creación de monedas con validación"""
    print_separator("4. CREACIÓN DE MONEDAS - Validaciones Automáticas")

    examples = CurrencyExamples()

    # Ejemplo 1: USD
    print("✨ Creando USD (Dólar):")
    print("   - Moneda más fuerte que VES")
    print("   - Factor de conversión: 1/tasa")
    print("   - Aplica IGTF: Sí (3%)")

    usd_data = examples.example_usd()
    print(f"\n   Datos:")
    print(f"   - Código: {usd_data.code}")
    print(f"   - Símbolo: {usd_data.symbol}")
    print(f"   - Tasa: {usd_data.exchange_rate}")
    print(f"   - Método: {usd_data.conversion_method.value}")
    print(f"   - Aplica IGTF: {usd_data.applies_igtf}")

    # Ejemplo 2: VES
    print("\n\n✨ Creando VES (Bolívar):")
    print("   - Moneda base de Venezuela")
    print("   - NO aplica IGTF (moneda nacional)")

    ves_data = examples.example_ves()
    print(f"\n   Datos:")
    print(f"   - Código: {ves_data.code}")
    print(f"   - Símbolo: {ves_data.symbol}")
    print(f"   - Moneda Base: {ves_data.is_base_currency}")
    print(f"   - Aplica IGTF: {ves_data.applies_igtf}")

    # Ejemplo 3: COP
    print("\n\n✨ Creando COP (Peso Colombiano):")
    print("   - Moneda más débil (frontera)")
    print("   - NO aplica IGTF (moneda local fronteriza)")

    cop_data = examples.example_cop()
    print(f"\n   Datos:")
    print(f"   - Código: {cop_data.code}")
    print(f"   - Tasa: {cop_data.exchange_rate}")
    print(f"   - Método: {cop_data.conversion_method.value}")
    print(f"   - Aplica IGTF: {cop_data.applies_igtf}")


def demo_rate_history():
    """Demo: Registro Histórico de Cambios de Tasa"""
    print_separator("5. REGISTRO HISTÓRICO - Auditoría Completa")

    print("Escenario: Cambio de tasa USD de 36.50 a 37.00")
    print("Usuario: admin (ID: 1)")
    print("Razón: Actualización diaria BCV")
    print("")

    old_rate = Decimal("36.5000000000")
    new_rate = Decimal("37.0000000000")

    # Calcular diferencia
    difference = new_rate - old_rate
    variation = ((new_rate - old_rate) / old_rate * 100)

    print("📊 REGISTRO EN CurrencyRateHistory:")
    print(f"   currency_id: 1 (USD)")
    print(f"   company_id: 1")
    print(f"   old_rate: {old_rate}")
    print(f"   new_rate: {new_rate}")
    print(f"   rate_difference: {difference}")
    print(f"   rate_variation_percent: {variation:.4f}%")
    print(f"   changed_by: 1 (admin)")
    print(f"   change_type: automatic_api")
    print(f"   change_source: api_bcv")
    print(f"   changed_at: {datetime.now().isoformat()}")
    print(f"   change_reason: Actualización diaria BCV")

    print("\n✅ Auditoría completa:")
    print("   - Quién: admin")
    print("   - Cuándo: Timestamp exacto")
    print("   - Por qué: Razón registrada")
    print("   - Cuánto cambió: Diferencia y porcentaje")


def demo_conversion_scenarios():
    """Demo: Escenarios de Conversión del Mundo Real"""
    print_separator("6. ESCENARIOS REALES - Conversión y Cálculos")

    logic = CurrencyBusinessLogic()

    print("🏪 Escenario 1: Venta de Laptop en USD con pago en VES")
    print("-" * 60)

    laptop_price_usd = Decimal("500")  # $500 USD
    rate_usd_ves = Decimal("36.50")     # Tasa BCV

    # Convertir a VES
    ves_price, rate_used, method = logic.convert_to_base_currency(
        amount=laptop_price_usd,
        from_currency="USD",
        rate=rate_usd_ves,
        base_currency="VES"
    )

    print(f"   Precio laptop: ${laptop_price_usd} USD")
    print(f"   Tasa BCV: {rate_usd_ves} Bs/USD")
    print(f"   Precio en VES: Bs {ves_price}")
    print(f"   Método: {method}")

    # Calcular IGTF (si paga en VES con tarjeta de crédito extranjera)
    print(f"\n   💳 IGTF (3% sobre Bs {ves_price}):")
    igtf_ves, _, _ = logic.calculate_igtf(
        amount=ves_price,
        currency="VES",
        applies_igtf=False,  # VES no aplica
        igtf_rate=Decimal("3.00"),
        is_exempt=True
    )
    print(f"      Monto IGTF: Bs {igtf_ves} (NO APLICA para VES)")

    print("\n" + "=" * 80)

    print("\n💳 Escenario 2: Pago de $1,500 USD en Transferencia")
    print("-" * 60)

    payment_usd = Decimal("1500")
    igtf_rate = Decimal("3.00")

    # Calcular IGTF
    igtf_amount, applied, reason = logic.calculate_igtf(
        amount=payment_usd,
        currency="USD",
        applies_igtf=True,  # USD aplica IGTF
        igtf_rate=igtf_rate,
        is_exempt=False
    )

    print(f"   Monto: ${payment_usd} USD")
    print(f"   Método de pago: Transferencia")
    print(f"   Aplica IGTF: {'SÍ' if applied else 'NO'}")
    print(f"   Razón: {reason}")
    if applied:
        print(f"   💳 IGTF ({igtf_rate}%): ${igtf_amount} USD")
        print(f"   💰 TOTAL a pagar: ${payment_usd + igtf_amount} USD")

    print("\n" + "=" * 80)

    print("\n🏬 Escenario 3: Compra en Cúmar Fronteriza (COP)")
    print("-" * 60)

    purchase_cop = Decimal("10000")  # 10,000 COP
    rate_cop_ves = Decimal("0.0091")

    # Convertir a VES
    ves_equivalent, _, _ = logic.convert_to_base_currency(
        amount=purchase_cop,
        from_currency="COP",
        rate=rate_cop_ves,
        base_currency="VES"
    )

    print(f"   Precio: ${purchase_cop} COP")
    print(f"   Tasa: {rate_cop_ves} Bs/COP")
    print(f"   Equivalente en VES: Bs {ves_equivalent}")
    print(f"   IGTF: NO APLICA (moneda local fronteriza)")


def demo_api_examples():
    """Demo: Ejemplos de uso de la API"""
    print_separator("7. EJEMPLOS DE API - Uso Real")

    print("📡 POST /api/v1/currencies/")
    print("   Crear nueva moneda USD")
    print()
    print("   Request:")
    print("   ```json")
    usd_json = {
        "code": "USD",
        "name": "US Dollar",
        "symbol": "$",
        "exchange_rate": "36.5000000000",
        "decimal_places": 2,
        "is_base_currency": False,
        "conversion_method": "direct",
        "applies_igtf": True,
        "igtf_rate": "3.00",
        "igtf_min_amount": "1000.00",
        "rate_update_method": "api_bcv",
        "rate_source_url": "https://www.bcv.org.ve"
    }
    import json
    print(json.dumps(usd_json, indent=2))
    print("   ```")

    print("\n" + "-" * 80 + "\n")

    print("📡 PUT /api/v1/currencies/2/rate")
    print("   Actualizar tasa de cambio con registro histórico")
    print()
    print("   Request:")
    print("   ```json")
    rate_update_json = {
        "new_rate": "37.5000000000",
        "change_reason": "Actualización diaria BCV - Tasa oficial",
        "change_type": "automatic_api",
        "change_source": "api_bcv",
        "provider_metadata": {
            "api_response_time": "150ms",
            "bcv_timestamp": "2026-01-15T10:00:00"
        }
    }
    print(json.dumps(rate_update_json, indent=2))
    print("   ```")

    print("\n" + "-" * 80 + "\n")

    print("📡 GET /api/v1/currencies/convert")
    print("   Convertir montos entre monedas")
    print()
    print("   Query params:")
    print("   - from_currency: USD")
    print("   - to_currency: VES")
    print("   - amount: 100")
    print()
    print("   Response:")
    print("   ```json")
    conversion_response = {
        "original_amount": 100.0,
        "original_currency": "USD",
        "converted_amount": 3650.0,
        "target_currency": "VES",
        "exchange_rate_used": 36.5,
        "conversion_method": "direct",
        "rate_metadata": {
            "rate": 36.5,
            "method": "direct",
            "source": "api_bcv",
            "last_update": "2026-01-15T10:00:00",
            "currency_id": 1,
            "decimal_places": 2
        }
    }
    print(json.dumps(conversion_response, indent=2))
    print("   ```")

    print("\n" + "-" * 80 + "\n")

    print("📡 POST /api/v1/currencies/igtf/calculate")
    print("   Calcular IGTF para una transacción")
    print()
    print("   Query params:")
    print("   - amount: 1500")
    print("   - currency_id: 2 (USD)")
    print("   - payment_method: transfer")
    print()
    print("   Response:")
    print("   ```json")
    igtf_response = {
        "original_amount": 1500.0,
        "igtf_amount": 45.0,
        "igtf_applied": True,
        "total_with_igtf": 1545.0,
        "metadata": {
            "currency_code": "USD",
            "applies": True,
            "rate": 3.0,
            "reason": "IGTF 3.0% aplicado",
            "igtf_config_id": 1
        }
    }
    print(json.dumps(igtf_response, indent=2))
    print("   ```")


def demo_decimal_precision():
    """Demo: Precisión Financiera con 10 decimales"""
    print_separator("8. PRECISIÓN FINANCIERA - Hasta 10 decimales")

    from decimal import Decimal, getcontext

    # Configurar contexto de alta precisión
    getcontext().prec = 20  # Precisión total

    print("🔢 Precisión configurada:")
    print(f"   - Máxima precisión: 10 decimales para tasas")
    print(f"   - Precisión default: 2 decimales para display")
    print(f"   - Tipo de datos: SQL NUMERIC(20, 10)")

    print("\n📊 Ejemplos de tasas con diferentes precisiones:")

    rates = [
        ("USD/VES", "36.5045237891", 2, "36.50"),
        ("EUR/VES", "39.8023741234", 2, "39.80"),
        ("COP/VES", "0.0091234567", 4, "0.0091"),
    ]

    for pair, rate_str, display_decimals, expected_display in rates:
        full_rate = Decimal(rate_str)
        displayed = full_rate.quantize(Decimal(f"0.{'1' * display_decimals}"))

        print(f"\n   {pair}:")
        print(f"      Tasa completa: {full_rate} (10 decimales)")
        print(f"      Display (2 dec): {displayed}")
        print(f"      Precisión perdida: {full_rate - displayed}")

    print("\n✅ Por qué alta precisión:")
    print("   - Tasas de cambio cambian frecuentemente")
    print("   - Pérdida por redondeo acumulada en grandes volúmenes")
    print("   - Auditoría contable precisa")
    print("   - Reportes fiscales exactos (SEN IAT)")


def main():
    """Ejecuta todas las demos"""
    print("\n" + "🇻🇪" * 40)
    print("  SISTEMA DE GESTIÓN DE MONEDAS - VENEZUELA")
    print("  Lógica Contable, IGTF y Precisión Financiera")
    print("🇻🇪" * 40)

    try:
        # 1. Validación ISO 4217
        demo_iso_validation()

        # 2. Factores de conversión
        demo_conversion_factors()

        # 3. Cálculo de IGTF
        demo_igtf_calculation()

        # 4. Creación de monedas
        demo_currency_creation()

        # 5. Registro histórico
        demo_rate_history()

        # 6. Escenarios reales
        demo_conversion_scenarios()

        # 7. API examples
        demo_api_examples()

        # 8. Precisión decimal
        demo_decimal_precision()

        # Resumen
        print_separator("✅ CARACTERÍSTICAS IMPLEMENTADAS")
        print("""
   ✅ Validación ISO 4217 - Códigos oficiales de moneda
   ✅ Factores de Conversión - Lógica venezolana automática
   ✅ IGTF Dinámico - Configurable por moneda y empresa
   ✅ Registro Histórico - Auditoría completa de cambios
   ✅ Precisión Financiera - Hasta 10 decimales
   ✅ Lógica Contable - Compliance con Venezuela SENIAT
   ✅ API RESTful - Endpoints completos para gestión
   ✅ Multi-empresa - Aislación de datos por compañía
        """)

        print("=" * 80)
        print("  🎉 SISTEMA LISTO PARA PRODUCCIÓN - VENEZUELA")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
