from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import schemas
import crud
import database
from models import User
from auth import verify_token, check_permission, authenticate_user, create_access_token
from config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

# ================= AUTENTICACIÓN MULTIEMPRESA =================

@router.post("/auth/login", response_model=schemas.LoginResponse)
def login_multicompany(
    login_data: schemas.LoginRequest,
    db: Session = Depends(database.get_db)
):
    """Login con soporte multiempresa"""
    user = authenticate_user(
        db=db, 
        username=login_data.username, 
        password=login_data.password,
        company_tax_id=login_data.company_tax_id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or company",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar token con información de empresa
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
            company=user.company
        )
    )

# Login legacy para compatibilidad
@router.post("/login/", response_model=schemas.Token)
def login_legacy(
    username: str, 
    password: str, 
    db: Session = Depends(database.get_db)
):
    """Login legacy - busca primera empresa activa del usuario"""
    user = authenticate_user(db=db, username=username, password=password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar token
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
    
    return {"access_token": access_token, "token_type": "bearer"}

# ================= GESTIÓN DE PERFIL =================

@router.get("/users/me", response_model=schemas.UserWithCompany)
def read_users_me(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener información del usuario actual"""
    return schemas.UserWithCompany(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        company_id=current_user.company_id,
        is_active=current_user.is_active,
        is_company_admin=current_user.is_company_admin,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        company=current_user.company
    )

@router.put("/users/me", response_model=schemas.User)
def update_my_profile(
    user_update: schemas.UserUpdate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Actualizar mi perfil"""
    return crud.update_user_profile(
        db=db,
        user_id=current_user.id,
        user_update=user_update,
        company_id=current_user.company_id
    )

# ================= REGISTRO (Solo si la empresa permite) =================

@router.post("/users/", response_model=dict)
def create_new_user(
    username: str, 
    email: str,
    password: str, 
    current_user: User = Depends(check_permission(require_company_admin=True)),
    db: Session = Depends(database.get_db)
):
    """Crear nuevo usuario en mi empresa (solo admin)"""
    db_user = crud.create_user_with_company(
        db=db, 
        username=username,
        email=email,
        password=password,
        company_id=current_user.company_id
    )
    return {
        "id": db_user.id, 
        "username": db_user.username, 
        "email": db_user.email,
        "company_id": db_user.company_id
    }

# ================= ENDPOINTS PROTEGIDOS DE PRUEBA =================

@router.get("/protected")
def protected_route(current_user: User = Depends(verify_token)):
    """Endpoint protegido de prueba"""
    return {
        "message": f"Hello {current_user.username}",
        "company": current_user.company.name,
        "role": current_user.role,
        "is_admin": current_user.is_company_admin
    }

@router.get("/admin-only")
def admin_only_route(current_user: User = Depends(check_permission(require_company_admin=True))):
    """Endpoint solo para administradores de empresa"""
    return {
        "message": f"Welcome admin {current_user.username}",
        "company": current_user.company.name
    }

@router.get("/manager-only")
def manager_only_route(current_user: User = Depends(check_permission(required_role="manager"))):
    """Endpoint solo para managers o superior"""
    return {
        "message": f"Welcome manager {current_user.username}",
        "company": current_user.company.name,
        "role": current_user.role
    }