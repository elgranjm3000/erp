"""
Auth optimized - Versión simplificada para resolver timeout

Fix: Eliminar todas las operaciones que puedan causar timeout
"""

from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import User, Company
from auth import verify_password, create_access_token
from config import ACCESS_TOKEN_EXPIRE_MINUTES
import schemas

def authenticate_multicompany_fast(db: Session, login_data: schemas.LoginRequest):
    """
    Autenticación OPTIMIZADA para evitar timeout.

    Cambios:
    1. Query simplificada sin joins complejos
    2. Sin eager loading de company hasta el final
    3. Una sola transacción
    """

    # Paso 1: Buscar usuario (query simple, sin joins)
    user = db.query(User).filter(
        User.username == login_data.username,
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Paso 2: Verificar password (CPU intensive pero necesario)
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Paso 3: Verificar empresa activa solo si es necesario
    if user.company_id:
        company = db.query(Company).filter(
            Company.id == user.company_id,
            Company.is_active == True
        ).first()

        if not company:
            raise HTTPException(
                status_code=401,
                detail="Company is not active"
            )

    # Paso 4: Actualizar último login
    user.last_login = datetime.utcnow()

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    # Paso 5: Generar token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "company_id": user.company_id,
            "role": user.role,
            "is_company_admin": user.is_company_admin
        },
        expires_delta=access_token_expires
    )

    # Paso 6: Buscar company SOLO para el response (no crítico)
    company_data = None
    if user.company_id:
        company_data = db.query(Company).filter(
            Company.id == user.company_id
        ).first()

    return schemas.LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserWithCompany(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            company_id=user.company_id,
            is_active=user.is_active,
            is_company_admin=user.is_company_admin,
            created_at=user.created_at,
            last_login=user.last_login,
            company=company_data
        )
    )
