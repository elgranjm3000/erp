# crud/audit.py
"""
CRUD functions para auditoría y logs de seguridad
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from models import AuditLog, User
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import HTTPException


def create_audit_log(
    db: Session,
    company_id: int,
    action_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> AuditLog:
    """Crear un registro de auditoría"""
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
    db.refresh(audit_log)
    return audit_log


def get_audit_logs(
    db: Session,
    company_id: int,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    ip_address: Optional[str] = None
) -> List[AuditLog]:
    """Obtener logs de auditoría con filtros"""
    query = db.query(AuditLog).filter(AuditLog.company_id == company_id)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if ip_address:
        query = query.filter(AuditLog.ip_address == ip_address)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()


def get_user_activity_summary(
    db: Session,
    company_id: int,
    user_id: int,
    days: int = 30
) -> Dict[str, Any]:
    """Obtener resumen de actividad de usuario"""
    from sqlalchemy import extract

    cutoff_date = datetime.now() - datetime.timedelta(days=days)

    # Estadísticas de acciones
    action_stats = db.query(
        AuditLog.action_type,
        func.count(AuditLog.id)
    ).filter(
        AuditLog.company_id == company_id,
        AuditLog.user_id == user_id,
        AuditLog.created_at >= cutoff_date,
        AuditLog.success == True
    ).group_by(AuditLog.action_type).all()

    # Último login
    last_login = db.query(AuditLog).filter(
        AuditLog.company_id == company_id,
        AuditLog.user_id == user_id,
        AuditLog.action_type == 'LOGIN',
        AuditLog.success == True
    ).order_by(AuditLog.created_at.desc()).first()

    # Intentos fallidos de login
    failed_logins = db.query(func.count(AuditLog.id)).filter(
        AuditLog.company_id == company_id,
        AuditLog.user_id == user_id,
        AuditLog.action_type == 'LOGIN',
        AuditLog.success == False,
        AuditLog.created_at >= cutoff_date
    ).scalar() or 0

    # IPs usadas
    ips_used = db.query(
        AuditLog.ip_address,
        func.count(func.distinct(AuditLog.ip_address))
    ).filter(
        AuditLog.company_id == company_id,
        AuditLog.user_id == user_id,
        AuditLog.created_at >= cutoff_date
    ).scalar() or 0

    return {
        "action_stats": action_stats,
        "last_login": last_login.created_at if last_login else None,
        "failed_logins": failed_logins,
        "unique_ips": ips_used,
        "total_actions": sum([stat[1] for stat in action_stats])
    }


def get_security_report(
    db: Session,
    company_id: int,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """Generar reporte de seguridad"""
    # Total de acciones por tipo
    actions_by_type = db.query(
        AuditLog.action_type,
        func.count(AuditLog.id)
    ).filter(
        AuditLog.company_id == company_id,
        AuditLog.created_at >= start_date,
        AuditLog.created_at <= end_date
    ).group_by(AuditLog.action_type).all()

    # Logins exitosos vs fallidos
    login_stats = db.query(
        AuditLog.action_type,
        AuditLog.success,
        func.count(AuditLog.id)
    ).filter(
        AuditLog.company_id == company_id,
        AuditLog.action_type == 'LOGIN',
        AuditLog.created_at >= start_date,
        AuditLog.created_at <= end_date
    ).group_by(AuditLog.success).all()

    # Usuarios más activos
    top_users = db.query(
        AuditLog.user_id,
        func.count(AuditLog.id)
    ).filter(
        AuditLog.company_id == company_id,
        AuditLog.created_at >= start_date,
        AuditLog.created_at <= end_date
    ).group_by(AuditLog.user_id).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10).all()

    # Acciones fallidas recientes
    recent_failures = db.query(AuditLog).filter(
        AuditLog.company_id == company_id,
        AuditLog.success == False,
        AuditLog.created_at >= start_date,
        AuditLog.created_at <= end_date
    ).order_by(AuditLog.created_at.desc()).limit(20).all()

    return {
        "actions_by_type": dict(actions_by_type),
        "login_stats": {"success": login_stats.get(True, 0), "failed": login_stats.get(False, 0)},
        "top_users": [{"user_id": u[0], "actions": u[1]} for u in top_users],
        "recent_failures": [
            {
                "id": f.id,
                "username": f.username,
                "action": f.action_type,
                "error": f.error_message,
                "created_at": f.created_at.isoformat()
            }
            for f in recent_failures
        ]
    }
