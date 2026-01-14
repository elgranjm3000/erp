from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import os
from sqlalchemy import text
from fastapi.responses import JSONResponse


# Importar solo los routers que existen
from routers import products, movements, warehouses, users, warehousesproducts, invoices, purchases, customers, suppliers, categories, companies

# Importar dependencias
import database
import config

# ================= CONFIGURACIÓN DE LOGGING =================

# Configurar logging según variables de entorno
log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=config.LOG_FILE if config.LOG_FILE else None
)
logger = logging.getLogger(__name__)

# ================= VARIABLES DE ENTORNO =================

# Usar orígenes permitidos desde config.py
ALLOWED_ORIGINS = config.ALLOWED_ORIGINS

# Agregar orígenes adicionales si está en producción
if os.getenv("PRODUCTION"):
    additional_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    ALLOWED_ORIGINS.extend([origin.strip() for origin in additional_origins if origin.strip()])

# ================= CREAR APLICACIÓN =================

app = FastAPI(
    title="Sistema ERP Multiempresa",
    description="Sistema de planificación de recursos empresariales con soporte multiempresa",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ================= CONFIGURAR CORS (ANTES de los routers) =================
# ⭐ CRÍTICO: Este middleware debe agregarse ANTES de los routers
# ⭐ IMPORTANTE: No usar allow_origins=["*"] con allow_credentials=True

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,                    # ✅ Permite cookies
    allow_methods=["*"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Requested-With",
        "Accept-Language",
        "Accept-Encoding",
        "X-CSRF-Token",
    ],
    expose_headers=[
        "Content-Type",
        "Content-Length",
        "X-Total-Count",
        "Access-Control-Allow-Credentials",
    ],
    max_age=7200,  # Cachear pre-flight requests por 2 horas
)

# ================= INCLUIR ROUTERS =================

app.include_router(users.router, prefix="/api/v1", tags=["👥 Usuarios"])
app.include_router(categories.router, prefix="/api/v1", tags=["🏷️ Categorías"])
app.include_router(companies.router, prefix="/api/v1", tags=["🏢 Empresas"])
app.include_router(products.router, prefix="/api/v1", tags=["📦 Productos"])
app.include_router(suppliers.router, prefix="/api/v1", tags=["📦 Proveedores"])
app.include_router(customers.router, prefix="/api/v1", tags=["👥 Clientes"])
app.include_router(invoices.router, prefix="/api/v1", tags=["📄 Facturas"])
app.include_router(purchases.router, prefix="/api/v1", tags=["🛒 Compras"])
app.include_router(movements.router, prefix="/api/v1", tags=["🔄 Movimientos"])
app.include_router(warehouses.router, prefix="/api/v1", tags=["🏭 Almacenes"])
app.include_router(warehousesproducts.router, prefix="/api/v1", tags=["📦 Stock"])

# ================= ENDPOINTS RAÍZ =================

@app.get("/")
def read_root():
    return {
        "message": "Sistema ERP Multiempresa",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "register_company": "/api/v1/auth/register-company",
            "login": "/api/v1/auth/login",
            "check_company": "/api/v1/auth/check-company-tax-id/{tax_id}",
            "check_username": "/api/v1/auth/check-username/{username}"
        }
    }

@app.get("/health")
def health_check():
    try:
        db = database.SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "healthy",
            "database": "connected",
            "allowed_origins": ALLOWED_ORIGINS
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    """Manejador para requests OPTIONS (preflight CORS)"""
    return {
        "message": "OK"
    }

# ================= MANEJO DE ERRORES =================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ================= STARTUP =================

@app.on_event("startup")
async def startup_event():
    try:
        db = database.SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Conexión a la base de datos exitosa")
        print("🚀 Sistema ERP iniciado correctamente")
        print("📚 Documentación: http://localhost:8000/docs")
        print(f"🔐 CORS permitido para: {', '.join(ALLOWED_ORIGINS)}")
        print("✅ Preflight CORS handler instalado")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)