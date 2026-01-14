# config.py
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

# ================= CONFIGURACIÓN DE SEGURIDAD =================
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_change_this_in_production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# ================= CONFIGURACIÓN DE LA APLICACIÓN =================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# ================= CONFIGURACIÓN DE LOGGING =================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "")

# ================= CONFIGURACIÓN DE CORS =================
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# ================= CONFIGURACIÓN DE IMPUESTOS VENEZUELA =================
# Tasas de retención de IVA
IVA_RETENTION_RATE_75 = float(os.getenv("IVA_RETENTION_RATE_75", "75.0"))
IVA_RETENTION_RATE_100 = float(os.getenv("IVA_RETENTION_RATE_100", "100.0"))

# Tasas de retención de ISLR
ISLR_RETENTION_RATE_1 = float(os.getenv("ISLR_RETENTION_RATE_1", "1.0"))
ISLR_RETENTION_RATE_2 = float(os.getenv("ISLR_RETENTION_RATE_2", "2.0"))
ISLR_RETENTION_RATE_3 = float(os.getenv("ISLR_RETENTION_RATE_3", "3.0"))

# Umbrales para retenciones
IVA_RETENTION_75_THRESHOLD = float(os.getenv("IVA_RETENTION_75_THRESHOLD", "50.0"))
IVA_RETENTION_100_THRESHOLD = float(os.getenv("IVA_RETENTION_100_THRESHOLD", "100.0"))
ISLR_RETENTION_1_THRESHOLD = float(os.getenv("ISLR_RETENTION_1_THRESHOLD", "5000.0"))
ISLR_RETENTION_2_THRESHOLD = float(os.getenv("ISLR_RETENTION_2_THRESHOLD", "10000.0"))
ISLR_RETENTION_3_THRESHOLD = float(os.getenv("ISLR_RETENTION_3_THRESHOLD", "20000.0"))
