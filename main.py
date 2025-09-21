from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
from sqlalchemy import text
from fastapi.responses import JSONResponse  # ⭐ IMPORTANTE


# Importar solo los routers que existen
from routers import products, movements, warehouses, users, warehousesproducts, invoices, purchases

# Importar dependencias
import database

# Crear la aplicación FastAPI
app = FastAPI(
    title="Sistema ERP Multiempresa",
    description="Sistema de planificación de recursos empresariales con soporte multiempresa",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= INCLUIR ROUTERS BÁSICOS =================

app.include_router(users.router, prefix="/api/v1", tags=["👥 Usuarios"])
app.include_router(products.router, prefix="/api/v1", tags=["📦 Productos"])
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
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# ================= MANEJO DE ERRORES =================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(  # ⭐ Debe usar JSONResponse, no dict
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
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)