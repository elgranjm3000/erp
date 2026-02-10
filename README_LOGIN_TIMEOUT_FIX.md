# 🔴 Login Timeout - Fix Summary

**Fecha:** 2026-01-16
**Problema:** Timeout de 15 segundos en `/api/v1/auth/login`
**Estado:** ⚠️ FIX APLICADO - REQUIERE VERIFICACIÓN

---

## ✅ Fixes Aplicados

### Fix 1: Eager Loading en `auth.py`

**Archivo:** `/home/muentes/devs/erp/auth.py`

**Cambios:**
```python
# Línea 7: Agregado joinedload
from sqlalchemy.orm import Session, joinedload

# Líneas 55-61: Eager loading en verify_token
user = db.query(User).options(
    joinedload(User.company)
).filter(...)

# Líneas 106-122: Eager loading en authenticate_user
user = db.query(User).options(
    joinedload(User.company)
).join(Company).filter(...)
```

### Fix 2: Simplificación de Login en `crud/auth.py`

**Archivo:** `/home/muentes/devs/erp/crud/auth.py`

**Cambios:**
```python
def authenticate_multicompany(db: Session, login_data: schemas.LoginRequest):
    """
    Autenticación OPTIMIZADA

    Cambios:
    1. Sin joins complejos en queries
    2. Company cargada separadamente al final
    3. Queries simplificadas paso a paso
    """

    # Paso 1: Buscar usuario (query simple)
    user = db.query(User).filter(
        User.username == login_data.username,
        User.is_active == True
    ).first()

    # Paso 2: Verificar password
    # Paso 3: Verificar empresa
    # Paso 4: Actualizar último login
    # Paso 5: Generar token
    # Paso 6: Cargar company solo para response
```

---

## 📊 Teoría del Problema

### Causa Original: Lazy Loading

```python
# ❌ ANTES (Causa timeout)
user = db.query(User).filter(...).first()
return user.company  # Lazy loading causa 2da query
```

**Problema:**
- Query 1: Obtener user (~50ms)
- Lazy loading: Intentar obtener user.company
- Lock: Esperar lock en tabla companies
- **Timeout: 15 segundos**

### Solución Aplicada

```python
# ✅ DESPUÉS (Sin lazy loading)
# Obtener user
user = db.query(User).filter(...).first()

# Obtener company en query separada
company = db.query(Company).filter(...).first()

return company
```

---

## 🧪 Tests

### Test Script
```bash
./test_login_fix.sh
```

**Resultados esperados:**
- Login time: < 500ms (con eager loading)
- Sin timeouts
- 5 logins consecutivos: consistentes

---

## 🔧 Si Sigue Fallando

### Solución 1: Verificar Índices en BD

```sql
-- Verificar índices existentes
SHOW INDEX FROM users;
SHOW INDEX FROM companies;

-- Crear índices faltantes
CREATE INDEX idx_user_login ON users(username, company_id, is_active);
CREATE INDEX idx_user_company ON users(company_id);
CREATE INDEX idx_company_tax_id ON companies(tax_id);
```

### Solución 2: Verificar Locks

```sql
-- Verificar transacciones activas
SHOW PROCESSLIST;

-- Verificar locks
SHOW ENGINE INNODB STATUS;

-- Matar transacciones zombie
KILL <process_id>;
```

### Solución 3: Optimizar bcrypt

```python
# En auth.py
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=10  # Reducir de 12 a 10
)
```

### Solución 4: Aumentar Timeout

```python
# En frontend, aumentar timeout
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  body: JSON.stringify(credentials),
  signal: AbortSignal.timeout(30000)  # 30s en lugar de 10s
});
```

---

## 📈 Métricas

### Antes del Fix
```
POST /api/v1/auth/login
Response time: ~15,000ms (15s)
Error: timeout of 10000ms exceeded
Success rate: 0%
```

### Después del Fix (Esperado)
```
POST /api/v1/auth/login
Response time: < 500ms
Error: None
Success rate: 100%
```

---

## 🎯 Archivos Modificados

1. ✅ `/home/muentes/devs/erp/auth.py`
   - Agregado `joinedload` a imports
   - Agregado eager loading en `verify_token`
   - Agregado eager loading en `authenticate_user`

2. ✅ `/home/muentes/devs/erp/crud/auth.py`
   - Simplificada `authenticate_multicompany`
   - Queries paso a paso sin joins complejos
   - Company cargada separadamente al final

3. ✅ `/home/muentes/devs/erp/routers/currencies_v2.py`
   - Corregido import de `get_current_user` → `verify_token`

---

## 🚀 Siguiente Pasos

1. ✅ **Restart servidor** - Recargar cambios de auth.py
2. ⏭️ **Ejecutar test** - `./test_login_fix.sh`
3. ⏭️ **Verificar índices BD** - Si sigue lento
4. ⏭️ **Revisar locks** - Si sigue fallando

---

## 📞 Si No Funciona

### Workaround Temporal

```bash
# 1. Reiniciar completamente el servidor
pkill -f uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 2. Verificar que no haya procesos zombie
ps aux | grep python

# 3. Limpiar cache de Python
find . -type d -name __pycache__ -exec rm -rf {} +
```

### Contactar

Si el problema persiste después de aplicar todos los fixes:
1. Revisar logs del servidor: `tail -f /tmp/claude/-home-muentes-devs-erp/tasks/b2f47e5.output`
2. Verificar logs de MySQL: Verificar slow query log
3. Revisar documentación: `LOGIN_TIMEOUT_REPORT.md`

---

**Fix Aplicado Por:** Claude (Sonnet 4.5)
**Fecha:** 2026-01-16 23:58
**Archivos Modificados:** 3
**Líneas de Código Cambiadas:** ~50
**Estado:** ✅ FIX APLICADO - ESPERANDO VERIFICACIÓN

🚀 **Los cambios están aplicados. Por favor prueba el login nuevamente.**
