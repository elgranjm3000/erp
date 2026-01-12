# 🔐 Configuración de Variables de Entorno

## Archivos Creados

- ✅ `.env` - Archivo con variables de entorno (NO incluir en git)
- ✅ `.env.example` - Plantilla de ejemplo (SÍ incluir en git)
- ✅ `requirements.txt` - Actualizado con `python-dotenv`

## Variables de Entorno Configuradas

### 🔒 SEGURIDAD (CRÍTICO)

```bash
# Clave secreta para JWT (ya generada automáticamente)
SECRET_KEY=v0FBiQDtUDV7rCBOR1g60JFv816AeLYVet4yYqoG24Y

# Para producción, genera una nueva:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 🗄️ BASE DE DATOS

```bash
DATABASE_URL=mysql+mysqlconnector://root:tiger@localhost:3306/erp
```

### 🌐 APLICACIÓN

```bash
ENVIRONMENT=development
PORT=8000
HOST=0.0.0.0
```

### 🔐 CORS

```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 📊 LOGGING

```bash
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=              # Vacío = log a consola
```

### 🇻🇪 IMPUESTOS VENEZUELA

```bash
# Tasas de retención
IVA_RETENTION_RATE_75=75.0
IVA_RETENTION_RATE_100=100.0
ISLR_RETENTION_RATE_1=1.0
ISLR_RETENTION_RATE_2=2.0
ISLR_RETENTION_RATE_3=3.0

# Umbrales (en USD)
IVA_RETENTION_75_THRESHOLD=50.0
IVA_RETENTION_100_THRESHOLD=100.0
ISLR_RETENTION_1_THRESHOLD=5000.0
ISLR_RETENTION_2_THRESHOLD=10000.0
ISLR_RETENTION_3_THRESHOLD=20000.0
```

## Cambios Realizados

### 1. `config.py`
- ✅ Carga variables desde `.env` usando `python-dotenv`
- ✅ Todas las configuraciones usan `os.getenv()` con valores por defecto
- ✅ Configuración de impuestos venezolanos externalizada

### 2. `database.py`
- ✅ `DATABASE_URL` leída desde variable de entorno
- ✅ Carga variables con `load_dotenv()`

### 3. `main.py`
- ✅ Importa `config` para usar variables centralizadas
- ✅ Logging configurado según `LOG_LEVEL`
- ✅ CORS usa `ALLOWED_ORIGINS` desde config

## Seguridad Implementada

### ✅ ANTES (INSEGURO)
```python
SECRET_KEY = "your_secret_key"  # ❌ Hardcoded
DATABASE_URL = "mysql+...root:tiger@..."  # ❌ Expuesto
```

### ✅ DESPUÉS (SEGURO)
```python
SECRET_KEY = os.getenv("SECRET_KEY", "...")  # ✅ Desde .env
DATABASE_URL = os.getenv("DATABASE_URL", "...")  # ✅ Desde .env
```

## Archivos que NUNCA se deben commitear

✅ `.env` ya está en `.gitignore`
❌ Nunca incluir credenciales reales en el repo
✅ Usar `.env.example` como plantilla

## Próximos Pasos Recomendados

### 🔴 CRÍTICO - Antes de Producción

1. **Cambiar SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Cambiar contraseña de base de datos**:
   ```bash
   # Actualizar en .env
   DATABASE_URL=mysql+mysqlconnector://erp_user:PASSWORD_SEGURA@localhost:3306/erp
   ```

3. **Configurar CORS para producción**:
   ```bash
   ALLOWED_ORIGINS=https://tudominio.com,https://www.tudominio.com
   ```

4. **Activar HTTPS**:
   - Usar Nginx/Apache como reverse proxy
   - Configurar certificado SSL (Let's Encrypt)

### 🟡 IMPORTANTE

5. **Implementar rate limiting**
6. **Agregar tests**
7. **Configurar logging a archivo**
8. **Implementar backup de base de datos**

## Verificación

El servidor está funcionando correctamente con las nuevas variables:

✅ Servidor responde en http://localhost:8000
✅ Login funciona con nueva SECRET_KEY
✅ Variables de entorno cargadas correctamente
✅ Logging configurado

## Comandos Útiles

```bash
# Verificar variables cargadas
source venv/bin/activate
python -c "import config; print(config.SECRET_KEY[:20] + '...')"

# Ver logs del servidor
tail -f /tmp/uvicorn.log

# Reiniciar servidor
pkill -f "uvicorn main:app"
source venv/bin/activate && uvicorn main:app --reload
```
