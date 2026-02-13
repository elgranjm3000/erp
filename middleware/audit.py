"""
Middleware para auditoría de seguridad - registra todas las acciones
"""

from fastapi import Request
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from models import AuditLog
from database import SessionLocal
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware para capturar IP y user agent para auditoría"""

    async def dispatch(self, request: Request, call_next):
        # Solo procesar respuestas exitosas y no OPTIONS
        if request.url.path in ["/health", "/metrics"] or request.method == "OPTIONS":
            return await call_next(request)

        # Obtener IP del cliente
        # Headers que pueden contener la IP real
        forwarded_for = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP") or request.headers.get("CF-Connecting-IP")
        if not real_ip:
            # X-Forwarded-For: X, Y, Z, etc.
            if forwarded_for:
                forwarded_for_parts = forwarded_for.split(",")[-1].strip().split(";")
                for part in reversed(forwarded_for_parts):
                    part = part.strip()
                    if part:
                        real_ip = part
                        break
            # Último recurso: Remote Address
            real_ip = request.client.host if not real_ip else real_ip

        # Obtener User Agent
        user_agent = request.headers.get("user-agent", "Unknown")

        # Guardar en el estado de la request para uso en endpoints
        request.state.audit_info = {
            "ip": real_ip,
            "user_agent": user_agent
        }

        response = await call_next(request)
        return response


# Función auxiliar para registrar logs
def log_audit(
    db: Session,
    company_id: int,
    user_id: int,
    username: str,
    action_type: str,
    entity_type: str = None,
    entity_id: int = None,
    ip_address: str = None,
    user_agent: str = None,
    details: str = None,
    success: bool = True,
    error_message: str = None
):
    """Función auxiliar para registrar logs de auditoría"""
    try:
        audit_log = AuditLog(
            company_id=company_id,
            user_id=user_id,
            username=username,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            success=success,
            error_message=error_message
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger.error(f"Error creating audit log: {e}")
        db.rollback()


# Tipos de acción para auditoría
class AuditActionType:
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CREATE_PRODUCT = "CREATE_PRODUCT"
    UPDATE_PRODUCT = "UPDATE_PRODUCT"
    DELETE_PRODUCT = "DELETE_PRODUCT"
    CREATE_SUPPLIER = "CREATE_SUPPLIER"
    UPDATE_SUPPLIER = "UPDATE_SUPPLIER"
    DELETE_SUPPLIER = "DELETE_SUPPLIER"
    CREATE_CUSTOMER = "CREATE_CUSTOMER"
    UPDATE_CUSTOMER = "UPDATE_CUSTOMER"
    DELETE_CUSTOMER = "DELETE_CUSTOMER"
    CREATE_WAREHOUSE = "CREATE_WAREHOUSE"
    UPDATE_WAREHOUSE = "UPDATE_WAREHOUSE"
    DELETE_WAREHOUSE = "DELETE_WAREHOUSE"
    CREATE_INVOICE = "CREATE_INVOICE"
    UPDATE_INVOICE = "UPDATE_INVOICE"
    DELETE_INVOICE = "DELETE_INVOICE"
    CREATE_PURCHASE = "CREATE_PURCHASE"
    UPDATE_PURCHASE = "UPDATE_PURCHASE"
