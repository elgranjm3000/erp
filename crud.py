from sqlalchemy.orm import Session
import models
import schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Funciones de productos
def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# Funciones de categorías
def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# Funciones de movimientos de inventario
def create_inventory_movement(db: Session, movement: schemas.InventoryMovementCreate):
    db_movement = models.InventoryMovement(**movement.dict())
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement

# Funciones de almacenes
def get_warehouses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Warehouse).offset(skip).limit(limit).all()

def create_warehouse(db: Session, warehouse: schemas.WarehouseCreate):
    db_warehouse = models.Warehouse(**warehouse.dict())
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse

# Hashear la contraseña
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Crear un nuevo usuario
def create_user(db: Session, username: str, password: str):
    hashed_password = hash_password(password)
    db_user = models.User(username=username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Autenticar usuario (verificar si existe y si la contraseña es correcta)
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user