"""
Endpoints para consultar logs de auditoría y seguridad
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from models import AuditLog, User, Company
from database import get_db
from schemas import UserBase
from middleware.audit import log_audit, AuditActionType

router = APIRouter(tags=["🔍 Auditoría"])


@router.get("/audit/stats/dashboard")
async def get_dashboard_stats(
    days: int = Query(7, ge=1, le=90, description="Días a consultar"),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas para el dashboard de seguridad

    - **days**: Número de días a consultar (por defecto 7)

    Retorna:
    - Total de acciones
    - Acciones por tipo (usando SQL directo para evitar errores)
    - Logins exitosos vs fallidos
    - Usuarios activos
    - Alertas de seguridad
    """
    cutoff_date = datetime.now() - timedelta(days=days)

    # Total de acciones - usar SQL directo
    total_actions = db.execute(
        text("SELECT COUNT(*) FROM audit_logs WHERE company_id = :cid AND created_at >= :cutoff"),
        {"cid": 1, "cutoff": cutoff_date}
    ).scalar()

    # Acciones por tipo - usar SQL directo
    actions_by_type = db.execute(
        text("""
            SELECT action_type, COUNT(*) as count
            FROM audit_logs
            WHERE company_id = :cid AND created_at >= :cutoff
            GROUP BY action_type
        """),
        {"cid": 1, "cutoff": cutoff_date}
    ).all()

    # Login stats - usar SQL directo
    login_stats = db.execute(
        text("""
            SELECT success, COUNT(*) as count
            FROM audit_logs
            WHERE company_id = :cid
              AND action_type = 'LOGIN'
              AND created_at >= :cutoff
            GROUP BY success
        """),
        {"cid": 1, "cutoff": cutoff_date}
    ).all()

    login_dict = {1 if row[0] == 1 else 0: row[1] for row in login_stats}

    # Usuarios únicos activos - usar SQL directo
    active_users = db.execute(
        text("SELECT COUNT(DISTINCT user_id) FROM audit_logs WHERE company_id = :cid AND created_at >= :cutoff"),
        {"cid": 1, "cutoff": cutoff_date}
    ).scalar()

    # Intentos fallidos recientes - usar query simple
    recent_failures = db.query(AuditLog).filter(
        AuditLog.company_id == 1,
        AuditLog.success == False,
        AuditLog.created_at >= cutoff_date
    ).order_by(AuditLog.created_at.desc()).limit(10).all()

    return {
        "total_actions": total_actions or 0,
        "actions_by_type": {str(row[0]): row[1] for row in actions_by_type},
        "login_stats": {
            "successful": login_dict.get(1, 0),
            "failed": login_dict.get(0, 0)
        },
        "active_users": active_users or 0,
        "recent_failures": [
            {
                "id": f.id,
                "username": f.username,
                "action": f.action_type,
                "ip": f.ip_address,
                "created_at": f.created_at.isoformat()
            }
            for f in recent_failures
        ],
        "period_days": days
    }


@router.get("/audit/logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0, description="Saltar registros"),
    limit: int = Query(50, ge=1, le=100, description="Límite de registros"),
    start_date: Optional[datetime] = Query(None, description="Fecha inicial"),
    end_date: Optional[datetime] = Query(None, description="Fecha final"),
    action_type: Optional[str] = Query(None, description="Tipo de acción"),
    entity_type: Optional[str] = Query(None, description="Tipo de entidad"),
    ip_address: Optional[str] = Query(None, description="Dirección IP"),
    db: Session = Depends(get_db)
):
    """
    Obtener logs de auditoría con filtros

    - **skip**: Número de registros a saltar
    - **limit**: Número máximo de registros a retornar (máx 100)
    - **start_date**: Fecha inicial para filtrar
    - **end_date**: Fecha final para filtrar
    - **action_type**: Filtrar por tipo de acción (LOGIN, LOGOUT, CREATE_PRODUCT, etc.)
    - **entity_type**: Filtrar por tipo de entidad (Product, Customer, Supplier, etc.)
    - **ip_address**: Filtrar por dirección IP
    """
    from crud.audit import get_audit_logs

    logs = get_audit_logs(
        db=db,
        company_id=1,  # TODO: Get from authenticated user
        skip=skip,
        limit=limit,
        user_id=None,
        action_type=action_type,
        entity_type=entity_type,
        start_date=start_date,
        end_date=end_date,
        ip_address=ip_address
    )

    return {
        "data": logs,
        "total": len(logs),
        "skip": skip,
        "limit": limit
    }


@router.get("/audit/security-report")
async def get_security_report(
    start_date: datetime = Query(..., description="Fecha inicial"),
    end_date: datetime = Query(..., description="Fecha final"),
    db: Session = Depends(get_db)
):
    """
    Generar reporte de seguridad para un rango de fechas

    Incluye:
    - Acciones por tipo
    - Estadísticas de login (exitosos vs fallidos)
    - Usuarios más activos
    - Acciones fallidas recientes
    """
    from crud.audit import get_security_report

    report = get_security_report(
        db=db,
        company_id=1,  # TODO: Get from authenticated user
        start_date=start_date,
        end_date=end_date
    )

    return report
