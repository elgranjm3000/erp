# 📋 GUÍA: POS vs NEW-USD (Sistema REF)

## 🎯 DIFERENCIAS CLAVE

Tienes **2 formas de crear facturas** con el sistema REF:

---

## 1. **`/invoices/pos`** - Punto de Venta (Retail)

### 🛒 CARACTERÍSTICAS
- **Tipo:** Venta rápida al estilo retail/supermercado
- **UI:** Grid de productos + carrito de compras
- **Flujo:** Visual e intuitivo

### 🎨 INTERFAZ
```
┌─────────────────────────────────────────┐
│  🔍 Search: Laptop HP                   │
├─────────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐          │
│  │ Laptop│  │ Mouse │  │...    │          │
│  │  HP   │  │       │  │       │          │
│  │ $800  │  │ $15   │  │       │          │
│  └──────┘  └──────┘  └──────┘          │
│                                         │
│  Grid de productos con precio REF       │
└─────────────────────────────────────────┘

         ↓ Click para agregar

┌─────────────────────────────────────────┐
│  🛒 CARRITO                             │
├─────────────────────────────────────────┤
│  Laptop HP x1                          │
│  $800 USD → Bs. 275,605.60             │
│                                         │
│  💵 Total REF: $800 USD                │
│  💰 Total VES: Bs. 319,702.50          │
│  ✅ Sin IGTF (efectivo)                 │
│                                         │
│  [COBRAR]                              │
└─────────────────────────────────────────┘
```

### ✅ VENTAJAS
- Rápido para ventas frecuentes
- Visual (ves el producto)
- Ideal para retail
- Carrito dinámico
- Cálculo automático en tiempo real

### 📌 CUÁNDO USARLO
- Tiendas retail
- Supermercados
- Farmacias
- Cualquier negocio con mucho tráfico
- Ventas rápidas del día a día

---

## 2. **`/invoices/new-usd`** - Formulario Tradicional

### 📝 CARACTERÍSTICAS
- **Tipo:** Formulario backoffice (más detallado)
- **UI:** Dropdowns + campos manuales
- **Flujo:** Más control manual

### 🎨 INTERFAZ
```
┌─────────────────────────────────────────┐
│  Crear Factura (Sistema REF)            │
├─────────────────────────────────────────┤
│  Cliente: *                              │
│  [Seleccionar cliente...]               │
│                                         │
│  Método de Pago: *                      │
│  [Efectivo ▼]                           │
│                                         │
│  Productos: *                            │
│  [+ Agregar Producto]                    │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Producto: [Laptop HP ▼]        │   │
│  │ Cantidad: [1]                   │   │
│  │ [🗑️]                            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ☐ Exento de IGTF                       │
│  Tasa Manual (opcional): [________]     │
│                                         │
│  [✅ Crear Factura con Sistema REF]      │
└─────────────────────────────────────────┘

         ↓ Preview automático

┌─────────────────────────────────────────┐
│  💵 PREVIEW REF (Sistema Actualizado)   │
│  [Activo]                               │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │ Total Referencia (USD)          │   │
│  │ $800.00                          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Tasa BCV (2026-01-17): 344.51 Bs/USD  │
│  Subtotal VES: Bs. 275,605.60          │
│  IVA (16%): + Bs. 44,096.90            │
│  IGTF (3%): + Bs. 9,591.07              │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Total a Pagar                   │   │
│  │ Bs. 329,293.58                  │   │
│  │ ⚠️ Incluye IGTF 3%               │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### ✅ VENTAJAS
- Más control manual
- Puedes elegir exactamente productos
- Configurar tasas manuales
- Exención IGTF manual
- Ideal para facturas complejas

### 📌 CUÁNDO USARLO
- Facturas a clientes específicos
- Pedidos personalizados
- Facturas con muchos items
- Necesitas tasa manual específica
- Clientes corporativos
- Backoffice

---

## 🔄 COMPARACIÓN RÁPIDA

| Característica | `/invoices/pos` | `/invoices/new-usd` |
|---|---|---|
| **Tipo** | Retail / Rápido | Backoffice / Detallado |
| **Selección productos** | Visual (grid) | Manual (dropdown) |
| **Carrito** | Sí | No (lista) |
| **Velocidad** | ⚡ Rápido | 🐌 Más lento |
| **Control manual** | Bajo | Alto |
| **Ideal para** | Ventas rápidas | Facturas complejas |
| **Uso típico** | Retail | B2B / Corporativo |

---

## 🎯 ¿CUÁL USAR?

### Usa **`/invoices/pos`** si:
- ✅ Tienes un negocio retail
- ✅ Necesitas agilidad
- ✅ Las ventas son rápidas
- ✅ Prefieres interfaz visual
- ✅ Tienes muchos productos

**Ejemplo:**
```
Cliente entra a tienda →
Selecciona productos en grid →
Va a caja →
Cajero usa POS →
Cobrar en 2 minutos
```

### Usa **`/invoices/new-usd`** si:
- ✅ Es una factura específica para un cliente
- ✅ Necesitas personalización
- ✅ Tienes muchos items
- ✅ Necesitas tasa manual
- ✅ Es un pedido especial

**Ejemplo:**
```
Cliente corporativo llama →
Pide presupuesto por 50 items →
Usas new-usd →
Configuras manualmente →
Generas factura
```

---

## 💡 AMBOS USAN SISTEMA REF

**Importante:** Ambas formas usan el mismo sistema REF por debajo:

```javascript
// AMBOS llaman a la misma API:
referencePricesAPI.calculateInvoiceTotals({
  items: [...],
  customer_id: 123,
  payment_method: "transferencia" // o "efectivo"
})

// Y obtienen el mismo resultado:
{
  subtotal_reference: 800.00,    // USD
  subtotal_target: 275605.60,    // VES
  exchange_rate: 344.507,
  iva_amount: 44096.90,
  igtf_amount: 9591.07,
  total_amount: 329293.58
}
```

**La única diferencia es la interfaz:**
- POS = Interfaz visual rápida
- new-usd = Formulario manual detallado

---

## 🚀 FLUJO RECOMENDADO

### Escenario 1: Tienda Retail (diario)
```
1. Cliente entra
2. Empleado va a /invoices/pos
3. Selecciona productos visualmente
4. Clic "Cobrar"
5. Listo ✅
```

### Escenario 2: Factura Especial
```
1. Cliente llama pidiendo cotización
2. Empleado va a /invoices/new-usd
3. Selecciona cliente del dropdown
4. Agrega productos manualmente
5. Revisa preview REF
6. Clic "Crear Factura"
7. Listo ✅
```

---

## 📊 ARQUITECTURA TÉCNICA

```
┌────────────────────────────────────────┐
│         SISTEMA REF (Backend)          │
│  referencePricesAPI.calculateTotals() │
└───────────┬────────────────────────────┘
            │
    ┌───────┴────────┐
    ↓                ↓
┌─────────────┐  ┌──────────────┐
│ /invoices/pos│  |/invoices/new│
│   (Retail)   │  │    -usd      │
└─────────────┘  │ (Backoffice) │
                 └──────────────┘
```

**Ambos consumen la misma API**, solo cambia la UI.

---

## ✅ CONCLUSIÓN

**Respuesta a tu pregunta:**

> "en frontend tengo invoices/new-usd, pero la idea es que eso sea pos"

**Mi recomendación:** Mantén **ambos**:
- Usa `/invoices/pos` para ventas rápidas retail
- Usa `/invoices/new-usd` para facturas detalladas backoffice

**O si prefieres unificar:**
- Puedes renombrar `/invoices/pos` → `/invoices/pos-retail`
- Puedes renombrar `/invoices/new-usd` → `/invoices/new`

**Lo importante:** Ambos funcionan con el sistema REF que implementamos. La diferencia es solo la experiencia de usuario, no el cálculo.

---

## 🎓 PRÓXIMOS PASOS

¿Quieres que:
1. Mantenga ambos separados (recomendado)?
2. Los una en uno solo?
3. Cambie los nombres para más claridad?

Avísame y ajusto según necesites! 🚀
