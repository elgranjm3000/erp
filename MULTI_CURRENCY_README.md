# 🌍 Arquitectura Multi-Moneda Escalable

Sistema multi-moneda **altamente escalable y desacoplado** para backends Python. No hay "hardcoding" solo para USD/VES - es completamente agnóstico a monedas.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Uso Rápido](#uso-rápido)
- [Componentes](#componentes)
- [Ejemplos](#ejemplos)
- [Tests](#tests)

## ✨ Características

### 🎯 Provider Pattern para Exchange Rates
- **Interfaz abstracta**: `ExchangeRateProvider` para implementar proveedores
- **Múltiples fuentes**: BCV (oficial), Binance (cripto), Fixer, Mock
- **Fallback automático**: Si uno falla, prueba el siguiente
- **Caché inteligente**: No satura APIs externas

### 💰 Lógica de Precios Agnóstica
- **Sin "precio en dólares"**: `CurrencyAmount(amount, currency)`
- **Conversión dinámica**: `amount.convert_to("VES", rate_manager)`
- **Precisión Decimal**: Cálculos financieros exactos

### 🧮 Motor de Impuestos Dinámico
- **Configurable**: Reglas en JSON/BD, no en código
- **Extensible**: Agregar impuestos sin modificar lógica
- **IGTF, IVA, ISLR**: Tasas actuales de Venezuela
- **Context-aware**: Diferentes tasas según método de pago

### 🔒 Inmutabilidad de Transacciones
- **Snapshots**: Estado exacto en el momento de creación
- **Auditoría**: `taxes_snapshot`, `exchange_rate_date`
- **No modificaciones**: `is_finalized=True`

### ⚡ Optimizaciones
- **Caché LRU**: Tasas frecuentes en memoria
- **Redis-ready**: Fácil migración a Redis
- **Batch conversions**: Múltiples montos en una llamada

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                   API Layer (FastAPI)                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          Transaction Service (Integración)              │
│  • Conversión de monedas                               │
│  • Cálculo de impuestos                                 │
│  • Creación de snapshots                                │
└─────┬───────────────┬──────────────────┬─────────────────┘
      │               │                  │
┌─────▼───────┐ ┌────▼─────┐     ┌─────▼──────────┐
│   Rate      │ │   Tax    │     │    Snapshot     │
│   Manager   │ │  Engine  │     │    Models      │
└─────┬───────┘ └────┬─────┘     └─────────────────┘
      │              │
┌─────▼──────┐ ┌────▼─────────┐
│  BCV       │ │  Tax Rules  │
│  Binance   │ │  Repository │
│  Mock      │ │  (DB/JSON)  │
└────────────┘ └──────────────┘
```

## 📦 Instalación

### Dependencias

```bash
pip install sqlalchemy pydantic requests beautifulsoup4
```

### Archivos creados

```
erp/
├── core/
│   └── exchange_rate_providers/
│       ├── __init__.py
│       ├── base.py              # Interfaz abstracta
│       ├── bcv_provider.py      # BCV scraper
│       ├── binance_provider.py  # Binance API
│       ├── mock_provider.py     # Mock para testing
│       └── factory.py           # Factory + Manager
│
├── services/
│   ├── __init__.py
│   ├── currency_conversion_service.py  # Conversión + caché
│   ├── tax_engine.py                  # Motor de impuestos
│   └── transaction_service.py          # Integración completa
│
├── models/
│   ├── __init__.py
│   └── transaction_snapshot.py         # Snapshots inmutables
│
├── schemas/
│   ├── __init__.py
│   └── transaction_schemas.py          # Pydantic schemas
│
├── tests/
│   ├── __init__.py
│   └── test_multi_currency_integration.py
│
└── demo_multi_currency.py              # Demo completa
```

## 🚀 Uso Rápido

### 1. Crear Servicio

```python
from services.transaction_service import create_transaction_service
from schemas.transaction_schemas import CreateTransactionRequest, TransactionItem, PaymentMethod

# Crear servicio con BCV -> Binance -> Mock como fallback
service = create_transaction_service(
    db=db_session,
    provider_priority=['bcv', 'binance', 'mock']
)
```

### 2. Crear Factura Multi-Moneda

```python
request = CreateTransactionRequest(
    base_currency="VES",  # Moneda base para totales
    customer_id=1,
    payment_method=PaymentMethod.TRANSFER,
    items=[
        TransactionItem(
            product_id=1,
            quantity=2,
            price_amount=Decimal("500"),  # $500 USD
            price_currency="USD",         # Precio agnóstico
            is_tax_exempt=False
        ),
        TransactionItem(
            product_id=2,
            quantity=1,
            price_amount=Decimal("740"),  # Bs 740
            price_currency="VES"
        )
    ]
)

response = service.create_invoice(
    request=request,
    company_id=1,
    user_id=1
)

print(f"Total: {response.total_base}")  # Bs XXX.XX
print(f"Impuestos: {response.total_tax}")  # Bs XX.XX
```

### 3. Conversión Simple

```python
from core.exchange_rate_providers import ExchangeRateManager
from services.currency_conversion_service import CurrencyConversionService, CurrencyAmount

# Crear manager
manager = ExchangeRateManager(['bcv', 'mock'])

# Crear monto agnóstico
price = CurrencyAmount(amount=Decimal("100"), currency="USD")

# Convertir a VES
ves_price = price.convert_to("VES", manager)

print(f"Price: {ves_price}")  # 3650.00 VES (ejemplo)
```

### 4. Calcular Impuestos

```python
from services.tax_engine import TaxEngine, TaxType

tax_engine = TaxEngine()

# Calcular IVA (16%)
iva = tax_engine.calculate_tax(
    amount=Decimal("10000"),
    currency="VES",
    tax_type=TaxType.IVA
)

print(f"IVA: {iva.tax_amount}")  # 1600.00 VES

# Calcular todos los impuestos
all_taxes = tax_engine.calculate_all_taxes(
    amount=Decimal("1500"),
    currency="USD"
)

for tax in all_taxes:
    print(f"{tax.tax_name}: ${tax.tax_amount}")
```

## 📚 Componentes

### 1. ExchangeRateProvider (Provider Pattern)

**Propósito**: Interfaz abstracta para obtener tasas de cambio

**Uso**:
```python
from core.exchange_rate_providers import BCVProvider, BinanceProvider

# Usar directamente
provider = BCVProvider()
rate = provider.get_rate("USD", "VES")
```

**Implementar nuevo proveedor**:
```python
from core.exchange_rate_providers import ExchangeRateProvider

class FixerProvider(ExchangeRateProvider):
    def get_rate(self, from_currency, to_currency, date=None):
        # Lógica para obtener desde Fixer.io
        pass

    def get_supported_currencies(self):
        return ["USD", "EUR", "GBP", ...]

    def refresh_rates(self):
        # Actualizar tasas
        pass
```

### 2. CurrencyConversionService

**Propósito**: Conversión de monedas con caché

**Características**:
- Caché LRU (máx 100 entradas, TTL 5 min)
- Precisión Decimal
- Inmutabilidad de resultados

**Uso**:
```python
result = CurrencyConversionService.convert(
    amount=Decimal("100"),
    from_currency="USD",
    to_currency="VES",
    rate_manager=manager
)

# Resultado inmutable
print(f"Converted: {result.converted_amount}")
print(f"Rate used: {result.rate_used}")
print(f"Provider: {result.provider}")
```

### 3. TaxEngine

**Propósito**: Cálculo dinámico de impuestos

**Características**:
- Reglas configurables
- Priorización de reglas
- Context-aware (método de pago, monto, etc.)

**Agregar regla personalizada**:
```python
from services.tax_engine import TaxEngine, TaxRule, TaxType

tax_engine = TaxEngine()

# Agregar nuevo impuesto
custom_tax = TaxRule(
    tax_type=TaxType.MUNICIPAL,
    name="Impuesto Municipal",
    rate=Decimal("2"),
    is_active=True,
    min_amount=Decimal("1000"),
    currency="USD",
    priority=5
)

tax_engine.add_rule(custom_tax)
```

### 4. TransactionSnapshot

**Propósito**: Inmutabilidad de transacciones

**Estructura**:
```python
snapshot = TransactionSnapshot(
    transaction_type="invoice",
    transaction_id=12345,
    amount_original=Decimal("1000"),
    currency_original="USD",
    amount_base=Decimal("36500"),
    currency_base="VES",
    exchange_rate=Decimal("36.5"),
    exchange_rate_date=datetime.now(),
    exchange_rate_provider="bcv",
    taxes_snapshot={
        "iva": {"rate": 16.0, "tax_amount": 5840.0},
        "igtf": {"rate": 3.0, "tax_amount": 1095.0}
    },
    transaction_metadata={...},
    is_finalized=True
)
```

## 🎨 Ejemplos

### Ejemplo 1: Factura con 3 monedas

```python
request = CreateTransactionRequest(
    base_currency="USD",
    items=[
        TransactionItem(product_id=1, quantity=1,
                      price_amount=Decimal("500"), price_currency="USD"),
        TransactionItem(product_id=2, quantity=2,
                      price_amount=Decimal("740"), price_currency="VES"),
        TransactionItem(product_id=3, quantity=1,
                      price_amount=Decimal("230"), price_currency="EUR")
    ]
)

# El sistema convierte automáticamente todo a USD
response = service.create_invoice(request, company_id=1, user_id=1)
```

### Ejemplo 2: Diferentes métodos de pago

```python
# Transferencia (IGTF aplica)
request_transfer = CreateTransactionRequest(
    base_currency="USD",
    payment_method=PaymentMethod.TRANSFER,
    items=[...]
)

# Efectivo (IGTF no aplica en algunos casos)
request_cash = CreateTransactionRequest(
    base_currency="USD",
    payment_method=PaymentMethod.CASH,
    items=[...]
)

# Los impuestos serán diferentes
response_transfer = service.create_invoice(request_transfer, ...)
response_cash = service.create_invoice(request_cash, ...)
```

### Ejemplo 3: Consultar tasa histórica

```python
from datetime import datetime

rate = CurrencyConversionService.get_rate(
    from_currency="USD",
    to_currency="VES",
    rate_manager=manager,
    date=datetime(2026, 1, 1)  # Tasa de esa fecha
)
```

## 🧪 Tests

Ejecutar tests:

```bash
# Todos los tests
pytest tests/test_multi_currency_integration.py -v

# Tests específicos
pytest tests/test_multi_currency_integration.py::TestCurrencyConversionService -v

# Con coverage
pytest tests/ --cov=services --cov=core --cov-report=html
```

### Tests incluidos:

- ✅ Provider Pattern (BCV, Binance, Mock)
- ✅ Conversión de monedas
- ✅ Caché de tasas
- ✅ Motor de impuestos
- ✅ Transacciones multi-moneda
- ✅ Inmutabilidad de snapshots
- ✅ Precisión Decimal

## 🔧 Configuración

### Variables de entorno

```bash
# Proveedor por defecto
DEFAULT_EXCHANGE_RATE_PROVIDER=bcv

# Orden de fallback
EXCHANGE_RATE_FALLBACK=bcv,binance,mock

# TTL de caché (minutos)
EXCHANGE_RATE_CACHE_TTL=5

# Redis (opcional)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Configuración de impuestos

En `services/tax_engine.py`, modificar `_initialize_default_rules()`:

```python
def _initialize_default_rules(self):
    # IVA estándar
    iva_standard = TaxRule(
        tax_type=TaxType.IVA,
        name="IVA Estándar",
        rate=Decimal("16"),  # ← CAMBIAR AQUÍ
        is_active=True,
        priority=10
    )
    # ...
```

## 🎯 Ventajas de esta Arquitectura

### ✅ Escalabilidad
- Agregar N monedas sin modificar código
- Proveedores de tasas "plug-and-play"
- Impuestos configurables

### ✅ Desacoplamiento
- Lógica de negocio independiente de fuentes de datos
- Servicios reutilizables
- Fácil testing (mocks)

### ✅ Precisión
- Decimal para cálculos financieros
- Snapshots inmutables
- Auditoría completa

### ✅ Performance
- Caché inteligente
- Fallback automático
- Batch operations

## 📖 Referencias

- [Provider Pattern](https://refactoring.guru/design-patterns/strategy-pattern)
- [Pydantic](https://docs.pydantic.dev/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Decimal para finanzas](https://docs.python.org/3/library/decimal.html)

## 🤝 Contribuir

Para agregar un nuevo proveedor de tasas:

1. Crear clase heredando de `ExchangeRateProvider`
2. Implementar métodos: `get_rate()`, `refresh_rates()`, etc.
3. Registrar en `ExchangeRateProviderFactory`
4. ¡Listo!

Para agregar un nuevo impuesto:

1. Crear `TaxRule` con parámetros deseados
2. `tax_engine.add_rule(nueva_regla)`
3. ¡Listo!

## 📝 Licencia

MIT

---

**Autor**: Claude (Anthropic)
**Fecha**: Enero 2026
**Versión**: 1.0.0

🌍 **Multi-Currency, Multi-Tenant, Multi-Provider** 🌍
