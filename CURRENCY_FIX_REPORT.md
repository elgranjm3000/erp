# Fix Report: Error al Guardar Monedas en Frontend

**Fecha:** 2026-01-16
**Problema:** Error al crear/guardar monedas desde el frontend

---

## ❌ Problemas Detectados

### 1. Columna `user_agent` Faltante
**Error:**
```
Unknown column 'currency_rate_history.user_agent' in 'field list'
```

**Causa:**
- El modelo Python `CurrencyRateHistory` tenía el campo `user_agent`
- La tabla en la base de datos NO tenía esta columna
- La migración anterior `b7d48f3525eb` no se aplicó correctamente

### 2. Tabla `igtf_config` Faltante
**Error:**
```
Table 'erp.igtf_config' doesn't exist
```

**Causa:**
- El modelo `IGTFConfig` existía en Python
- La tabla no se creó nunca en la base de datos
- No había migración para crearla

---

## ✅ Solución Aplicada

### Migración Creada: `0b4ff9112d8a`

**Archivo:** `/home/muentes/devs/erp/alembic/versions/0b4ff9112d8a_fix_user_agent_column_and_create_igtf_.py`

**Cambios:**
1. ✅ Agregó columna `user_agent` a `currency_rate_history` (VARCHAR(500), NULL)
2. ✅ Creó tabla `igtf_config` con todos los campos necesarios:
   - `id` (PK)
   - `company_id` (FK)
   - `currency_id` (FK)
   - `is_special_contributor` (Boolean)
   - `igtf_rate` (Numeric(5,2))
   - `min_amount_local` (Numeric(20,2))
   - `min_amount_foreign` (Numeric(20,2))
   - `is_exempt` (Boolean)
   - `exempt_transactions` (Text/JSON)
   - `applicable_payment_methods` (Text/JSON)
   - `valid_from` (DateTime)
   - `valid_until` (DateTime)
   - `created_at` (DateTime)
   - `created_by` (FK)
   - `notes` (Text)
   - Índices y restricciones únicas

**Ejecución:**
```bash
alembic upgrade head
# ✅ SUCCESS: b7d48f3525eb -> 0b4ff9112d8a
```

---

## 🧪 Tests de Verificación

### ✅ Test 1: Crear Moneda
```bash
POST /api/v1/currencies/
{
  "code": "CAD",
  "name": "Canadian Dollar",
  "symbol": "C$",
  "exchange_rate": "27.15"
}
```
**Resultado:** ✅ Moneda creada exitosamente (ID: 32)

### ✅ Test 2: Historial de Tasas
```bash
GET /api/v1/currencies/28/rate/history
```
**Resultado:** ✅ Retorna historial correctamente

### ✅ Test 3: Estadísticas
```bash
GET /api/v1/currencies/28/statistics
```
**Resultado:** ✅ Retorna estadísticas completas

### ✅ Test 4: Config IGTF
```bash
GET /api/v1/currencies/igtf/config
```
**Resultado:** ✅ Retorna array vacío (sin configuraciones especiales)

### ✅ Test 5: Actualizar Tasa
```bash
PUT /api/v1/currencies/28/rate
{
  "new_rate": "38.50",
  "change_reason": "Test del fix"
}
```
**Resultado:** ✅ Tasa actualizada, historial actualizado automáticamente

---

## 📊 Verificación de Histórico

**Antes del fix:**
- Error 500 al intentar crear moneda
- Error 500 al consultar historial
- Error 500 al consultar estadísticas
- Error 500 al listar config IGTF

**Después del fix:**
- ✅ Crear moneda: 200 OK
- ✅ Historial: 200 OK (2 registros)
- ✅ Estadísticas: 200 OK
- ✅ Config IGTF: 200 OK
- ✅ Actualizar tasa: 200 OK

---

## 🎯 Endpoints Verificados

| Endpoint | Método | Estado |
|----------|--------|--------|
| `/api/v1/currencies/` | POST | ✅ Funcional |
| `/api/v1/currencies/{id}/rate` | PUT | ✅ Funcional |
| `/api/v1/currencies/{id}/rate/history` | GET | ✅ Funcional |
| `/api/v1/currencies/{id}/statistics` | GET | ✅ Funcional |
| `/api/v1/currencies/igtf/config` | GET | ✅ Funcional |

---

## 🚀 Estado Actual

**Frontend:** ✅ READY
**Backend:** ✅ READY
**Base de Datos:** ✅ FIXED

**Conclusión:**
El error al guardar monedas desde el frontend ha sido **completamente resuelto**.

Todos los endpoints de monedas funcionan correctamente:
- Creación de monedas ✅
- Actualización de tasas ✅
- Historial de cambios ✅
- Estadísticas ✅
- Configuración IGTF ✅

El frontend puede ahora crear, editar y gestionar monedas sin errores.

---

## 📝 Archivos Modificados/Creados

1. **Migración creada:**
   - `/home/muentes/devs/erp/alembic/versions/0b4ff9112d8a_fix_user_agent_column_and_create_igtf_.py`

2. **Scripts de prueba:**
   - `/home/muentes/devs/erp/test_fix_moneda.sh`
   - `/home/muentes/devs/erp/test_all_endpoints_fix.sh`

3. **Reportes:**
   - Este archivo (`CURRENCY_FIX_REPORT.md`)

---

**Fix completado por:** Claude (Sonnet 4.5)
**Fecha de resolución:** 2026-01-16 18:56
**Estado:** ✅ RESUELTO
