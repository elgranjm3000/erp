from pydantic import BaseModel
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

# Import para evitar problemas de referencias circulares
if TYPE_CHECKING:
    from .schemas import Product, Category

# Esquema para el producto (sin categoría completa)
class ProductBase(BaseModel):
    name: str
    description: str
    price: int
    quantity: int
    category_id: int

class ProductCreate(ProductBase):
    pass

# Producto con referencia simple a la categoría
class Product(ProductBase):
    id: int
    category: Optional["CategoryBase"] = None  # Cambiar a CategoryBase para evitar ciclos

    class Config:
        from_attributes = True

# Esquema para la categoría (sin productos completos)
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

# Categoría con productos sin la referencia completa a la categoría
class Category(CategoryBase):
    id: int
    products: List[ProductBase] = []  # Cambiar a ProductBase para evitar ciclos

    class Config:
        from_attributes = True

# Esquema para el movimiento de inventario
class InventoryMovementBase(BaseModel):
    product_id: int
    movement_type: str
    quantity: int

class InventoryMovementCreate(InventoryMovementBase):
    pass

class InventoryMovement(InventoryMovementBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Esquema para almacén
class WarehouseBase(BaseModel):
    name: str
    location: str

class WarehouseCreate(WarehouseBase):
    pass

class Warehouse(WarehouseBase):
    id: int

    class Config:
        from_attributes = True

# Esquema para la creación de usuarios (si es necesario)
class UserCreate(BaseModel):
    username: str
    password: str

# Esquema para el login
class Login(BaseModel):
    username: str
    password: str

# Esquema para el token de acceso
class Token(BaseModel):
    access_token: str
    token_type: str
