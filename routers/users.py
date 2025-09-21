from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import schemas
import crud
import database
from models import User, Company
from auth import verify_token, check_permission, authenticate_user, create_access_token, hash_password
from config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

# ================= AUTENTICACIÓN MULTIEMPRESA =================

# ================= REGISTRO PÚBLICO DE COMPAÑÍA =================

@router.post("/auth/register-company")
def register_company_public(
    registration_data: schemas.CompanyRegistrationRequest,
    db: Session = Depends(database.get_db)
):
    """
    Registro público de compañía con usuario administrador
    No requiere autenticación previa - Respuesta simplificada
    """
    try:
        # 1. Verificar que el tax_id no exista
        existing_company = db.query(Company).filter(
            Company.tax_id == registration_data.company_tax_id.upper()
        ).first()
        
        if existing_company:
            raise HTTPException(
                status_code=400,
                detail="Company with this tax ID already exists"
            )
        
        # 2. Verificar que el username no exista globalmente
        existing_user = db.query(User).filter(
            User.username == registration_data.admin_username
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already exists. Please choose a different one."
            )
        
        # 3. Crear la compañía con valores por defecto
        new_company = Company(
            name=registration_data.company_name,
            legal_name=registration_data.company_name,
            tax_id=registration_data.company_tax_id.upper(),
            address=registration_data.company_address,
            phone=registration_data.company_phone,
            email=registration_data.company_email,
            currency="USD",
            timezone="UTC",
            date_format="YYYY-MM-DD",
            invoice_prefix="INV",
            next_invoice_number=1,
            logo_url=None,
            is_active=True
        )
        
        db.add(new_company)
        db.flush()
        
        # 4. Crear el usuario administrador
        hashed_password = hash_password(registration_data.admin_password)
        
        admin_user = User(
            username=registration_data.admin_username,
            email=registration_data.admin_email,
            hashed_password=hashed_password,
            company_id=new_company.id,
            role="admin",
            is_company_admin=True,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(new_company)
        db.refresh(admin_user)
        
        # 5. Generar token de acceso automático
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
        
        # 6. Respuesta simple sin esquemas complejos
        return {
            "success": True,
            "message": "Company and admin user created successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "company": {
                "id": new_company.id,
                "name": new_company.name,
                "tax_id": new_company.tax_id,
                "address": new_company.address
            },
            "user": {
                "id": admin_user.id,
                "username": admin_user.username,
                "email": admin_user.email,
                "role": admin_user.role,
                "is_company_admin": admin_user.is_company_admin
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating company: {str(e)}"
        )
# ================= VERIFICAR DISPONIBILIDAD =================

@router.get("/auth/check-company-tax-id/{tax_id}")
def check_company_tax_id_availability(
    tax_id: str,
    db: Session = Depends(database.get_db)
):
    """Verificar si un tax_id de compañía está disponible"""
    existing = db.query(Company).filter(
        Company.tax_id == tax_id.upper()
    ).first()
    
    return {
        "tax_id": tax_id.upper(),
        "available": existing is None,
        "message": "Tax ID is available" if existing is None else "Tax ID already exists"
    }

@router.get("/auth/check-username/{username}")
def check_username_availability(
    username: str,
    db: Session = Depends(database.get_db)
):
    """Verificar si un username está disponible"""
    existing = db.query(User).filter(
        User.username == username
    ).first()
    
    return {
        "username": username,
        "available": existing is None,
        "message": "Username is available" if existing is None else "Username already exists"
    }



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