# 💵 Sistema Multi-Moneda Venezuela - Flujo Completo

## 📊 RESUMEN DEL SISTEMA

El sistema tiene **2 componentes integrados** que trabajan juntos:

### 1. **Módulo de Monedas** (`/currencies`)
- Gestión de monedas (USD, VES, EUR, etc.)
- Tasas de cambio manuales
- Configuración IGTF
- Sistema multi-moneda genérico

### 2. **Sistema de Precios REF** (implementado recientemente)
- `price_usd` en productos (PRECIO DE REFERENCIA)
- Cálculo automático en facturas
- Usa **tasa BCV del día**
- Sistema específico para Venezuela

---

## 🔄 FLUJO DE TRABAJO COMPLETO

### PASO 1: Configurar Monedas (única vez)

```
/currencies → Nueva Moneda
```

**Crear monedas:**
- **USD** (Dólar Americano)
  - `is_base_currency: true` ✅
  - `code: USD`
  - `symbol: $`

- **VES** (Bolívares)
  - `code: VES`
  - `symbol: Bs`
  - `applies_igtf: true`
  - `igtf_rate: 3.00`

### PASO 2: Sincronizar Tasa BCV

```
/currencies → Botón "🔄 Sincronizar BCV"
```

**Qué hace:**
- Conecta al Banco Central de Venezuela
- Obtiene tasa oficial del día
- Guarda en `daily_rates` table

**Resultado:**
```
USD → VES: 344.507 Bs/USD
Fecha: 2026-01-17
Fuente: BCV
```

### PASO 3: Crear Productos con Precio REF

```
/products/new → Precio de Referencia (USD)
```

**Campos:**
```
Nombre: Laptop HP
SKU: LAPT-HP-001
💵 price_usd: 800.00  ← PRECIO REF (USD)
Price VES: [auto-calculado]  ← Se calcula solo
```

**Cálculo automático:**
```
price_usd ($800) × tasa BCV (344.507) = Bs. 275,605.60
```

### PASO 4: Facturar con Sistema REF

```
/invoices/pos → POS
```

**Al agregar productos:**
1. Usuario agrega "Laptop HP" al carrito
2. Sistema detecta `price_usd = $800`
3. Calcula automáticamente:
   ```
   Subtotal REF: $800 USD
   Tasa BCV: 344.507
   Subtotal VES: Bs. 275,605.60
   IVA (16%): Bs. 44,096.90
   IGTF (3%): Bs. 9,591.07 [transferencia]
              Bs. 0.00 [efectivo] ✅
   ```

**Resultado según método de pago:**

| Método de Pago | Subtotal | IVA | IGTF | Total VES |
|---|---|---|---|---|
| **Transferencia** | Bs. 275,605.60 | Bs. 44,096.90 | Bs. 9,591.07 | **Bs. 329,293.57** |
| **Efectivo** | Bs. 275,605.60 | Bs. 44,096.90 | **Bs. 0.00** | **Bs. 319,702.50** |

**Ahorro pagando en efectivo:** Bs. 9,591.07 💰

---

## 🎯 PANTALLAS Y COMPONENTES

### 1. `/currencies` - Gestión de Monedas

**Widgets visibles:**
- [📊] Stats: Total monedas, Moneda base, Con IGTF
- [💵] **Widget Tasa BCV** (nueva integración)
  - Muestra tasa actual USD → VES
  - Botón "Sincronizar BCV"
  - Indica si la tasa está actualizada
  - Link a productos

**Acciones:**
- Nueva moneda
- Editar tasa
- Ver historial
- Sincronizar BCV

**Flujo:**
```
Usuario ve tasa BCV → Entiende que se usa en productos →
Va a /products/new → Crea producto con price_usd
```

### 2. `/products/new` - Crear Producto

**Sección de precios:**

```
┌─────────────────────────────────────────────┐
│ 💵 Precio de Referencia (USD)              │
│ Precio oficial en dólares (moneda estable)  │
│                                             │
│ [$] 800.00____________________              │
│                                             │
│ ⚡ Este precio se usará para calcular       │
│    automáticamente el precio en VES         │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │ 📊 Precio Calculado en VES          │   │
│ │ Tasa BCV: 344.51 Bs/USD             │   │
│ │ Precio VES: Bs. 275,605.60          │   │
│ └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘

Precio en VES (calculado automáticamente)
[Bs] 275,605.60__________________  ← Auto-fill
```

**Componentes:**
- `REFPriceCalculator` - Muestra cálculo en tiempo real
- `price_usd` - Campo principal (azul prominente)
- `price` - Campo VES (auto-calculado)

### 3. `/invoices/pos` - Punto de Venta

**Carrito con totales REF:**

```
┌─────────────────────────────────────────────┐
│ 💵 Total Referencia (USD)                  │
│ $800.00                                     │
└─────────────────────────────────────────────┘

Tasa BCV (2026-01-17): 344.51 Bs/USD
Subtotal VES: Bs. 275,605.60
IVA (16%): + Bs. 44,096.90

IGTF (3%): + Bs. 9,591.07  ← Solo transferencia
                            ← Efectivo: Bs. 0.00

┌─────────────────────────────────────────────┐
│ Total a Pagar                               │
│ ⚠️ Incluye IGTF 3%                          │
│                                             │
│ Bs. 329,293.57                              │
└─────────────────────────────────────────────┘
```

**Método de pago:**
- **Efectivo:** Sin IGTF ✅
- **Transferencia/Zelle/Pago Móvil:** Con IGTF (3%)

---

## 🔗 CONEXIÓN ENTRE SISTEMAS

### Diagrama de Flujo

```
┌───────────────────────────────────────────────────────────┐
│ 1. /CURRENCIES                                           │
│    - Configurar USD y VES                                │
│    - Sincronizar tasa BCV                                │
│    - Widget muestra tasa actual                          │
└───────────────────┬───────────────────────────────────────┘
                    │
                    │ daily_rates (BCV: 344.507)
                    ▼
┌───────────────────────────────────────────────────────────┐
│ 2. /PRODUCTS/NEW                                         │
│    - Usuario ingresa price_usd: $800                    │
│    - REFPriceCalculator usa tasa BCV                    │
│    - Calcula: 800 × 344.507 = Bs. 275,605.60            │
│    - Guarda product con price_usd                        │
└───────────────────┬───────────────────────────────────────┘
                    │
                    │ Product { price_usd: 800 }
                    ▼
┌───────────────────────────────────────────────────────────┐
│ 3. /INVOICES/POS                                          │
│    - Usuario agrega producto al carrito                  │
│    - referencePricesAPI.calculateInvoiceTotals()        │
│    - Usa price_usd + tasa BCV del día                   │
│    - Calcula:                                           │
│      • Subtotal REF: $800 USD                           │
│      • Subtotal VES: Bs. 275,605.60                     │
│      • IVA (16%): Bs. 44,096.90                         │
│      • IGTF (3%): Bs. 9,591.07 [transferencia]         │
│                  Bs. 0.00 [efectivo]                   │
└───────────────────────────────────────────────────────────┘
```

---

## 📦 ESTRUCTURA DE DATOS

### Tablas Involucradas

**1. currencies**
```sql
id: 1 (USD)
code: USD
is_base_currency: true
exchange_rate: 1.0

id: 2 (VES)
code: VES
applies_igtf: true
igtf_rate: 3.00
```

**2. daily_rates**
```sql
company_id: 2
base_currency_id: 1 (USD)
target_currency_id: 2 (VES)
exchange_rate: 344.507
rate_date: 2026-01-17
source: BCV
```

**3. products**
```sql
id: 27
name: Laptop HP
price: 275605.60  ← VES (calculado)
price_usd: 800.00  ← USD (REF) ✅
```

**4. invoice_items**
```sql
product_id: 27
quantity: 1
unit_price_reference: 800.00  ← USD
unit_price_target: 275605.60  ← VES
exchange_rate: 344.507
iva_amount: 44096.90
igtf_amount: 9591.07  ← Transferencia
                0.00  ← Efectivo
```

---

## 🎨 COMPONENTES FRONTEND

### Por Página

**`/currencies`**
- `BCVRateWidget` - Muestra tasa BCV actual
- `CurrencyForm` - Formulario crear/editar moneda
- `RateUpdateModal` - Actualizar tasa manual
- `RateHistory` - Historial de cambios

**`/products/new`**
- `REFPriceCalculator` - Calcula precio VES en tiempo real
- Campo `price_usd` prominente (azul)
- Campo `price` VES (auto-fill)

**`/invoices/pos`**
- Display REF totals (bimonetario)
- Cálculo automático al cambiar método de pago
- Indicador IGTF (efectivo vs electrónico)

---

## ✅ VENTAJAS DEL SISTEMA INTEGRADO

1. **Única fuente de verdad:** `price_usd` como precio REF
2. **Transparencia:** Usuario ve tasa BCV que se usa
3. **Actualización automática:** Tasa BCV se sincroniza diariamente
4. **Trazabilidad:** Cada factura registra tasa usada
5. **Flexibilidad:** Permite tasa manual si es necesario
6. **Compliance:** IGTF según ley venezolana
7. **Eficiencia:** Cálculos automáticos, sin errores manuales

---

## 🚀 PRÓXIMOS PASOS

1. ✅ Frontend REF completado
2. ✅ Productos migrados a `price_usd`
3. ⏳ **Historial de conversiones en facturas**
4. ⏳ **Reportes bimonetarios**
5. ⏳ **Auditoría de cambios de precios**

---

## 📞 SOPORTE

¿Preguntas?
- Ver módulo `/currencies` para configurar monedas
- Ver `/products/new` para crear productos con REF
- Ver `/invoices/pos` para facturar con cálculos automáticos
