# 🇻🇪 Sistema de Gestión de Monedas - Lógica Contable Venezolana

Sistema completo de configuración de monedas para bases de datos SQL (PostgreSQL/MySQL) con backend Python, cumplimiento de normativas venezolanas y precisión financiera.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Modelo de Datos](#modelo-de-datos)
- [Lógica de Negocio](#lógica-de-negocio)
- [IGTF - Impuesto a Grandes Transacciones](#igtf)
- [API Endpoints](#api-endpoints)
- [Ejemplos de Uso](#ejemplos-de-uso)

---

## ✨ Características

### 🎯 Identificación y Validación
- **ISO 4217**: Validación automática de códigos de moneda
- **Símbolo de impresión**: Compatibilidad con sistemas de imprenta digital
- **Nombre oficial**: Mapeo a lista oficial ISO

### 💰 Gestión de Tasas de Cambio
- **Actualización manual**: Desde panel administrativo
- **Actualización automática**: Via scraping o API (BCV, Binance, Fixer)
- **Registro histórico**: Cada cambio queda registrado con auditoría completa

### 📊 Precisión Numérica
- **Hasta 10 decimales**: Para tasas de cambio
- **Default: 2 decimales**: Para display de precios
- **Tipo SQL**: `NUMERIC(20, 10)` para máxima precisión

### 🧮 Factores de Conversión (Lógica Venezolana)
- **VES (Bolívar)**: `None` (moneda base, no aplica conversión)
- **USD, EUR**: Factor = `1 / tasa` (más fuerte que VES)
- **COP, ARS**: Factor = `tasa` (más débil, fronterizas)
- **Triangulación**: Via USD para monedas sin tasa directa

### 💳 Obligaciones Tributarias (IGTF)
- **IGTF configurable**: Tasa por moneda y empresa
- **Divisas (USD, EUR)**: Aplican 3% por defecto
- **VES (Bolívar)**: NO aplica (moneda nacional)
- **Contribuyentes especiales**: Configuración avanzada
- **Exenciones**: Por tipo de transacción y método de pago

---

## 🏗️ Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                       │
│  POST /api/v1/currencies/                                   │
│  PUT  /api/v1/currencies/{id}/rate                           │
│  GET  /api/v1/currencies/{id}/rate/history                   │
│  POST /api/v1/currencies/igtf/calculate                      │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│              CurrencyService (Lógica de Negocio)             │
│  • validate_iso_4217()                                        │
│  • calculate_conversion_factor()                              │
│  • calculate_igtf()                                           │
│  • create_currency()                                          │
│  • update_currency_rate()                                     │
│  • get_currency_history()                                     │
└───────┬─────────────────────────────────┬──────────────────────┘
        │                                 │
┌───────▼───────────┐         ┌─────────▼───────────────┐
│   Currency Model  │         │  CurrencyRateHistory     │
│   - code (ISO)     │         │  - old_rate               │
│   - exchange_rate │         │  - new_rate               │
│   - applies_igtf   │         │  - rate_difference         │
│   - igtf_rate      │         │  - changed_by              │
│   - conversion...  │         │  - changed_at              │
└───────────────────┘         └──────────────────────────┘
        │
┌───────▼───────────────────────────────────────────────────────┐
│                     Database (PostgreSQL/MySQL)               │
│  CREATE TABLE currencies (                                     │
│    id INT PRIMARY KEY,                                       │
│    code VARCHAR(3) NOT NULL,  -- ISO 4217                  │
│    exchange_rate NUMERIC(20,10),  -- ¡Precisión!            │
│    conversion_method VARCHAR(20),                          │
│    applies_igtf BOOLEAN,                                   │
│    igtf_rate NUMERIC(5,2)                                 │
│    ...                                                      │
│  );                                                        │
│                                                            │
│  CREATE TABLE currency_rate_history (                      │
│    id INT PRIMARY KEY,                                     │
│    old_rate NUMERIC(20,10),                               │
│    new_rate NUMERIC(20,10),                               │
│    rate_variation_percent NUMERIC(10,4),                 │
│    changed_by INT,                                        │
│    changed_at TIMESTAMP,                                  │
│    change_reason TEXT                                     │
│  );                                                        │
└────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Modelo de Datos

### Tabla: `currencies`

```sql
CREATE TABLE currencies (
    -- Identificación
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    code VARCHAR(3) NOT NULL,  -- ISO 4217 (USD, VES, EUR)
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NOT NULL,  -- Símbolo de impresión ($, Bs, €)

    -- Tasa de cambio (PRECISIÓN FINANCIERA)
    exchange_rate NUMERIC(20, 10) NOT NULL DEFAULT 1.0,
    decimal_places INT NOT NULL DEFAULT 2,

    -- Moneda base
    is_base_currency BOOLEAN NOT NULL DEFAULT FALSE,

    -- Factor de conversión
    conversion_factor NUMERIC(20, 10),
    conversion_method VARCHAR(20),  -- 'direct', 'inverse', 'via_usd'

    -- IGTF (Obligaciones tributarias)
    applies_igtf BOOLEAN NOT NULL DEFAULT FALSE,
    igtf_rate NUMERIC(5, 2) NOT NULL DEFAULT 3.00,
    igtf_exempt BOOLEAN NOT NULL DEFAULT FALSE,
    igtf_min_amount NUMERIC(20, 2),

    -- Actualización automática
    rate_update_method VARCHAR(20) NOT NULL DEFAULT 'manual',
    last_rate_update TIMESTAMP,
    next_rate_update TIMESTAMP,
    rate_source_url VARCHAR(500),

    -- Auditoría
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by INT,
    updated_by INT,

    CONSTRAINT uq_currency_code_per_company UNIQUE (company_id, code)
);
```

### Tabla: `currency_rate_history`

**Propósito**: Registro histórico inmutable de todos los cambios de tasa.

```sql
CREATE TABLE currency_rate_history (
    id SERIAL PRIMARY KEY,
    currency_id INT NOT NULL,
    company_id INT NOT NULL,

    -- Cambios registrados
    old_rate NUMERIC(20, 10) NOT NULL,
    new_rate NUMERIC(20, 10) NOT NULL,
    rate_difference NUMERIC(20, 10) NOT NULL,
    rate_variation_percent NUMERIC(10, 4),

    -- Metadata del cambio
    changed_by INT,
    change_type VARCHAR(20) NOT NULL,  -- 'manual', 'automatic_api', etc.
    change_source VARCHAR(100),
    user_ip VARCHAR(45),
    change_reason TEXT,

    -- Timestamp
    changed_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Ejemplo de registro**:

| Campo | Valor |
|-------|-------|
| currency_id | 1 (USD) |
| old_rate | 36.5000000000 |
| new_rate | 37.0000000000 |
| rate_difference | 0.5000000000 |
| rate_variation_percent | 1.3699% |
| changed_by | 5 (admin) |
| change_type | automatic_api |
| change_source | api_bcv |
| changed_at | 2026-01-15 10:00:00 |
| change_reason | Actualización diaria BCV |

---

## 🧮 Lógica de Negocio

### 1. Validación ISO 4217

Cada moneda se valida contra la lista oficial ISO 4217:

```python
def validate_iso_4217(code: str) -> Tuple[bool, Optional[str]]:
    """
    Valida que el código sea ISO 4217 válido.

    Ejemplos válidos:
    - USD (United States Dollar) ✅
    - VES (Venezuelan Bolívar) ✅
    - EUR (Euro) ✅

    Ejemplos inválidos:
    - XYZ (No existe) ❌
    - US (Faltan caracteres) ❌
    - DOLLAR (No es código) ❌
    """
```

### 2. Factores de Conversión

#### Regla por tipo de moneda:

```python
SI code == "VES":
    factor = None  # Moneda base, no aplica conversión

ELIF code in ["USD", "EUR", "GBP"]:  # Más fuerte que VES
    factor = 1 / exchange_rate
    # Ejemplo: USD 36.50 → factor = 1/36.50 = 0.0274

ELIF code in ["COP", "ARS"]:  # Más débil (frontera)
    factor = exchange_rate
    # Ejemplo: COP 0.0091 → factor = 0.0091

ELSE:  # Otras monedas
    factor = None  # Requiere triangulación
```

#### Ejemplos de conversión:

```
1 USD = 0.0274 VES  (factor: 1/36.50)
100 COP = 0.91 VES   (factor: 0.0091)
1 EUR = 0.0251 VES  (factor: 1/39.80)
```

### 3. Registro Histórico de Cambios

**¿Qué se registra?**

- Valor ANTERIOR de la tasa
- Valor NUEVO de la tasa
- Diferencia absoluta (nuevo - antiguo)
- Variación porcentual
- Usuario/proceso que realizó el cambio
- IP address
- Razón del cambio
- Timestamp exacto

**¿Por qué?**

- Auditoría contable completa
- Reportes fiscales (SEN IAT)
- Análisis de tendencias
- Reconstrucción de estados históricos
- Trazabilidad de errores

---

## 💳 IGTF - Impuesto a Grandes Transacciones Financieras

### ¿Qué es el IGTF?

El **Impuesto a las Grandes Transacciones Financieras** es un tributo venezolano que grava:
- Pagos en divisas (USD, EUR)
- Transferencias internacionales
- Tarjetas de crédito/débito extranjeras

### Tasas

| Operación | Tasa |
|-----------|------|
| Pagos en divisas (electrónico) | 3% |
| Pagos en efectivo (divisas) | 3% |
| Transferencias al exterior | 3% |

### Lógica de Aplicación

```python
def aplica_igtf(currency_code: str) -> bool:
    """
    Determina si aplica IGTF según moneda.

    VES (Bolívar): NO aplica (moneda nacional)
    USD, EUR: SÍ aplica (divisas)
    Otras: Depende de configuración
    """
    if currency_code == "VES":
        return False, "Moneda nacional, no aplica IGTF"

    elif currency_code in ["USD", "EUR"]:
        return True, "Divisa extranjera, aplica IGTF (Ley)"

    else:
        return False, "Requiere configuración especial"
```

### Ejemplo de Cálculo

```python
# Transacción de $1,500 USD

monto = 1500  # USD
igtf_rate = 3.00  # 3%

# Cálculo
igtf_amount = (monto * igtf_rate) / 100
             = (1500 * 3) / 100
             = 45 USD

# Total a pagar
total = monto + igtf_amount
      = 1500 + 45
      = 1,545 USD
```

### Configuración Avanzada

```python
# Contribuyente especial de IGTF
igtf_config = {
    "is_special_contributor": True,  # Retiene 100%
    "igtf_rate": 3.00,
    "min_amount_local": 1000,  # Bs 1000 mínimo
    "exempt_transactions": [
        "pago_nomina",
        "pago_proveedores_nacionales"
    ],
    "applicable_payment_methods": [
        "transfer",
        "credit_card",
        "debit_card"
    ]
}
```

---

## 🌐 API Endpoints

### 1. Crear Moneda

```http
POST /api/v1/currencies/
Content-Type: application/json

{
    "code": "USD",
    "name": "US Dollar",
    "symbol": "$",
    "exchange_rate": "36.5000000000",
    "decimal_places": 2,
    "is_base_currency": false,
    "conversion_method": "direct",
    "applies_igtf": true,
    "igtf_rate": "3.00",
    "igtf_min_amount": "1000.00",
    "rate_update_method": "api_bcv",
    "rate_source_url": "https://www.bcv.org.ve"
}
```

**Validaciones automáticas**:
- ✅ Código ISO 4217 válido
- ✅ Símbolo no vacío
- ✅ Tasa positiva
- ✅ Solo una moneda base por empresa
- ✅ Factor de conversión calculado automáticamente

### 2. Actualizar Tasa (con Historial)

```http
PUT /api/v1/currencies/2/rate
Content-Type: application/json

{
    "new_rate": "37.0000000000",
    "change_reason": "Actualización diaria BCV - Tasa oficial",
    "change_type": "automatic_api",
    "change_source": "api_bcv",
    "provider_metadata": {
        "api_response_time": "150ms",
        "bcv_timestamp": "2026-01-15T10:00:00"
    }
}
```

**Genera automáticamente**:
1. Registro en `currency_rate_history`
2. Cálculo de diferencia y variación
3. Registro de usuario e IP
4. Timestamp exacto

### 3. Consultar Historial

```http
GET /api/v1/currencies/2/rate/history?limit=50
```

**Response** (ordenado por fecha descendente):

```json
[
    {
        "id": 1234,
        "currency_id": 2,
        "old_rate": 36.5000000000,
        "new_rate": 37.0000000000,
        "rate_difference": 0.5000000000,
        "rate_variation_percent": 1.3699,
        "changed_by": 5,
        "change_type": "automatic_api",
        "change_source": "api_bcv",
        "changed_at": "2026-01-15T10:00:00",
        "change_reason": "Actualización diaria BCV"
    }
]
```

### 4. Convertir Montos

```http
GET /api/v1/currencies/convert?from_currency=USD&to_currency=VES&amount=100
```

**Response**:

```json
{
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
        "last_update": "2026-01-15T10:00:00"
    }
}
```

### 5. Calcular IGTF

```http
POST /api/v1/currencies/igtf/calculate?amount=1500&currency_id=2&payment_method=transfer
```

**Response**:

```json
{
    "original_amount": 1500.0,
    "igtf_amount": 45.0,
    "igtf_applied": true,
    "total_with_igtf": 1545.0,
    "metadata": {
        "currency_code": "USD",
        "applies": true,
        "rate": 3.0,
        "reason": "IGTF 3.0% aplicado",
        "igtf_config_id": 1
    }
}
```

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Venta de Laptop en USD

```python
# Precio: $500 USD
# Cliente paga en VES

# 1. Convertir precio a VES
rate = 36.50  # Tasa BCV
price_ves = 500 * 36.50  # Bs 18,250

# 2. Cliente paga con tarjeta de crédito (aplica IGTF)
igtf_rate = 3.00
igtf_ves = (18250 * 3) / 100  # Bs 547.50

# 3. Total a pagar
total = 18250 + 547.50  # Bs 18,797.50
```

### Ejemplo 2: Compra Fronteriza (COP)

```python
# Precio: 10,000 COP
# Rate: 1 COP = 0.0091 VES

# Convertir a VES
price_ves = 10000 * 0.0091  # Bs 91

# IGTF NO aplica (moneda local fronteriza)
igtf = 0

# Total
total = 91  # Bs 91
```

### Ejemplo 3: Factura Multi-Divisa

```python
# Items:
# - 2 Laptops @ $500 USD c/u
# - 1 Monitor @ €230 EUR

# Configuración
base_currency = "VES"
rate_usd_ves = 36.50
rate_eur_ves = 39.80
igtf_rate = 3.00

# Cálculos
laptops_ves = (2 * 500) * 36.50  # Bs 36,500
monitor_ves = 230 * 39.80        # Bs 9,154
subtotal = 36500 + 9154         # Bs 45,654

# IGTF (sobre divisas)
igtf_laptops = (36500 * 3) / 100    # Bs 1,095
igtf_monitor = (9154 * 3) / 100     # Bs 274.62
total_igtf = 1095 + 274.62        # Bs 1,369.62

# Total factura
total = 45654 + 1369.62           # Bs 47,023.62
```

---

## 🎯 Cumplimiento Normativo

### 🇻🇪 Normativas Venezolanas

| Norma | Descripción | Implementación |
|--------|-------------|----------------|
| **Ley de IGTF** | 3% sobre pagos en divisas | `applies_igtf`, `igtf_rate` |
| **SEN IAT** | Reporte de tasas históricas | `currency_rate_history` |
| **Providencia** | Precisión en cálculos | `NUMERIC(20, 10)` |
| **ISO 4217** | Códigos estándar | `validate_iso_4217()` |

### 🌍 Normativas Internacionales

| Norma | Descripción | Implementación |
|--------|-------------|----------------|
| **ISO 4217** | Códigos de moneda | Lista oficial ISO |
| **GAAP** | Precisión financiera | Decimal con 10 decimales |
| **IFRS** | Revelación de tasas | `currency_rate_history` |

---

## 🔧 Instalación

```bash
# Archivos creados:
erp/
├── models/
│   └── currency_config.py              # Modelos SQL
├── schemas/
│   └── currency_config_schemas.py       # Pydantic schemas
├── services/
│   └── currency_business_service.py     # Lógica de negocio
├── routers/
│   └── currency_config_router.py        # API endpoints
├── tests/
│   └── test_currency_config.py          # Tests
└── demo_currency_venezuela.py          # Demo completa
```

### Migración de Base de Datos

```sql
-- PostgreSQL
CREATE TABLE currencies (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES companies(id),
    code VARCHAR(3) NOT NULL,
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    exchange_rate NUMERIC(20, 10) NOT NULL DEFAULT 1.0,
    decimal_places INT NOT NULL DEFAULT 2,
    is_base_currency BOOLEAN NOT NULL DEFAULT FALSE,
    conversion_factor NUMERIC(20, 10),
    conversion_method VARCHAR(20),
    applies_igtf BOOLEAN NOT NULL DEFAULT FALSE,
    igtf_rate NUMERIC(5, 2) NOT NULL DEFAULT 3.00,
    igtf_exempt BOOLEAN NOT NULL DEFAULT FALSE,
    igtf_min_amount NUMERIC(20, 2),
    rate_update_method VARCHAR(20) NOT NULL DEFAULT 'manual',
    last_rate_update TIMESTAMP,
    next_rate_update TIMESTAMP,
    rate_source_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by INT REFERENCES users(id),
    updated_by INT REFERENCES users(id),
    notes TEXT,
    CONSTRAINT uq_currency_code_per_company UNIQUE (company_id, code)
);

CREATE TABLE currency_rate_history (
    id SERIAL PRIMARY KEY,
    currency_id INT NOT NULL REFERENCES currencies(id),
    company_id INT NOT NULL REFERENCES companies(id),
    old_rate NUMERIC(20, 10) NOT NULL,
    new_rate NUMERIC(20, 10) NOT NULL,
    rate_difference NUMERIC(20, 10) NOT NULL,
    rate_variation_percent NUMERIC(10, 4),
    changed_by INT REFERENCES users(id),
    change_type VARCHAR(20) NOT NULL,
    change_source VARCHAR(100),
    user_ip VARCHAR(45),
    change_reason TEXT,
    provider_metadata TEXT,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_currency_company ON currencies(company_id);
CREATE INDEX idx_currency_code ON currencies(code);
CREATE INDEX idx_rate_history_currency ON currency_rate_history(currency_id, changed_at);
```

---

## 📊 Reportes

### 1. Reporte de Tasas Históricas

```python
# Obtener historial de USD en los últimos 30 días
history = service.get_currency_history(
    currency_id=1,  # USD
    company_id=1,
    limit=1000
)

# Análisis
for entry in history:
    print(f"{entry.changed_at}: {entry.old_rate} → {entry.new_rate}")
    print(f"  Variación: {entry.rate_variation_percent}%")
```

### 2. Reporte de IGTF

```python
# Calcular IGTF para todas las transacciones del mes
total_igtf = 0

for invoice in invoices:
    if invoice.currency.code != "VES":  # Divisa
        igtf_amount, applied, _ = service.calculate_igtf_for_transaction(
            amount=invoice.amount,
            currency_id=invoice.currency_id,
            company_id=invoice.company_id
        )
        if applied:
            total_igtf += igtf_amount

print(f"Total IGTF del mes: {total_igtf} VES")
```

---

## 🎉 Conclusión

Sistema **production-ready** con:

✅ Validación ISO 4217
✅ Precisión financiera (10 decimales)
✅ Factores de conversión automáticos
✅ Cálculo de IGTF
✅ Registro histórico completo
✅ Auditoría SENIAT-ready
✅ API RESTful
✅ Multi-empresa
✅ Lógica contable venezolana

**🇻🇪 Hecho para Venezuela** pero **escalable a cualquier país**.
