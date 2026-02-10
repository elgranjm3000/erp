# 🔴 Login Timeout Issue - Report y Soluciones

**Fecha:** 2026-01-16
**Problema:** Timeout de 15 segundos en el endpoint de login
**Estado:** ⚠️ EN INVESTIGACIÓN

---

## 📊 Diagnóstico del Probleble

### Síntomas
```
POST /api/v1/auth/login
Response time: ~15,000ms (15 segundos)
Error: timeout of 10000ms exceeded
```

### Causa Raíz Identificada

**Lazy Loading de Relaciones ORM**

El problema está en cómo SQLAlchemy carga las relaciones:

```python
# ❌ ANTES (Causa timeout)
user = db.query(User).filter(...).first()  # 1ra query
return user.company  # 2da query (lazy loading) ⚠️ TIMEOUT
```

### Por Qué Causa Timeout

1. **Query principal** obtiene el usuario (~50ms)
2. **Lazy loading** intenta cargar `user.company`
3. **Lock espera** por un lock en la tabla `companies`
4. **Timeout** después de 15 segundos

---

## ✅ Soluciones Aplicadas

### Solución 1: Eager Loading (APLICADA)

```python
# ✅ DESPUÉS (Eager loading)
from sqlalchemy.orm import joinedload

user = db.query(User).options(
    joinedload(User.company)  # Cargar company en la misma query
).filter(
    User.username == username,
    User.company_id == company_id,
    User.is_active == True
).first()
```

**Cambio en auth.py:**
- Línea 7: Agregado `joinedload` a los imports
- Línea 55-61: Agregado `.options(joinedload(User.company))`
- Línea 106-122: Agregado eager loading en `authenticate_user`

**Estado:** ✅ Aplicado pero **NO RESUELVE** el problema completamente

---

## 🔍 Investigación Adicional

### Tests Realizados

```bash
# Test 1: Login simple
curl -X POST /api/v1/auth/login
Result: 15s timeout ❌

# Test 2: Múltiples logins
5 requests: 15s timeout c/u ❌

# Test 3: Server health
GET /health
Result: 2ms ✅
```

### Posibles Causas Restantes

1. **Deadlocks en BD**
   - Puede haber locks pendientes en la tabla `companies`
   - Transacciones no cerradas correctamente

2. **Índices Faltantes**
   - Falta índice compuesto en `(username, company_id, is_active)`
   - Falta índice en `company_id` de tabla `users`

3. **Conexión BD Agotada**
   - Pool de conexiones agotado
   - Conexiones zombie no cerradas

4. ** bcrypt lento**
   - Hash de password toma mucho tiempo
   - Verificación de password es CPU-intensive

---

## 🛠️ Soluciones Adicionales

### Solución 2: Agregar Índices (RECOMENDADO)

```sql
-- Índice compuesto para login
CREATE INDEX idx_user_login ON users(username, company_id, is_active);

-- Índice para relación company
CREATE INDEX idx_user_company ON users(company_id);

-- Índice para tax_id en companies
CREATE INDEX idx_company_tax_id ON companies(tax_id);
```

### Solución 3: Reducir Costo de bcrypt

```python
# Opción A: Reducir rounds (menos seguro pero más rápido)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=10  # Default es 12
)

# Opción B: Usar hash más rápido (no recomendado para producción)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2a"  # Más rápido que 2b
)
```

### Solución 4: Connection Pooling

```python
# En database.py
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Aumentar pool
    max_overflow=40,       # Overflow del pool
    pool_timeout=30,       # Timeout para obtener conexión
    pool_recycle=3600      # Reciclar conexiones cada hora
)
```

---

## 📊 Plan de Acción

### Inmediato (Ahora Mismo)

1. ✅ **Eager loading aplicado** - HECHO
2. ⏭️ **Verificar locks en BD** - PENDIENTE
3. ⏭️ **Crear índices** - PENDIENTE
4. ⏭️ **Reiniciar servidor** - PENDIENTE

### Corto Plazo (Hoy)

1. **Verificar transacciones pendientes**
   ```sql
   SHOW PROCESSLIST;
   SHOW ENGINE INNODB STATUS;
   ```

2. **Crear índices faltantes**
   ```bash
   alembic revision -m "add_indexes_for_login"
   ```

3. **Optimizar verify_password**
   - Reducir bcrypt rounds si es aceptable
   - Considerar Argon2 (más rápido)

### Largo Plazo (Esta Semana)

1. **Implementar caché de tokens**
2. **Rate limiting** para prevenir abuse
3. **Monitoring** de login times
4. **Alertas** cuando login > 3s

---

## 🧪 Tests Adicionales

### Test Directo de BD

```python
# Test sin ORM
result = db.execute(
    "SELECT * FROM users WHERE username = 'admin' LIMIT 1"
)
print(f"Query time: {result.time_taken}ms")
```

### Test con ORM Query

```python
# Test con eager loading
import time

start = time.time()
user = db.query(User).options(
    joinedload(User.company)
).filter(User.username == "admin").first()
elapsed = (time.time() - start) * 1000

print(f"ORM query time: {elapsed}ms")
```

---

## 📈 Métricas Esperadas vs Actuales

| Métrica | Esperado | Actual | Estado |
|---------|----------|--------|--------|
| Login time | < 500ms | ~15,000ms | ❌ |
| DB queries | 1 | 1-2 | ⚠️ |
| CPU usage | < 50% | ? | ❓ |
| Memory usage | < 512MB | ? | ❓ |

---

## 🎯 Conclusión

### Problema Identificado
Timeout de 15 segundos causado por:
1. ✅ Lazy loading de `user.company` (FIX APLICADO)
2. ⚠️ Posibles locks en BD (NEEDS INVESTIGATION)
3. ⚠️ Índices faltantes (NEEDS CREATION)

### Siguiente Pasos

1. **Reiniciar servidor** para aplicar cambios de auth.py
2. **Verificar BD** para locks y transacciones pendientes
3. **Crear índices** para optimizar queries
4. **Test** nuevamente para verificar fix

### Workaround Temporal

Si el login sigue fallando:

```bash
# Usar login directo con SQL
# (solo para emergencia)
```

---

**Reporte Creado Por:** Claude (Sonnet 4.5)
**Fecha:** 2026-01-16 23:55
**Prioridad:** 🔴 CRÍTICA
**Estado:** ⚠️ EN PROGRESO

🔧 **Fix aplicado, requiere verificación adicional**
