from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from models import fake_users_db, User, Company
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
import database

# Instancia del contexto de password para el hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Función para encriptar la contraseña
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Función para verificar la contraseña
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Función para crear un JWT
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ⭐ FUNCIÓN MEJORADA PARA MULTIEMPRESA
def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Obtener información del token
        username: str = payload.get("sub")
        company_id: int = payload.get("company_id")

        if username is None or company_id is None:
            raise credentials_exception

        # ⭐ BUSCAR USUARIO CON EMPRESA ESPECÍFICA
        user = db.query(User).filter(
            User.username == username,
            User.company_id == company_id,
            User.is_active == True
        ).first()
        
        if user is None:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception

# ⭐ FUNCIÓN CORREGIDA - ACEPTA PARÁMETROS OPCIONALES
def check_permission(required_role: str = None, require_company_admin: bool = False):
    """Dependency para verificar permisos específicos"""
    def permission_checker(current_user: User = Depends(verify_token)):
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
            
        if require_company_admin and not current_user.is_company_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company admin privileges required"
            )
            
        if required_role:
            role_hierarchy = {"viewer": 1, "user": 2, "manager": 3, "admin": 4}
            user_level = role_hierarchy.get(current_user.role, 0)
            required_level = role_hierarchy.get(required_role, 4)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' or higher required"
                )
                
        return current_user
    return permission_checker

def authenticate_user(db: Session, username: str, password: str, company_tax_id: str = None):
    """Autenticar usuario con empresa opcional"""
    
    if company_tax_id:
        # Buscar por empresa específica
        user = db.query(User).join(Company).filter(
            User.username == username,
            Company.tax_id == company_tax_id.upper(),
            User.is_active == True,
            Company.is_active == True
        ).first()
    else:
        # Buscar primera empresa activa del usuario
        user = db.query(User).join(Company).filter(
            User.username == username,
            User.is_active == True,
            Company.is_active == True
        ).first()
    
    if not user or not verify_password(password, user.hashed_password):
        return None
        
    # Actualizar último login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

def create_user_with_company(
    db: Session, 
    username: str, 
    email: str, 
    password: str, 
    company_id: int,
    role: str = "user",
    is_company_admin: bool = False
):
    """Crear usuario asignado a una empresa"""
    
    # Verificar que no exista el usuario en esa empresa
    existing_user = db.query(User).filter(
        User.username == username,
        User.company_id == company_id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists in this company"
        )
    
    # Verificar email único en la empresa
    if email:
        existing_email = db.query(User).filter(
            User.email == email,
            User.company_id == company_id
        ).first()
        
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Email already exists in this company"
            )
    
    # Verificar que exista la empresa
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    hashed_password = hash_password(password)
    
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        company_id=company_id,
        role=role,
        is_company_admin=is_company_admin
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# Middleware para filtro automático por empresa
class CompanyFilter:
    def __init__(self, user: User):
        self.user = user
        self.company_id = user.company_id
        
    def filter_query(self, query, model):
        """Aplica filtro automático por empresa"""
        if hasattr(model, 'company_id'):
            return query.filter(model.company_id == self.company_id)
        return query

def get_current_company_filter(current_user: User = Depends(verify_token)):
    """Dependency para obtener el filtro de empresa actual"""
    return CompanyFilter(current_user)

# ⭐ MANTENER FUNCIÓN LEGACY PARA COMPATIBILIDAD
def get_user(db, username: str):
    """Función legacy - mantener por compatibilidad"""
    if isinstance(db, dict):
        # Para fake_users_db
        if username in db:
            user_data = db[username]
            return User(**user_data)
    else:
        # Para base de datos real
        user = db.query(User).filter(User.username == username).first()
        return user
    return None