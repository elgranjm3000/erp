from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas
import crud
import database
from auth import verify_token, check_permission
from models import Company, User
from typing import List

router = APIRouter()

# ================= GESTIÓN DE EMPRESAS =================

@router.post("/companies/", response_model=schemas.Company)
def create_company(
    company_data: schemas.CompanyCreate,
    db: Session = Depends(database.get_db)
):
    """Crear nueva empresa con usuario administrador"""
    return crud.create_company_with_admin(db, company_data)

@router.get("/companies/me", response_model=schemas.Company)
def get_my_company(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener información de mi empresa"""
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put("/companies/me", response_model=schemas.Company)
def update_my_company(
    company_update: schemas.CompanyUpdate,
    current_user: User = Depends(check_permission(require_company_admin=True)),
    db: Session = Depends(database.get_db)
):
    """Actualizar información de mi empresa (solo admin)"""
    return crud.update_company(db, current_user.company_id, company_update)

@router.get("/companies/me/dashboard", response_model=schemas.CompanyDashboard)
def get_company_dashboard(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Dashboard con métricas de la empresa"""
    return crud.get_company_dashboard(db, current_user.company_id)

@router.get("/companies/me/settings", response_model=schemas.CompanySettings)
def get_company_settings(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener configuraciones de la empresa"""
    return crud.get_company_settings(db, current_user.company_id)

@router.put("/companies/me/settings", response_model=schemas.CompanySettings)
def update_company_settings(
    settings: schemas.CompanySettings,
    current_user: User = Depends(check_permission(require_company_admin=True)),
    db: Session = Depends(database.get_db)
):
    """Actualizar configuraciones de la empresa"""
    return crud.update_company_settings(db, current_user.company_id, settings)

# ================= GESTIÓN DE USUARIOS DE LA EMPRESA =================

@router.get("/companies/me/users", response_model=List[schemas.User])
def get_company_users(
    current_user: User = Depends(check_permission(role="manager")),
    db: Session = Depends(database.get_db)
):
    """Listar usuarios de mi empresa"""
    return crud.get_company_users(db, current_user.company_id)

@router.post("/companies/me/users", response_model=schemas.User)
def create_company_user(
    user_data: schemas.UserCreateForCompany,
    current_user: User = Depends(check_permission(require_company_admin=True)),
    db: Session = Depends(database.get_db)
):
    """Crear nuevo usuario en mi empresa"""
    return crud.create_user_for_company(db, user_data, current_user.company_id)

@router.put("/companies/me/users/{user_id}", response_model=schemas.User)
def update_company_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    current_user: User = Depends(check_permission(require_company_admin=True)),
    db: Session = Depends(database.get_db)
):
    """Actualizar usuario de mi empresa"""
    return crud.update_company_user(db, user_id, current_user.company_id, user_update)

@router.delete("/companies/me/users/{user_id}")
def deactivate_company_user(
    user_id: int,
    current_user: User = Depends(check_permission(require_company_admin=True)),
    db: Session = Depends(database.get_db)
):
    """Desactivar usuario de mi empresa"""
    return crud.deactivate_company_user(db, user_id, current_user.company_id)

# ================= AUTENTICACIÓN MEJORADA =================

@router.post("/auth/login", response_model=schemas.LoginResponse)
def login_multicompany(
    login_data: schemas.LoginRequest,
    db: Session = Depends(database.get_db)
):
    """Login con soporte multiempresa"""
    return crud.authenticate_multicompany(db, login_data)

@router.post("/auth/register-company", response_model=schemas.LoginResponse)
def register_company_and_login(
    company_data: schemas.CompanyCreate,
    db: Session = Depends(database.get_db)
):
    """Registrar empresa y hacer login automático"""
    return crud.register_company_and_login(db, company_data)