# crud/auth.py
"""
Funciones CRUD para autenticación y gestión de usuarios
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import Optional
import models
import sys
# Importar schemas.py directamente para evitar importar el package schemas/
import importlib.util
spec = importlib.util.spec_from_file_location("schemas_file", "/home/muentes/devs/erp/schemas.py")
if 'schemas_file' not in sys.modules:
    schemas_file = importlib.util.module_from_spec(spec)
    sys.modules['schemas_file'] = schemas_file
    spec.loader.exec_module(schemas_file)
schemas = sys.modules['schemas_file']
from auth import hash_password, create_access_token
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from .base import pwd_context

# ================= AUTENTICACIÓN BÁSICA =================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(
    db: Session, 
    username: str, 
    password: str, 
    company_tax_id: Optional[str] = None
):
    """Autenticar usuario con soporte multiempresa"""
    if company_tax_id:
        # Buscar usuario en empresa específica
        user = db.query(models.User).join(models.Company).filter(
            models.User.username == username,
            models.Company.tax_id == company_tax_id.upper(),
            models.User.is_active == True
        ).first()
    else:
        # Buscar usuario activo (para compatibilidad legacy)
        user = db.query(models.User).filter(
            models.User.username == username,
            models.User.is_active == True
        ).first()
    
    if not user or not verify_password(password, user.hashed_password):
        return None
    
    return user

def create_user(db: Session, username: str, password: str):
    """Legacy: crear usuario con empresa por defecto"""
    hashed_password = hash_password(password)
    
    # Buscar o crear empresa por defecto
    default_company = db.query(models.Company).filter(models.Company.id == 1).first()
    if not default_company:
        default_company = models.Company(
            name="Empresa Principal",
            legal_name="Empresa Principal C.A.",
            tax_id="DEFAULT-001",
            currency="USD",
            timezone="UTC",
            invoice_prefix="INV"
        )
        db.add(default_company)
        db.commit()
        db.refresh(default_company)
    
    db_user = models.User(
        username=username, 
        hashed_password=hashed_password,
        company_id=1,
        email=f"{username}@empresa.local",
        role="admin",
        is_company_admin=True,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ================= GESTIÓN MULTIEMPRESA =================

def authenticate_multicompany(db: Session, login_data: schemas.LoginRequest):
    """
    Autenticación - VERSIÓN EMERGENCY CON LOGGING
    """
    print(f"[LOGIN] ===== LOGIN REQUEST =====")
    print(f"[LOGIN] Username: {login_data.username}")
    print(f"[LOGIN] Company Tax ID: {login_data.company_tax_id}")

    from crud.auth_emergency import authenticate_multicompany_emergency

    return authenticate_multicompany_emergency(db, login_data)

def register_company_and_login(db: Session, company_data: schemas.CompanyCreate):
    """Registrar empresa nueva y hacer login automático"""
    from .companies import create_company_with_admin
    
    company = create_company_with_admin(db, company_data)
    
    admin_user = db.query(models.User).filter(
        models.User.company_id == company.id,
        models.User.is_company_admin == True
    ).first()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": admin_user.username,
            "company_id": admin_user.company_id,
            "role": admin_user.role,
            "is_company_admin": admin_user.is_company_admin
        },
        expires_delta=access_token_expires
    )
    
    return schemas.LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserWithCompany(
            id=admin_user.id,
            username=admin_user.username,
            email=admin_user.email,
            role=admin_user.role,
            company_id=admin_user.company_id,
            is_active=admin_user.is_active,
            is_company_admin=admin_user.is_company_admin,
            created_at=admin_user.created_at,
            last_login=admin_user.last_login,
            company=company
        )
    )

# ================= GESTIÓN DE USUARIOS DE EMPRESA =================

def get_company_users(db: Session, company_id: int):
    """Obtener usuarios de una empresa"""
    return db.query(models.User).filter(
        models.User.company_id == company_id
    ).all()

def create_user_for_company(
    db: Session, 
    user_data: schemas.UserCreateForCompany, 
    company_id: int
):
    """Crear usuario para empresa específica"""
    # Verificar si el username ya existe en la empresa
    existing_user = db.query(models.User).filter(
        models.User.username == user_data.username,
        models.User.company_id == company_id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists in this company"
        )
    
    hashed_password = hash_password(user_data.password)
    
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        company_id=company_id,
        role=user_data.role,
        is_company_admin=user_data.is_company_admin
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def update_company_user(
    db: Session, 
    user_id: int, 
    company_id: int, 
    user_update: schemas.UserUpdate
):
    """Actualizar usuario de empresa"""
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.company_id == company_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found in this company")
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

def deactivate_company_user(db: Session, user_id: int, company_id: int):
    """Desactivar usuario de empresa"""
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.company_id == company_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found in this company")
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}

def update_user_profile(
    db: Session, 
    user_id: int, 
    user_update: schemas.UserUpdate, 
    company_id: int
):
    """Actualizar perfil de usuario"""
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.company_id == company_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

def create_user_with_company(
    db: Session, 
    username: str, 
    email: str, 
    password: str, 
    company_id: int
):
    """Crear usuario con empresa específica"""
    hashed_password = hash_password(password)
    
    db_user = models.User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        company_id=company_id,
        role="user",
        is_company_admin=False,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user